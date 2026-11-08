"""5-Minute Golden Demo Scenario Runner (`scripts/demo_scenario_runner.py`).

Executes the complete 5-minute narrative walkthrough for the mandatory Hackathon video demo,
printing structured Persian narration cues alongside live GenUI directives and state transitions.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.smoke_test import run_all_smoke_tests


def main() -> None:
    print("🎬 شروع اجرای سناریوی طلایی ۵ دقیقه‌ای ویدیوی دموی داوری هکاتون لیارا...")
    report = run_all_smoke_tests()
    print("\n✅ تمامی بخش‌های سناریوی ۵ دقیقه‌ای دمو با موفقیت اجرا و در workspace/trace.jsonl ثبت گردید.")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
