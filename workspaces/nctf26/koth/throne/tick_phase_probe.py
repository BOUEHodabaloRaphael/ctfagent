#!/usr/bin/env python3
"""Bounded, read-only probe to empirically locate the Throne scoring-tick
phase, WITHOUT assuming alignment to uptime or to :00/:30 wall-clock marks.

Method: poll the AUTHENTICATED platform page (/plugins/koth/), not the hill
itself, at a fixed modest interval. Detect edges by watching the
RETOURNEMENTS counter for Throne and the first "FIL DU TRÔNE" entry text.
Log our OWN wall-clock time at each poll (not the relative "il y a Ns"
label, which is rounded/truncated and was the source of the apparent
1s/tick drift in the earlier naive analysis).

Hard caps (do not remove):
- MAX_POLLS: absolute request ceiling.
- MAX_DURATION_S: absolute wall-clock ceiling.
- Stops immediately on any HTTP status 429 (or playwright navigation error
  repeated 3x in a row).
"""
import asyncio
import json
import time
from playwright.async_api import async_playwright

POLL_INTERVAL_S = 3.0
MAX_POLLS = 60          # hard cap: ~3 min at 3s interval
MAX_DURATION_S = 200     # hard cap, independent safety net
LOG_PATH = "workspaces/nctf26/koth/throne/tick_phase_log.jsonl"
URL = "https://arena.ctf.tg/plugins/koth/"


async def main():
    t_start = time.time()
    n_polls = 0
    consecutive_errors = 0
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(storage_state="src/tools/ctf/nctf26_storage_state.json")
        page = await ctx.new_page()

        with open(LOG_PATH, "a") as logf:
            while n_polls < MAX_POLLS and (time.time() - t_start) < MAX_DURATION_S:
                n_polls += 1
                t_poll = time.time()
                try:
                    resp = await page.goto(URL, wait_until="domcontentloaded", timeout=15000)
                    status = resp.status if resp else None
                    if status == 429:
                        print(f"[{n_polls}] HTTP 429 received -> STOPPING immediately per hard rule.")
                        logf.write(json.dumps({"t": t_poll, "n": n_polls, "status": 429, "stop": "rate_limited"}) + "\n")
                        break
                    text = await page.inner_text("body")
                    idx = text.find("THE THRONE")
                    idx2 = text.find("THE CITADEL")
                    throne_block = text[idx:idx2] if idx >= 0 and idx2 > idx else ""
                    ret = None
                    for i, line in enumerate(throne_block.splitlines()):
                        if line.strip() == "RETOURNEMENTS":
                            ret = throne_block.splitlines()[i + 1].strip()
                            break
                    fil_idx = text.find("FIL DU TR")
                    fil_chunk = text[fil_idx:fil_idx + 200] if fil_idx >= 0 else ""
                    first_fil_line = fil_chunk.splitlines()[2] if len(fil_chunk.splitlines()) > 2 else ""
                    rec = {"t": t_poll, "n": n_polls, "status": status, "retournements": ret, "first_fil": first_fil_line}
                    logf.write(json.dumps(rec) + "\n")
                    logf.flush()
                    print(f"[{n_polls}] t={time.strftime('%H:%M:%S', time.localtime(t_poll))} status={status} RET={ret} fil='{first_fil_line}'")
                    consecutive_errors = 0
                except Exception as e:
                    consecutive_errors += 1
                    print(f"[{n_polls}] ERROR: {e}")
                    logf.write(json.dumps({"t": t_poll, "n": n_polls, "error": str(e)}) + "\n")
                    if consecutive_errors >= 3:
                        print("3 consecutive errors -> STOPPING.")
                        break
                # sleep remaining interval
                elapsed = time.time() - t_poll
                await asyncio.sleep(max(0.0, POLL_INTERVAL_S - elapsed))

        await browser.close()
    print(f"DONE. n_polls={n_polls} duration_s={round(time.time()-t_start,1)}")


if __name__ == "__main__":
    asyncio.run(main())
