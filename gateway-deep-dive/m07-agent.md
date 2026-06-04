# Module 7: Running a local agent

Every previous module tested the gateway using raw `curl` commands and `make` targets - direct MCP calls. In this module you run a real Python agent backed by [Strands Agents SDK](https://strandsagents.com/) that connects to your gateway and uses its tools to take natural language pizza orders.

## Architecture

The agent lives in `src/agent/`. It authenticates to your gateway with a Cognito JWT, discovers the available MCP tools at startup, and hands them to the Strands `Agent` as callable functions. You interact with it through a chat loop in your terminal.

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

**Trigger the interceptor's redirect (client2 only):**

```
I'd like to order a Pineapple pizza please
```

> The interceptor from Module 5 rewrites `pizzaId=5` to `pizzaId=1`. You will see `[Tool called: create-order___create-order]` in the output - check the interceptor logs in CloudWatch to confirm the rewrite happened.

Type `exit` or `quit` to stop the agent.

## How it works under the hood

1. `make run-agent-client1` / `make run-agent-client2` launches `src/agent/agent.py` with the gateway URL and Cognito credentials for the chosen client as environment variables
2. `mcp_client.py` calls `identity_helper.get_token()` to fetch a JWT from Cognito using the saved credentials
3. An MCP `streamablehttp_client` connects to the gateway with `Authorization: Bearer <token>`
4. `mcp_client.list_tools_sync()` calls `tools/list` - the gateway validates the JWT and returns the tools the token's scopes permit
5. The Strands `Agent` receives the tool list and uses them as callable functions
6. On each user message, the agent decides which tool to call, issues a `tools/call` MCP request, and streams the response back to your terminal
7. Gateway runs the full pipeline: JWT → interceptor → Cedar → target → interceptor → response

## Next step

Head to [Module 8](m08-observability.md) to explore Gateway observability with CloudWatch.
