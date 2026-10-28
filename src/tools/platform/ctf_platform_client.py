#!/usr/bin/env python3
"""
Generic CTF platform client (Playwright, headless).

Handles the recurring "platform integration" steps that sit outside a single
challenge: login, challenge listing, challenge detail / attachment download,
and flag submission. Works against CTFd out of the box (REST API fast-path)
and falls back to generic DOM scraping/interaction for platforms that only
render server-side HTML, so it is not locked to one CTF engine.

This never opens a visible browser window and never touches the operator's
personal Chrome profile/session: every command launches its own isolated,
headless Chromium context and persists auth state to a local JSON file
(--session-file) so subsequent commands can reuse the login.

Usage:
    python3 ctf_platform_client.py check   --base-url https://ctf.example.com
    python3 ctf_platform_client.py login   --base-url https://ctf.example.com --username U --password P
    python3 ctf_platform_client.py status  --base-url https://ctf.example.com
    python3 ctf_platform_client.py list-challenges --base-url https://ctf.example.com
    python3 ctf_platform_client.py show-challenge  --base-url https://ctf.example.com --id 12
    python3 ctf_platform_client.py download        --base-url https://ctf.example.com --id 12
    python3 ctf_platform_client.py submit          --base-url https://ctf.example.com --id 12 --flag "FLAG{...}"
    python3 ctf_platform_client.py scoreboard      --base-url https://ctf.example.com

Credentials can be passed on the CLI, but prefer an env file
(--env-file, KEY=VALUE lines: CTF_BASE_URL / CTF_USERNAME / CTF_PASSWORD) so
secrets never appear in shell history or process listings.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print(json.dumps({"ok": False, "error": "playwright not installed. Run: pip3 install playwright && playwright install chromium"}))
    sys.exit(1)

DEFAULT_SESSION_FILE = "workspaces/bugpwn/session/storage_state.json"
DEFAULT_ENV_FILE = "workspaces/bugpwn/.env"
DEFAULT_ARTIFACT_DIR = "workspaces/bugpwn/artifacts"
DEFAULT_LOG_DIR = "workspaces/bugpwn/logs"


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------

def load_env_file(path: str) -> dict:
    env = {}
    p = Path(path)
    if not p.exists():
        return env
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip()
    return env


def now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def append_log(log_dir: str, name: str, record: dict) -> None:
    d = Path(log_dir)
    d.mkdir(parents=True, exist_ok=True)
    with (d / name).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def mask(secret: Optional[str]) -> str:
    if not secret:
        return ""
    if len(secret) <= 2:
        return "*" * len(secret)
    return secret[0] + "*" * (len(secret) - 2) + secret[-1]


def new_context(playwright, headless: bool, storage_state: Optional[str], timeout: int):
    browser = playwright.chromium.launch(
        headless=headless,
        args=["--no-sandbox", "--disable-setuid-sandbox"] if headless else [],
    )
    kwargs = {"viewport": {"width": 1366, "height": 900}}
    if storage_state and Path(storage_state).exists():
        kwargs["storage_state"] = storage_state
    context = browser.new_context(**kwargs)
    context.set_default_timeout(timeout)
    return browser, context


def save_session(context, session_file: str) -> None:
    Path(session_file).parent.mkdir(parents=True, exist_ok=True)
    context.storage_state(path=session_file)


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------

def cmd_check(args) -> int:
    """Validate connectivity/target reachability without using any credentials."""
    with sync_playwright() as p:
        browser, context = new_context(p, args.headless, None, args.timeout)
        page = context.new_page()
        result = {"ok": False, "base_url": args.base_url}
        try:
            resp = page.goto(args.base_url, wait_until="domcontentloaded", timeout=args.timeout)
            result["ok"] = True
            result["status"] = resp.status if resp else None
            result["title"] = page.title()
            result["final_url"] = page.url
            # best-effort platform fingerprint
            html = page.content()
            if "ctfd" in html.lower() or "csrfnonce" in html.lower():
                result["platform_guess"] = "ctfd"
            else:
                result["platform_guess"] = "unknown"
        except Exception as e:
            result["error"] = str(e)
        finally:
            browser.close()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result["ok"] else 1


def _find_login_fields(page):
    """Return (username_locator, password_locator, submit_locator) best-effort."""
    password = page.locator('input[type="password"]').first
    username = None
    for sel in [
        'input[name="name"]',
        'input[name="username"]',
        'input[name="email"]',
        'input[type="email"]',
        'input[type="text"]',
    ]:
        loc = page.locator(sel).first
        if loc.count() if hasattr(loc, "count") else False:
            pass
        try:
            if loc and loc.is_visible():
                username = loc
                break
        except Exception:
            continue
    submit = None
    for sel in ['button[type="submit"]', 'input[type="submit"]', 'form button']:
        loc = page.locator(sel).first
        try:
            if loc.is_visible():
                submit = loc
                break
        except Exception:
            continue
    return username, password, submit


def cmd_login(args) -> int:
    with sync_playwright() as p:
        browser, context = new_context(p, args.headless, None, args.timeout)
        page = context.new_page()
        result = {"ok": False}
        try:
            login_url = args.base_url.rstrip("/") + "/login"
            page.goto(login_url, wait_until="networkidle", timeout=args.timeout)

            username_loc, password_loc, submit_loc = _find_login_fields(page)
            if username_loc is None or password_loc is None:
                result["error"] = "could not locate login form fields"
                result["page_title"] = page.title()
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return 1

            username_loc.fill(args.username)
            password_loc.fill(args.password)

            if submit_loc is not None:
                submit_loc.click()
            else:
                password_loc.press("Enter")

            page.wait_for_load_state("networkidle", timeout=args.timeout)

            html_lower = page.content().lower()
            indicators = [kw for kw in ("logout", "log out", "scoreboard", "challenges", "profile") if kw in html_lower]
            looks_failed = any(kw in html_lower for kw in ("invalid", "incorrect", "your username or password"))

            result["ok"] = bool(indicators) and not looks_failed
            result["final_url"] = page.url
            result["title"] = page.title()
            result["indicators_found"] = indicators
            result["looks_failed"] = looks_failed

            save_session(context, args.session_file)
            result["session_file"] = args.session_file
        except PlaywrightTimeout:
            result["error"] = "timeout during login"
        except Exception as e:
            result["error"] = str(e)
        finally:
            browser.close()

        append_log(args.log_dir, "auth.log", {
            "ts": now_stamp(), "action": "login", "username": mask(args.username),
            "ok": result.get("ok", False),
        })
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok") else 1


def _fetch_json(page, path: str) -> dict:
    script = """
    async (p) => {
        try {
            const r = await fetch(p, {headers: {'Accept': 'application/json'}, credentials: 'same-origin'});
            const text = await r.text();
            return {status: r.status, text: text};
        } catch (e) {
            return {status: 0, text: String(e)};
        }
    }
    """
    return page.evaluate(script, path)


def _extract_csrf_nonce(html: str) -> Optional[str]:
    m = re.search(r'csrfNonce["\']?\s*[:=]\s*["\']([a-fA-F0-9]+)["\']', html)
    if m:
        return m.group(1)
    m = re.search(r'name=["\']nonce["\']\s+value=["\']([^"\']+)["\']', html)
    if m:
        return m.group(1)
    return None


def cmd_status(args) -> int:
    with sync_playwright() as p:
        browser, context = new_context(p, args.headless, args.session_file, args.timeout)
        page = context.new_page()
        result = {"ok": False}
        try:
            page.goto(args.base_url, wait_until="networkidle", timeout=args.timeout)
            api = _fetch_json(page, "/api/v1/users/me")
            if api["status"] == 200:
                try:
                    data = json.loads(api["text"])
                    result["ok"] = True
                    result["source"] = "api"
                    result["data"] = data
                except json.JSONDecodeError:
                    pass
            if not result["ok"]:
                html_lower = page.content().lower()
                result["ok"] = "logout" in html_lower or "log out" in html_lower
                result["source"] = "dom"
                result["title"] = page.title()
                result["url"] = page.url
        except Exception as e:
            result["error"] = str(e)
        finally:
            browser.close()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok") else 1


def cmd_list_challenges(args) -> int:
    with sync_playwright() as p:
        browser, context = new_context(p, args.headless, args.session_file, args.timeout)
        page = context.new_page()
        result = {"ok": False, "challenges": []}
        try:
            page.goto(args.base_url, wait_until="networkidle", timeout=args.timeout)
            api = _fetch_json(page, "/api/v1/challenges")
            if api["status"] == 200:
                try:
                    data = json.loads(api["text"])
                    chals = data.get("data", data if isinstance(data, list) else [])
                    result["ok"] = True
                    result["source"] = "api"
                    result["challenges"] = chals
                except json.JSONDecodeError:
                    pass

            if not result["ok"]:
                # generic DOM fallback
                chal_url = args.base_url.rstrip("/") + "/challenges"
                page.goto(chal_url, wait_until="networkidle", timeout=args.timeout)
                time.sleep(1.5)  # allow client-side rendering
                candidates = page.locator(
                    "[data-challenge-id], .challenge-button, .challenge-card, button.challenge, "
                    "a.challenge, li.challenge"
                )
                count = candidates.count()
                scraped = []
                for i in range(count):
                    el = candidates.nth(i)
                    try:
                        scraped.append({
                            "index": i,
                            "text": el.inner_text().strip(),
                            "data_id": el.get_attribute("data-challenge-id"),
                        })
                    except Exception:
                        continue
                result["source"] = "dom"
                result["ok"] = len(scraped) > 0
                result["challenges"] = scraped
                if not scraped:
                    # dump full page so Claude can inspect structure manually
                    dump_dir = Path(args.artifact_dir)
                    dump_dir.mkdir(parents=True, exist_ok=True)
                    dump_path = dump_dir / f"challenges_page_{now_stamp()}.html"
                    dump_path.write_text(page.content(), encoding="utf-8")
                    result["raw_dump"] = str(dump_path)
                    result["note"] = "No challenge elements matched known selectors; inspect raw_dump."
        except Exception as e:
            result["error"] = str(e)
        finally:
            browser.close()

        out_dir = Path(args.artifact_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"challenges_{now_stamp()}.json"
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        result["saved_to"] = str(out_path)

        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok") else 1


def cmd_show_challenge(args) -> int:
    with sync_playwright() as p:
        browser, context = new_context(p, args.headless, args.session_file, args.timeout)
        page = context.new_page()
        result = {"ok": False, "id": args.id}
        try:
            page.goto(args.base_url, wait_until="networkidle", timeout=args.timeout)
            if args.id is not None:
                api = _fetch_json(page, f"/api/v1/challenges/{args.id}")
                if api["status"] == 200:
                    try:
                        data = json.loads(api["text"])
                        result["ok"] = True
                        result["source"] = "api"
                        result["data"] = data.get("data", data)
                    except json.JSONDecodeError:
                        pass

            if not result["ok"]:
                chal_url = args.base_url.rstrip("/") + "/challenges"
                page.goto(chal_url, wait_until="networkidle", timeout=args.timeout)
                time.sleep(1.0)
                target = None
                if args.id is not None:
                    loc = page.locator(f'[data-challenge-id="{args.id}"]').first
                    if loc.count() if hasattr(loc, "count") else True:
                        target = loc
                if target is None and args.name:
                    target = page.get_by_text(args.name, exact=False).first
                if target is not None:
                    target.click()
                    page.wait_for_timeout(1000)
                    modal_text = page.locator("body").inner_text()
                    files = page.locator('a[href*="/files/"], a[href*="/download"]').all()
                    file_links = []
                    for f in files:
                        try:
                            file_links.append(f.get_attribute("href"))
                        except Exception:
                            continue
                    result["ok"] = True
                    result["source"] = "dom"
                    result["modal_text"] = modal_text[:4000]
                    result["file_links"] = [l for l in file_links if l]
                else:
                    result["error"] = "challenge not found via id or name on /challenges page"
        except Exception as e:
            result["error"] = str(e)
        finally:
            browser.close()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok") else 1


def cmd_download(args) -> int:
    with sync_playwright() as p:
        browser, context = new_context(p, args.headless, args.session_file, args.timeout)
        page = context.new_page()
        result = {"ok": False, "saved": []}
        try:
            page.goto(args.base_url, wait_until="networkidle", timeout=args.timeout)
            links = []
            if args.id is not None:
                api = _fetch_json(page, f"/api/v1/challenges/{args.id}")
                if api["status"] == 200:
                    try:
                        data = json.loads(api["text"]).get("data", {})
                        links = data.get("files", [])
                    except json.JSONDecodeError:
                        pass
            if not links and args.url:
                links = [args.url]

            dest_dir = Path(args.out_dir)
            dest_dir.mkdir(parents=True, exist_ok=True)

            for link in links:
                full_url = link if link.startswith("http") else args.base_url.rstrip("/") + link
                resp = context.request.get(full_url)
                filename = full_url.split("/")[-1].split("?")[0] or f"file_{now_stamp()}"
                dest = dest_dir / filename
                dest.write_bytes(resp.body())
                result["saved"].append(str(dest))

            result["ok"] = len(result["saved"]) > 0
        except Exception as e:
            result["error"] = str(e)
        finally:
            browser.close()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok") else 1


def cmd_submit(args) -> int:
    with sync_playwright() as p:
        browser, context = new_context(p, args.headless, args.session_file, args.timeout)
        page = context.new_page()
        result = {"ok": False, "id": args.id, "flag": args.flag}
        try:
            page.goto(args.base_url, wait_until="networkidle", timeout=args.timeout)
            html = page.content()
            nonce = _extract_csrf_nonce(html)

            api_tried = False
            if args.id is not None and nonce:
                api_tried = True
                script = """
                async ({cid, flag, nonce}) => {
                    try {
                        const r = await fetch('/api/v1/challenges/attempt', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json', 'CSRF-Token': nonce},
                            credentials: 'same-origin',
                            body: JSON.stringify({challenge_id: cid, submission: flag})
                        });
                        const text = await r.text();
                        return {status: r.status, text: text};
                    } catch (e) {
                        return {status: 0, text: String(e)};
                    }
                }
                """
                api = page.evaluate(script, {"cid": args.id, "flag": args.flag, "nonce": nonce})
                if api["status"] == 200:
                    try:
                        data = json.loads(api["text"])
                        inner = data.get("data", {})
                        result["ok"] = True
                        result["source"] = "api"
                        result["status_text"] = inner.get("status")
                        result["message"] = inner.get("message")
                        result["correct"] = inner.get("status") == "correct"
                    except json.JSONDecodeError:
                        pass

            if not result["ok"] and not api_tried:
                result["note"] = "API path unavailable (no csrf nonce or no id); DOM fallback required but not yet located automatically for this platform."
                result["source"] = "none"
        except Exception as e:
            result["error"] = str(e)
        finally:
            browser.close()

        append_log(args.log_dir, "submissions.log", {
            "ts": now_stamp(), "id": args.id, "flag": args.flag,
            "ok": result.get("ok", False), "correct": result.get("correct"),
            "message": result.get("message"),
        })
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("correct") else 1


def cmd_scoreboard(args) -> int:
    with sync_playwright() as p:
        browser, context = new_context(p, args.headless, args.session_file, args.timeout)
        page = context.new_page()
        result = {"ok": False}
        try:
            page.goto(args.base_url, wait_until="networkidle", timeout=args.timeout)
            api = _fetch_json(page, "/api/v1/scoreboard")
            if api["status"] == 200:
                try:
                    result["ok"] = True
                    result["data"] = json.loads(api["text"]).get("data")
                except json.JSONDecodeError:
                    pass
            if not result["ok"]:
                sb_url = args.base_url.rstrip("/") + "/scoreboard"
                page.goto(sb_url, wait_until="networkidle", timeout=args.timeout)
                result["ok"] = True
                result["source"] = "dom"
                result["text"] = page.locator("body").inner_text()[:3000]
        except Exception as e:
            result["error"] = str(e)
        finally:
            browser.close()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok") else 1


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main() -> int:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--env-file", default=DEFAULT_ENV_FILE, help="KEY=VALUE file with CTF_BASE_URL/CTF_USERNAME/CTF_PASSWORD")
    common.add_argument("--base-url", help="Override base URL")
    common.add_argument("--username", help="Override username (login only)")
    common.add_argument("--password", help="Override password (login only)")
    common.add_argument("--session-file", default=DEFAULT_SESSION_FILE)
    common.add_argument("--artifact-dir", default=DEFAULT_ARTIFACT_DIR)
    common.add_argument("--log-dir", default=DEFAULT_LOG_DIR)
    common.add_argument("--headless", type=lambda x: x.lower() == "true", default=True)
    common.add_argument("--timeout", type=int, default=30000)

    parser = argparse.ArgumentParser(
        description="Generic headless CTF platform client (Playwright).",
        parents=[common],
    )

    sub = parser.add_subparsers(dest="command")

    sub.add_parser("check", parents=[common], add_help=False)
    sub.add_parser("login", parents=[common], add_help=False)
    sub.add_parser("status", parents=[common], add_help=False)
    sub.add_parser("list-challenges", parents=[common], add_help=False)

    p_show = sub.add_parser("show-challenge", parents=[common], add_help=False)
    p_show.add_argument("--id", type=int)
    p_show.add_argument("--name")

    p_dl = sub.add_parser("download", parents=[common], add_help=False)
    p_dl.add_argument("--id", type=int)
    p_dl.add_argument("--url")
    p_dl.add_argument("--out-dir", default=DEFAULT_ARTIFACT_DIR)

    p_submit = sub.add_parser("submit", parents=[common], add_help=False)
    p_submit.add_argument("--id", type=int, required=True)
    p_submit.add_argument("--flag", required=True)

    sub.add_parser("scoreboard", parents=[common], add_help=False)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 1

    env = load_env_file(args.env_file)
    args.base_url = args.base_url or env.get("CTF_BASE_URL")
    args.username = args.username or env.get("CTF_USERNAME")
    args.password = args.password or env.get("CTF_PASSWORD")

    if not args.base_url:
        print(json.dumps({"ok": False, "error": "base_url is required (--base-url or CTF_BASE_URL in env file)"}))
        return 1

    if args.command == "login" and (not args.username or not args.password):
        print(json.dumps({"ok": False, "error": "username/password required for login (CLI flags or env file)"}))
        return 1

    commands = {
        "check": cmd_check,
        "login": cmd_login,
        "status": cmd_status,
        "list-challenges": cmd_list_challenges,
        "show-challenge": cmd_show_challenge,
        "download": cmd_download,
        "submit": cmd_submit,
        "scoreboard": cmd_scoreboard,
    }
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
