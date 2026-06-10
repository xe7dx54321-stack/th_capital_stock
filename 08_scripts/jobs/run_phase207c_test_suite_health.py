import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

from smr_phase207c_test_suite_health import main


if __name__ == "__main__":
    raise SystemExit(main())
