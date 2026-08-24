#!/usr/bin/env python3
"""
Logout and storage-cleanup helper.

This script first revokes the session through the API, confirms the revocation,
then attaches to the browser via CDP, navigates to the sign-in page, clears the
better-auth storage entries, and records the final browser state.

Environment variables:
  AUDIT_ORIGIN   Target origin (default: https://platform.opulentia.ai)
  CDP_PORT       Chrome DevTools port (default: 9223)
  OUTPUT_DIR     Where to write results (default: ./audit_out)
"""
import json
import os
import time

import requests
import websocket

ORIGIN = os.environ.get("AUDIT_ORIGIN", "https://platform.opulentia.ai").rstrip("/")
PORT = int(os.environ.get("CDP_PORT", "9223"))
OUT = os.environ.get("OUTPUT_DIR", "./audit_out")
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"


def api_logout(cookie):
    r = requests.post(
        f"{ORIGIN}/api/auth/sign-out",
        headers={
            "better-auth-cookie": cookie,
            "user-agent": UA,
            "accept": "application/json",
            "content-type": "application/json",
        },
        json={},
        timeout=15,
    )
    post = requests.get(
        f"{ORIGIN}/api/auth/get-session",
        headers={"better-auth-cookie": cookie, "user-agent": UA, "accept": "application/json"},
        timeout=15,
    )
    return {"sign_out": {"status": r.status_code, "body": r.text}, "post_get_session": {"status": post.status_code, "body": post.text}}


def cdp_clear():
    pages = requests.get(f"http://127.0.0.1:{PORT}/json/list", timeout=10).json()
    page = next((p for p in pages if p["type"] == "page" and ORIGIN.replace("https://", "").replace("http://", "") in p.get("url", "")), None)
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
    # Clear better-auth keys, other app session keys, and navigate to sign-in.
    rpc(
        "Runtime.evaluate",
        {
            "expression": f"""(()=>{{
                Object.keys(localStorage).forEach(k=>{{ if(k.startsWith('better-auth') || k.startsWith('opulent')) localStorage.removeItem(k); }});
                Object.keys(sessionStorage).forEach(k=>{{ sessionStorage.removeItem(k); }});
                window.location.href='{ORIGIN}/auth?mode=signin';
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
    os.makedirs(OUT, exist_ok=True)
    cookie_file = os.path.join(OUT, "auth_cookie.txt")
    cookie = open(cookie_file).read().strip() if os.path.exists(cookie_file) else ""
    if not cookie:
        raise SystemExit("No auth cookie found. Run extract_cookie.py first.")

    result = {"api": api_logout(cookie), "browser": cdp_clear()}
    with open(os.path.join(OUT, "logout_test.json"), "w") as f:
        json.dump(result, f, indent=2)
    print(f"Saved {OUT}/logout_test.json")


if __name__ == "__main__":
    main()
