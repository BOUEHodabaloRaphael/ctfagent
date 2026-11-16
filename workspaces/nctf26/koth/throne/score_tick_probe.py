#!/usr/bin/env python3
"""Bounded, read-only probe against the authenticated JSON API
`/plugins/koth/api/state` to directly observe Throne-only team score jumps
(the `top` list inside hills[id=koth-throne]), bracketing each poll with
its own request start/end time. Goal: confirm whether +5 jumps happen on a
stable ~30s cadence, and record the observation-time bracket vs any
`events[].ts` (server-side event timestamp) for the same transition,
distinguishing publication/display delay from the event's own timestamp.

Hard caps:
- MAX_POLLS (absolute request ceiling)
- MAX_DURATION_S (absolute wall-clock ceiling)
- stop immediately on HTTP 429
"""
import asyncio
import json
import time
from playwright.async_api import async_playwright

POLL_INTERVAL_S = 5.0
MAX_POLLS = 20
MAX_DURATION_S = 110
LOG_PATH = "workspaces/nctf26/koth/throne/score_tick_log.jsonl"
URL = "https://arena.ctf.tg/plugins/koth/api/state"


async def main():
    t_start = time.time()
    n = 0
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(storage_state="src/tools/ctf/nctf26_storage_state.json")
        page = await ctx.new_page()
        with open(LOG_PATH, "a") as logf:
            while n < MAX_POLLS and (time.time() - t_start) < MAX_DURATION_S:
                n += 1
                t0 = time.time()
                try:
                    resp = await page.goto(URL, wait_until="load", timeout=12000)
                    status = resp.status
                    t1 = time.time()
                    if status == 429:
                        print(f"[{n}] HTTP 429 -> STOP")
                        logf.write(json.dumps({"n": n, "t0": t0, "t1": t1, "status": 429, "stop": True}) + "\n")
                        break
                    body = await resp.text()
                    data = json.loads(body)
                    throne = next(h for h in data["hills"] if h["id"] == "koth-throne")
                    rec = {
                        "n": n, "t0": t0, "t1": t1, "status": status,
                        "top": throne["top"],
                        "king_holder": throne["king"]["holder"],
                        "king_reign_s": throne["king"]["reign_seconds"],
                        "takeovers": throne["king"]["takeovers"],
                    }
                    logf.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    logf.flush()
                    print(f"[{n}] win=[{t0:.3f},{t1:.3f}] holder={throne['king']['holder']} reign={throne['king']['reign_seconds']} "
                          f"takeovers={throne['king']['takeovers']} top={throne['top']}")
                except Exception as e:
                    print(f"[{n}] ERROR {e}")
                    logf.write(json.dumps({"n": n, "error": str(e), "t": time.time()}) + "\n")
                elapsed = time.time() - t0
                await asyncio.sleep(max(0.0, POLL_INTERVAL_S - elapsed))
        await browser.close()
    print(f"DONE n={n} duration={round(time.time()-t_start,1)}s")


if __name__ == "__main__":
    asyncio.run(main())
