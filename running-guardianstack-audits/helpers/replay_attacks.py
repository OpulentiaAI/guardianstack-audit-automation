#!/usr/bin/env python3
"""
Bounded replay/refresh/logout attack tests.

Reads the captured credential from OUTPUT_DIR/auth_cookie.txt and the target
config, then exercises the session endpoints from inside and outside the
original browser context.

Environment variables:
  AUDIT_CONFIG   Path to a JSON target config file (optional)
  AUDIT_ORIGIN   Target origin override
  OUTPUT_DIR     Directory containing auth_cookie.txt and results (default: ./audit_out)
"""
import json
import os
import sys

import requests

_HELPERS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HELPERS_DIR)
from audit_config import load_config  # noqa: E402

UA_CHROME = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
UA_FIREFOX = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0"


def request(name, url, method="GET", headers=None, body=None, timeout=15):
    try:
        r = requests.request(method, url, headers=headers, data=body, timeout=timeout)
        print(f"{name}: {r.status_code} {r.text[:200]}")
        return {"status": r.status_code, "headers": dict(r.headers), "body": r.text[:2000]}
    except Exception as e:
        print(f"{name}: ERR {e}")
        return {"error": str(e)}


def parse_credential(full, token_keys):
    """Return a mapping of token key -> value if the credential can be split."""
    parts = {}
    if ";" in full:
        for kv in [p.strip() for p in full.split(";") if p.strip()]:
            if "=" in kv:
                k, v = kv.split("=", 1)
                parts[k] = v
    if not parts:
        parts = {"session": full}

    if token_keys:
        session_key = token_keys.get("session")
        secondary_key = token_keys.get("secondary")
        if session_key and session_key in parts:
            session_only = f"{session_key}={parts[session_key]}"
        else:
            session_only = full
        if secondary_key and secondary_key in parts:
            secondary_only = f"{secondary_key}={parts[secondary_key]}"
        else:
            secondary_only = None
    else:
        session_only = full
        secondary_only = None
    return parts, session_only, secondary_only


def make_headers(config, credential, ua=None, use_cookie=False):
    headers = {"user-agent": ua or UA_CHROME, "accept": "application/json"}
    if use_cookie:
        headers["Cookie"] = credential
    else:
        headers[config.get("auth_header", "better-auth-cookie")] = credential
    return headers


def main():
    config = load_config()
    origin = config["origin"].rstrip("/")
    out = os.environ.get("OUTPUT_DIR", "./audit_out")
    endpoints = config.get("endpoints", {})
    token_keys = config.get("token_keys")
    auth_header = config.get("auth_header", "better-auth-cookie")

    credential_file = os.path.join(out, "auth_cookie.txt")
    if not os.path.exists(credential_file):
        raise SystemExit("No auth cookie found. Run extract_cookie.py first.")
    full = open(credential_file).read().strip()
    if not full:
        raise SystemExit("auth_cookie.txt is empty.")

    parts, session_only, secondary_only = parse_credential(full, token_keys)
    session_path = endpoints.get("session", "/api/auth/get-session")
    signout_path = endpoints.get("signout", "/api/auth/sign-out")
    secondary_path = endpoints.get("secondary_token")

    def session_req(name, credential, ua=None, use_cookie=False):
        return request(name, f"{origin}{session_path}", headers=make_headers(config, credential, ua, use_cookie))

    results = {}
    results["get_session_full_ua_match"] = session_req("get_session_full_ua_match", full, UA_CHROME)
    results["get_session_full_ua_diff"] = session_req("get_session_full_ua_diff", full, UA_FIREFOX)
    results["get_session_session_token_only"] = session_req("get_session_session_token_only", session_only, UA_CHROME)
    if secondary_only:
        results["get_session_secondary_token_only"] = session_req("get_session_secondary_token_only", secondary_only, UA_CHROME)

    # Only try the Cookie-header variant when the credential looks like a cookie string and we are not already using Cookie as the auth header.
    if "=" in full and auth_header.lower() != "cookie":
        results["get_session_cookie_header"] = session_req("get_session_cookie_header", full, UA_CHROME, use_cookie=True)
    else:
        results["get_session_cookie_header"] = {"status": "Not applicable", "reason": "credential is not a cookie string or auth header is Cookie"}

    results["get_session_no_cred"] = request(
        "get_session_no_cred", f"{origin}{session_path}",
        headers={"user-agent": UA_CHROME, "accept": "application/json"},
    )

    if secondary_path:
        secondary_url = f"{origin}{secondary_path}"
        results["secondary_token_session_token_only"] = request(
            "secondary_token_session_token_only", secondary_url,
            headers=make_headers(config, session_only, UA_CHROME),
        )
        results["secondary_token_ua_diff"] = request(
            "secondary_token_ua_diff", secondary_url,
            headers=make_headers(config, full, UA_FIREFOX),
        )

    # Sign-out and post-logout replay.
    results["sign_out"] = request(
        "sign_out", f"{origin}{signout_path}", method="POST",
        headers={**make_headers(config, full, UA_CHROME), "content-type": "application/json"},
        body=b"{}",
    )
    results["get_session_after_signout"] = session_req("get_session_after_signout", full, UA_CHROME)
    if secondary_path:
        results["secondary_token_after_signout"] = request(
            "secondary_token_after_signout", f"{origin}{secondary_path}",
            headers=make_headers(config, session_only, UA_CHROME),
        )

    with open(os.path.join(out, "replay_tests.json"), "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved {out}/replay_tests.json")


if __name__ == "__main__":
    main()
