# Contributing

## Branch workflow

1. Work only on the assigned member branch.
2. Synchronise reviewed `main` before starting work.
3. Keep changes small and limited to the assigned issue.
4. Run relevant tests and security checks.
5. Inspect staged files before committing.
6. Push the branch and open or update a pull request.
7. Obtain the required review before merge.

Do not force push shared branches or commit directly to `main`.

## Commit format

Use `type(scope): clear result`.

Examples:

- `feat(ebpf): emit bounded socket event`
- `test(api): deny cross-user order access`
- `fix(masking): redact bearer tokens`
- `docs(threat-model): add dashboard trust boundary`
- `chore(deps): patch vulnerable parser`

## Pull-request evidence

Describe what changed, why it changed, tests executed, security impact, screenshots or measurements when relevant, and remaining limitations.

## Sensitive data

Never commit credentials, private keys, populated `.env` files, personal data, packet captures, sensitive logs, or production information.

