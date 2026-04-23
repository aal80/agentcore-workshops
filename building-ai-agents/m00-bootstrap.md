# Module 0: Bootstrap

Before starting Module 1, you need to set up your local environment and deploy the base AWS infrastructure. This takes about 5 minutes.

## Prerequisites

Make sure you have the following installed and configured:

| Requirement | Version | Check |
|---|---|---|
| Python | 3.13+ | `python3 --version` |
| uv | latest | `uv --version` |
| AWS CLI | v2 | `aws --version` |
| Terraform | 1.5+ | `terraform --version` |
| make | any | `make --version` |

Your AWS credentials must be configured and have permissions to create IAM roles, S3 buckets, and SSM parameters:

## Deploy the base infrastructure

The Terraform configuration in [terraform/](terraform/) sets up shared resources used across all modules. Deploy it now:

```bash
make deploy-infra
```

This runs `terraform init && terraform apply --auto-approve` and creates:

- A random project name prefix to avoid naming conflicts
- `tmp/aws_region.txt` and `tmp/aws_account_id.txt` for use in later make targets

> All the modules in [terraform/workshop.tf](terraform/workshop.tf) are commented out — this is expected, you'll enable them as you progress with the workshop.

After apply completes, verify the `tmp/` files were created:

```bash
cat tmp/aws_region.txt
cat tmp/aws_account_id.txt
```

## Next Step

You're ready to start! Head to [Module 1](m01-local-agent.md) to build your first agent.
