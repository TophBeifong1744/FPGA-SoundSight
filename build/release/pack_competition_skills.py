"""导出两个自包含比赛 Skill；不运行 EDA，不读取旧仓库或本机工具配置。"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SUBMISSION = (ROOT / 'file-map.json').is_file()
if SUBMISSION:
    ROOT = ROOT.parent
    _mapping = json.loads((ROOT/'build/file-map.json').read_text('utf-8'))
    _inputs = {r['source_path']: ROOT/r['restore_path'] for r in _mapping['files']}


def locate(relative):
    if not SUBMISSION:
        return ROOT/relative
    if relative in _inputs:
        return _inputs[relative]
    for old,new in (('research/competition-skills','skill'),('document/evidence','data/evidence')):
        if relative == old or relative.startswith(old+'/'):
            return ROOT/(new+relative[len(old):])
    raise FileNotFoundError('Submission input missing: '+relative)
SKILLS = ("fpga-module-verification", "pynq-overlay-dma-validation")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ("board/output/soundsight-competition-skills.zip" if SUBMISSION else "release/output/soundsight-competition-skills.zip"))
    args = parser.parse_args()
    target = args.output.resolve()
    if target.exists():
        parser.error("目标包已存在；选新文件名或核实旧包用途结束后再移除，不自动覆盖")
    entries, sources = {}, []

    def add(path, name, rename_references=False):
        name = name.lower()
        if not re.fullmatch(r"[a-z0-9_./-]+", name) or ".." in Path(name).parts or name in entries:
            raise ValueError("非法/重复导出路径: " + name)
        raw = path.read_bytes()
        data = raw
        if rename_references and path.suffix == ".md":
            text = raw.decode("utf-8-sig")
            # 只映射入口/说明/许可证名称，历史日志内容不改写。
            for old, new in (("SKILL.md", "skill.md"), ("README.md", "readme.md"), ("LICENSE.txt", "license.txt")):
                text = text.replace("](" + old + ")", "](" + new + ")")
            data = text.encode("utf-8")
        entries[name] = data
        sources.append({"source": path.relative_to(ROOT).as_posix(), "export": name,
                        "source_sha256": hashlib.sha256(raw).hexdigest(),
                        "export_sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})

    for skill in SKILLS:
        directory = locate("research/competition-skills/" + skill)
        for path in sorted(directory.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(directory)
            if {"evidence", "history", "__pycache__", "results"} & set(rel.parts) or path.name in {".gitattributes", "repair-manifest.json"}:
                continue
            add(path, "skills/" + skill + "/" + rel.as_posix(), rename_references="history" not in rel.parts)
    add(locate("release/check_competition_skills.py"), "check_competition_skills.py")
    add(locate("release/competition-skills-readme.md"), "readme.md")
    add(locate("document/competition-skills-ai-corrections.md"), "ai-corrections.md")
    add(locate("LICENSE"), "license.txt")
    evidence = locate("document/evidence/competition-skills-20261018")
    # 交付包保留本次实际首错及重测，不复制整个历史数据库或仿真缓存。
    for name in ("before-migration.json", "before-migration-unit.log"):
        add(evidence / name, "evidence/history-20261018/" + name)
    for path in sorted((evidence / "source-run").rglob("*")):
        if path.is_file():
            add(path, "evidence/history-20261018/source-run/" + path.relative_to(evidence / "source-run").as_posix())
    current = locate("document/evidence/competition-skills-20261104")
    # Keep executed source checks, not transient extraction/install directories.
    for name in ("README.md", "session-contract.json", "session-audit.json"):
        add(current / (name.lower() if SUBMISSION else name), "evidence/current-20261104/" + name)
    add(locate("document/evidence/final-board-20261103/original/speaker-3d-20211119-121119-401147.json"),
        "evidence/current-20261104/session-input.json")
    for path in sorted((current / "source-run-final").rglob("*")):
        if path.is_file():
            add(path, "evidence/current-20261104/source-run/" + path.relative_to(current / "source-run-final").as_posix())
    entries["source-map.json"] = (json.dumps({"files": sources, "scope": "packaging provenance, not hardware identity"}, ensure_ascii=False, indent=2) + "\n").encode()
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(entries.items()):
            info = zipfile.ZipInfo(name, (2026, 11, 4, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    with zipfile.ZipFile(target) as archive:
        if archive.testzip() is not None or set(archive.namelist()) != set(entries):
            raise RuntimeError("ZIP 内容校验失败")
        if any(archive.read(name) != data for name, data in entries.items()):
            raise RuntimeError("ZIP 导出字节不一致")
    print(json.dumps({"archive": str(target), "files": len(entries), "bytes": target.stat().st_size,
                      "sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "board": "NOT_RUN"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
