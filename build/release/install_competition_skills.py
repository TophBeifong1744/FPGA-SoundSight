"""Install the two local, reviewed skills without network or hardware access."""
import argparse
import json
from pathlib import Path
import shutil

NAMES = ("fpga-module-verification", "pynq-overlay-dma-validation")
EXCLUDED_DIRS = {"evidence", "history", "__pycache__", "results"}
EXCLUDED_FILES = {".gitattributes", "repair-manifest.json"}


def skill_files(root):
    for path in sorted(root.rglob("*")):
        if path.is_file():
            rel = path.relative_to(root)
            if not EXCLUDED_DIRS.intersection(rel.parts) and path.name not in EXCLUDED_FILES:
                if path.is_symlink():
                    raise ValueError("Symlink is not an installable source: " + str(path))
                yield path, rel


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skills-root", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    source, destination = args.skills_root.resolve(), args.destination.resolve()
    entries = []
    # Preflight both destinations before creating either skill. Do not overwrite
    # an existing installation or another task's local modification.
    for name in NAMES:
        if (destination / name).exists():
            parser.error("Existing installation preserved: " + str(destination / name))
        root = source / name
        if not (root / "SKILL.md").is_file() and not (root / "skill.md").is_file():
            parser.error("Missing source SKILL.md: " + name)
        for path, rel in skill_files(root):
            if rel.as_posix() == 'skill.md':
                rel = Path('SKILL.md')
            entries.append((path, destination / name / rel))
    for path, target in entries:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    for path, target in entries:
        if path.read_bytes() != target.read_bytes():
            raise RuntimeError("Installed bytes differ: " + str(target))
    print(json.dumps({"installed": list(NAMES), "files": len(entries),
                      "hardware_actions": 0, "network_used": False,
                      "content_verified": True}))


if __name__ == "__main__":
    main()

