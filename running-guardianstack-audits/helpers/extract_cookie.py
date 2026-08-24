#!/usr/bin/env python3
"""
Extract the better-auth-cookie header value from a CDP capture.

This script searches the Network events in a CDP dump for the first
/api/auth/ request that carried a `better-auth-cookie` header and writes the
value to auth_cookie.txt in OUTPUT_DIR. If no header is found it falls back to
the `better-auth_cookie` localStorage entry.

Environment variables:
  CDP_CAPTURE   Path to the CDP capture file (default: ./audit_out/simulate_signup.json)
  OUTPUT_DIR    Where to write auth_cookie.txt (default: ./audit_out)
"""
import json
import os

CDP_CAPTURE = os.environ.get("CDP_CAPTURE", "./audit_out/simulate_signup.json")
OUT = os.environ.get("OUTPUT_DIR", "./audit_out")


def main():
    os.makedirs(OUT, exist_ok=True)
    data = json.load(open(CDP_CAPTURE))
    cookie = ""

    # First try network request headers.
    for msg in data.get("events", []):
        if msg.get("method") == "Network.requestWillBeSent":
            req = msg["params"]["request"]
            if "/api/auth/" in req.get("url", ""):
                c = req.get("headers", {}).get("better-auth-cookie", "")
                if c:
                    cookie = c
                    break

    # Fallback to localStorage.
    if not cookie:
        state = data.get("state", {})
        value = state.get("result", {}).get("result", {}).get("value") if state else None
        if value and isinstance(value, str):
            parsed = json.loads(value)
            cookie_entry = next((v for k, v in parsed.get("localStorage", []) if k == "better-auth_cookie"), "")
            if cookie_entry:
                try:
                    cookie_obj = json.loads(cookie_entry)
                    parts = [f"{k}={v.get('value')}" for k, v in cookie_obj.items() if v.get("value")]
                    cookie = "; ".join(parts)
                except Exception:
                    cookie = cookie_entry

    if not cookie:
        print("No better-auth-cookie value found.")
        return

    out_path = os.path.join(OUT, "auth_cookie.txt")
    with open(out_path, "w") as f:
        f.write(cookie)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
