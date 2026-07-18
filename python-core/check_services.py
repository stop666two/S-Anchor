import sys
import time
import urllib.request

services = [
    ('Go', 'http://127.0.0.1:8080/api/health'),
    ('Python', 'http://127.0.0.1:9001/api/health'),
    ('Frontend', 'http://127.0.0.1:8000'),
]

all_ok = True
for name, url in services:
    ok = False
    for attempt in range(3):
        try:
            r = urllib.request.urlopen(url, timeout=3)
            if r.status == 200:
                print(f'       {name}:        OK')
                ok = True
                break
        except Exception:
            if attempt < 2:
                time.sleep(2)
    if not ok:
        print(f'       {name}:        OFFLINE')
        all_ok = False

sys.exit(0 if all_ok else 1)
