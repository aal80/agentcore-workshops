# Module 1: Understanding AgentCore Gateway

This module builds a mental model of what AgentCore Gateway is and how its parts fit together. It is a conceptual module - no AWS resources are deployed just yet.

## What are you building?

Throughout this workshop you will build a backend and MCP gateway for a pizza shop AI ordering assistant. You will implement two tools as Lambda functions and one more tool as OpenAPI-documented HTTP endpoint:

| Tool | Backend | What it does |
|---|---|---|
| `get-menu` | Lambda | Returns the current menu with pizza names and prices |
| `create-order` | Lambda | Takes a `pizzaId` argument and returns the order confirmation |
| `get-promotions` | HTTP endpoint | Returns current pizza promotions and special offers |

By the end of this workshop you will have:

- All tools accessible via a single MCP endpoint, secured with inbound JWT and outbound AWS IAM/API Key, governed by access policies
- An interceptor that inspects and modifies requests and responses
- A Strands agent that can submit pizza orders using those tools

## What are the building blocks of AgentCore Gateway?

**Gateway** is a component of [Amazon Bedrock AgentCore](https://aws.amazon.com/bedrock/agentcore) that allows you to aggregate and expose a wide variety of backend targets (HTTP endpoints, Lambda functions, MCP servers, API Gateway stages) as [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) endpoints. Any agentic framework that speaks MCP - Strands, LangChain, LangGraph, Claude Desktop, and others - can discover and call these tools through a secured gateway URL.

![](./images/m01-arch.png)

Let's examine several of Gateway's core concepts. All of them are mapped to the above diagram.

### Gateway (Module 2)

A **Gateway** is the top-level construct. It provides an MCP endpoint exposed over HTTPS (`gateway_url`) and handles:

- **Protocol translation** - Converts MCP JSON-RPC calls to the target's native invocation format and vice-versa.
- **Authentication** - Validates the caller's inbound identity and authenticates to outbound downstream targets - the agent (MCP client) never holds credentials for the target
- **Policy enforcement** - Evaluates fine-grained access policies before forwarding requests to targets
- **Interceptors** - Allows you to intercept, inspect, and modify MCP requests and responses
- **Observability** - Emits structured telemetry to CloudWatch for every tool invocation, giving you an audit trail and latency visibility out of the box
- **Semantic tool search** - Exposes a built-in search tool that lets agents find relevant tools using natural language queries rather than exact tool names — useful when your gateway exposes a large number of tools

### Gateway Targets (Module 2)

A **Target** is a backend resource registered with a Gateway, such as an HTTP endpoint, a Lambda function, or an API Gateway stage. Each target carries:

- A **tool schema** - the tool name, description, and input parameters that Gateway publishes via MCP's `tools/list`. Gateway can auto-discover schemas for MCP and HTTP targets (build from OpenAPI spec). For Lambda targets you define it inline, as you will see in the next module.
- A **credential provider** - how Gateway authenticates to the target (e.g. IAM role, API key, or OAuth2 token)

### Request authorizers (Module 3)

An **authorizer** is the inbound authentication mechanism attached to a Gateway. It runs first - before interceptors, before policy evaluation, before any target is invoked. AgentCore supports four types: `None`, `JWT`, `AWS IAM`, and `Authenticate only`.

This workshop starts with `None` in Module 2 and upgrades to `JWT` with Amazon Cognito in Module 3.

### Policy Engine (Module 4)

A **Policy Engine** is a component that evaluates fine-grained authorization policies before each tool call. Without any `permit` policy, the engine denies everything by default. Policies can be scoped to specific tools, JWT claims, or even specific arguments passed to a tool.

You will progressively strengthen security posture by adding policies in Module 4. 

### Interceptors (Module 5)

An **Interceptor** is a Lambda function that Gateway runs on every request and/or response. It can read headers, inspect the MCP payload, modify arguments, enrich responses, or short-circuit with a synthetic response entirely. 

You will build a pass-through and a mutating interceptor in Module 5.

### Outbound identity (Module 6)

When the Gateway invokes a downstream target, it authenticates using a **Credential Provider** - Gateway's IAM role, API Key, or an OAuth2 token. The calling client never holds credentials for the downstream targets.

The companion to this is AgentCore Identity's **Token Vault** — an encrypted store for long-lived secrets like API keys and OAuth2 `client_secret`. The gateway retrieves secrets from the vault at request time, so they never appear in your agent code, environment variables, or Terraform state.

You will set this up in Module 6.

### Running an AI agent (Module 7)

Once the gateway is setup, in Module 7 you will connect a real Python agent to it. The agent is built with [Strands Agents SDK](https://strandsagents.com/) — it authenticates to the gateway, discovers available tools via `tools/list`, and uses them to handle natural language pizza orders in a terminal chat loop.

### Observability (Module 8)

AgentCore Gateway emits OTEL-formatted, structured telemetry automatically. You will explore the application logs and end-to-end traces flowing through CloudWatch, and use the GenAI Observability dashboard to see what happened during your agent session in Module 8.

## Next step

Let's start building! Continue to [Module 2](m02-first-tool.md) to deploy the gateway and your first tool.
