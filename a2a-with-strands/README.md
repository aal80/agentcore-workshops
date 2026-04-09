# A2A Multi-Agent Workshop with Strands on AWS Bedrock AgentCore

This workshop demonstrates how to build, deploy, and connect multiple AI agents using the **Agent-to-Agent (A2A) protocol** on **AWS Bedrock AgentCore**. Three agents collaborate: a Weather Agent and a Shopping Agent act as specialized sub-agents, while an Orchestrator Agent coordinates them to answer questions like *"Find me running shoes for a marathon in Seattle next week."*

---

## Architecture

![](./images/arch.png)

**Key technologies:**

| Component | Technology |
|---|---|
| Agent framework | [Strands Agents](https://strandsagents.com) |
| Inter-agent protocol | [A2A (Agent-to-Agent)](https://google.github.io/A2A/) — JSON-RPC 2.0 |
| Hosting platform | AWS Bedrock AgentCore Runtime |
| Authentication | AWS Cognito (OAuth2 client credentials) |
| Infrastructure | Terraform |
| Container registry | Amazon ECR |
| Package manager | [uv](https://docs.astral.sh/uv/) |
| Observability | AWS X-Ray + OpenTelemetry |

---

## How the A2A Protocol Works

**A2A** (Agent-to-Agent) is Google's open standard for inter-agent communication over HTTP. Every A2A-compliant agent exposes two things:

1. **Agent Card** at `GET /.well-known/agent-card.json` — a JSON document describing the agent's name, description, capabilities, and endpoint URL. Clients use this for discovery.
2. **Message endpoint** at `POST /` — accepts JSON-RPC 2.0 messages with method `message/send`.

A message looks like:
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "messageId": "msg-001",
      "parts": [{ "kind": "text", "text": "What is the weather in Seattle?" }]
    }
  }
}
```

The response includes artifacts (the agent's answer) in the task result.

---

## How AgentCore Hosting Works

AgentCore supports two protocols for containerized agents:

**A2A mode** (`server_protocol = "A2A"` in Terraform):
- AgentCore handles JWT authentication and routes A2A JSON-RPC to the container
- Container uses Strands `A2AServer` + FastAPI, exposing both `/.well-known/agent-card.json` and `POST /`
- Used by: Weather Agent, Shopping Agent

**HTTP mode** (no `protocol_configuration` in Terraform):
- AgentCore exposes the container as a plain invocation target, called via `invoke-agent-runtime`
- Container uses `BedrockAgentCoreApp` with `@app.entrypoint`
- Used by: Orchestrator Agent

---

## Prerequisites

- **AWS CLI** configured with permissions for ECR, Bedrock AgentCore, Cognito, IAM, and CloudWatch
- **Terraform** >= 1.5
- **Docker** with `buildx` for linux/arm64 cross-compilation
- **Python 3.13+** and **uv** (`pip install uv` or `brew install uv`)
- **jq** (`brew install jq`)
- Bedrock model access enabled in your region (Claude models)

---

## Project Structure

```
.
├── Makefile                        # Build, deploy, and test commands
├── orchestrator_invoker.py         # Python script for invoking the orchestrator
├── agents/
│   ├── weather/
│   │   ├── main.py                 # Weather agent code
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   ├── shopping/
│   │   ├── main.py                 # Shopping agent code
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   └── orchestrator/
│       ├── main.py                 # Orchestrator agent code
│       ├── Dockerfile
│       └── pyproject.toml
└── terraform/
    ├── main.tf                     # Root module — uncomment agents here as you progress
    ├── providers.tf
    ├── cognito/                    # OAuth2 server (always deployed)
    ├── weather-agent/              # AgentCore runtime for weather (A2A)
    ├── shopping-agent/             # AgentCore runtime for shopping (A2A)
    └── orchestrator-agent/         # AgentCore runtime for orchestrator (HTTP)
```

---

## Step 0: Initial Setup

### Install pre-requisites

Open Terminal in VSCode and run following commands

```bash
sudo apt-get install -y make jq
```

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```bash
git clone https://github.com/aal80/agentcore-workshops
cd agentcore-workshops/a2a-with-strands
```

### Test AWS Variables

```bash
make test-vars
```

You should see:

```text
> get-vars
AWS_ACCOUNT_ID=626216789561
AWS_REGION=us-east-1
```

### Log in to ECR

```bash
make login-to-ecr
```

This resolves your AWS account ID and region (cached in `./tmp/`), then authenticates Docker against your ECR registry.

### Deploy Cognito

Open `terraform/main.tf`. By default only the `cognito` module is active — the agent modules are commented out:

```hcl
module "cognito" {
  source       = "./cognito"
  project_name = local.project_name
  region       = data.aws_region.current.region
}

