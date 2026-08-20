# Create the OPULENT GuardianStack audit automation

Use this prompt to create the OPULENT automation. Install the sibling `running-guardianstack-audits` folder with it.

```text
Create an OPULENT automation named "GuardianStack website session audit".

The user gives the automation one website URL.

The goal is to find exploitable security vulnerabilities in signup, sign-in, session handling, account recovery, and logout. The automation must try to execute each plausible attack against the assessor owned account. It must report attacks that succeeded, partly succeeded, and were blocked.

Load the configured OPULENT security context. Confirm that the website is authorized. If it is not covered, ask for approval and stop.

Load running-guardianstack-audits/SKILL.md and follow it.

Use your computer to create one clean desktop for the website. Keep the same desktop through signup, email verification, CDP capture, logout, and cleanup.

Open the website in Chrome and attach CDP before signup. Create one account with the configured test email. Follow the normal signup and verification path. Ask the operator to complete CAPTCHA, MFA, or consent when needed.

Record the entry URL, canonical origin, redirects, browser version, cookies, storage, session rotation, authentication request, refresh behavior, and logout behavior. Redact secret values before saving evidence. Treat each suspicious behavior as an attack hypothesis and attempt the smallest safe proof.

After login, open the terminal. Run every applicable attack in references/audit-method.md that the security context allows. This includes session fixation, credential replay, browser or device binding bypass, one time token reuse, OAuth state checks, refresh reuse, logout revocation bypass, and assessor only account or MFA checks. Use one read only request when an attack needs authenticated proof. Stop each attack once the result is clear.

For each attack, record the hypothesis, action taken, result, redacted evidence, demonstrated impact, and cleanup. Use Succeeded, Partly succeeded, Blocked, Not applicable, or Not authorized. Create a finding for every successful or partly successful attack.

Log out and clean up the test account according to policy. Record any session or desktop that remains active.

Write one file named guardianstack-audit.md using references/report-template.md. Include the full attack coverage table and short redacted snippets that prove each result. Return the Markdown file and a short completion message. Create no other report format.
```
