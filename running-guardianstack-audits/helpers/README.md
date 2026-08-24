# GuardianStack audit helpers

These scripts make the live signup/session audit reproducible from both the
browser (computer use) and the terminal.

## Setup

```bash
pip install -r helpers/requirements.txt
```

Set the environment variables the scripts expect:

```bash
export AUDIT_ORIGIN="https://platform.opulentia.ai"
export AUDIT_NAME="GuardianStack Audit"
export AUDIT_EMAIL="<assessor-owned inbox>"
export AUDIT_PASSWORD="<random strong password>"
export CDP_PORT=9223
export OUTPUT_DIR="./audit_out"
```

## Workflow

1. `start_audit_desktop.sh` — launch a dedicated Chrome profile with remote debugging.
2. `fill_signup.py` — navigate to the signup page, type credentials, submit, and
   capture network/storage/screenshot evidence.
3. `extract_cookie.py` — pull the `better-auth-cookie` header/token out of the capture.
4. `replay_attacks.py` — run the bounded replay/refresh/logout attack table.
5. `logout_and_clear.py` — revoke the session and confirm the browser clears state.
6. `setup_mailbox.py` (optional) — provision a temporary mail.tm inbox if an
   assessor-owned address is not yet configured.

Each helper writes to `OUTPUT_DIR` (default `./audit_out`).
