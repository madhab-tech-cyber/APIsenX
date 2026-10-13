# Contributing

## Branch workflow

1. Work only on the assigned member branch.
2. Link the work to a scoped issue with acceptance evidence.
3. Synchronise reviewed `main` before starting work.
4. Keep changes small and limited to the assigned issue.
5. Run relevant tests and security checks.
6. Inspect unstaged and staged changes before committing.
7. Push the branch and open or update a pull request.
8. Obtain the required owner review before merge.

Do not force push shared branches or commit directly to `main`.

The detailed requirements, reviewer matrix, approval states and merge blockers
are defined in
[`docs/coding-and-review-standards.md`](docs/coding-and-review-standards.md).

## Commit format

Use `type(scope): clear result`.

Examples:

- `feat(ebpf): emit bounded socket event`
- `test(api): deny cross-user order access`
- `fix(masking): redact bearer tokens`
- `docs(threat-model): add dashboard trust boundary`
- `chore(deps): patch vulnerable parser`

## Pull-request evidence

Describe the linked issue, what changed, why it changed, exact checks and test
counts, security impact, screenshots or measurements when relevant, required
reviewers, rollback and remaining limitations.

A zero-test run is not passing evidence. Do not merge security-sensitive work
without the required component owner and Member 1 approval.

## Sensitive data

Never commit credentials, private keys, populated `.env` files, personal data, packet captures, sensitive logs, or production information.

