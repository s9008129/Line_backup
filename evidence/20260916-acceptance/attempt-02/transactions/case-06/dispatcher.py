#!/usr/bin/env python3
import argparse, json
p=argparse.ArgumentParser(); p.add_argument('--counter'); p.add_argument('--outcome'); p.add_argument('--crash-after-dispatch', action='store_true'); n=p.parse_args()
with open(n.counter, 'a', encoding='utf-8') as f: f.write(json.dumps({'outcome': n.outcome})+'\n')
raise SystemExit(1 if n.crash_after_dispatch else 0)
