# Module 2 - Prerequisites & Initial Setup

In this module you will install workshop pre-requisites and use them to provision a Cognito User Pool and Client that will be used by the agents. 

## Prerequisites

- **AWS CLI** configured with permissions for ECR, Bedrock AgentCore, Cognito, IAM, and CloudWatch
- **Terraform** >= 1.5
- **Docker** with `buildx` for linux/arm64 cross-compilation
- **Python 3.13+** and **uv**
- **jq**

### Install dependencies

### Install QEMU (on non-ARM64 machines only)

> Skip this step if you're running on arm64, e.g. **macOS with Apple Silicon** or **AWS Graviton** instances.

AgentCore requires container images built for ARM64. If you're running on an x86_64, install QEMU to enable cross-platform builds:

```bash
docker run --privileged --rm tonistiigi/binfmt --install arm64
ls /proc/sys/fs/binfmt_misc/qemu-aarch64
mount | grep binfmt_misc
```

This registers the ARM64 QEMU emulator with the Linux kernel via `binfmt_misc`, allowing Docker to execute ARM64 binaries during the build. You only need to do this once per machine.

### Install make, jq, uv

Install `make, jq, uv`. Below commands are using `yum`, depending on your OS you might need to use `brew`, `apt-get`, or similar package managers. 

```bash
sudo yum install -y make jq
```

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Ensure Claude 4.5 Haiku Model is active in Amazon Bedrock

You might need this step if you've never used Bedrock before, or if you're running the workshop in AWS-provided account. 

Open [Bedrock Playground](https://us-west-2.console.aws.amazon.com/bedrock/home?region=us-west-2#/playground) and select `Claude Haiky 4.5`. 

Start chatting with the model. 
- If model responds - continue to the next step
- If you're getting an error message - wait 3-5 minutes, refresh and retry until model responds. 

### Clone the workshop from Github

```bash
git clone --no-checkout --depth 1 https://github.com/aal80/agentcore-workshops
cd agentcore-workshops
git sparse-checkout set a2a-with-strands
git checkout
cd a2a-with-strands
```

### Bootstrap the infrastructure

```bash
make deploy-infra
```

This runs `terraform apply` to create the ECR repositories used in this workshop. Once Terraform finishes, you can see files in the `./tmp/` directory with various properties used in the following steps.

### Test AWS variables

```bash
make test-vars
```

You should see:

```text
> AWS_ACCOUNT_ID=123123123123
> AWS_REGION=us-west-2
```

### Log in to ECR

```bash
make login-to-ecr
```

Authenticates Docker against your ECR registry using the account ID and region cached in `./tmp/`.

### Deploy Cognito

Open `terraform/workshop.tf` and uncomment the `cognito` module:

```hcl
module "cognito" {
  source       = "./cognito"
  project_name = local.project_name
  region       = data.aws_region.current.region
}
```

Then deploy:

```bash
make deploy-infra
```

Terraform provisions:
- A **Cognito User Pool** — the OAuth2 authorization server
- A **User Pool Domain** — provides the `/oauth2/token` endpoint
- A **Resource Server** with scope `resource/read`
- An **App Client** with `client_credentials` flow — the identity the Orchestrator uses to call sub-agents

Credentials are saved to `./tmp/`:
- `cognito_token_endpoint.txt`
- `cognito_client_id.txt`
- `cognito_client_secret.txt`

You'll need these credentials later when the Orchestrator calls the protected sub-agents.

## Next Step

[Continue to Module 3 - Setting up the Weather Agent](03-weather-agent.md)

## Workshop Table Of Contents

1. [Overview](README.md) - Overview, architecture, understanding the protocols.
1. [Prerequisites & Setup](02-prereqs.md) — Install dependencies, QEMU, bootstrap infrastructure, deploy Cognito
2. [Weather Agent](03-weather-agent.md) — Build, deploy, and test the Weather sub-agent
3. [Shopping Agent](04-shopping-agent.md) — Build, deploy, and test the Shopping sub-agent
4. [Orchestrator Agent](05-orchestrator-agent.md) — Build, deploy, and test the Orchestrator + observability & troubleshooting
5. [Cleanup](06-cleanup.md) — Destroy all AWS resources