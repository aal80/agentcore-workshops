# Module 4: Scaling with AgentCore Gateway & Identity

In Module 3 your agent gained persistent memory. But every tool it uses — `get_return_policy`, `get_product_info`, `get_technical_support` — lives directly in its own codebase.

Imagine you now have to build a Sales Agent that needs `get_product_info`, a Returns Agent that needs `get_return_policy`, and an Inventory Agent that needs both. You'd copy the same tool code into every agent. Any fix or change has to be replicated everywhere. There's no central place to control which agent is allowed to call which tool.

In this module you'll solve that with **Amazon Bedrock AgentCore Gateway**. Gateway converts Lambda functions and REST APIs into [Model Context Protocol (MCP)](https://modelcontextprotocol.io/docs/getting-started/intro) endpoints — a standard that any agent framework understands. Your agents connect to a single Gateway URL and discover all available tools through the MCP protocol, regardless of where the underlying functions are deployed.

## Why this matters

| Before (Modules 1–3) | After (this module) |
|---|---|
| Each agent has its own copy of each tool | Tools are deployed once, shared across agents |
| Updating a tool means updating every agent | Update the tool implementation, such as a Lambda function, all agents see the change |
| No access control between agents and tools | Cognito JWT authentication + Cedar policies |
| Tools run on your laptop | Tools run in cloud and are always available |

## Architecture

| Resource | Purpose |
|---|---|
| Lambda function | Hosts `check_warranty_status` as a centralized tool |
| AgentCore Gateway | Exposes the Lambda as an MCP endpoint |
| Cognito User Pool | Issues JWT tokens for inbound authentication to Gateway |
| Gateway IAM Role | Allows Gateway to invoke Lambda on your behalf |
| `tmp/gateway_url.txt` | Written by Terraform for local testing |
| `tmp/cognito_token_endpoint.txt`, `tmp/cognito_client_id.txt`, `tmp/cognito_client_secret_arn.txt` | Cognito credentials written by Terraform |

## Authentication Model

In addition to scaling, AgentCore Gateway adds the security layer. It requires agents to securely authenticate both inbound and outbound connections. **AgentCore Identity** provides seamless agent identity and access management across AWS services and third-party applications such as Slack and Zoom, while supporting any standard OAuth2 identity providers such as Okta, Entra, and Amazon Cognito. In this module you'll see how AgentCore Gateway integrates with AgentCore Identity to provide secure connections via inbound and outbound authentication.

**Inbound authentication** — When an agent (or other MCP client) calls a tool in the Gateway, it passes an OAuth2 access token generated from the user's Identity Provider (IdP). AgentCore Gateway validates this token and uses it to decide whether to allow or deny the request.

**Outbound authentication** — If a tool running in the Gateway needs to access an external resource (a downstream API, a third-party service), Gateway can pass authorization credentials to that resource on the tool's behalf, using API Key, IAM, or OAuth Token.

In this lab, Amazon Cognito acts as the IdP. The `make get-cognito-access-token` command (Step 4) fetches a token from Cognito, which the agent presents to the Gateway on every request.

## Step 1: Before using Gateway

Before adding Gateway, let's confirm what the current agent is doing. Make sure the test prompt in [src/agent/agent.py](src/agent/agent.py) asks a warranty question:

```python
if __name__ == "__main__":
    # ... prompts from previous modules, comment them out
    agent("I have a Gaming Console Pro. My warranty serial number is MNO33333333. Am I covered?")
```

```bash
make test-agent-locally
```

The agent has no `check_warranty_status` tool yet — it will fall back to the knowledge base or admit it can't answer. There's nothing stopping any future agent from calling the same tools with no authentication.

## Step 2: Deploy the Gateway infrastructure

Open [terraform/workshop.tf](terraform/workshop.tf) and uncomment the `gateway` module:

```hcl
module "gateway" {
  source       = "./gateway"
  project_name = local.project_name
  region       = data.aws_region.current.region
}
```

Then deploy:

```bash
make deploy-infra
```

This will:
1. Deploy a Lambda function containing `check_warranty_status`
2. Create a Cognito User Pool and App Client for inbound JWT authentication
3. Create the AgentCore Gateway with the Cognito JWT authorizer
4. Register the Lambda as a Gateway target, exposing the tool as an MCP tool
5. Write `tmp/gateway_url.txt`, `tmp/cognito_token_endpoint.txt`, `tmp/cognito_client_id.txt`, and `tmp/cognito_client_secret_arn.txt`

