# sre-tools

Infrastructure, Kubernetes and CI/CD work from an SRE, built one commit at a time. Everything here runs locally or in GitHub Actions, with no cloud bill.

## What's in the repo

| Path | What it does |
| --- | --- |
| [`.pre-commit-config.yaml`](.pre-commit-config.yaml) | Git hooks: Terraform fmt, validate and tflint; yamllint; shellcheck; secret and private key detection |
| [`.github/workflows/lint.yml`](.github/workflows/lint.yml) | Runs the same hooks on every pull request and push to `main` |
| [`.tflint.hcl`](.tflint.hcl), [`.yamllint.yaml`](.yamllint.yaml) | Linter settings shared by local hooks and CI |

## Run the checks locally

```sh
pip install pre-commit
pre-commit install          # run hooks on every commit
pre-commit run --all-files  # run them once on the whole repo
```

The Terraform hooks need `terraform` and `tflint` on your `PATH`.

## Learning log

Daily notes on what I'm learning: [sre-til](https://github.com/AnuRadhaRao/sre-til).

## License

[MIT](LICENSE)
