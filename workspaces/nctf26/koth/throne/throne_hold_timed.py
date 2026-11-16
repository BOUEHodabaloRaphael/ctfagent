#!/usr/bin/env python3
"""BOUNDED, non-flood timing-synchronized claim trial for The Throne.

Derived from measured data only (no arbitrary constants):
- period = 30.3814s (mean of 5 normalized gaps between 6 precise server
  event timestamps from /plugins/koth/api/state `events[]`, stdev 0.0804s)
- anchor_ts = 1794024980.204 (most recent precise event used in that fit)
- Cross-validation: extrapolating 7 periods forward from anchor_ts predicted
  tick at 1794025192.874, landing INSIDE an independently-measured
  request-bracket [1794025192.230, 1794025196.904] (width 4.674s) where a
  score jump (+5, Unkn0wn) was directly observed -- offset +0.644s from the
  bracket's early edge. THIS IS A SINGLE CROSS-VALIDATION POINT, not several
  independent confirmations. Treat the model as a hypothesis to test, not a
  proven schedule.

MARGIN (derived, not guessed):
  margin = max_observed_own_latency (1.515s, from 20 platform-API probe
           requests) + single cross-validation residual (0.644s)
         = 2.159s -> we fire the claim 2.2s before each predicted tick.
  This is a best-effort estimate from one data set; it may be wrong.

Hard caps (do not remove):
- MAX_CLAIMS: absolute ceiling on claim POSTs issued by this trial.
- MAX_DURATION_S: absolute wall-clock ceiling.
- Stops immediately on HTTP 429 from either the hill or the platform.
- Exactly ONE claim attempt per predicted tick (no retries/bursts to
  compensate for timing uncertainty).

After the trial, re-check /plugins/koth/api/state `top` list and `events`
for Th3N00bs to see whether any predicted-tick claim actually scored.
If not, the honest conclusion is: phase not confirmed precisely enough,
report that plainly rather than re-running with a smaller margin.
"""
import hmac, hashlib, time, json, urllib.request, urllib.error

HILL_KEY = b"d2e775a9aa7633e140a43cb6998778e7c63f7abeb4e3f583"  # from /debug leak
TEAM = "b792a5aa3c4babf5"  # our team token (masked-equivalent: safe, it's OUR own public claim token)
URL = "http://13.37.197.230:28490/throne"

PERIOD_S = 30.3814
ANCHOR_TS = 1794024980.204
MARGIN_S = 2.159  # derived above; not arbitrary

MAX_CLAIMS = 12         # hard cap: ~6 minutes of ticks at this period
MAX_DURATION_S = 420     # independent safety net
LOG_PATH = "workspaces/nctf26/koth/throne/timed_claims_log.jsonl"


def next_tick_after(now: float) -> float:
    k = int((now - ANCHOR_TS) // PERIOD_S) + 1
    return ANCHOR_TS + k * PERIOD_S


def claim():
    ts = int(time.time())
    sig = hmac.new(HILL_KEY, f"{TEAM}|{ts}".encode(), hashlib.sha1).hexdigest()
    body = json.dumps({"team": TEAM, "ts": ts, "sig": sig}).encode()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"}, method="POST")
    t0 = time.time()
    try:
        resp = urllib.request.urlopen(req, timeout=5)
        t1 = time.time()
        return t0, t1, resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        t1 = time.time()
        return t0, t1, e.code, e.read().decode()
    except Exception as e:
        t1 = time.time()
        return t0, t1, None, str(e)


def main():
    t_start = time.time()
    n = 0
    with open(LOG_PATH, "a") as logf:
        while n < MAX_CLAIMS and (time.time() - t_start) < MAX_DURATION_S:
            target_tick = next_tick_after(time.time())
            fire_at = target_tick - MARGIN_S
            sleep_s = fire_at - time.time()
            if sleep_s > 0:
                time.sleep(sleep_s)
            n += 1
            t0, t1, status, body = claim()
            rec = {"n": n, "predicted_tick": target_tick, "fire_at": fire_at,
                   "t0": t0, "t1": t1, "status": status, "body": body}
            logf.write(json.dumps(rec) + "\n")
            logf.flush()
            print(f"[{n}] predicted_tick={target_tick:.3f} fired=[{t0:.3f},{t1:.3f}] status={status} {body}")
            if status == 429:
                print("HTTP 429 -> STOPPING immediately.")
                break
            # sleep past this tick before computing the next one
            time.sleep(max(0.0, target_tick + 1.0 - time.time()))
    print(f"DONE n={n} duration={round(time.time()-t_start,1)}s")


if __name__ == "__main__":
    main()