Verify the Gateway is active in the AWS Console:

1. Open the [Amazon Bedrock AgentCore console](https://console.aws.amazon.com/bedrock-agentcore/)
2. In the left navigation, go to **Build → Gateway**
3. You should see `<prefix>-customersupport-gw` with status **Active**
4. Click into it and confirm the **Targets** tab shows the Lambda target with the `check_warranty_status` tool

## Step 3: Understand the centralized tool

The Lambda behind the Gateway hosts one tool. Examine the deployed code at [src/lambdas/tool-check-warranty-status/handler.py](src/lambdas/tool-check-warranty-status/handler.py).

**`check_warranty_status`** — a new tool not available in earlier modules. It checks warranty coverage given a product serial number and optionally a customer email:

```python
def lambda_handler(event, context):
    serial_number  = event.get("serial_number", "")
    customer_email = event.get("customer_email")
    # looks up warranty coverage from customer database
```

The tool schema that describes this to the Gateway is defined inline in [terraform/gateway/gateway.tf](terraform/gateway/gateway.tf) as an `inline_payload` block. It tells Gateway the tool name, description, and input parameters — the same information the `@tool` docstring would provide locally.

## Step 4: Get a Cognito access token

The Gateway requires a valid JWT token for every request. Fetch one using the Cognito credentials written by Terraform:

```bash
make get-cognito-access-token
```

This reads `tmp/cognito_token_endpoint.txt`, `tmp/cognito_client_id.txt`, and retrieves the client secret from AWS Secrets Manager using the ARN in `tmp/cognito_client_secret_arn.txt`, then calls the Cognito token endpoint and writes the resulting token to `tmp/access_token.txt`.

## Step 5: Connect the agent to Gateway

Open [src/agent/agent.py](src/agent/agent.py). You'll find the Gateway integration already wired in but commented out. Make the following changes:

**Import `mcp_tools_list` from the MCP client module:**

```python
from tools.return_policy import get_return_policy
from tools.product_info import get_product_info
from tools.tech_support import get_technical_support
from mcp_client import mcp_tools_list
```

**Update the Agent initialization** to merge local tools with MCP tools from Gateway:

```python
agent = Agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[
        get_product_info,
        get_return_policy,
        get_technical_support,
    ] + mcp_tools_list,   # adds check_warranty_status from Gateway
    session_manager=session_manager,
)
```

`mcp_tools_list` is populated in [src/agent/mcp_client.py](src/agent/mcp_client.py) by calling `mcp_client.list_tools_sync()` against the Gateway. The agent sees the remote tool exactly like a local `@tool`-decorated function.

## Step 6: Run the agent with Gateway tools

`make test-agent-locally` already picks up the Gateway env vars automatically from `tmp/`. Just run:

```bash
make test-agent-locally
```

Try a few prompts to exercise all tools:

```python
if __name__ == "__main__":
    agent("I have a Gaming Console Pro. My warranty serial number is MNO33333333. Am I covered?")
    # agent("My headphones are broken, I need technical support")
```

You should see `check_warranty_status` listed alongside the local tools when the agent enumerates available capabilities.

## How it works under the hood

1. `mcp_client.list_tools_sync()` connects to `<gateway_url>` with the JWT bearer token
2. Gateway validates the token against the Cognito User Pool's discovery URL
3. Gateway returns the MCP tool manifest (names, descriptions, schemas) from the inline tool schema defined in Terraform
4. When the agent selects `check_warranty_status`, it invokes the tool via the MCP session
5. Gateway forwards the request to the Lambda function
6. Lambda executes and returns the result
7. Gateway returns the result back to the MCP client, which surfaces it to the agent

Authentication is enforced at Step 2 — no valid JWT means no tool access, regardless of which agent is calling.

---

## Congratulations!

Your tools are now centralized and authenticated.

- **`check_warranty_status`** is a new enterprise tool available to all authorized agents without any local code
- **Cognito JWT authentication** enforces that only agents with valid tokens can call any tool
- **MCPClient** is the only change to the agent code — it connects to the Gateway and pulls tools over MCP

In the next module you'll finally deploy your agent to the cloud to run on AgentCore Runtime. 
