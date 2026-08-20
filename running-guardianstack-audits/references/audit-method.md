# Audit method

Use one assessor owned account and the ordinary website flow. Keep the work inside the approved origin, test window, and OPULENT security context.

## Desktop and browser

Create one clean desktop for the audit and keep it for the full run. Use a normal Chrome profile. Record enough information to resume the same desktop if email verification or operator input interrupts the flow.

Attach CDP to the active Chrome target. Use CDP to observe the browser. Do not inject application code or change application state outside normal signup, login, logout, and disposable account cleanup.

## What to capture

Before signup, record the entry URL, origin, browser version, cookies, storage keys, IndexedDB names, service workers, and the public signup request.

During signup, record:

- each navigation and redirect origin;
- the signup method;
- email verification, OAuth, or SSO steps;
- the final request before authentication;
- the first authenticated response;
- the default account role and tenant.

After signup, record:

- whether the session identifier changed;
- cookie names and their `HttpOnly`, `Secure`, `SameSite`, domain, path, and lifetime settings;
- local storage and session storage keys;
- the names of authentication headers and cookies;
- the read only session or profile request;
- refresh behavior;
- logout and revocation behavior.

## CDP evidence

Useful CDP surfaces include Page navigation events, Network request and response events, cookies, Runtime evaluation for redacted storage inventories, Storage usage, IndexedDB names, and service worker registrations.

Capture values in redacted form. A useful storage record looks like this:

```json
{
  "store": "localStorage",
  "key": "session_key_name",
  "length": 192,
  "sha256_prefix": "12ab34cd56ef"
}
```

A useful request record looks like this:

```json
{
  "method": "GET",
  "path": "/api/session",
  "status": 200,
  "authorization": "Bearer [REDACTED]",
  "response_shape": ["session", "user"]
}
```

## Attack execution

Observation finds the candidate weakness. Exploitation proves whether the weakness has security impact. Run each applicable attack once, or stop earlier when you have clear proof.

### Session fixation

Record the anonymous session identifier before signup. Complete signup or login. Check whether the authenticated session keeps the same identifier. When it does, test whether the original identifier can access the assessor account from a separate profile or terminal process.

### Session credential replay

Capture the credential used by the assessor account. From a separate process, send one request to the approved read only session or profile endpoint. Start with the credential alone. Add only headers that the browser proved necessary. Record whether the response returns the assessor identity without password, MFA, device proof, or notification.

### Browser and device binding

When approved, place the captured credential in a fresh browser profile or approved second device. Open only the assessor account session or profile page. Record whether the site accepts the credential, asks for step up verification, blocks it, or warns the account owner.

### Verification and recovery token reuse

For a link or code issued to the assessor inbox, complete the normal verification or password reset once. Try the same value one more time. Record whether it is rejected after use. Run the recovery branch only when account recovery is in scope.

### OAuth state and return checks

When signup uses OAuth or SSO, compare the authorization request and callback. Confirm that the state value is fresh. Try a callback with a missing or changed state value against the assessor flow. Record whether the site rejects it. Test only return locations already approved for the audit.

### Refresh credential reuse

When the browser uses a refresh credential, allow one normal refresh. Then try the prior refresh credential once more from the approved separate process. Record whether the server rejects the reused credential and revokes the session family.

### Logout and revocation bypass

Capture the approved read only session request before logout. Log out normally. Repeat the same request from the browser and the separate process. When available and approved, repeat after password change or sign out everywhere. Record which credentials still work.

### Account and MFA behavior

Use only assessor controlled email aliases. Compare the normal response for a new alias and an existing assessor alias to identify account enumeration. If MFA is enabled, test the ordinary recovery and remembered device paths. Record any path that reaches the assessor account without the required factor. Use no guessing, spraying, rate limit evasion, or CAPTCHA bypass.

## Attack result

Give every attack one result:

- `Succeeded` means the attack achieved the unauthorized session or control bypass on the assessor account.
- `Partly succeeded` means a security control failed, but the full account impact was not reached.
- `Blocked` means the application rejected the attack in the expected way.
- `Not applicable` means the website does not use that control.
- `Not authorized` means the current scope does not allow the attempt.

For `Succeeded` and `Partly succeeded`, create a finding with the attack steps, demonstrated impact, evidence snippet, cleanup, recommendation, and retest.

## Cleanup

Log out through the website. Confirm whether cookies and browser storage are cleared. Check whether the former session remains valid. Delete the disposable account only when policy allows it.

Stop when you see another user's data, unexpected privilege, an unapproved origin, payment, instability, or rate limiting.
