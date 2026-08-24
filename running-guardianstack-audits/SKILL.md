---
name: running-guardianstack-audits
description: Find exploitable signup and sign-in flaws on an authorized website. Use when asked to attack a test account through the browser and CDP, prove session vulnerabilities, run a GuardianStack audit, or report results.
---

# Run a GuardianStack audit

The user gives you a website. Use the configured OPULENT security context for
authorization and the assessor-owned test identity. If the website is not covered
by that context, ask for approval before opening it.

## Goal

Find security vulnerabilities in signup, sign-in, session handling, account
recovery, and logout. Actively try to reproduce each plausible attack against the
assessor-owned account. A configuration concern is not enough — attempt the
smallest safe proof that shows whether the weakness can be exploited.

Do not stop after collecting cookies or network traffic. Turn each suspicious
behavior into an attack hypothesis, execute the bounded attack, and record
whether it succeeded or the control blocked it.

Your output is one Markdown report. Stop after the audit, cleanup, and report.
Make no code, configuration, deployment, or production control changes.

Read before you start:

- `references/audit-method.md` — the attack checklist.
- `references/report-template.md` — the report structure.
- `helpers/README.md` — the helper scripts that make this reproducible.

## Configure the audit

Set the context once at the start of the session:

```bash
export AUDIT_ORIGIN="https://platform.opulentia.ai"
export AUDIT_NAME="GuardianStack Audit"
export AUDIT_EMAIL="<assessor-owned inbox>"
export AUDIT_PASSWORD="<random strong password>"
export CDP_PORT=9223
export OUTPUT_DIR="./audit_out"
```

If no assessor-owned inbox is configured, run `python helpers/setup_mailbox.py`
to create a temporary mail.tm address. If the site rejects that domain, ask the
operator for an approved test identity — do not invent one.

## Run the audit

### 1. Start the audit desktop

Use the helper to launch a clean Chrome profile with remote debugging enabled:

```bash
./running-guardianstack-audits/helpers/start_audit_desktop.sh
```

This opens the signup page and suppresses the password-manager save dialog.
Keep this browser window for the entire audit.

### 2. Attach CDP before signup

The signup helper attaches to the running Chrome, navigates to
`$AUDIT_ORIGIN/auth?mode=signup`, enables `Network`, `Page`, `Runtime`, and
`Log`, and records every event.

Run it in a terminal:

```bash
python running-guardianstack-audits/helpers/fill_signup.py
```

This script:

- uses `Input.dispatchKeyEvent` to type into React controlled `name`, `email`,
  and `password` inputs (setting `value` directly does not update React state);
- clicks the `Create account` / `Sign up` button;
- captures the final signup request and the first authenticated response;
- saves network events, response bodies, storage state, and a screenshot to
  `$OUTPUT_DIR/simulate_signup.json` and `$OUTPUT_DIR/simulate_signup.png`.

If the site presents CAPTCHA, MFA, or a consent step, ask the operator to
handle it and then continue the capture.

### 3. Extract the session credential

Pull the `better-auth-cookie` token out of the capture:

```bash
python running-guardianstack-audits/helpers/extract_cookie.py
```

This writes `$OUTPUT_DIR/auth_cookie.txt`. Use this token only for the
authorized replay tests.

### 4. Inspect the browser state

From the capture, record:

- exact entry URL and canonical origin;
- browser version, OS, and start time;
- every origin used during signup;
- all cookies (document.cookie + `Network.getAllCookies`);
- `localStorage`, `sessionStorage`, `IndexedDB`, and service workers;
- where the durable `__Secure-better-auth.session_token` lives and every place
  the same credential appears.

Redact secret values before saving notes.

### 5. Run the attack list

Use `references/audit-method.md` to build the attack list. Run
`helpers/replay_attacks.py` to exercise the common replay, refresh, and
logout cases:

```bash
python running-guardianstack-audits/helpers/replay_attacks.py
```

It writes `$OUTPUT_DIR/replay_tests.json` with results for:

- full cookie, matching UA;
- full cookie, different UA;
- session token only;
- Convex JWT only;
- `Cookie` header instead of `better-auth-cookie`;
- Convex token minting from session token;
- Convex token with different UA;
- no credential;
- sign-out and post-logout replay.

For each suspected weakness, write the hypothesis before the attempt, execute
the smallest safe proof, and record the action, result, redacted evidence, and
cleanup. Each attack should end as `Succeeded`, `Partly succeeded`, `Blocked`,
`Not applicable`, or `Not authorized`. A `Succeeded` or `Partly succeeded` attack
becomes a finding.

### 6. Log out and clean up

Run the logout helper to revoke the server session and confirm the browser
clears state:

```bash
python running-guardianstack-audits/helpers/logout_and_clear.py
```

It writes `$OUTPUT_DIR/logout_test.json`. Check that:

- `POST /api/auth/sign-out` returns success;
- `GET /api/auth/get-session` returns `null` afterwards;
- `GET /api/auth/convex/token` returns `401 Unauthorized` afterwards;
- `better-auth_*` keys are removed from `localStorage` / `sessionStorage`.

Delete the disposable test account if the configured policy allows it. If no
account-deletion endpoint responds, record that the account still exists and the
active session was revoked.

## Write the report

Copy the structure from `references/report-template.md` into a new file named
`guardianstack-audit.md`. Replace every placeholder with the observed result.

Include every attack attempt, including attacks the application blocked. Add
short, redacted snippets from CDP, the terminal, and the browser when they
prove the result. Mark anything you could not execute as `Not authorized` or
`Not observed` with a reason. Separate what you proved from what you infer.

Return the Markdown file and state:

- the canonical origin;
- the test account alias;
- the number of confirmed findings;
- any checks you could not complete;
- the logout and cleanup state.
