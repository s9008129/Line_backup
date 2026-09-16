#!/usr/bin/env python3
import argparse, json, os, time
p = argparse.ArgumentParser()
p.add_argument('--counter')
p.add_argument('--outcome')
p.add_argument('--crash-after-dispatch', action='store_true')
n = p.parse_args()
with open(n.counter, 'a', encoding='utf-8') as fh:
    fh.write(json.dumps({'outcome': n.outcome, 'pid': os.getpid(), 'ppid': os.getppid(),
                         'at': time.time()}) + '\n')
open('/private/tmp/line-backup-acceptance-case-01/dispatch-started.barrier', 'w').close()
parent = os.getppid()
deadline = time.time() + 300.0
while time.time() < deadline:
    if os.getppid() != parent:
        raise SystemExit(3)
    try:
        os.kill(parent, 0)
    except OSError:
        raise SystemExit(3)
    time.sleep(0.25)
raise SystemExit(4)
