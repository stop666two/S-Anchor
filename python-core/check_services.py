import urllib.request, sys

services = [
    ('Go', 'http://127.0.0.1:8080/api/health'),
    ('Python', 'http://127.0.0.1:9001/api/health'),
    ('Frontend', 'http://127.0.0.1:8000'),
]

all_ok = True
for name, url in services:
    try:
        r = urllib.request.urlopen(url, timeout=3)
        status = r.status
        if status == 200:
            print(f'       {name}:        OK')
        else:
            print(f'       {name}:        HTTP {status}')
    except Exception:
        print(f'       {name}:        OFFLINE')
        all_ok = False

sys.exit(0 if all_ok else 1)
