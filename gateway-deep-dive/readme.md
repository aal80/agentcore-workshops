# AgentCore Gateway Deep Dive - Workshop

## Overview

[Amazon Bedrock AgentCore Gateway](https://aws.amazon.com/bedrock/agentcore/) converts Lambda functions and HTTP services into [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) endpoints that any agent framework can discover and call. It handles authentication, authorization, request/response transformation, and secure outbound identity — all without changes to your tool implementations.

![](./images/intro.png)

In this workshop, you will progressively build the backend for a **Pizza Shop AI ordering system**. You will expose pizza tools (get menu, create order) through AgentCore Gateway and layer on increasingly sophisticated security and transformation controls.

The workshop follows a deliberate learning arc: early modules expose raw MCP calls so you can see exactly what the protocol looks like on the wire. By Module 6 you graduate to a full AI agent built with Strands SDK that discovers and calls those same tools automatically.

## Workshop Journey

* [Module 0: Bootstrap](./m00-bootstrap.md) — Install prerequisites, clone the repo, configure your account
* [Module 1: Understanding AgentCore Gateway](./m01-gateway-basics.md) — Core concepts: MCP, targets, tool schemas, authorizers, policies. 
* [Module 2: Your first tool — no auth](./m02-first-tool.md) — Deploy two Lambda-backed pizza tools and call them via MCP using `curl`
* [Module 3: Adding JWT authentication](./m03-jwt-auth.md) — Secure inbound access with Amazon Cognito; test with `curl`
* [Module 4: Adding policies](./m04-policies.md) — Fine-grained authorization policies; test scope differences with two Cognito clients using `curl`
* [Module 5: Adding interceptors](./m05-interceptors.md) — Inspect and transform requests and responses with a Lambda interceptor; test with `curl`
* [Module 6: Outbound identity](./m06-outbound-identity.md) — Introduce a Strands agent that discovers tools from the gateway and places orders end-to-end, with credentials managed by AgentCore Token Vault
* [Module 7: Conclusion and cleanup](./m07-conclusion.md) — Recap, resources, and teardown

## Let's get started!

Next step → [Module 0: Bootstrap](./m00-bootstrap.md)
