"""Bounded input and filesystem primitives. No archive extractall, hooks or shell."""

import hashlib
import io
import json
import os
import re
import stat
import unicodedata
import uuid
import zipfile
from pathlib import Path
from .errors import AFError

MAX_FILE = 2 * 1024 * 1024
MAX_TOTAL = 16 * 1024 * 1024
MAX_FILES = 512
RESERVED = re.compile(r'^(CON|PRN|AUX|NUL|COM[1-9¹²³]|LPT[1-9¹²³])(?:\.|$)', re.I)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def relative(value):
    if not isinstance(value, str) or not value or len(value) > 200:
        raise AFError('Invalid relative path', 5)
    if '\\' in value or any(ord(c) < 32 for c in value) or any(c in value for c in ':<>"|?*'):
        raise AFError('Unsafe path: ' + value, 5)
    parts = value.split('/')
    if any(p in ('', '.', '..') or p.endswith((' ', '.')) or RESERVED.match(p) or len(p) > 100 for p in parts):
        raise AFError('Unsafe path: ' + value, 5)
    return value


def no_links(path):
    """Reject links/reparse points in ALL existing ancestors, before resolving."""
    path = Path(os.path.abspath(path))
    for p in (path, *path.parents):
        if p.exists() or p.is_symlink():
            s = p.lstat()
            if stat.S_ISLNK(s.st_mode) or getattr(s, 'st_file_attributes', 0) & 0x400:
                raise AFError('Links/reparse points are not managed: ' + p.name, 5)
    return path


def within(root, rel):
    relative(rel)
    root = no_links(root)
    p = no_links(root / rel)
    if not p.is_relative_to(root):
        raise AFError('Path escapes target root', 5)
    return p


def read_bytes(path, limit=MAX_FILE):
    path = no_links(path)
    s = path.stat()
    if not stat.S_ISREG(s.st_mode) or s.st_nlink != 1 or s.st_size > limit:
        raise AFError('Non-regular, linked or oversized file: ' + path.name, 5)
    with path.open('rb') as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise AFError('File exceeds size limit', 5)
    return data


def parse_json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise AFError('Duplicate JSON key: ' + key)
            result[key] = value
        return result
    try:
        return json.loads(data, object_pairs_hook=pairs, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise AFError('Invalid JSON') from exc


def read_json(path):
    return parse_json(read_bytes(path))


def atomic_json(path, value):
    path = no_links(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name('.' + path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temp.open('xb') as f:
            f.write(canonical(value))
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def tree(root):
    root = no_links(root)
    if not root.is_dir():
        raise AFError('Expected directory: ' + root.name, 3)
    result, seen, total = {}, set(), 0
    for p in sorted(root.rglob('*')):
        no_links(p)
        rel = relative(p.relative_to(root).as_posix())
        key = unicodedata.normalize('NFC', rel).casefold()
        if key in seen:
            raise AFError('Case/Unicode path collision: ' + rel, 5)
        seen.add(key)
        if p.is_dir():
            result[rel + '/'] = 'directory'
        else:
            data = read_bytes(p)
            total += len(data)
            result[rel] = digest(data)
        if len(result) > MAX_FILES or total > MAX_TOTAL:
            raise AFError('Tree exceeds file/size limits', 5)
    return result


def safe_zip(data, destination):
    if len(data) > MAX_TOTAL:
        raise AFError('Archive too large', 5)
    destination = no_links(destination)
    if destination.exists():
        raise AFError('Extraction target must be new', 3)
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
        items, seen, size = [], set(), 0
        if len(z.infolist()) > MAX_FILES:
            raise AFError('Too many archive entries', 5)
        for item in z.infolist():
            rel = relative(item.filename.rstrip('/'))
            key = unicodedata.normalize('NFC', rel).casefold()
            mode = item.external_attr >> 16
            kind = stat.S_IFMT(mode)
            if key in seen or kind not in (0, stat.S_IFREG, stat.S_IFDIR) or item.flag_bits & 1:
                raise AFError('Duplicate, encrypted or special archive entry', 5)
            seen.add(key)
            if item.file_size > MAX_FILE or item.file_size > max(1, item.compress_size) * 100:
                raise AFError('Archive expansion limit', 5)
            size += item.file_size
            if size > MAX_TOTAL:
                raise AFError('Archive total size limit', 5)
            items.append((item, rel))
        for item, rel in items:
            for parent in Path(rel).parents:
                if str(parent) != '.' and any(r.casefold() == parent.as_posix().casefold() and not i.is_dir() for i, r in items):
                    raise AFError('Archive file/directory collision', 5)
        destination.mkdir(parents=True)
        for item, rel in items:
            p = within(destination, rel)
            if item.is_dir():
                p.mkdir(parents=True, exist_ok=True)
            else:
                p.parent.mkdir(parents=True, exist_ok=True)
                with p.open('xb') as f:
                    f.write(z.read(item))
        tree(destination)
    except (zipfile.BadZipFile, RuntimeError, OSError) as exc:
        raise AFError('Invalid archive or extraction failed', 5) from exc
