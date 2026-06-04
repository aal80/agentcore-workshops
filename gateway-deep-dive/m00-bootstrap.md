# Module 0: Bootstrap

This module explains how to set up your workshop environment and install required dependencies. This takes about 5 minutes.

## Step 1: Install prerequisites (skip this step if you're using AWS-provided workshop accounts)

> **If you're using an AWS-provided workshop account**, all dependencies are pre-installed. Skip to [Step 2](#step-2-clone-the-workshop).

Make sure you have the following installed and configured:

| Requirement | Version | Check |
|---|---|---|
| AWS CLI | v2 | `aws --version` |
| Terraform | 1.5+ | `terraform --version` |
| Python | 3.13 | `python3 --version` |
| uv | latest | `uv --version` |
| Node.js | 22.x | `node --version` |
| make | any | `make --version` |
| jq | any | `jq --version` |

## Step 2: Clone the workshop

Copy and run the following commands in VS Code Terminal:

```bash
git clone --no-checkout --depth 1 https://github.com/aal80/agentcore-workshops
cd agentcore-workshops
git sparse-checkout set gateway-deep-dive
git checkout
cd gateway-deep-dive
```

## Step 3: Explore the project structure

Open the `gateway-deep-dive` folder in Visual Studio Code. You will find:

1. **Markdown modules** (`m01-*.md` through `m07-*.md`) - step-by-step instructions
2. **Terraform configuration** (`terraform/`) - infrastructure as code for each module
3. **Lambda source code** (`src/lambdas/`) - Lambda functions implementing pizza tools
4. **Python agent** (`src/agent/`) - an AI agent you will use in Module 7

## Step 4: Enable Transactional Search

This enables enhanced observability (CloudWatch + X-Ray) for AgentCore resources.

```bash
make enable-cloudwatch-transactional-search
```

Expected output (last line):

```text
{
    "Destination": "CloudWatchLogs",
    "Status": "PENDING"
}
```

Enabling Transactional Search can take 5–10 minutes. You do not need to wait - proceed with the workshop now.

> [OPTIONAL TROUBLESHOOTING] If you see the error below, Transactional Search is already enabled. You can safely ignore it.
> ```text
> aws: [ERROR]: An error occurred (InvalidRequestException) when calling the UpdateTraceSegmentDestination operation: The destination is already set to CloudWatchLogs
> ```

## Next step

Head to [Module 1](m01-gateway-basics.md) to understand AgentCore Gateway concepts before writing any code.
