"""
System State Analyzer — generates system_state.json ground truth.

Canonical invocation (from repo root):
    python scripts/state_analyzer/analyzer.py

setup.bat and run.bat are the authoritative entrypoints for this project.
Both delegate to scripts/manager.py, which is parsed automatically — no
--manual-docker-files flag required for this repo.
"""

import json
import os
import sys
import argparse

# Allow running from any working directory
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from code_reader import CodeReader
from docker_reader import DockerReader
from builder import StateBuilder


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Generate system_state.json — a deterministic ground-truth snapshot.\n"
            "setup.bat and run.bat are treated as canonical entrypoints; "
            "scripts/manager.py is always parsed for Docker configuration."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--root",
        default=os.path.abspath(os.path.join(_HERE, "../.."))
,
        help="Repo root directory (default: two levels up from this script)",
    )
    parser.add_argument(
        "--manual-docker-files",
        nargs="*",
        metavar="FILE",
        help="Additional files to scan for docker commands (on top of manager.py)",
    )
    parser.add_argument(
        "--output",
        default="system_state.json",
        help="Output filename, relative to --root (default: system_state.json)",
    )
    parser.add_argument(
        "--max-size-mb",
        type=int,
        default=5,
        help="Skip files larger than this (MB). Default: 5",
    )
    args = parser.parse_args()

    root_dir = os.path.abspath(args.root)
    print(f"\n{'='*60}")
    print(f"  Breeding Vat \u2014 System State Analyzer")
    print(f"{'='*60}")
    print(f"  Root : {root_dir}")
    print(f"  Limit: {args.max_size_mb} MB per file")
    print(f"{'='*60}\n")

    # \u2500\u2500 Step 1: Code & docs \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    print("[1/3] Reading code and documentation...")
    code_reader = CodeReader(root_dir, max_file_size_mb=args.max_size_mb)
    code_reader.analyze_repo()
    code_results = code_reader.get_results()
    code_results["_root_dir"] = root_dir   # pass through for contradiction checks
    print(f"      {len(code_results['modules'])} modules  |  "
          f"{len(code_results['intent_from_md'])} intent docs  |  "
          f"{len(code_results['skipped_files'])} skipped")

    # \u2500\u2500 Step 2: Docker \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    print("\n[2/3] Inspecting Docker setup (via scripts/manager.py)...")
    docker_reader = DockerReader(root_dir, max_file_size_mb=args.max_size_mb)

    # Always include the canonical bat files for intent scanning
    for canon in ("setup.bat", "run.bat"):
        docker_reader.analyze_specific_file(canon)

    if args.manual_docker_files:
        for f in args.manual_docker_files:
            docker_reader.analyze_specific_file(f)

    docker_reader.analyze_runtime()   # parses manager.py + Dockerfiles + live docker ps
    docker_results = docker_reader.get_results()

    ri = docker_results.get("required_images", {})
    bs = docker_results.get("runtime_truth", {}).get("image_build_status", {})
    built   = sum(1 for v in bs.values() if v == "built")
    missing = sum(1 for v in bs.values() if v == "MISSING")
    print(f"      {len(ri)} required images  |  "
          f"{built} built  |  {missing} missing")

    # \u2500\u2500 Step 3: Build state \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    print("\n[3/3] Building unified state...")
    builder = StateBuilder(code_results, docker_results)
    system_state = builder.build()

    # \u2500\u2500 Output \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    output_path = os.path.join(root_dir, args.output)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(system_state, f, indent=2, default=str)

    sh = system_state["structural_health"]
    print(f"\n{'='*60}")
    print(f"  Output : {output_path}")
    print(f"  Modules: {len(system_state['modules'])}")
    print(f"  Broken imports  : {sh.get('total_broken', 0)}")
    print(f"  Parse errors    : {sh.get('total_parse_errors', 0)}")
    print(f"  Orphan suspects : {len(system_state['orphan_suspects'])}")
    print(f"  Contradictions  : {len(system_state['contradictions'])}")
    recs = system_state["review_recommendations"]
    crit = sum(1 for r in recs if r["priority"] == "critical")
    high = sum(1 for r in recs if r["priority"] == "high")
    print(f"  Recommendations : {len(recs)}  ({crit} critical  {high} high)")
    print(f"{'='*60}\n")

    if crit:
        print("  \u26a0  CRITICAL actions required \u2014 see review_recommendations in output.")
    elif high:
        print("  \u26a1 High-priority issues found \u2014 review broken imports.")
    else:
        print("  \u2713  No critical issues detected.")

    print()


if __name__ == "__main__":
    main()
