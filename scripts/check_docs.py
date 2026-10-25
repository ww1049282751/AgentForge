"""Lightweight checks for the personal skill collection; no third-party dependencies.

This validates structure, not complete YAML, Markdown anchors, source truth,
host invocation, or model behavior. It never reads private .local materials.
"""
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def blank(text):
    return re.sub(r"[^\n]", " ", text)


def markdown_prose(text):
    """Mask code and comments before inspecting common inline Markdown links."""
    lines = []
    fence = None
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line.rstrip("\r\n"))
        if fence:
            lines.append(blank(line))
            if (marker and marker[1][0] == fence[0] and len(marker[1]) >= fence[1]
                    and not marker[2].strip()):
                fence = None
        elif marker and (marker[1][0] != "`" or "`" not in marker[2]):
            fence = (marker[1][0], len(marker[1]))
            lines.append(blank(line))
        elif line.startswith(("    ", "\t")):
            lines.append(blank(line))
        else:
            lines.append(line)
    text = "".join(lines)
    text = re.sub(r"<!--.*?-->", lambda m: blank(m[0]), text, flags=re.S)
    return re.sub(r"(?<!`)(`+)(?!`)(.*?)(?<!`)\1(?!`)",
                  lambda m: blank(m[0]), text, flags=re.S)


def markdown_destinations(text):
    """Read inline links/images with escaped/balanced paths and optional titles.

    This is deliberately not a complete CommonMark parser: reference links,
    HTML links, block-container nesting and heading anchors are not validated.
    """
    text = markdown_prose(text)
    for match in re.finditer(r"(?<!\\)\[(?:\\.|[^\]\\\n])*\]\(", text):
        i = match.end()
        while i < len(text) and text[i].isspace():
            i += 1
        destination = []
        if i < len(text) and text[i] == "<":
            i += 1
            while i < len(text) and text[i] not in ">\n<":
                if text[i] == "\\" and i + 1 < len(text):
                    i += 1
                destination.append(text[i])
                i += 1
            if i >= len(text) or text[i] != ">":
                continue
            i += 1
        else:
            depth = 0
            while i < len(text):
                char = text[i]
                if char == "\\" and i + 1 < len(text):
                    destination.append(text[i + 1])
                    i += 2
                    continue
                if char.isspace() or (char == ")" and depth == 0):
                    break
                if char == "(":
                    depth += 1
                elif char == ")":
                    depth -= 1
                destination.append(char)
                i += 1
            if depth:
                continue
        end_destination = i
        while i < len(text) and text[i].isspace():
            i += 1
        if i > end_destination and i < len(text) and text[i] in "\"'(":
            closing = ")" if text[i] == "(" else text[i]
            i += 1
            while i < len(text) and text[i] != closing:
                if text[i] == "\\" and i + 1 < len(text):
                    i += 1
                i += 1
            if i >= len(text):
                continue
            i += 1
            while i < len(text) and text[i].isspace():
                i += 1
        if i < len(text) and text[i] == ")":
            yield "".join(destination)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_repo(root):
    root = Path(root).resolve()
    skills_dir = root / "skills"
    require(skills_dir.is_dir(), "Missing skills directory")
    skills = sorted(p for p in skills_dir.iterdir() if p.is_dir() and not p.name.startswith("."))
    require(skills, "No skill directories found")
    names = set()
    scenario_count = 0

    for skill in skills:
        require(skill.resolve().is_relative_to(root), "Skill directory escapes repository")
        entry = skill / "SKILL.md"
        require(entry.is_file(), f"Missing entry: {skill.name}/SKILL.md")
        text = entry.read_text(encoding="utf-8")
        front = re.match(r"\A---\n(.*?)\n---(?:\n|$)", text, re.S)
        require(front is not None, f"Missing frontmatter: {skill.name}")
        values = {}
        for field in ("name", "description"):
            found = re.findall(rf"^{field}:[ \t]*(.*)$", front[1], re.M)
            require(len(found) == 1, f"Expected one {field}: {skill.name}")
            value = found[0].strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1]
            require(value and value not in ("|", ">", "|-", ">-", "|+", ">+"),
                    f"{field} must be non-empty single-line text: {skill.name}")
            values[field] = value
        name = values["name"]
        require(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) and len(name) <= 64,
                f"Invalid skill name: {name}")
        require(name not in names, f"Duplicate skill name: {name}")
        require(name == skill.name, f"Skill name differs from directory: {skill.name}")
        names.add(name)

        scenarios = skill / "evals/scenarios.json"
        if scenarios.exists():
            data = json.loads(scenarios.read_text(encoding="utf-8"))
            require(isinstance(data, dict), f"Scenario document must be an object: {skill.name}")
            cases = data.get("cases")
            require(isinstance(cases, list) and cases, f"No scenario cases: {skill.name}")
            ids = set()
            for case in cases:
                require(isinstance(case, dict), f"Scenario must be an object: {skill.name}")
                case_id = case.get("id")
                require(isinstance(case_id, str) and case_id.strip() and case_id not in ids,
                        f"Missing or duplicate scenario id: {skill.name}")
                ids.add(case_id)
                request = case.get("request")
                expected = case.get("expected")
                require(isinstance(request, str) and request.strip(),
                        f"Missing scenario request: {skill.name}/{case_id}")
                require(isinstance(case.get("shouldTrigger"), bool),
                        f"Invalid trigger flag: {skill.name}/{case_id}")
                require(isinstance(expected, list) and expected
                        and all(isinstance(item, str) and item.strip() for item in expected),
                        f"Missing expected behavior: {skill.name}/{case_id}")
                if "inputFiles" in case:
                    inputs = case["inputFiles"]
                    require(isinstance(inputs, list) and inputs
                            and all(isinstance(item, str) and item.strip() for item in inputs),
                            f"Invalid input files: {skill.name}/{case_id}")
                    for item in inputs:
                        material = (scenarios.parent / item).resolve()
                        require(material.is_relative_to(skill.resolve()) and material.is_file(),
                                f"Missing or external scenario input: {skill.name}/{case_id} -> {item}")
            scenario_count += len(cases)

    files = [root / name for name in ("README.md", "AGENTS.md", "CHANGELOG.md")]
    for folder in ("docs", "skills"):
        files.extend(sorted((root / folder).rglob("*.md")))
    checked = 0
    for path in files:
        require(path.is_file() and path.resolve().is_relative_to(root),
                f"Missing or external Markdown file: {path}")
        text = path.read_text(encoding="utf-8")
        for link in markdown_destinations(text):
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = (path.parent / unquote(parsed.path)).resolve()
            require(target.is_relative_to(root) and target.exists(),
                    f"Broken or external local link: {path.relative_to(root)} -> {link}")
            checked += 1
    return {
        "skills": len(skills),
        "markdownFiles": len(files),
        "localLinks": checked,
        "skillScenarios": scenario_count,
        "semanticOrModelEvaluation": False,
    }


if __name__ == "__main__":
    try:
        print(json.dumps(check_repo(ROOT), ensure_ascii=False, indent=2))
    except (ValueError, OSError) as error:
        print(f"Validation failed: {error}", file=sys.stderr)
        raise SystemExit(1)
