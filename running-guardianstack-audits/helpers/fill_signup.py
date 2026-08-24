#!/usr/bin/env python3
"""
Computer-use/CDP auth-form helper.

Use this to drive the signup or sign-in form in a browser already launched with
remote debugging. It navigates to the configured URL, types into the React/
controlled fields using CDP key events, submits the form, and captures network
events, storage, cookies, and a screenshot.

Environment variables:
  AUDIT_CONFIG   Path to a JSON target config file (optional)
  AUDIT_MODE     "signup" or "signin" (default: signup)
  AUDIT_ORIGIN   Target origin override (default: https://platform.opulentia.ai)
  AUDIT_EMAIL    Test email address
  AUDIT_NAME     Display name for new account (signup only)
  AUDIT_PASSWORD Account password
  CDP_PORT       Chrome DevTools port (default: 9223)
  OUTPUT_DIR     Where to write the capture (default: ./audit_out)
"""
import base64
import json
import os
import sys
import time

import requests
import websocket

# Allow importing the shared config loader from the helpers directory.
_HELPERS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HELPERS_DIR)
from audit_config import load_config  # noqa: E402


PORT = int(os.environ.get("CDP_PORT", "9223"))
MODE = os.environ.get("AUDIT_MODE", "signup").lower()
EMAIL = os.environ.get("AUDIT_EMAIL", "")
NAME = os.environ.get("AUDIT_NAME", "GuardianStack Audit")
PASSWORD = os.environ.get("AUDIT_PASSWORD", "")
OUT = os.environ.get("OUTPUT_DIR", "./audit_out")


def find_page(origin_host):
    pages = requests.get(f"http://127.0.0.1:{PORT}/json/list", timeout=10).json()
    for p in pages:
        if p.get("type") == "page" and origin_host in p.get("url", ""):
            return p
    return None


