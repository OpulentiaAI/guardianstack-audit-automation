# GuardianStack audit automation

This repository contains an OPULENT automation and skill for authorized website sign-in security audits.

The user supplies one website URL. The agent creates an assessor owned account, keeps one desktop for the audit, captures signup and session behavior through CDP, attempts the approved attack paths, and returns one redacted Markdown report.

## Contents

- `automation/CREATE_OPULENT_AUTOMATION_PROMPT.md` contains the automation creation prompt.
- `running-guardianstack-audits/SKILL.md` contains the core agent runbook.
- `running-guardianstack-audits/references/audit-method.md` contains the attack methods and evidence rules.
- `running-guardianstack-audits/references/report-template.md` contains the Markdown report structure.

## Scope

Use this package only for systems and accounts that the operator is authorized to test. The runbook limits attacks to an assessor owned account and bounded proof. It records successful attacks, partial attacks, blocked attacks, and checks that were outside scope.

The automation ends after cleanup and reporting. Remediation, deployment, and production control changes require separate approval.
