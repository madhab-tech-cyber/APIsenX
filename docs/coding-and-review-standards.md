# Coding and Review Standards

**Approver:** Member 1 - Team Lead and Security Architect

**Approved baseline date:** 2026-10-13

**Applies to:** Every API-Sentinel component, script, test and document

These standards approve the development process, not unfinished implementations.
Component readiness must be supported by its own tests and review evidence.

## 1. Repository and change discipline

- Work on the assigned member branch and link every change to a scoped issue.
- Synchronise reviewed `main` before starting; never commit directly to
  `main`, force push a shared branch or bypass protection.
- Keep a change limited to one reviewable result. Do not mix unrelated cleanup,
  generated output or another member's implementation.
- Stage named files only. Review `git diff`, `git status`,
  `git diff --cached --check` and `git diff --cached` before committing.
- Use `type(scope): clear result` commits and keep the pull request current.
- Do not merge security-sensitive work without the required owner review and
  passing checks.

## 2. Shared coding requirements

- Treat all external, cross-process and persisted data as untrusted. Validate
  type, length, allowed values, bounds and schema version at the receiving
  boundary.
- Apply authentication and server-side authorisation to every sensitive path.
  Default to denial when identity, ownership, role or policy context is missing.
- Keep failures explicit and safe. Do not leak credentials, internals, stack
  traces or unmasked personal data in responses or logs.
- Use bounded memory, queues, payloads, retries and timeouts. Security monitoring
  must not become an unbounded availability risk.
- Keep policy and interface formats versioned. Reject incompatible versions
  rather than guessing.
- Separate detection from blocking. A new blocking action requires deterministic
  criteria, Member 1 approval, route-specific failure behavior and tested
  rollback.
- Preserve TLS and package-signature/checksum verification. Never disable a
  security control merely to make a build or test pass.
- Avoid hidden mutable global state. Make dependencies and configuration
  explicit and testable.

## 3. Language and component expectations

### Python, analytics and mock API

- Use type annotations for public functions and Pydantic or equivalent bounded
  schemas for API inputs.
- Keep authorization decisions in testable policy functions; route handlers must
  not infer ownership from user-controlled fields.
- Use structured, privacy-safe logging. Never log bearer tokens or raw sensitive
  bodies.
- Run explicit unittest targets until repository-wide discovery is configured:

  ```bash
  python -m unittest tests/test_authorization.py tests/test_mock_api.py -v
  ```

### Rust collector and enforcement

- Use safe Rust by default. Any `unsafe` block needs a documented invariant,
  focused tests and reviewer approval.
- Bound channels, batches and retries; handle parse, transport and shutdown errors
  without panic-driven control flow.
- Run formatting, linting and tests with the repository-pinned toolchain once its
  manifest is introduced.

### eBPF layer

- Use verifier-safe bounded loops and map sizes, initialise emitted structures
  and validate every user-space event field.
- Request only the minimum Linux capabilities and document attach points,
  kernel requirements, drop behaviour and cleanup.
- Do not capture raw payloads or attempt to bypass TLS.

### Dashboard

- Enforce roles on the server for every query and action; client-side route
  guards are not an authorisation control.
- Encode untrusted output, protect state-changing requests from CSRF, avoid
  unsafe HTML rendering and display only masked evidence.
- Pin dependencies and run type, unit, accessibility and production-build checks
  once the dashboard scaffold exists.

### Scripts, CI and dependencies

- Scripts must be non-interactive, reproducible, fail on errors and target only
  the authorised lab.
- Commit manifests and lock files for each ecosystem. Do not hand-edit lock files
  except through the supported package manager.
- CI must preserve underlying exit status and fail when required tests execute
  zero cases.
- Generate an SBOM and run dependency, static, secret and applicable container
  scans before release. Findings need an owner and remediation/acceptance record.

## 4. Test and evidence standard

Behavior changes require tests that can fail for the changed behavior. Where
relevant, cover:

- one allowed case and one denied case;
- malformed, missing and boundary-value inputs;
- wrong role, tenant, owner or policy version;
- timeout, unavailable dependency and recovery behavior;
- sensitive-data leakage in errors, logs and persisted evidence; and
- concurrency, load or accuracy claims with a repeatable method and environment.

A command that executes zero tests is a failed validation step. Record passed,
failed, skipped and unrun checks separately. Do not replace meaningful tests with
syntax checks or disable assertions to obtain a green result.

## 5. Pull-request evidence and review

Every pull request must state:

- linked issue and intended result;
- changed components and interfaces;
- exact commands and test counts;
- security and privacy impact;
- performance/accuracy method when claimed;
- remaining limitations, risks and rollback; and
- required reviewers and their approval.

Security-sensitive review ownership:

| Change | Required reviewers |
|---|---|
| Scope, threat model, risk acceptance, blocking or release | Member 1 plus affected component owner |
| eBPF privileges, hooks or event schema | Members 1, 2 and receiving owner |
| Collector, enforcement, rate limit or rollback | Members 1 and 3 |
| Detection, BOLA/BFLA, masking or audit API | Members 1 and 4 |
| Authentication, ownership model or OpenAPI contract | Members 1 and 5 |
| Dashboard RBAC, CI, scans, SBOM or release automation | Members 1 and 6 |

Authors do not provide the sole approval for their own security-sensitive change.

## 6. Approval states and merge blockers

- **Approved:** scope is complete, required evidence passes, interfaces match and
  required reviewers approve.
- **Conditionally approved:** useful foundation work is present, but listed
  conditions must be resolved before integration or release.
- **Not approved:** evidence is absent, behavior contradicts policy, or a
  critical/high unmitigated security concern remains.

Block merge or release when any of these applies:

- missing issue, required review or executed test evidence;
- known critical/high vulnerability without approved remediation;
- secret, private key, real personal data or sensitive capture in the change;
- contract/interface drift without an assigned correction;
- unbounded input, queue, retry or privileged operation;
- security check bypass, disabled TLS verification or unverified artifact; or
- undocumented failure behavior for an enforcement path.

## 7. Standard pre-commit sequence

```bash
git status
git diff --check
python -m unittest tests/test_authorization.py tests/test_mock_api.py -v
python -m compileall -q src mock-api tests
git diff
git add path/to/reviewed-file
git diff --cached --check
git diff --cached
```

Add component-specific build, lint, scan and integration commands as manifests
and runnable components are introduced.
