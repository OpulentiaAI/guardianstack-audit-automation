#!/usr/bin/env python3
"""
Computer-use/CDP signup helper.

Use this to drive the signup form in a browser already launched with remote
debugging. It navigates to ORIGIN/auth?mode=signup, types into the React
controlled name/email/password fields using CDP key events, submits the form,
captures network events, storage, cookies, and a screenshot, then writes them to
OUTPUT_DIR.

Environment variables:
  AUDIT_ORIGIN    Target origin (default: https://platform.opulentia.ai)
  AUDIT_EMAIL     Test email address
  AUDIT_NAME      Display name for the new account
  AUDIT_PASSWORD  Account password
  CDP_PORT        Chrome DevTools port (default: 9223)
  OUTPUT_DIR      Where to write the capture (default: ./audit_out)
"""
import base64
import json
import os
import time

import requests
import websocket

PORT = int(os.environ.get("CDP_PORT", "9223"))
ORIGIN = os.environ.get("AUDIT_ORIGIN", "https://platform.opulentia.ai").rstrip("/")
EMAIL = os.environ.get("AUDIT_EMAIL", "")
NAME = os.environ.get("AUDIT_NAME", "GuardianStack Audit")
PASSWORD = os.environ.get("AUDIT_PASSWORD", "")
OUT = os.environ.get("OUTPUT_DIR", "./audit_out")


def find_page():
    pages = requests.get(f"http://127.0.0.1:{PORT}/json/list", timeout=10).json()
    for p in pages:
        if p.get("type") == "page" and ORIGIN.replace("https://", "").replace("http://", "") in p.get("url", ""):
            return p
    # No matching page; create a new one on the signup URL.
    return requests.put(
        f"http://127.0.0.1:{PORT}/json/new?{ORIGIN}/auth?mode=signup",
        timeout=10,
    ).json()


def main():
    os.makedirs(OUT, exist_ok=True)
    page = find_page()
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

    # Enable CDP domains.
    send("Network.enable", {
        "maxTotalBufferSize": 100_000_000,
        "maxResourceBufferSize": 50_000_000,
        "maxPostDataSize": 0,
    })
    send("Page.enable")
    send("Runtime.enable")
    send("Log.enable")

    rpc("Page.navigate", {"url": f"{ORIGIN}/auth?mode=signup"}, timeout=30)

    # Wait for load.
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
        # Focus and select all existing content, then type the new value.
        rpc(
            "Runtime.evaluate",
            {
                "expression": f"(()=>{{ const el=document.querySelector('{selector}'); el.focus(); el.select(); return el&&el.tagName; }})()",
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
                send("Input.dispatchKeyEvent", {"type": "keyDown", "key": ch, "code": f"Key{ch.upper()}", "windowsVirtualKeyCode": ord(ch)})
                send("Input.dispatchKeyEvent", {"type": "char", "text": ch})
                send("Input.dispatchKeyEvent", {"type": "keyUp", "key": ch, "code": f"Key{ch.upper()}", "windowsVirtualKeyCode": ord(ch)})
            time.sleep(0.01)
        time.sleep(0.3)

    type_into("input#name", NAME)
    type_into("input#email", EMAIL)
    type_into("input#password", PASSWORD)

    # Click the submit button.
    rect = rpc(
        "Runtime.evaluate",
        {
            "expression": "(()=>{ const b=document.querySelector('button[type=submit]'); const r=b.getBoundingClientRect(); return JSON.stringify({x:r.x+r.width/2, y:r.y+r.height/2}); })()",
            "returnByValue": True,
        },
        timeout=10,
    )
    if rect and rect.get("result", {}).get("value"):
        r = json.loads(rect["result"]["value"])
        send("Input.dispatchMouseEvent", {"type": "mousePressed", "x": r["x"], "y": r["y"], "button": "left", "clickCount": 1})
        send("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": r["x"], "y": r["y"], "button": "left", "clickCount": 1})
    else:
        rpc("Runtime.evaluate", {"expression": "document.querySelector('button[type=submit]').click()"})
    print("Submitted signup form")

    time.sleep(2)
    drain(15)

    # Fetch response bodies for interesting requests.
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
        with open(os.path.join(OUT, "simulate_signup.png"), "wb") as f:
            f.write(base64.b64decode(screenshot["result"]["data"]))

    out = {
        "events": events,
        "bodies": bodies,
        "state": state,
        "cookies": cookies,
    }
    with open(os.path.join(OUT, "simulate_signup.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(f"Saved {len(events)} events to {OUT}/simulate_signup.json")
    ws.close()


if __name__ == "__main__":
    main()
