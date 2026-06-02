# Module 6: Outbound identity

This module addresses two credential management concerns that have been present since Module 3:

1. **Agent → Gateway**: The agent stores `COGNITO_CLIENT_ID` and `COGNITO_CLIENT_SECRET` in plaintext environment variables to fetch tokens. Any process that can read those env vars can call your gateway.

2. **Gateway → Lambda**: The gateway invokes Lambda using an IAM role (`gateway_iam_role`). This is already secure — but understanding the mechanism helps you extend it.

You will fix concern #1 by storing the Cognito credentials in **AgentCore's Token Vault** via a **Credential Provider**, and introduce the **Workload Identity** concept that ties a logical agent identity to a set of stored credentials.

## Concepts

### Workload Identity

A **Workload Identity** is a named, non-secret identifier for an agent or workload. Think of it as the agent's "username" — it does not contain any secrets itself. It is used to tell AgentCore *which* credential provider to use when fetching tokens.

### Credential Provider

A **Credential Provider** stores OAuth2 client credentials (`client_id` + `client_secret`) in AgentCore's managed Token Vault. When the agent needs a token, it presents its Workload Identity token to AgentCore Identity, which exchanges it for an actual OAuth2 access token — without the agent ever seeing the `client_secret`.

### The two-step token exchange

```
Agent                         AgentCore Identity              Cognito
  │                                  │                           │
  ├─► get_workload_access_token()    │                           │
  │   (identifies the workload)      │                           │
  │◄─ workload_access_token ─────────┤                           │
  │                                  │                           │
  ├─► get_token(                     │                           │
  │     provider=credential_provider │                           │
  │     auth_token=workload_token)   │                           │
  │                                  ├─► fetch from Token Vault  │
  │                                  ├─► client_credentials ─────►
  │                                  │◄─ access_token ───────────┤
  │◄─ access_token ──────────────────┤                           │
  │                                  │                           │
  ├─► POST /mcp  Authorization: Bearer <access_token>
  ▼
AgentCore Gateway
```

The agent never touches `client_id` or `client_secret` at runtime. The secrets live only in the Token Vault.

### Gateway → Lambda: IAM role (already configured)

The `gateway_iam_role {}` credential provider in the Gateway Target resource means the gateway assumes its own IAM role when invoking Lambda. This is already in place from Module 2. The IAM role policy (`gateway_invoke_lambda`) grants exactly `lambda:InvokeFunction` on the two pizza tool functions — nothing more.

## Step 1: Deploy the Token Vault resources

Open `terraform/identity.tf` and **uncomment the entire file**.

The variables (`cognito_client_id`, `cognito_client_secret`, `cognito_discovery_url`) will be passed on the command line or via `-var-file`. Terraform marks them as `ephemeral = true` so they are never persisted in state.

> **Why ephemeral?** Regular sensitive variables are still stored (encrypted) in `terraform.tfstate`. Ephemeral variables exist only in memory during the apply — the secret is written into the Token Vault via the AWS API and never touches the state file.

## Step 2: Deploy with credentials

```bash
make deploy-infra \
  -var cognito_client_id=$(cat ./tmp/cognito_client_id.txt) \
  -var cognito_client_secret=$(cat ./tmp/cognito_client_secret.txt) \
  -var cognito_discovery_url=$(cat ./tmp/cognito_token_endpoint.txt | sed 's|/oauth2/token||')/.well-known/openid-configuration
```

Or add a `deploy-identity` target to the Makefile that reads the tmp files:

```bash
make deploy-identity
```

This creates:
- `aws_bedrockagentcore_workload_identity.pizza_agent` → writes `tmp/workload_identity_name.txt`
- `aws_bedrockagentcore_oauth2_credential_provider.cognito` → stores `client_id` + `client_secret` in Token Vault, writes `tmp/credential_provider_name.txt`

## Step 3: Start the Python agent

The Python agent in `src/agent/` is pre-configured to use the Token Vault when `WORKLOAD_ID_NAME` and `CREDENTIAL_PROVIDER_NAME` are set, and fall back to plaintext Cognito credentials otherwise.

```bash
make run-agent
```

The Makefile reads both `tmp/workload_identity_name.txt` and `tmp/credential_provider_name.txt`. When both are present, the agent's `identity_helper.py` takes the Token Vault path:

```python
def get_token():
    if not CREDENTIAL_PROVIDER_NAME:
        return _get_token_from_cognito_endpoint()  # plaintext (Modules 3–5)
    else:
        return _get_token_from_token_vault()        # Token Vault (this module)
```

**Token Vault path** (`identity_helper.py`):

```python
def _get_token_from_token_vault():
    # Step 1: identify the workload
    response = identity_client.get_workload_access_token(
        workload_name=WORKLOAD_ID_NAME
    )
    workload_token = response["workloadAccessToken"]

    # Step 2: exchange for a Cognito access token
    access_token = asyncio.run(identity_client.get_token(
        provider_name=CREDENTIAL_PROVIDER_NAME,
        scopes=[COGNITO_SCOPE],
        auth_flow="M2M",
        agent_identity_token=workload_token,
    ))
    return access_token
```

## Step 4: Order a pizza through the agent

```text
User prompt (type 'exit' to quit): What pizzas do you have?
```

Expected response:

```text
[Tool called: get-menu___get-menu]

Here's our current menu:

1. Margherita — $12.99
2. Pepperoni — $14.99
3. Four Cheese — $15.99
4. BBQ Chicken — $16.99
5. Pineapple Deluxe — $15.49
6. Veggie Supreme — $14.99

What would you like to order?
```

```text
User prompt: I'll have the Four Cheese please.
```

```text
[Tool called: create-order___create-order]

Your order is confirmed! 🍕

- **Item:** Four Cheese
- **Total:** $15.99
- **Order ID:** ORD-...
```

The agent fetched a Cognito token using the Token Vault, called the Gateway with it, and the Gateway invoked the Lambda using its IAM role. No secrets were passed through the agent process.

## Gateway → Lambda: reviewing the IAM flow

Open `terraform/gateway.tf` and look at the gateway target:

```hcl
credential_provider_configuration {
  gateway_iam_role {}
}
```

When Gateway calls Lambda, it uses the IAM role defined in `aws_iam_role.gateway`. The `gateway_invoke_lambda` policy restricts this role to only `lambda:InvokeFunction` on the exact two pizza Lambda ARNs. The Lambda never receives any Cognito token — it only receives the tool arguments.

This is the correct pattern: the agent authenticates to the Gateway using OAuth2; the Gateway authenticates to Lambda using IAM. Each hop uses the appropriate authentication mechanism for that trust boundary.

## Congratulations!

Both authentication hops are now secure:

| Hop | Mechanism | Secrets in agent? |
|---|---|---|
| Agent → Gateway | OAuth2 JWT via Token Vault | No — Token Vault holds `client_secret` |
| Gateway → Lambda | IAM role | No — IAM is credential-free |

You have completed the security layers:
- ✅ Inbound JWT auth (Module 3)
- ✅ Cedar policies (Module 4)
- ✅ Secure outbound credentials via Token Vault (this module)

## Next step

Head to [Module 7](m07-conclusion.md) for a recap and cleanup instructions.
