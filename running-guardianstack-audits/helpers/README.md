# GuardianStack audit helpers

These scripts make the live signup/session audit reproducible through a mix of
browser computer-use and terminal CDP calls. They are deliberately generic: copy
`audit_config.json.example` to `audit_config.json` and adjust the selectors,
endpoints, and auth header for the target you are auditing.

## Setup

```bash
pip install -r helpers/requirements.txt
```

Create a target config (start from the Opulent/Better Auth example):

```bash
cp running-guardianstack-audits/helpers/audit_config.json.example \
   running-guardianstack-audits/helpers/audit_config.json
```

Then set the per-run variables the scripts expect:

```bash
export AUDIT_EMAIL="<assessor-owned inbox>"
export AUDIT_PASSWORD="<random strong password>"
export AUDIT_NAME="GuardianStack Audit"
export CDP_PORT=9223
export OUTPUT_DIR="./audit_out"
```

You can also override config values with environment variables:

- `AUDIT_ORIGIN` — target origin
- `SIGNUP_PATH` / `SIGNIN_PATH` — auth page paths
- `AUTH_HEADER` — name of the header that carries the session credential
- `STORAGE_PREFIX` — prefix for auth-related `localStorage` keys

## Workflow

1. `start_audit_desktop.sh` — launch a dedicated Chrome profile with remote debugging.
2. `fill_signup.py` — navigate to the configured signup page, type into the form,
   submit, and capture network/storage/screenshot evidence.
3. `extract_cookie.py` — pull the configured authorization credential out of the
   capture and write `audit_out/auth_cookie.txt`.
4. `replay_attacks.py` — run the bounded replay/refresh/logout attack table.
5. `logout_and_clear.py` — revoke the session and confirm the browser clears state.
6. `setup_mailbox.py` (optional) — provision a temporary mail.tm inbox if no
   assessor-owned address is configured.

Each helper writes to `OUTPUT_DIR` (default `./audit_out`).

## Adapting to a new target

Edit `audit_config.json`:

- `origin`, `signup_path`, `signin_path`
- `auth_header` — the request header that carries the session (e.g.
  `better-auth-cookie`, `Cookie`, or `Authorization`)
- `selectors.signup` / `selectors.signin` — CSS selectors for the form fields
- `endpoints` — the signup, sign-in, session, sign-out, and optional secondary-token paths
- `token_keys` — if the credential is a `;`-delimited cookie string, list the
  session and optional secondary key names
- `storage_prefix` — prefix for client-side storage keys the helper should clear

If the target uses a standard `Authorization: Bearer <token>` header, set
`auth_header` to `Authorization`, leave `token_keys` empty, and the helpers will
treat the whole captured value as the credential.