# module "weather_agent" { ... }    ← commented out
# module "shopping_agent" { ... }   ← commented out
# module "orchestrator_agent" { ... } ← commented out
```

Deploy Cognito now:

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

You'll need these credentials later when the Orchestrator calls protected sub-agents.

---

## Step 1: Weather Agent

### Understanding the Code

Open [`agents/weather/main.py`](agents/weather/main.py). The Weather Agent is a Strands agent with one tool — `internet_search` — that queries DuckDuckGo for live weather data:

```python
@tool
async def internet_search(keywords: str, max_results: int = 3) -> str:
    """Search the internet for current information."""
    results = await asyncio.wait_for(
        asyncio.to_thread(lambda: DDGS().text(keywords, region="us-en", max_results=max_results)),
        timeout=8.0
    )
    # format results and return as text
```

The `@tool` decorator exposes this function to the Strands `Agent`. When a user asks about weather, the LLM decides when to call `internet_search` and with what keywords.

The agent is configured with a focused system prompt:

```python
system_prompt = """You are a Weather Assistant. Answer weather-related questions
by searching the internet for current conditions, forecasts, and weather events.
Always return concise answer in format "The weather in {location} is {temperature}. It is {conditions}"
"""

agent = Agent(system_prompt=system_prompt, tools=[internet_search], name="Weather Agent")
```

**Serving the agent via A2A:**

The Strands `A2AServer` wraps the agent and exposes it as an A2A-compliant HTTP server. `serve_at_root=True` mounts the A2A endpoints at `/` instead of `/a2a`:

```python
a2a_server = A2AServer(
    agent=agent,
    http_url=runtime_url,   # the public URL — embedded in the agent card
    serve_at_root=True,
)

app = FastAPI()
app.get("/ping")(lambda: {"status": "healthy"})   # health check
app.mount("/", a2a_server.to_fastapi_app())        # A2A at root
```

`A2AServer` automatically registers:
- `GET /.well-known/agent-card.json` — agent discovery
- `POST /` — handles `message/send` JSON-RPC requests

The agent runs on port 9000 via uvicorn:
```python
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
```

**The Dockerfile** builds for linux/arm64, installs dependencies with `uv`, and starts uvicorn with OpenTelemetry auto-instrumentation:

```dockerfile
FROM --platform=linux/arm64 ghcr.io/astral-sh/uv:python3.13-bookworm-slim
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache
COPY main.py ./
CMD ["uv", "run", "opentelemetry-instrument", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]
```

### Build the Weather Agent image and push to ECR

```bash
make build-and-push-weather-agent
```

This creates the ECR repository `a2a-workshop-weather-agent` (if needed), builds the linux/arm64 image, and pushes it.

### Deploy to AgentCore

Uncomment the `weather_agent` module in `terraform/main.tf`:

```hcl
module "weather_agent" {
  source                = "./weather-agent"
  project_name          = local.project_name
  region                = data.aws_region.current.region
  ecr_repo_prefix       = local.project_name_short
  cognito_client_id     = module.cognito.client_id
  cognito_discovery_url = module.cognito.discovery_url
}
```

Then apply:

```bash
make deploy-infra
```

Terraform creates:
- An **IAM role** allowing AgentCore to pull from ECR, invoke Bedrock, and write CloudWatch/X-Ray
- An **AgentCore runtime** referencing the ECR image by digest (not `:latest` tag — immutable)
- A **JWT authorizer** validating Cognito tokens: only callers with a valid `resource/read` token can invoke this agent
- A **CloudWatch log group** at `/aws/vendedlogs/agentcore/weather-agent/applogs` with log delivery

The key Terraform block for the runtime:

```hcl
resource "aws_bedrockagentcore_agent_runtime" "weather_agent" {
  agent_runtime_artifact {
    container_configuration {
      container_uri = local.weather_agent_ecr_uri   # image@sha256:<digest>
    }
  }
  authorizer_configuration {
    custom_jwt_authorizer {
      discovery_url   = var.cognito_discovery_url   # Cognito OIDC discovery endpoint
      allowed_clients = [var.cognito_client_id]     # only our app client can call
    }
  }
  protocol_configuration {
    server_protocol = "A2A"   # AgentCore routes A2A JSON-RPC to the container
  }
}
```

The runtime URL is saved to `./tmp/weather_agent_runtime_url.txt`.

### Test

Get a Cognito bearer token first:

```bash
make get-cognito-access-token
```

This posts `client_credentials` to the Cognito token endpoint and saves the token to `./tmp/access_token.txt`.

Now test the Weather Agent:

```bash
make test-weather-agent
```

**Part 1 — Agent card retrieval:**
```bash
curl "https://bedrock-agentcore.<region>.amazonaws.com/.../invocations/.well-known/agent-card.json" \
  -H "Authorization: Bearer <token>" | jq .
