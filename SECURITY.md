# Security Policy

## Supported code

Only the latest reviewed commit on `main` is supported. Development branches are experimental.

## Reporting a vulnerability

Do not open a public issue for a vulnerability that contains exploit details, credentials, personal information, or sensitive logs. Report it privately to the team lead and include:

- affected component and version;
- reproduction steps using the authorised lab;
- expected and observed behaviour;
- impact and suggested remediation;
- minimal, masked evidence.

Never include real credentials, production data, or third-party targets.

## Response targets

- Actively exploited critical: investigate immediately; patch or mitigate within 24 hours.
- Critical: patch within 48 hours.
- High: patch within 7 days and before release.
- Medium: patch within 30 days or document an owner and deadline.
- Low: track for planned maintenance.

Every patch must pass tests, static analysis, dependency scanning, secret scanning, and applicable container checks. Update the SBOM and remediation record after patching.

## Release requirement

Do not release with a known critical or high-severity vulnerability. Record lower-severity accepted risks with the reason, owner, mitigation, and deadline.

