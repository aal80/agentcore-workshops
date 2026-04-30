# Module 5: Deploying the Agent to AgentCore Runtime

In Module 4 your agent became a secure, gateway-connected service with centralized tools. But it still runs on your laptop. Every time your machine sleeps, the agent disappears. There's no scalable endpoint, no container to ship, and no observability pipeline to tell you what the agent is actually doing in production.

In this module you'll deploy the agent to **Amazon Bedrock AgentCore Runtime** — a fully managed container runtime purpose-built for AI agents. AgentCore Runtime handles session management, auto-scaling, and built-in observability so you can focus on agent logic instead of infrastructure.

## Why this matters

| Before (Modules 1–4) | After (this module) |
|---|---|
| Agent runs locally (`uv run agent.py`) | Agent runs as a managed cloud endpoint |
| No HTTP endpoint to call | Invokable via `aws bedrock-agentcore invoke-agent-runtime` |
| No operational visibility | CloudWatch GenAI Observability: traces, spans, token counts |
| Session state in memory | AgentCore manages session lifecycle |
| Manual scaling | Auto-scaled by the runtime |

## Architecture

| Resource | Purpose |
|---|---|
| ECR repository | Hosts the agent Docker image |
| AgentCore Runtime IAM role | Allows the runtime to pull from ECR, call Bedrock, write logs |
| AgentCore Runtime | Managed container that runs `runtime.py` |
| `tmp/ecr_repo_uri.txt` | ECR URI written by Terraform |
| `tmp/runtime_execution_role_arn.txt` | Role ARN written by Terraform |
| `tmp/agent_runtime_arn.txt` | Runtime ARN written by `make deploy-agent` |

## How AgentCore Runtime works

AgentCore Runtime wraps your agent in a managed container. You provide:

1. A Docker image hosted in the Elastic Container Registry (ECR)
2. An entrypoint that uses `BedrockAgentCoreApp` to handle the invocation lifecycle

The runtime handles the rest: routing requests to your container, managing session context through the `context` object, auto-scaling, and emitting telemetry to CloudWatch.

Your entrypoint in [src/agent/runtime.py](src/agent/runtime.py) uses four key lines:

```python
from bedrock_agentcore.runtime import BedrockAgentCoreApp   

app = BedrockAgentCoreApp()  

@app.entrypoint  
async def invoke(payload, context=None):
    ...

if __name__ == "__main__":
    app.run()  
```

The `context` object provided to your entrypoint contains `session_id`, `request_headers`, and other runtime metadata that your agent can use for session continuity and authentication.

## Step 1: Review the runtime entrypoint

Open [src/agent/runtime.py](src/agent/runtime.py) and review the structure. Compare it to [src/agent/agent.py](src/agent/agent.py):

- `runtime.py` uses `BedrockAgentCoreApp` and `@app.entrypoint` — this is what AgentCore Runtime calls
- `agent.py` is the local dev version with `if __name__ == "__main__":` — this stays unchanged for local testing
- `runtime.py` propagates the caller's JWT from `context.request_headers` to the MCP Gateway client, so the same Cognito token chain works end-to-end
- Memory session ID comes from `context.session_id`, giving the runtime control over session lifecycle

Both files share the same tools, system prompt, and memory configuration — only the invocation wrapper differs.

## Step 2: Deploy the infrastructure

## Login to ECR

```
make login-to-ecr
```

This authenticates Docker against your ECR registry using the account ID and region cached in ./tmp/.


Open [terraform/workshop.tf](terraform/workshop.tf) and uncomment the `runtime` module:

```hcl
# --- Module 5: Uncomment to deploy AgentCore Runtime infrastructure (ECR + IAM role)
module "runtime" {
  source       = "./runtime"
  project_name = local.project_name
  region       = data.aws_region.current.region
}
```

Then apply:

```bash
make deploy-infra
```

Terraform creates:
- An ECR repository for your agent image
- An IAM role that the runtime assumes, with permissions for Bedrock, ECR, CloudWatch, and X-Ray

After apply, verify the output files exist:

```bash
cat tmp/ecr_repo_uri.txt
cat tmp/runtime_execution_role_arn.txt
```

## Step 3: Build and push the agent image

The agent's [Dockerfile](src/agent/Dockerfile) builds for `linux/arm64` (matching the Lambda architecture from Module 4). It installs dependencies from `pyproject.toml` and runs `runtime.py`.

First, make sure Docker Desktop is running and QEMU is installed for cross-platform builds:

```bash
make install-qemu
```

Then build and push:

```bash
make build-agent
make push-agent
```

`build-agent` builds the image and tags it with the ECR URI. `push-agent` logs in to ECR and pushes.

> **Note:** The first build takes a few minutes. Subsequent builds are faster because most layers are cached.

## Step 4: Deploy the agent runtime

```bash
make deploy-agent
```

This calls `aws bedrock-agentcore create-agent-runtime` with:
- Your ECR image URI
- The runtime IAM role
- `MEMORY_ID` and `GATEWAY_URL` as environment variables (read from `tmp/`)

The runtime ARN is written to `tmp/agent_runtime_arn.txt`.

Check the deployment status — it takes about 2–3 minutes to reach `ACTIVE`:

```bash
make agent-status
```

You should see output like:

```json
{
  "status": "ACTIVE",
  "name": "xxxx-building-ai-agents-customer-support-agent",
  "endpoint": "https://..."
}
```

Keep running `make agent-status` until `status` is `ACTIVE` before proceeding.

## Step 5: Invoke the agent

```bash
make invoke-agent
```

This base64-encodes a test payload and calls `aws bedrock-agentcore invoke-agent-runtime`. The default prompt is:

```
My laptop is running very slow. What should I do?
```

The agent will use `get_technical_support` to retrieve relevant troubleshooting steps from the knowledge base and respond.

To invoke with a custom prompt:

```bash
make invoke-agent PROMPT="I have a Gaming Console Pro. My warranty serial number is MNO33333333. Am I covered?"
```

This prompt exercises the Gateway: the runtime agent will fetch a Cognito token (using the environment variables injected at deploy time) and call `check_warranty_status` via the MCP Gateway.

> **Note:** The first invocation after deployment may take a few extra seconds as the container warms up.

## Step 6: Observability in CloudWatch

AgentCore Runtime automatically emits traces to CloudWatch GenAI Observability. To view them:

1. Open the [CloudWatch console](https://console.aws.amazon.com/cloudwatch)
2. In the left navigation, choose **Application Signals → GenAI**
3. Find your agent runtime and select a trace

Each trace shows the full invocation: tool calls, model inputs and outputs, token counts, and latency at every step. This is the same observability pipeline you'd use in production — no code changes required.

You can also query logs directly:

```bash
aws logs filter-log-events \
  --log-group-name /aws/bedrock-agentcore/runtimes \
  --filter-pattern "ERROR" \
  --no-cli-pager \
  | jq '.events[].message'
```

## What you built

Your agent now runs as a fully managed cloud service:

- **Containerized** — reproducible, portable, version-controlled via ECR image tags
- **Scalable** — AgentCore Runtime handles traffic spikes automatically
- **Observable** — every invocation is traced end-to-end in CloudWatch GenAI Observability
- **Secure** — the runtime IAM role follows least-privilege; Cognito token propagation keeps the Gateway auth chain intact
- **Memory-aware** — session IDs come from the runtime context, giving AgentCore Memory proper session boundaries across invocations

The local development workflow is unchanged: `make test-agent-locally` still runs `agent.py` directly. `runtime.py` is the production entrypoint — same agent logic, different invocation wrapper.
