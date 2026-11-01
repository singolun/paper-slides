#!/usr/bin/env python3
"""Inspect paper numbering and verify module integration without editing the project.

This is a conservative source checker, not a TeX parser, compiler, or math reviewer.
Only the snapshot subcommand writes a file: the explicitly requested JSON baseline.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


INCLUDE = re.compile(r"\\include\s*\{\s*contents/paper([1-9]\d*)(?:\.tex)?\s*\}")
GRAPHIC = re.compile(r"\\includegraphics\*?\s*(?:\[[^\]]*\]\s*)?\{([^{}]+)\}")


def uncomment(text):
    """Remove TeX comments, retaining line boundaries and escaped percent signs."""
    lines = []
    for line in text.splitlines(keepends=True):
        for index, char in enumerate(line):
            if char != "%":
                continue
            backslashes = 0
            cursor = index - 1
            while cursor >= 0 and line[cursor] == "\\":
                backslashes += 1
                cursor -= 1
            if backslashes % 2 == 0:
                line = line[:index] + ("\n" if line.endswith("\n") else "")
                break
        lines.append(line)
    return "".join(lines)


def read(path):
    return path.read_bytes().decode("utf-8")


def emit(result):
    print(json.dumps(result, ensure_ascii=False, indent=2))


def root_path(value):
    root = Path(value).expanduser().resolve()
    if not (root / "main.tex").is_file():
        raise ValueError(f"No main.tex at project root: {root}")
    for name in ("contents", "figures"):
        if not (root / name).is_dir():
            raise ValueError(f"Missing project directory: {root / name}")
    return root


def inspect(root):
    used = set()
    for folder, pattern in (("contents", r"paper([1-9]\d*)\.tex"),
                            ("figures", r"paper([1-9]\d*)")):
        for path in (root / folder).iterdir():
            match = re.fullmatch(pattern, path.name)
            if match:
                used.add(int(match.group(1)))
    includes = [int(m.group(1)) for m in INCLUDE.finditer(uncomment(read(root / "main.tex")))]
    used.update(includes)
    number = max(used, default=0) + 1
    return {"root": str(root), "used_numbers": sorted(used),
            "active_includes": includes, "suggested_next_number": number,
            "module": f"contents/paper{number}.tex", "figures": f"figures/paper{number}"}


def protected_files(root, number):
    """Hash template/configuration and every pre-existing non-target paper asset.

    Deliberately exclude build products and the skill package itself. Include new
    source/config/figure files in the comparison so adding a new theme is detected.
    """
    candidates = set()
    for path in root.iterdir():
        if path.is_file() and (path.suffix in {".sty", ".cls", ".tex", ".bib"}
                               or path.name in {"Makefile", "latexmkrc", ".latexmkrc", "latexindent.yaml"}):
            candidates.add(path)
    for name in ("contents", "figures", "vi", "src", "contrib", ".vscode"):
        folder = root / name
        if folder.is_dir():
            candidates.update(p for p in folder.rglob("*") if p.is_file())
    result = {}
    target = f"contents/paper{number}.tex"
    figure_prefix = f"figures/paper{number}/"
    for path in sorted(candidates):
        relative = path.relative_to(root).as_posix()
        if relative in {"main.tex", target} or relative.startswith(figure_prefix):
            continue
        result[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def snapshot(root, number, output):
    output = Path(output).expanduser().resolve()
    # Never accidentally overwrite a project source or a previous baseline.
    if output.suffix != ".json" or output.exists():
        raise ValueError("Baseline must be a new .json file; choose another --output path")
    if output.is_relative_to(root):
        raise ValueError("Save the baseline outside the project, for example under /tmp")
    data = {"version": 1, "root": str(root), "paper": number,
            "main": read(root / "main.tex"), "protected": protected_files(root, number),
            "target_existed": (root / f"contents/paper{number}.tex").exists()}
    with output.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    emit({"baseline": str(output), "protected_file_count": len(data["protected"]),
          "target_existed": data["target_existed"]})


def check_main(main, number, errors):
    clean = uncomment(main)
    matches = [m for m in INCLUDE.finditer(clean) if int(m.group(1)) == number]
    if len(matches) != 1:
        errors.append(f"main.tex must include contents/paper{number} exactly once; found {len(matches)}")
        return
    begin = clean.find(r"\begin{document}")
    end = clean.find(r"\end{document}")
    bottom = clean.find(r"\makebottom")
    if begin < 0 or end < 0 or not begin < matches[0].start() < end:
        errors.append("Target include must be inside the document body")
    if bottom >= 0 and matches[0].start() > bottom:
        errors.append("Target include must precede makebottom")


def compare_baseline(root, number, main, baseline, errors):
    data = json.loads(Path(baseline).read_text(encoding="utf-8"))
    if data.get("version") != 1 or data.get("root") != str(root) or data.get("paper") != number:
        raise ValueError("Baseline version, project root or paper number does not match")
    before = data["main"]
    existing = any(int(m.group(1)) == number for m in INCLUDE.finditer(uncomment(before)))
    if existing:
        same = main == before
    else:
        # Permit exactly one standalone include line, retaining every other byte.
        lines = main.splitlines(keepends=True)
        addition = re.compile(r"\s*\\include\{contents/paper" + str(number) + r"\}\s*")
        indices = [i for i, line in enumerate(lines) if addition.fullmatch(line)]
        same = len(indices) == 1 and "".join(line for i, line in enumerate(lines) if i != indices[0]) == before
        clean = uncomment(main)
        included = [int(m.group(1)) for m in INCLUDE.finditer(clean)]
        if included and included[-1] != number:
            errors.append("New paper include must follow the existing paper includes")
    if not same:
        errors.append("main.tex changed beyond the single permitted include addition")
    after = protected_files(root, number)
    for name in sorted(set(data["protected"]) | set(after)):
        if data["protected"].get(name) != after.get(name):
            errors.append(f"Protected source/asset added, changed or removed: {name}")


def check(root, number, baseline):
    errors, warnings = [], []
    module = root / f"contents/paper{number}.tex"
    main = read(root / "main.tex")
    check_main(main, number, errors)
    if baseline:
        compare_baseline(root, number, main, baseline, errors)
    else:
        warnings.append("No baseline supplied; template preservation is unverified")
    if not module.is_file():
        errors.append(f"Missing module: {module.relative_to(root)}")
        text = ""
    else:
        text = uncomment(read(module))
    forbidden = re.compile(
        r"\\(?:documentclass|usepackage|RequirePackage|usetheme|usecolortheme|usefonttheme|"
        r"setbeamertemplate|setbeamercolor|setbeamerfont|setmainfont|setsansfont|setmonofont|"
        r"setCJKmainfont|setCJKsansfont|setCJKmonofont|graphicspath|hypersetup|"
        r"AtBeginSection|AtBeginSubsection|appendix|includeonly|include|input|"
        r"maketitle|makebottom|titlepage|sectionpage|subsectionpage|tableofcontents|"
        r"title|subtitle|author|institute|date|subject|addbibresource)\b|"
        r"\\(?:begin|end)\s*\{document\}"
    )
    for match in forbidden.finditer(text):
        errors.append(f"Standalone/template/global command in module: {match.group()}")
    if len(re.findall(r"\\section(?:\[|\s*\{)", text)) != 1:
        errors.append("A paper module must have exactly one section")
    if not re.search(r"\\sectioninfo\s*\{", text):
        errors.append("Missing sectioninfo paper metadata")
    subsections = len(re.findall(r"\\subsection(?:\[|\s*\{)", text))
    if subsections < 2:
        errors.append("Organize the paper into multiple substantive subsections")
    frames = len(re.findall(r"\\begin\s*\{frame\}", text))
    if frames == 0 or frames != len(re.findall(r"\\end\s*\{frame\}", text)):
        errors.append("Missing or unbalanced frame environments")
    if re.search(r"\\tiny\b|\\begin\{frame\}\[[^\]]*\bshrink\b", text):
        errors.append("Do not solve density with tiny or frame[shrink]")
    if re.search(r"\b(?:TODO|TBD|PLACEHOLDER)\b|paperX/|在此(?:提出|给出|写出|记录)", text, re.I):
        errors.append("Unresolved scaffold placeholder in module")
    labels = re.findall(r"\\label\s*\{([^{}]+)\}", text)
    if len(labels) != len(set(labels)):
        errors.append("Duplicate labels in paper module")
    if any(not label.startswith(f"paper{number}:") for label in labels):
        warnings.append(f"Use paper{number}: prefixes for labels in a multi-paper deck")
    graphics = GRAPHIC.findall(text)
    figure_dir = (root / f"figures/paper{number}").resolve()
    for graphic in graphics:
        graphic = graphic.strip()
        if "\\" in graphic or "#" in graphic:
            warnings.append(f"Dynamic graphic path needs manual inspection: {graphic}")
            continue
        path = (root / "figures" / graphic).resolve()
        if not graphic.startswith(f"paper{number}/") or not path.is_relative_to(figure_dir):
            errors.append(f"Figure outside figures/paper{number}/: {graphic}")
        elif not path.is_file():
            errors.append(f"Missing figure: {graphic}")
        elif path.suffix.lower() in {".png", ".jpg", ".jpeg"}:
            warnings.append(f"Raster figure: verify original is raster and record rationale: {graphic}")
        elif path.suffix.lower() != ".pdf":
            errors.append(f"Use explicit .pdf or supported raster suffix: {graphic}")
    if not graphics:
        warnings.append("No includegraphics found; check that appropriate visual evidence is present")
    emit({"ok": not errors, "module": str(module), "frames": frames, "subsections": subsections,
          "graphics": len(graphics), "template_verified": bool(baseline) and not errors,
          "errors": errors, "warnings": warnings,
          "not_checked": ["mathematical correctness", "compilation", "rendered layout"]})
    return 1 if errors else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("inspect", "snapshot", "check"):
        command = sub.add_parser(name)
        command.add_argument("--root", default=".", help="Project directory containing main.tex")
        if name != "inspect":
            command.add_argument("--paper", type=int, required=True)
        if name == "snapshot":
            command.add_argument("--output", required=True, help="New baseline JSON outside project")
        if name == "check":
            command.add_argument("--baseline", help="JSON from snapshot, required to verify template preservation")
    args = parser.parse_args()
    try:
        root = root_path(args.root)
        if args.command != "inspect" and args.paper < 1:
            raise ValueError("Paper number must be a positive integer")
        if args.command == "inspect":
            emit(inspect(root))
        elif args.command == "snapshot":
            snapshot(root, args.paper, args.output)
        else:
            return check(root, args.paper, args.baseline)
    except (OSError, ValueError, KeyError) as error:
        emit({"ok": False, "error": str(error)})
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
