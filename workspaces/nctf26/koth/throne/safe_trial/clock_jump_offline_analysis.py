#!/usr/bin/env python3
"""Offline analysis (NO network) of the clock-jump guard in
throne_hold_timed_safe.py. Replicates the exact check used there:

    mono_now, wall_now = time.monotonic(), time.time()
    if abs(wall_now - (wall0 + mono_now - mono0)) > 0.25:
        -> stop

but brackets EVERY wall_now reading with two monotonic reads (before and
after) to tell apart:
  (a) a TRUE wall-clock jump (e.g. NTP step): monotonic progresses normally
      and smoothly across the bracket, only wall jumps.
  (b) a PROCESS/SANDBOX PAUSE (descheduled, suspended, migrated): the gap
      between consecutive monotonic readings themselves is anomalously
      large (bigger than the sleep we asked for), meaning the whole
      process was stalled, not just the wall clock skewing.

Same sleep pattern as the real script's wait loop (<=0.2s increments) for
~90s, matching the duration of the executed trial. No requests sent.
"""
import json
import time

DURATION_S = 90
SLEEP_STEP_S = 0.2
LOG_PATH = "workspaces/nctf26/koth/throne/safe_trial/clock_jump_offline_log.jsonl"
GUARD_THRESHOLD_S = 0.25


def main():
    wall0 = time.time()
    mono0 = time.monotonic()
    prev_mono_after = mono0
    n = 0
    anomalies = []
    with open(LOG_PATH, "w") as logf:
        t_end_mono = mono0 + DURATION_S
        while time.monotonic() < t_end_mono:
            n += 1
            mono_before = time.monotonic()
            wall_now = time.time()
            mono_after = time.monotonic()

            # Same formula as the real guard:
            skew = wall_now - (wall0 + mono_before - mono0)
            # Gap between consecutive monotonic observations across loop
            # iterations: should be close to SLEEP_STEP_S if the process
            # ran continuously; a much bigger gap means the process itself
            # was stalled between iterations (sandbox pause), independent
            # of any wall-clock skew.
            inter_iteration_mono_gap = mono_before - prev_mono_after
            # Width of the bracket around this single wall_now read.
            bracket_width = mono_after - mono_before

            rec = {
                "n": n,
                "mono_before": mono_before,
                "wall_now": wall_now,
                "mono_after": mono_after,
                "bracket_width_s": bracket_width,
                "inter_iteration_mono_gap_s": inter_iteration_mono_gap,
                "skew_vs_guard_formula_s": skew,
                "would_trigger_guard": abs(skew) > GUARD_THRESHOLD_S,
            }
            logf.write(json.dumps(rec) + "\n")
            if abs(skew) > GUARD_THRESHOLD_S or inter_iteration_mono_gap > (SLEEP_STEP_S * 2):
                anomalies.append(rec)
                print(f"[{n}] ANOMALY: skew={skew:.4f}s inter_gap={inter_iteration_mono_gap:.4f}s "
                      f"bracket_width={bracket_width:.4f}s")
            prev_mono_after = mono_after
            time.sleep(SLEEP_STEP_S)
    print(f"DONE n_iterations={n} anomalies={len(anomalies)}")
    if anomalies:
        print("See", LOG_PATH, "for full detail; anomalies list above has the key numbers.")
    else:
        print("No anomaly reproduced in this offline run (no network, isolated timing loop).")


if __name__ == "__main__":
    main()
