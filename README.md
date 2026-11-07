# Learning Projects

This repository holds separate projects and exercises as I learn different tools and workflows.

## Projects

- [GitHub and GitLab CI/CD crash course](Github%20CICD/README.md) — Flask demo app, pipeline examples, and notes on the compatibility updates made for this project.
- [triage-agent](triage-agent/README.md) — an AI on-call triage agent, built up into a containerised stack.

## Linting

Every pull request runs rule-based checks from [`.github/workflows/lint.yaml`](.github/workflows/lint.yaml). The rules live in the repo, so CI and local runs agree:

| Files | Tool | Rules |
| --- | --- | --- |
| Python | [ruff](https://docs.astral.sh/ruff/) (lint and format) | [`triage-agent/pyproject.toml`](triage-agent/pyproject.toml) |
| Markdown | [markdownlint-cli2](https://github.com/DavidAnson/markdownlint-cli2) | [`.markdownlint-cli2.yaml`](.markdownlint-cli2.yaml) |
| Dockerfiles | [hadolint](https://github.com/hadolint/hadolint) | [`.hadolint.yaml`](.hadolint.yaml) |

`Github CICD/` is skipped, because it's the upstream tutorial code and has its own CI. To run the same checks before each commit:

```sh
pip install pre-commit
pre-commit install          # then commits are checked automatically
pre-commit run --all-files  # or check everything now
```

The Dockerfile hook expects `hadolint` on your `PATH`.
