#!/usr/bin/env python3
"""
Logout and storage-cleanup helper.

This script first revokes the session through the API, confirms the revocation,
then attaches to the browser via CDP, navigates to the configured sign-in page,
clears target storage entries, and records the final browser state.

Environment variables:
  AUDIT_CONFIG   Path to a JSON target config file (optional)
  CDP_PORT       Chrome DevTools port (default: 9223)
  OUTPUT_DIR     Where to write results (default: ./audit_out)
"""
import json
import os
import sys
import time

import requests
import websocket

_HELPERS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HELPERS_DIR)
from audit_config import load_config  # noqa: E402

PORT = int(os.environ.get("CDP_PORT", "9223"))
OUT = os.environ.get("OUTPUT_DIR", "./audit_out")
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"


def api_logout(origin, signout_path, auth_header, credential):
    r = requests.post(
        f"{origin}{signout_path}",
        headers={auth_header: credential, "user-agent": UA, "accept": "application/json", "content-type": "application/json"},
        json={},
        timeout=15,
    )
    session_path = config.get("endpoints", {}).get("session", "/api/auth/get-session")
    post = requests.get(
        f"{origin}{session_path}",
        headers={auth_header: credential, "user-agent": UA, "accept": "application/json"},
        timeout=15,
    )
    return {
        "sign_out": {"status": r.status_code, "body": r.text},
        "post_get_session": {"status": post.status_code, "body": post.text},
    }


def cdp_clear(origin, signin_path, storage_prefix):
    origin_host = origin.replace("https://", "").replace("http://", "")
    pages = requests.get(f"http://127.0.0.1:{PORT}/json/list", timeout=10).json()
    page = next((p for p in pages if p["type"] == "page" and origin_host in p.get("url", "")), None)
    if not page:
        return {"error": "No browser page for origin found"}
    ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=10)
    counter = [0]

    def rpc(method, params=None, timeout=20):
        counter[0] += 1
        payload = {"id": counter[0], "method": method}
        if params:
            payload["params"] = params
        ws.send(json.dumps(payload))
        start = time.time()
        while time.time() - start < timeout:
            ws.settimeout(max(0.5, timeout - (time.time() - start)))
            try:
                msg = json.loads(ws.recv())
                if msg.get("id") == counter[0]:
                    return msg
            except Exception:
                pass
        return None

    rpc("Runtime.enable")
    pre = rpc(
        "Runtime.evaluate",
        {"expression": "JSON.stringify({localStorage:Object.keys(localStorage), sessionStorage:Object.keys(sessionStorage), cookies:document.cookie})", "returnByValue": True},
        timeout=10,
    )

    prefix = json.dumps(storage_prefix)
    rpc(
        "Runtime.evaluate",
        {
            "expression": f"""(()=>{{
                Object.keys(localStorage).forEach(k=>{{ if(k.startsWith({prefix}) || ['token','session','auth_token','access_token'].includes(k)) localStorage.removeItem(k); }});
                Object.keys(sessionStorage).forEach(k=>{{ if(k.startsWith({prefix}) || ['token','session','auth_token','access_token'].includes(k)) sessionStorage.removeItem(k); }});
                window.location.href='{origin}{signin_path}';
            }})()""",
            "returnByValue": True,
        },
        timeout=10,
    )
    time.sleep(2)
    post = rpc(
        "Runtime.evaluate",
        {"expression": "JSON.stringify({url:location.href, title:document.title, localStorage:Object.keys(localStorage), sessionStorage:Object.keys(sessionStorage), cookies:document.cookie})", "returnByValue": True},
        timeout=10,
    )
    ws.close()
    return {"pre": pre, "post": post}


def main():
    global config
    config = load_config()
    origin = config["origin"].rstrip("/")
    endpoints = config.get("endpoints", {})
    signout_path = endpoints.get("signout", "/api/auth/sign-out")
    signin_path = config.get("signin_path", "/auth?mode=signin")
    auth_header = config.get("auth_header", "better-auth-cookie")
    storage_prefix = config.get("storage_prefix", "better-auth")

    os.makedirs(OUT, exist_ok=True)
    credential_file = os.path.join(OUT, "auth_cookie.txt")
    credential = open(credential_file).read().strip() if os.path.exists(credential_file) else ""
    if not credential:
        raise SystemExit("No auth cookie found. Run extract_cookie.py first.")

    result = {
        "api": api_logout(origin, signout_path, auth_header, credential),
        "browser": cdp_clear(origin, signin_path, storage_prefix),
    }
    with open(os.path.join(OUT, "logout_test.json"), "w") as f:
        json.dump(result, f, indent=2)
    print(f"Saved {OUT}/logout_test.json")


if __name__ == "__main__":
    main()
