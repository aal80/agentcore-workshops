# Module 0: Bootstrap

This module explains how to set up your local environment and bootstrap the base AWS infrastructure required for the workshop. This takes about 5 minutes.

> If you're using AWS-Provided Workshop accounts the below dependencies come pre-installed. You can skip directly to the [Clone the Workshop from Github](#clone-the-workshop-from-github-section) section.

## Prerequisites (ONLY WHEN NOT USING AWS-PROVIDED WORKSHOP ACCOUNTS)

- AWS Account with appropriate permissions
- Python 3.13+ installed locally
- AWS CLI configured with credentials

## Install dependencies (ONLY WHEN NOT USING AWS-PROVIDED WORKSHOP ACCOUNTS)

Make sure you have the following installed and configured:

| Requirement | Version | Check |
|---|---|---|
| Python | 3.13+ | `python3 --version` |
| uv | latest | `uv --version` |
| AWS CLI | v2 | `aws --version` |
| Terraform | 1.5+ | `terraform --version` |
| make | any | `make --version` |

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

## Explore the project structure in Visual Studio Code

![](./images/m00-vscode.png)

Below are the assets you can find in Visual Studio Code that you'll be using throughout the workshop:

1. Source code of the agent and MCP tools implemented as Lambda functions.
1. Terraform configuration for deploying AgentCore resources. You'll be updating the `workshop.tf` as you progress to introduce new resource types. 
1. Text files representing the technical support Knowledge Base.
1. Main editing window. This is where you'll be making changes to project files. 
1. Terminal window. This is where you'll be running commands. 

## Explore the infrastructure configuration

The Terraform configuration in [./terraform](terraform/) sets up shared resources used across all modules. Explore [terraform/workshop.tf](terraform/workshop.tf). During the workshop you will gradually enable modules in this file.

## Next Step

You're ready to start! Head to [Module 1](m01-local-agent.md) to build your first agent.
