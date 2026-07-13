import json
import sys


print(json.dumps({"args": sys.argv[1:], "status": "ok"}))
