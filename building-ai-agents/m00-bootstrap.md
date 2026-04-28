# Module 0: Bootstrap

This module explains how to set up your local environment and bootstrap the base AWS infrastructure required for the workshop. This takes about 5 minutes.

## Install dependencies (ONLY WHEN NOT USING AWS-PROVIDED WORKSHOP ACCOUNTS)

If you're using AWS-Provided Workshop accounts the below dependencies come pre-installed. You can skip to the [Clone the Workshop from Github](#clone-the-workshop-from-github-section) section.

## Prerequisites

Make sure you have the following installed and configured:

| Requirement | Version | Check |
|---|---|---|
| Python | 3.13+ | `python3 --version` |
| uv | latest | `uv --version` |
| AWS CLI | v2 | `aws --version` |
| Terraform | 1.5+ | `terraform --version` |
| make | any | `make --version` |

### Install QEMU (on non-ARM64 machines only)

> You can skip this step if you're running on arm64, e.g. macOS with Apple Silicon or AWS Graviton instances.

AgentCore requires container images built for ARM64. If you're running on an x86_64, install QEMU to enable cross-platform builds:

```bash
docker run --privileged --rm tonistiigi/binfmt --install arm64
ls /proc/sys/fs/binfmt_misc/qemu-aarch64
mount | grep binfmt_misc
```

This registers the ARM64 QEMU emulator with the Linux kernel via `binfmt_misc`, allowing Docker to execute ARM64 binaries during the build. You only need to do this once per machine.

### Install make, jq, uv, boto3

Install `make`, `jq`, `uv`. Below commands are using `yum`, depending on your OS you might need to use `brew`, `apt-get`, or similar package managers.

```
# Install jq
sudo yum install -y make jq

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install boto3
pip install boto3
```

## Clone the Workshop from Github section

```
git clone --no-checkout --depth 1 https://github.com/aal80/agentcore-workshops
cd agentcore-workshops
git sparse-checkout set building-ai-agents
git checkout
cd building-ai-agents
```

## Bootstrap the infrastructure

The Terraform configuration in [terraform/](terraform/) sets up shared resources used across all modules. Deploy it now:

```bash
make deploy-infra
```

This runs `terraform init && terraform apply --auto-approve` and creates:

- A random project name prefix to avoid naming conflicts
- `tmp/aws_region.txt` and `tmp/aws_account_id.txt` for use in later make targets

> All the modules in [terraform/workshop.tf](terraform/workshop.tf) are commented out at this point — this is expected, you'll enable them as you progress with the workshop.

After apply completes, verify the `tmp/` files were created:

```bash
make test-vars
```

You should see the below output (account ID and region might have different values):

```
> AWS_ACCOUNT_ID=123123123123
> AWS_REGION=us-west-2
```

## Login to ECR

```
make login-to-ecr
```

This authenticates Docker against your ECR registry using the account ID and region cached in ./tmp/.

## Next Step

You're ready to start! Head to [Module 1](m01-local-agent.md) to build your first agent.
