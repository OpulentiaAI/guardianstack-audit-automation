---
name: running-guardianstack-audits
description: Find exploitable signup and sign-in flaws on an authorized website. Use when asked to attack a test account through CDP, prove session vulnerabilities, run a GuardianStack audit, or report results.
---

# Run a GuardianStack audit

The user gives you a website. Use the configured OPULENT security context for authorization and the assessor owned test identity. If the website is not covered by that context, ask for approval before opening it.

## Goal

Find security vulnerabilities in signup, sign-in, session handling, account recovery, and logout. Actively try to reproduce each plausible attack against the assessor owned account. A configuration concern is not enough. Attempt the smallest safe proof that shows whether the weakness can be exploited.

Do not stop after collecting cookies or network traffic. Turn each suspicious behavior into an attack hypothesis, execute the bounded attack, and record whether it succeeded or the control blocked it.

Your output is one Markdown report. Stop after the audit, cleanup, and report. Make no code, configuration, deployment, or production control changes.

Read:

- `references/audit-method.md` before opening the website.
- `references/report-template.md` before writing the report.

## Run the audit

1. Parse the website and record the exact entry URL and canonical origin.
2. Use your computer to create a clean desktop for this origin. Keep that desktop through signup, verification, capture, logout, and cleanup. Reuse it only for the same audit.
3. Open the website in a normal Chrome session. Record the browser version, operating system, start time, and whether the profile already has cookies or storage for the origin.
4. Attach to the browser through CDP before signup. Keep the connection open so you can see navigation, network activity, cookies, storage, and session changes across the whole flow.
5. Create one account through the normal signup path with the configured test email. Use the site's regular verification flow. Ask the operator to handle CAPTCHA, MFA, or a consent step when needed.
6. Record every origin used during signup. Stop if the browser reaches an unapproved service, shows another user's data, grants unexpected access, or asks for payment.
7. Use CDP to capture the final request before authentication and the first authenticated response. Record request methods, paths, status codes, header names, cookie settings, and response shape. Remove credential values before saving notes.
8. Inspect local storage, session storage, cookies, IndexedDB, and service workers. For sensitive values, record the key name, length, and a short hash. Never place the value in the report.
9. Check whether the anonymous session changes after signup. Record how the browser authenticates, where the session credential lives, and whether the same credential appears in more than one place.
10. Build the attack list from `references/audit-method.md`. Run every applicable and authorized attack against the assessor owned account. Use a fresh browser profile or terminal process when the attack needs separation from the original session.
11. For each suspected weakness, write the hypothesis before the attempt. Execute the smallest safe attack that can prove or disprove it. Record the exact action, result, redacted evidence, and cleanup.
12. Continue until every listed attack is `Succeeded`, `Partly succeeded`, `Blocked`, `Not applicable`, or `Not authorized`. A vulnerability that succeeded or partly succeeded becomes a finding. A blocked attack stays in the attack coverage table.
13. Log out through the normal interface. Use CDP to confirm what the browser clears and whether the prior session still works. Delete the disposable account when the configured policy allows it.
14. Close or retain the desktop according to the configured retention policy. Record anything that remains active.

## Write the report

Copy the structure from `references/report-template.md` into a new file named `guardianstack-audit.md`. Replace every placeholder with the observed result.

Include every attack attempt, including attacks that the application blocked. Add short redacted snippets from CDP, the terminal, and the browser when they prove the result. Mark anything you could not execute as `Not authorized` or `Not observed`, with the reason. Separate what you proved from what you infer.

Return the Markdown file and state:

- the canonical origin;
- the test account alias;
- the number of confirmed findings;
- any checks you could not complete;
- the logout and cleanup state.
