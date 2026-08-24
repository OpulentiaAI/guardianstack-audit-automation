#!/usr/bin/env python3
"""
Create a temporary assessor mailbox using the mail.tm API.

If the site rejects disposable providers, the operator can replace the address
with an assessor-owned inbox before signup.

Environment variables:
  MAIL_API       Mail.tm API base (default: https://api.mail.tm)
  MAIL_SEED      Optional local-part seed for reproducibility
  OUTPUT_DIR     Where to write mailbox credentials (default: ./audit_out)
"""
import json
import os
import secrets

import requests

API = os.environ.get("MAIL_API", "https://api.mail.tm")
OUT = os.environ.get("OUTPUT_DIR", "./audit_out")


def main():
    os.makedirs(OUT, exist_ok=True)
    # Get a domain.
    try:
        domains = requests.get(f"{API}/domains", timeout=15).json()["hydra:member"]
    except Exception as e:
        print(f"Could not fetch mail.tm domains: {e}")
        return
    if not domains:
        raise SystemExit("No mail.tm domains available")
    domain = domains[0]["domain"]

    seed = os.environ.get("MAIL_SEED", secrets.token_hex(8))
    address = f"{seed}@{domain}"
    password = secrets.token_urlsafe(16)

    r = requests.post(
        f"{API}/accounts",
        headers={"content-type": "application/json"},
        json={"address": address, "password": password},
        timeout=15,
    )
    if r.status_code not in (200, 201):
        raise SystemExit(f"Failed to create mailbox: {r.status_code} {r.text}")

    # Get token.
    t = requests.post(
        f"{API}/token",
        headers={"content-type": "application/json"},
        json={"address": address, "password": password},
        timeout=15,
    ).json()
    token = t.get("token", "")

    creds = {
        "address": address,
        "password": password,
        "token": token,
        "api": API,
    }
    with open(os.path.join(OUT, "mailbox_creds.json"), "w") as f:
        json.dump(creds, f, indent=2)
    print(f"Created mailbox {address}; credentials saved to {OUT}/mailbox_creds.json")


if __name__ == "__main__":
    main()
