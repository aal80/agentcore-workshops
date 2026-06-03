# Module 9: Conclusion and cleanup

## Congratulations!

You've completed the AgentCore Gateway Deep Dive! Here's what you built across all eight modules:

| Module | What you added |
|---|---|
| 1 | Learned the core Gateway concepts: targets, tool schemas, authorizers, interceptors, policy engine, and outbound identity |
| 2 | Deployed a Gateway with two Lambda-backed tools (`get-menu`, `create-order`) and called them via MCP |
| 3 | Secured inbound access with Cognito JWT authentication — unauthenticated requests rejected at the gateway |
| 4 | Enforced fine-grained authorization with Cedar policies — per-tool permissions, scope-based access, and argument-based rules |
| 5 | Added a Lambda interceptor — inspected and mutated requests and responses without touching tool code |
| 6 | Secured outbound calls to an HTTP backend with an API Key Credential Provider — key lives in the Token Vault, never in your agent |
| 7 | Ran a local Python agent against the gateway — natural language pizza ordering with Cedar policies and the interceptor in action |
| 8 | Observed the gateway in CloudWatch — application logs, interceptor logs, and end-to-end traces in GenAI Observability |

You started with a bare gateway and two Lambda functions, and ended with a fully secured, observable MCP endpoint — one that a real agent can talk to. Every security layer was additive: each module built on the previous one without breaking what came before.

The patterns you learned here apply to any domain. The Gateway's tool abstraction, JWT + Cedar authorization model, interceptor pipeline, credential injection, and observability hooks are reusable primitives. Take them and adapt them to your own backend — whether that's an internal tool catalog, a customer-facing assistant, or a multi-agent orchestration layer.

## Key takeaways

**AgentCore Gateway is protocol translation + security.** Your Lambda functions are plain handlers that know nothing about MCP. The Gateway converts MCP calls to Lambda invocations, enforces authentication and authorization, and formats the response — without code changes to your tools.

**JWT + Cedar = defense in depth.** JWT authentication verifies *who* is calling. Cedar policies answer *what they can do* and *with what arguments*. The two layers are independent — you can change policies without touching authentication, and vice versa.

**Interceptors are the right place for cross-cutting logic.** Logging, header validation, context injection, request mutation — all belong in an interceptor, not in your tool code. They're centrally configurable and run on every request.

**Secrets belong in the Token Vault.** The `aws_bedrockagentcore_api_key_credential_provider` resource stores credentials in AgentCore's managed vault. The gateway retrieves and injects them at request time — they never appear in your agent, your MCP client, or Terraform state.

**Observability is built in.** Application logs and X-Ray traces flow automatically once you wire the CloudWatch Log Delivery resources. No SDK instrumentation required in your tool code.

## Cleanup

```bash
make destroy
```

This runs `terraform destroy --auto-approve` and removes the `tmp/` directory.

## Next steps

**Amazon Bedrock AgentCore**
- [AgentCore Developer Guide](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/what-is-bedrock-agentcore.html) — full reference for Gateway, Identity, Runtime, Memory, and Observability
- [AgentCore Gateway](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway.html) — authorizer types, HTTP targets, MCP server targets
- [AgentCore Identity](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/identity.html) — workload identity, credential providers, Token Vault, OAuth2 flows
- [Cedar policy language](https://www.cedarpolicy.com/learn) — conditions, entity types, schema validation

**Companion workshops**
- [Building AI Agents with Amazon Bedrock AgentCore](https://github.com/aal80/agentcore-workshops/tree/main/building-ai-agents) — AgentCore Runtime, Memory, Knowledge Base, and Observability from the agent's perspective, including the Agent → Gateway identity pattern

**Strands Agents SDK**
- [Strands Agents documentation](https://strandsagents.com) — tool definitions, model providers, MCP integration, multi-agent patterns
- [Strands Agents GitHub](https://github.com/strands-agents/sdk-python) — source, examples, and community