```

Expected response:
```json
{
  "name": "Weather Agent",
  "description": "An agent that answers weather questions using live internet search.",
  "url": "https://bedrock-agentcore.<region>.amazonaws.com/.../invocations/",
  "capabilities": { "streaming": false }
}
```

**Part 2 — A2A message:**
```bash
curl -X POST "https://bedrock-agentcore.<region>.amazonaws.com/.../invocations/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "jsonrpc": "2.0", "id": "1", "method": "message/send",
    "params": { "message": { "role": "user", "messageId": "msg-001",
      "parts": [{ "kind": "text", "text": "What is the weather in Seattle?" }] } }
  }' | jq .result.artifacts
```

The agent calls `internet_search`, Claude formats the result, and the response arrives as A2A artifacts.

---

## Step 2: Shopping Agent

### Understanding the Code

Open [`agents/shopping/main.py`](agents/shopping/main.py). The Shopping Agent follows the exact same pattern as the Weather Agent. Its tool `search_amazon` prefixes queries with `site:amazon.com` to return product results with titles and links:

```python
@tool
async def search_amazon(query: str, max_results: int = 5) -> str:
    """Search Amazon for clothing and apparel products."""
    results = await asyncio.wait_for(
        asyncio.to_thread(lambda: DDGS().text(f"site:amazon.com {query}", region="us-en", max_results=max_results)),
        timeout=8.0
    )
    # format as numbered list with title, description, and Amazon URL
```

The system prompt focuses Claude on mapping weather conditions to specific clothing categories:

```python
system_prompt = """You are a Shopping Assistant specializing in weather-appropriate clothing.
Examples of weather-to-apparel mapping:
- Cold + snow → insulated waterproof jacket, thermal base layer, snow boots
- Hot + sunny → lightweight breathable shirt, UV-protection hat, shorts
- Rain + mild → rain jacket, waterproof shoes
"""
```

The server setup is identical to the Weather Agent — `A2AServer` + FastAPI + `/ping` health check on port 9000.

### Build and Push

```bash
make build-and-push-shopping-agent
```

### Deploy to AgentCore

Uncomment the `shopping_agent` module in `terraform/main.tf`:

```hcl
module "shopping_agent" {
  source                = "./shopping-agent"
  project_name          = local.project_name
  region                = data.aws_region.current.region
  ecr_repo_prefix       = local.project_name_short
  cognito_client_id     = module.cognito.client_id
  cognito_discovery_url = module.cognito.discovery_url
}
```

Then apply:

```bash
make deploy-infra
```

Same infrastructure as the Weather Agent (IAM role, AgentCore runtime with A2A + JWT auth, CloudWatch logs). Runtime URL saved to `./tmp/shopping_agent_runtime_url.txt`.

### Test

```bash
make test-shopping-agent
```

Sends the message `"It is raining in Seattle. What should I wear?"` as an A2A request and displays the agent card and product recommendations.

---

## Step 3: Orchestrator Agent

### Understanding the Code

Open [`agents/orchestrator/main.py`](agents/orchestrator/main.py). The Orchestrator is the most complex component — it coordinates the Weather and Shopping agents using three layers.

**Layer 1 — Cognito token management**

The Orchestrator must authenticate before calling the JWT-protected sub-agents. It fetches a bearer token using the `client_credentials` OAuth2 flow and caches it in memory (refreshing 2 minutes before expiry):

```python
_token_cache: dict = {"token": "", "expires_at": 0.0}

async def get_bearer_token() -> str:
    if time.time() < _token_cache["expires_at"] - 120:
        return _token_cache["token"]   # still valid — return cached

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(COGNITO_TOKEN_ENDPOINT, data={
            "grant_type": "client_credentials",
            "client_id": COGNITO_CLIENT_ID,
            "client_secret": COGNITO_CLIENT_SECRET,
            "scope": "resource/read",
        })
    data = resp.json()
    _token_cache["token"] = data["access_token"]
    _token_cache["expires_at"] = time.time() + data.get("expires_in", 3600)
    return _token_cache["token"]
