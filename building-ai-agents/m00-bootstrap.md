# Module 0: Bootstrap

This module explains how to set up your workshop environment and install required dependencies. This takes about 5 minutes.

## Step 1: Enable Transaction Search 

This step enables Transaction Search, which will allow you to get enhanced observability for your agents running on AgentCore. 

To enable Trasactional Search, run the following command in VS Code Terminal:

```bash
make enable-cloudwatch-transactional-search
```

## Step 2: Installing prerequisites (ONLY WHEN NOT USING AWS-PROVIDED WORKSHOP ACCOUNTS)

#### IMPORTANT: If you're using AWS-provided Workshop accounts, all the below dependencies come pre-installed. Skip directly to [Step 3: Clone the Workshop from Github](#step-3-clone-the-workshop-from-github-section) section.

Make sure you have the following installed and configured:

| Requirement | Version | Check |
|---|---|---|
| Python | 3.13 | `python3 --version` |
| uv | latest | `uv --version` |
| AWS CLI | v2 | `aws --version` |
| Terraform | 1.5+ | `terraform --version` |
| make | any | `make --version` |

## Step 3: Clone the Workshop from Github section

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
