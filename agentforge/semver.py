"""Strict SemVer 2.0.0 parsing and precedence (build metadata is ignored)."""

import re
from functools import total_ordering
from .errors import AFError

RX = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?\Z")


@total_ordering
class Version:
    def __init__(self, value):
        m = RX.fullmatch(value) if isinstance(value, str) else None
        if not m:
            raise AFError("Invalid exact SemVer: " + str(value))
        self.core = tuple(map(int, m.group(1, 2, 3)))
        self.pre = tuple(m.group(4).split('.')) if m.group(4) else ()
        if any(x.isdigit() and len(x) > 1 and x.startswith('0') for x in self.pre):
            raise AFError("Numeric prerelease identifiers cannot have leading zeros")
        self.value = value

    def __eq__(self, other):
        return isinstance(other, Version) and (self.core, self.pre) == (other.core, other.pre)

    def __lt__(self, other):
        if self.core != other.core:
            return self.core < other.core
        if not self.pre or not other.pre:
            return bool(self.pre) and not other.pre
        for a, b in zip(self.pre, other.pre):
            if a == b:
                continue
            if a.isdigit() and b.isdigit():
                return int(a) < int(b)
            if a.isdigit() != b.isdigit():
                return a.isdigit()
            return a < b
        return len(self.pre) < len(other.pre)