```

The Cognito credentials arrive via environment variables set in the Terraform `environment_variables` block.

**Layer 2 — A2A client with lazy agent discovery**

Before sending a message, the Orchestrator needs each sub-agent's `AgentCard`. `A2ACardResolver` fetches it from `/.well-known/agent-card.json`. Cards are cached in module-level globals and fetched lazily on the first tool call:

```python
_weather_agent_card = None
_shopping_agent_card = None

async def discover_agents():
    httpx_client = await get_httpx_client()   # httpx client with Authorization header set

    _weather_agent_card = await A2ACardResolver(
        httpx_client=httpx_client, base_url=WEATHER_AGENT_URL
    ).get_agent_card()

    _shopping_agent_card = await A2ACardResolver(
        httpx_client=httpx_client, base_url=SHOPPING_AGENT_URL
    ).get_agent_card()
```

`send_message_to_agent()` builds an A2A `Message`, sends it, and extracts the response text. Note that `a2a_client.send_message()` yields `(Task, None)` tuples, and `Part` is a Pydantic `RootModel` so text lives at `.root.text`:

```python
async def send_message_to_agent(agent_card, message_text):
    a2a_client = ClientFactory(ClientConfig(httpx_client=httpx_client, streaming=False)).create(agent_card)

    message = Message(
        kind="message", role=Role.user,
        parts=[Part(TextPart(kind="text", text=message_text))],
        message_id=uuid4().hex,
    )

    async for event in a2a_client.send_message(message):
        task, _ = event                               # yields (Task, None) tuples
        text = task.artifacts[0].parts[0].root.text   # Part is a RootModel
        return text
```

**Layer 3 — Strands tools and the agent**

The two `@tool` functions are what the Strands Agent calls. They contain the lazy-discovery logic and delegate to `send_message_to_agent`:

```python
@tool
async def send_message_to_weather_agent(location: str, timeframe: str):
    """Retrieves weather for {location} and {timeframe}"""
    if _weather_agent_card == None:
        await discover_agents()
    return await send_message_to_agent(
        _weather_agent_card,
        f"Summarize weather for {location} for {timeframe} in less than 10 words",
    )

@tool
async def send_message_to_shopping_agent(weather_conditions: str, item: str):
    """Recommends products given weather conditions and a specific item request."""
    if _shopping_agent_card == None:
        await discover_agents()
    message = f"Weather conditions: {weather_conditions}\nThe user is looking for: {item}"
    return await send_message_to_agent(_shopping_agent_card, message)
```

The system prompt instructs Claude to always call both tools in sequence, combining weather and shopping into one response:

```python
system_prompt = """You are a personal weather-to-wardrobe and outdoor gear assistant.

For every request:
1. Extract the location and time frame from the user's prompt
2. Call send_message_to_weather_agent with that location and time frame
3. Call send_message_to_shopping_agent with:
   - weather_conditions: the result from step 2
   - item: the specific item or activity from the user's prompt
4. Present a concise combined response: weather summary followed by product recommendations
"""

agent = Agent(
    system_prompt=system_prompt,
    tools=[send_message_to_weather_agent, send_message_to_shopping_agent],
    name="Orchestrator Agent",
)
```

**The entrypoint** uses `BedrockAgentCoreApp` (HTTP mode, not A2A). It's an async generator that yields streaming events back to the caller:

```python
app = BedrockAgentCoreApp()

@app.entrypoint
async def invoke_agent(payload, context):
    prompt = payload.get("prompt", "")

    async with asyncio.timeout(120):
        async for event in agent.stream_async(prompt=prompt):
            if "message" in event or ("event" in event and "metadata" in event["event"]):
                yield event
