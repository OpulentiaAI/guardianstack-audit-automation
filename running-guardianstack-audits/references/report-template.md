# GuardianStack session audit: {{canonical_origin}}

Confidential. Authorized recipients only.

## Executive summary

{{Summarize what was tested, the main result, and the practical risk in plain language.}}

## Website and account

| Field | Result |
| --- | --- |
| Entry URL | {{entry_url}} |
| Canonical origin | {{canonical_origin}} |
| Audit date | {{date}} |
| Browser and operating system | {{browser_and_os}} |
| Test account alias | {{account_alias}} |
| Signup method | {{signup_method}} |
| Final account role | {{account_role}} |

## Signup and origin record

{{Describe the signup path and list each origin in order. Note verification, MFA, CAPTCHA, OAuth, or SSO steps.}}

## Session controls

| Check | Result | What was observed |
| --- | --- | --- |
| Anonymous session changed after signup | {{Pass, Fail, or Not observed}} | {{observation}} |
| Session cookie settings | {{Pass, Fail, or Not observed}} | {{observation}} |
| Credential in browser storage | {{Pass, Fail, or Not observed}} | {{observation}} |
| Duplicate credential storage | {{Pass, Fail, or Not observed}} | {{observation}} |
| Read only session replay | {{Pass, Fail, or Not authorized}} | {{observation}} |
| Logout and revocation | {{Pass, Fail, or Not observed}} | {{observation}} |

## Attack attempts

| Attack | Hypothesis | Action taken | Result | Evidence |
| --- | --- | --- | --- | --- |
| Session fixation | {{hypothesis}} | {{bounded attempt}} | {{Succeeded, Partly succeeded, Blocked, Not applicable, or Not authorized}} | {{redacted evidence}} |
| Session credential replay | {{hypothesis}} | {{bounded attempt}} | {{result}} | {{redacted evidence}} |
| Browser or device binding bypass | {{hypothesis}} | {{bounded attempt}} | {{result}} | {{redacted evidence}} |
| Verification or recovery token reuse | {{hypothesis}} | {{bounded attempt}} | {{result}} | {{redacted evidence}} |
| OAuth state or return check | {{hypothesis}} | {{bounded attempt}} | {{result}} | {{redacted evidence}} |
| Refresh credential reuse | {{hypothesis}} | {{bounded attempt}} | {{result}} | {{redacted evidence}} |
| Logout or revocation bypass | {{hypothesis}} | {{bounded attempt}} | {{result}} | {{redacted evidence}} |
| Account enumeration or MFA bypass | {{hypothesis}} | {{bounded attempt}} | {{result}} | {{redacted evidence}} |

{{Add any other attack suggested by the observed signup or session flow. Report attacks that were blocked as well as attacks that succeeded.}}

## Findings

### F-001. {{Finding title}}

Severity: {{Critical, High, Medium, Low, or Informational}}

Status: {{Confirmed, Needs review, or Not observed}}

Observed behavior:

{{State only what the browser, CDP capture, or replay showed.}}

Attack executed:

{{State the exact bounded attack that was attempted against the test account and whether it succeeded.}}

Evidence snippet:

```json
{{Paste a short redacted CDP or storage snippet.}}
```

Demonstrated impact:

{{State what the test account proof showed.}}

Possible impact:

{{Label any wider risk as an inference.}}

Recommendation:

{{Give the direct control change.}}

Retest:

{{State the smallest check that would prove the issue is fixed.}}

{{Repeat the finding section for each confirmed or needs review finding. Remove the example when there are no findings.}}

## Replay evidence

```http
GET {{approved_read_only_path}}
Authorization: Bearer [REDACTED]

HTTP {{status}}
{{redacted_response_shape}}
```

{{State whether the site required a password, MFA, device proof, or user notification. Write Not authorized when replay was outside scope.}}

## Logout and cleanup

| Item | Final state |
| --- | --- |
| Test account | {{deleted, retained, or blocked}} |
| Browser cookies | {{cleared, retained, or not observed}} |
| Local and session storage | {{cleared, retained, or not observed}} |
| Server session | {{revoked, active, or not observed}} |
| Desktop | {{closed or retained until date}} |

## Limitations

{{List anything the audit could not verify and why.}}

## Evidence notes

{{List the redacted screenshots, CDP records, request summaries, and timestamps used for the report. Do not include live credentials or unrelated personal data.}}
