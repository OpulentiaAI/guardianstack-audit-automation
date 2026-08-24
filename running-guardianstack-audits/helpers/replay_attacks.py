#!/usr/bin/env python3
"""
Bounded replay/refresh/logout attack tests against the Better Auth endpoints.

Reads the auth cookie from OUTPUT_DIR/auth_cookie.txt and ORIGIN from the
environment, then exercises the session from inside and outside the original
browser context.

Environment variables:
  AUDIT_ORIGIN   Target origin (default: https://platform.opulentia.ai)
  OUTPUT_DIR     Directory containing auth_cookie.txt and results (default: ./audit_out)
"""
import json
import os

import requests

ORIGIN = os.environ.get("AUDIT_ORIGIN", "https://platform.opulentia.ai").rstrip("/")
OUT = os.environ.get("OUTPUT_DIR", "./audit_out")

UA_CHROME = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
UA_FIREFOX = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0"


def request(name, path, method="GET", headers=None, body=None, timeout=15):
    try:
        r = requests.request(method, f"{ORIGIN}{path}", headers=headers, data=body, timeout=timeout)
        print(f"{name}: {r.status_code} {r.text[:200]}")
        return {"status": r.status_code, "headers": dict(r.headers), "body": r.text[:2000]}
    except Exception as e:
        print(f"{name}: ERR {e}")
        return {"error": str(e)}


def main():
    cookie_file = os.path.join(OUT, "auth_cookie.txt")
    full = open(cookie_file).read().strip() if os.path.exists(cookie_file) else ""
    if not full:
        raise SystemExit("No auth cookie found. Run extract_cookie.py first.")

    parts = {}
    for kv in [p.strip() for p in full.split(";") if p.strip()]:
        if "=" in kv:
            k, v = kv.split("=", 1)
            parts[k] = v

    session_token = f"__Secure-better-auth.session_token={parts.get('__Secure-better-auth.session_token', '')}"
    convex_jwt = f"__Secure-better-auth.convex_jwt={parts.get('__Secure-better-auth.convex_jwt', '')}"

    results = {}

    results["get_session_full_ua_match"] = request(
        "get_session_full_ua_match", "/api/auth/get-session",
        headers={"better-auth-cookie": full, "user-agent": UA_CHROME, "accept": "application/json"},
    )

    results["get_session_full_ua_diff"] = request(
        "get_session_full_ua_diff", "/api/auth/get-session",
        headers={"better-auth-cookie": full, "user-agent": UA_FIREFOX, "accept": "application/json"},
    )

    results["get_session_session_token_only"] = request(
        "get_session_session_token_only", "/api/auth/get-session",
        headers={"better-auth-cookie": session_token, "user-agent": UA_CHROME, "accept": "application/json"},
    )

    results["get_session_convex_jwt_only"] = request(
        "get_session_convex_jwt_only", "/api/auth/get-session",
        headers={"better-auth-cookie": convex_jwt, "user-agent": UA_CHROME, "accept": "application/json"},
    )

    results["get_session_cookie_header"] = request(
        "get_session_cookie_header", "/api/auth/get-session",
        headers={"Cookie": full, "user-agent": UA_CHROME, "accept": "application/json"},
    )

    results["convex_token_session_token_only"] = request(
        "convex_token_session_token_only", "/api/auth/convex/token",
        headers={"better-auth-cookie": session_token, "user-agent": UA_CHROME, "accept": "application/json"},
    )

    results["convex_token_ua_diff"] = request(
        "convex_token_ua_diff", "/api/auth/convex/token",
        headers={"better-auth-cookie": full, "user-agent": UA_FIREFOX, "accept": "application/json"},
    )

    results["get_session_no_cred"] = request(
        "get_session_no_cred", "/api/auth/get-session",
        headers={"user-agent": UA_CHROME, "accept": "application/json"},
    )

    # Logout and post-logout replay.
    results["sign_out"] = request(
        "sign_out", "/api/auth/sign-out", method="POST",
        headers={"better-auth-cookie": full, "user-agent": UA_CHROME, "accept": "application/json", "content-type": "application/json"},
        body=b"{}",
    )

    results["get_session_after_signout"] = request(
        "get_session_after_signout", "/api/auth/get-session",
        headers={"better-auth-cookie": full, "user-agent": UA_CHROME, "accept": "application/json"},
    )

    results["convex_token_after_signout"] = request(
        "convex_token_after_signout", "/api/auth/convex/token",
        headers={"better-auth-cookie": session_token, "user-agent": UA_CHROME, "accept": "application/json"},
    )

    with open(os.path.join(OUT, "replay_tests.json"), "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved {OUT}/replay_tests.json")


if __name__ == "__main__":
    main()
