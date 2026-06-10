import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

from smr_phase207c_test_suite_health import build_backlog_update


def main():
    result = build_backlog_update()
    if "--markdown" in sys.argv and "phase207c_test_health_brief" in result:
        print(result["phase207c_test_health_brief"]["markdown"])
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
