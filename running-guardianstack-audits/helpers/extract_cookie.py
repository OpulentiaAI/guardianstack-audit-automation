#!/usr/bin/env python3
"""
Extract the authorization credential from a CDP capture.

The script searches Network events for the configured auth header on an auth
endpoint and writes the value to auth_cookie.txt in OUTPUT_DIR. If no header is
found, it falls back to localStorage under the configured storage prefix.

Environment variables:
  AUDIT_CONFIG   Path to a JSON target config file (optional)
  CDP_CAPTURE    Path to the CDP capture file (default: ./audit_out/simulate_signup.json)
  OUTPUT_DIR     Where to write auth_cookie.txt (default: ./audit_out)
"""
import json
import os
import sys

_HELPERS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HELPERS_DIR)
from audit_config import load_config  # noqa: E402


def main():
    config = load_config()
    auth_header = config.get("auth_header", "better-auth-cookie")
    storage_prefix = config.get("storage_prefix", "better-auth")

    cdp_capture = os.environ.get("CDP_CAPTURE", "./audit_out/simulate_signup.json")
    out = os.environ.get("OUTPUT_DIR", "./audit_out")
    os.makedirs(out, exist_ok=True)

    data = json.load(open(cdp_capture))
    credential = ""

    # First try network request headers on auth endpoints.
    for msg in data.get("events", []):
        if msg.get("method") == "Network.requestWillBeSent":
            req = msg["params"]["request"]
            url = req.get("url", "")
            if "/api/auth/" in url or "/auth/" in url:
                c = req.get("headers", {}).get(auth_header, "")
                if c:
                    credential = c
                    break

    # Fallback to localStorage.
    if not credential:
        state = data.get("state", {})
        value = None
        try:
            value = state["result"]["result"]["value"]
        except Exception:
            pass
        if value and isinstance(value, str):
            try:
                parsed = json.loads(value)
                ls = parsed.get("localStorage", [])
                for key, val in ls:
                    if key.startswith(storage_prefix) or key in ("token", "session", "auth_token"):
                        try:
                            obj = json.loads(val)
                            if isinstance(obj, dict):
                                parts = []
                                for k, v in obj.items():
                                    if isinstance(v, dict) and v.get("value"):
                                        parts.append(f"{k}={v['value']}")
                                    elif isinstance(v, str):
                                        parts.append(f"{k}={v}")
                                if parts:
                                    credential = "; ".join(parts)
                            else:
                                credential = str(obj)
                        except Exception:
                            credential = val
                        if credential:
                            break
            except Exception:
                pass

    if not credential:
        print(f"No credential found (looked for header '{auth_header}' and storage prefix '{storage_prefix}').")
        return

    out_path = os.path.join(out, "auth_cookie.txt")
    with open(out_path, "w") as f:
        f.write(credential)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
