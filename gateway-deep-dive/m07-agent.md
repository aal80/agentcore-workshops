# Module 7: Running a local agent

Every previous module tested the gateway using direct MCP calls with `curl` commands and `make` targets. In this module you run a real AI agent backed by [Strands Agents SDK](https://strandsagents.com/) that connects to your gateway and uses its tools to process natural language pizza orders.

## Architecture

The agent code lives in `src/agent/`. It authenticates to your gateway with a Cognito JWT, discovers the available MCP tools at startup, and hands them to the Strands `Agent` instance as callable functions. You interact with it through a chat loop in your terminal.

```python
# Retrieving tools in mcp_client.py
mcp_client = MCPClient(lambda: streamablehttp_client(
    GATEWAY_URL,
    headers={"Authorization": f"Bearer {gateway_token}"}
))

mcp_client.start()
mcp_tools_list = mcp_client.list_tools_sync()

# Creating an agent in agent.py
model = BedrockModel(model_id="us.anthropic.claude-sonnet-4-6")
agent = Agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[mcp_tools_list],
)
```

## Step 1: Choose your client

The gateway enforces Cedar policies based on Cognito scopes. You have two clients to choose from:

| Client |  Tools available |
|---|---|
| `client1` | `get-menu`, `get-promotions` |
| `client2` | `get-menu`, `create-order`, `get-promotions` |

Decide which client to use before running the agent - it determines what the agent can do.

## Step 2: Run the agent

Pick the client that matches what you want to test:

```bash
# client1 - browse menu and promotions only
make run-agent-client1

# client2 - full ordering capability
make run-agent-client2
```

You will see the agent connect to the gateway, discover the available tools, and drop you into a chat prompt:

```
----------------------------------------
Welcome to AgentCore Pizzeria!
Available gateway tools: 3
----------------------------------------

You (type 'exit' to quit):
```

## Step 3: Try some prompts

Here are a few prompts to explore the gateway's layers in action:

**Browse the menu:**

```
What pizzas do you have?
```

**Check promotions:**

```
Are there any promotions today?
```

**Place an order:**
```
I'd like to order a Margherita please
```

> This will only work for `client2`. `client1` is not authorized by the access policy you've created in Module 4. 

**Try to order a pineapple pizza (client2 only):**

```
I'd like to order a Pineapple pizza please
```

The interceptor from Module 5 rewrites `pizzaId=5` to `pizzaId=1`. You will see `[Tool called: create-order___create-order]` in the output, and a result like:

```text
Your order has been placed! However, it looks like the system made a substitution — here's what was confirmed:

- **Order ID:** ORDER-bf9c20ec-361c-4d3d-a6b7-8c2272007cd1
- **Item:** Margherita (substituted from Pineapple Deluxe)
- **Total:** $12.99
```

Type `exit` or `quit` to stop the agent.

## How it works under the hood

1. `make run-agent-client1` / `make run-agent-client2` launches `src/agent/agent.py` with the gateway URL and Cognito credentials for the chosen client as environment variables
2. `mcp_client.py` calls `identity_helper.get_token()` to fetch a JWT from Cognito using the saved credentials
3. An MCP `streamablehttp_client` connects to the gateway with `Authorization: Bearer <token>`
4. `mcp_client.py` calls makes a POST request ot the gateway, asking for `tools/list` - the gateway validates the JWT and returns the tools the access policies permit
5. The Strands `Agent` receives the tool list and uses them as callable functions
6. On each user prompt, the agent uses LLM to decide which tool to call, issues a `tools/call` MCP request to the gateway, and streams the response back to your terminal
7. Gateway runs the full pipeline: JWT validation → interceptor → Policy validation → target → interceptor → response.

## Next step

Head to [Module 8](m08-observability.md) to explore Gateway observability with CloudWatch.
