# Module 7: Conclusion and cleanup

Congratulations on completing the AgentCore Gateway Deep Dive!

## What you built

Over seven modules you progressively built the backend for a pizza shop AI ordering system:

| Module | What you did |
|---|---|
| 0 | Configured your environment and enabled Transactional Search |
| 1 | Learned Gateway concepts: targets, tool schemas, authorizers, policies, interceptors |
| 2 | Deployed a Gateway with two Lambda-backed tools (`get-menu`, `create-order`) and called them via MCP |
| 3 | Secured inbound access with Cognito JWT authentication (`CUSTOM_JWT` authorizer) |
| 4 | Enforced fine-grained authorization with Cedar policies (permit by tool, scope-based permit, input-based forbid) |
| 5 | Added a Lambda interceptor to inspect and transform requests and responses |
| 6 | Replaced plaintext credentials with AgentCore Token Vault, and reviewed Gateway — Lambda IAM auth |

## Key takeaways

**AgentCore Gateway is protocol translation + security.** Your Lambda functions are plain Node.js handlers that know nothing about MCP. Gateway converts MCP calls to Lambda invocations, adds authentication and authorization, and formats the response — all without code changes to your tools.

**JWT + Cedar = defense in depth.** JWT authentication verifies *who* is calling. Cedar policies answer *what they can do* and *with what arguments*. The two layers are independent: you can add, remove, or change policies without touching authentication, and vice versa.

**Interceptors are a seam, not a workaround.** Interceptors are the right place for cross-cutting concerns like logging, header validation, context injection, and response enrichment. They keep that logic out of your tool Lambdas and make it centrally configurable.

**Secrets belong in the Token Vault.** The `aws_bedrockagentcore_oauth2_credential_provider` resource stores OAuth2 credentials in AgentCore's managed Token Vault. Agents never see the `client_secret` at runtime — the Token Vault issues access tokens on their behalf.

## Architecture overview

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│  Python Agent (Strands)                                                    │
│      │                                                                     │
│      │  get_workload_access_token() ──► AgentCore Identity ──► Token Vault │
│      │  get_token() ──────────────────► Cognito ──► JWT                   │
│      │                                                                     │
│      │  POST /mcp  Authorization: Bearer <JWT>                             │
│      ▼                                                                     │
│  AgentCore Gateway                                                         │
│      ├─ JWT validation (Cognito OIDC)                                      │
│      ├─ Cedar policy evaluation                                            │
│      ├─ Interceptor Lambda (REQUEST / RESPONSE)                            │
│      │                                                                     │
│      ├──► Lambda: get-menu  (via IAM role)                                 │
│      └──► Lambda: create-order  (via IAM role)                             │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

## Cleanup

To remove all AWS resources and local artifacts:

```bash
make destroy
```

This runs `terraform destroy --auto-approve` and removes the `tmp/` directory.

> If you deployed the Token Vault resources in Module 6, Terraform will need the Cognito credentials to destroy them. Pass the same `-var` flags used during deployment, or set them as environment variables:
>
> ```bash
> TF_VAR_cognito_client_id=$(cat ./tmp/cognito_client_id.txt) \
> TF_VAR_cognito_client_secret=$(cat ./tmp/cognito_client_secret.txt) \
> TF_VAR_cognito_discovery_url=<your-discovery-url> \
> make destroy
> ```

## What to explore next

- **[AgentCore Gateway documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway.html)** — authorizer types, HTTP targets, MCP server targets
- **[Cedar policy language](https://www.cedarpolicy.com/learn)** — conditions, entity types, schema validation
- **[Strands Agents SDK](https://strandsagents.com/)** — building agents that connect to gateways
- **[Building AI Agents workshop](../building-ai-agents/readme.md)** — the companion workshop covering AgentCore Memory, Knowledge Base, Runtime, and Observability

---

*Workshop complete. Thanks for building with AgentCore!*