```

**The Dockerfile** starts via `uv run main.py` which hits `if __name__ == "__main__": app.run(...)`:

```dockerfile
CMD ["uv", "run", "main.py"]
```

### Build and Push

```bash
make build-and-push-orchestrator-agent
```

### Deploy to AgentCore

Uncomment the `orchestrator_agent` module in `terraform/main.tf`:

```hcl
module "orchestrator_agent" {
  source                 = "./orchestrator-agent"
  project_name           = local.project_name
  region                 = data.aws_region.current.region
  ecr_repo_prefix        = local.project_name_short
  cognito_client_id      = module.cognito.client_id
  cognito_client_secret  = module.cognito.client_secret
  cognito_discovery_url  = module.cognito.discovery_url
  cognito_token_endpoint = module.cognito.token_endpoint
  weather_agent_runtime_url  = module.weather_agent.runtime_url
  shopping_agent_runtime_url = module.shopping_agent.runtime_url
}
```

Then apply:

```bash
make deploy-infra
```

Unlike the sub-agents, the Orchestrator runtime has **no JWT authorizer** (callers authenticate with AWS IAM credentials) and **no `protocol_configuration`** (HTTP mode). The sub-agent URLs and Cognito credentials are injected as environment variables:

```hcl
resource "aws_bedrockagentcore_agent_runtime" "orchestrator_agent" {
  environment_variables = {
    WEATHER_AGENT_RUNTIME_URL  = var.weather_agent_runtime_url
    SHOPPING_AGENT_RUNTIME_URL = var.shopping_agent_runtime_url
    COGNITO_TOKEN_ENDPOINT     = var.cognito_token_endpoint
    COGNITO_CLIENT_ID          = var.cognito_client_id
    COGNITO_CLIENT_SECRET      = var.cognito_client_secret
  }
  network_configuration {
    network_mode = "PUBLIC"
  }
  # no protocol_configuration → HTTP mode
  # no authorizer_configuration → AWS IAM auth
}
```

The runtime ARN is saved to `./tmp/orchestrator_agent_runtime_arn.txt`.

### Test

```bash
make test-orchestrator
```

This runs `orchestrator_invoker.py`, which invokes the agent via boto3:

```python
response = client.invoke_agent_runtime(
    agentRuntimeArn=RUNTIME_ARN,
    payload='{"prompt": "Find me running shoes for a marathon in Seattle next week"}',
    contentType="application/json"
)
```

What happens inside the Orchestrator:
1. Payload arrives at `invoke_agent(payload, context)`
2. Claude reads the prompt and decides to call `send_message_to_weather_agent(location="Seattle", timeframe="next week")`
3. Orchestrator fetches a Cognito token, discovers the Weather Agent card, sends an A2A message
4. Claude receives the weather result, calls `send_message_to_shopping_agent(weather_conditions="...", item="running shoes for a marathon")`
5. Orchestrator sends A2A message to Shopping Agent
6. Claude synthesizes a final response: weather summary + product recommendations

---

## Observability

### CloudWatch Logs (Weather and Shopping Agents)

Application logs stream to CloudWatch:
- Weather Agent: `/aws/vendedlogs/agentcore/weather-agent/applogs`
- Shopping Agent: `/aws/vendedlogs/agentcore/shopping-agent/applogs`

Check these first if an agent is not responding.

### X-Ray Tracing

All agents include `aws-opentelemetry-distro`. Weather and Shopping Dockerfiles run with `opentelemetry-instrument` prefix. Traces appear in the AWS X-Ray console showing model invocations and tool calls.

---

## Teardown

```bash
make destroy
```

Runs `terraform destroy` and removes `./tmp/`. Deletes all AWS resources: Cognito, AgentCore runtimes, IAM roles, CloudWatch log groups.

> ECR repositories are not managed by Terraform. Delete them manually via the AWS console or:
> ```bash
> aws ecr delete-repository --repository-name a2a-workshop-weather-agent --force
> aws ecr delete-repository --repository-name a2a-workshop-shopping-agent --force
> aws ecr delete-repository --repository-name a2a-workshop-orchestrator-agent --force
> ```

---

## Troubleshooting

### Container restarting on AgentCore

Check CloudWatch logs for the agent. A common cause is a **protocol mismatch**: if the container serves `A2AServer` (FastAPI on port 9000) but Terraform has no `protocol_configuration` block, or vice versa. Ensure:

- `server_protocol = "A2A"` in Terraform ↔ container uses `A2AServer` + FastAPI + port 9000
- No `protocol_configuration` in Terraform ↔ container uses `BedrockAgentCoreApp` + port 8080

### 401 Unauthorized when calling sub-agents

The bearer token is expired or missing. Re-run `make get-cognito-access-token`. Tokens expire after 1 hour.

### Silent tool failures in Strands

Strands catches tool exceptions and passes the error text to Claude, which generates an apologetic response rather than raising. To debug, wrap tool internals with `try/except Exception as e: logger.exception(e)` and check CloudWatch logs for `ERROR` lines.

### `RuntimeError: Event loop is closed`

This happens when an `httpx.AsyncClient` is created in one `asyncio.run()` call and reused in a later one (e.g., at module import time, then inside uvicorn's loop). Always initialize `_httpx_client = None` at module level and create it lazily on first use inside an async function.
