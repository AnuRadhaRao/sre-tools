# sre-tools

A small but complete reliability platform, built one commit at a time.

This repo is a working portfolio from an SRE with ~8 years of production experience. It grows into a platform you could actually run: infrastructure as code, Kubernetes, GitOps delivery, observability with SLOs, CI/CD on three different systems, and the reliability practice around all of it. Every part has a design write-up, a decision record, and CI that tests it.

## Runs locally, for free

Everything here works without a cloud account:

| Layer | Local stand-in |
| --- | --- |
| AWS APIs | [LocalStack](https://github.com/localstack/localstack) |
| Terraform | `terraform test` with mock providers, `terraform plan` |
| Kubernetes | [kind](https://kind.sigs.k8s.io/) or [k3d](https://k3d.io/) |
| CI | GitHub Actions on public repos (free) |

Where a feature only exists in the real cloud (EKS, AKS), the code is written and validated with `plan` and policy checks, and the README says so.

## Roadmap

| # | Project | Folder | Status |
| --- | --- | --- | --- |
| 0 | Repo foundation: linting, CI, ADRs | `.github/`, `docs/adr/` | In progress |
| 1 | AWS landing zone in Terraform | `terraform/` | Planned |
| 2 | Kubernetes platform (kind locally, EKS module) | `k8s/` | Planned |
| 3 | GitOps with Argo CD | `gitops/` | Planned |
| 4 | Observability and SLOs | `observability/` | Planned |
| 5 | One app, three CI systems: Jenkins, TeamCity, GitHub Actions | `ci/` | Planned |
| 6 | Reliability practice: incidents, chaos, load tests, DR | `reliability/` | Planned |
| 7 | Security and policy as code | `security/` | Planned |
| 8 | Azure parity: AKS and the same patterns | `azure/` | Planned |

## Principles

- **Explain the why.** Each project has a README with the design and its trade-offs, and an ADR for every significant choice in [`docs/adr/`](docs/adr/).
- **Nothing by hand.** If it can't be recreated from this repo, it doesn't count.
- **Tested infra.** Lint, policy checks and tests run on every pull request.
- **Cheap by default.** Local first; anything that costs money says how much and how to tear it down.

## Learning log

Daily notes on what I'm learning live in [sre-til](https://github.com/AnuRadhaRao/sre-til).

## License

[MIT](LICENSE)