def main():
    config = load_config()
    origin = config["origin"].rstrip("/")
    path = config.get(f"{MODE}_path", "/auth?mode=signup")
    url = f"{origin}{path}"
    selectors = config["selectors"].get(MODE, {})
    origin_host = origin.replace("https://", "").replace("http://", "")

    os.makedirs(OUT, exist_ok=True)
    page = find_page(origin_host)
    if not page:
        page = requests.put(f"http://127.0.0.1:{PORT}/json/new?{url}", timeout=10).json()
    print(f"Attached to page {page['id']} @ {page['url']}")
    ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=10)

    events = []
    counter = [0]

    def send(method, params=None):
        counter[0] += 1
        payload = {"id": counter[0], "method": method}
        if params:
            payload["params"] = params
        ws.send(json.dumps(payload))
        return counter[0]

    def rpc(method, params=None, timeout=20):
        mid = send(method, params)
        start = time.time()
        while time.time() - start < timeout:
            ws.settimeout(max(0.5, timeout - (time.time() - start)))
            try:
                msg = json.loads(ws.recv())
                events.append(msg)
                if msg.get("id") == mid:
                    return msg
            except Exception:
                pass
        return None

    def drain(seconds):
        deadline = time.time() + seconds
        while time.time() < deadline:
            try:
                ws.settimeout(1)
                msg = json.loads(ws.recv())
                events.append(msg)
            except Exception:
                pass

    send("Network.enable", {
        "maxTotalBufferSize": 100_000_000,
        "maxResourceBufferSize": 50_000_000,
        "maxPostDataSize": 0,
    })
    send("Page.enable")
    send("Runtime.enable")
    send("Log.enable")

    rpc("Page.navigate", {"url": url}, timeout=30)

    loaded = False
    start = time.time()
    while time.time() - start < 25 and not loaded:
        try:
            ws.settimeout(2)
            msg = json.loads(ws.recv())
            events.append(msg)
            if msg.get("method") == "Page.loadEventFired":
                loaded = True
        except Exception:
            pass
    print(f"Page loaded: {loaded}")
    time.sleep(2)

    def type_into(selector, value):
        if not selector or value is None or value == "":
            return
        rpc(
            "Runtime.evaluate",
            {
                "expression": f"(()=>{{ const el=document.querySelector('{selector}'); if(el){{ el.focus(); el.select(); }} return el&&el.tagName; }})()",
                "returnByValue": True,
            },
            timeout=10,
        )
        send("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Delete", "code": "Delete", "windowsVirtualKeyCode": 46})
        send("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Delete", "code": "Delete", "windowsVirtualKeyCode": 46})
        time.sleep(0.2)
        for ch in value:
            if ch == "\n":
                send("Input.dispatchKeyEvent", {"type": "rawKeyDown", "key": "Return", "code": "Enter", "windowsVirtualKeyCode": 13})
                send("Input.dispatchKeyEvent", {"type": "char", "text": "\r", "unmodifiedText": "\r"})
                send("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Return", "code": "Enter", "windowsVirtualKeyCode": 13})
            else:
                code = f"Key{ch.upper()}" if ch.isalpha() else ""
                send("Input.dispatchKeyEvent", {"type": "keyDown", "key": ch, "code": code, "windowsVirtualKeyCode": ord(ch)})
                send("Input.dispatchKeyEvent", {"type": "char", "text": ch})
                send("Input.dispatchKeyEvent", {"type": "keyUp", "key": ch, "code": code, "windowsVirtualKeyCode": ord(ch)})
            time.sleep(0.01)
        time.sleep(0.3)

    if MODE == "signup" and selectors.get("name"):
        type_into(selectors["name"], NAME)
    if selectors.get("email"):
        type_into(selectors["email"], EMAIL)
    if selectors.get("password"):
        type_into(selectors["password"], PASSWORD)

    submit = selectors.get("submit", "button[type=submit]")
    rect = rpc(
        "Runtime.evaluate",
        {
            "expression": f"(()=>{{ const b=document.querySelector('{submit}'); if(!b) return ''; const r=b.getBoundingClientRect(); return JSON.stringify({{x:r.x+r.width/2, y:r.y+r.height/2}}); }})()",
            "returnByValue": True,
        },
        timeout=10,
    )
    if rect and rect.get("result", {}).get("value"):
        try:
            r = json.loads(rect["result"]["value"])
            send("Input.dispatchMouseEvent", {"type": "mousePressed", "x": r["x"], "y": r["y"], "button": "left", "clickCount": 1})
            send("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": r["x"], "y": r["y"], "button": "left", "clickCount": 1})
        except (json.JSONDecodeError, KeyError):
            rpc("Runtime.evaluate", {"expression": f"document.querySelector('{submit}').click()"})
    else:
        rpc("Runtime.evaluate", {"expression": f"document.querySelector('{submit}').click()"})
    print(f"Submitted {MODE} form")

    time.sleep(2)
    drain(15)

    post_ids = []
    for msg in events:
        if msg.get("method") == "Network.requestWillBeSent":
            req = msg["params"]["request"]
            if req["method"] == "POST" or "/api/auth/" in req["url"]:
                post_ids.append(msg["params"]["requestId"])

    bodies = {}
    for rid in post_ids[:20]:
        try:
            bodies[rid] = rpc("Network.getResponseBody", {"requestId": rid}, timeout=5)
        except Exception as e:
            bodies[rid] = {"error": str(e)}

    state = rpc(
        "Runtime.evaluate",
        {
            "expression": "JSON.stringify({url:location.href, title:document.title, bodyText:document.body.innerText.slice(0,2000), cookies:document.cookie, localStorage:Object.entries(localStorage), sessionStorage:Object.entries(sessionStorage)})",
            "returnByValue": True,
        },
        timeout=10,
    )
    cookies = rpc("Network.getAllCookies", timeout=10)

    screenshot = rpc("Page.captureScreenshot", timeout=10)
    if screenshot and screenshot.get("result"):
        with open(os.path.join(OUT, f"simulate_{MODE}.png"), "wb") as f:
            f.write(base64.b64decode(screenshot["result"]["data"]))

    out = {
        "events": events,
        "bodies": bodies,
        "state": state,
        "cookies": cookies,
    }
    with open(os.path.join(OUT, f"simulate_{MODE}.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(f"Saved {len(events)} events to {OUT}/simulate_{MODE}.json")
    ws.close()


if __name__ == "__main__":
    main()
