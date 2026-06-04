# Module 4: Adding policies

JWT authentication you implemented in the previous module tells you **who** is calling. OAuth2 scopes let you go one step further - you can restrict a token to a set of allowed operations (e.g. `gateway/get_menu` but not `gateway/create_order`). For many use cases, that is enough.

But scopes are coarse-grained. They carry high-level intent - "this client can place orders" - but they know nothing about the request payload. There is no OAuth2 scope for "this client may only order up to 2 pizzas at a time, and they cannot be pineapple." For that kind of fine-grained authorization validation you need a policy engine that can inspect not just OAuth2 scopes, but the actual tool names and arguments at request time.

In this module you will attach a **Policy Engine** to your gateway and write authorization policies that control exactly which tools each caller can invoke - and under what conditions, including rules based on the arguments passed to a tool in request body.

## Architecture

In this module you will extend your gateway implementation and add the new AgentCore Policy component:

![](./images/m04-arch.png)

## Policy Engine overview

AgentCore's Policy engine evaluates [Cedar](https://www.cedarpolicy.com/) policies on every tool call. Cedar is an open-source policy language developed by AWS - it is expressive, fast to evaluate, and formally verifiable. Policies are written as `permit` and `forbid` statements that reference the caller's identity (`principal`), the operation being performed (`action`), and the resource being accessed (`resource`). 

There are two important things to keep in mind:

- The default behaviour is **deny-all**. Without explicit **permit** policies - nothing gets through.
- **`forbid` always overrides `permit`**. A single `forbid` policy can block a request even if multiple `permit` policies would allow it.

By the end of this module you will gradually implement the following fine-grained authorization approach: 

1. JWT Validation by Gateway authorizer (from Module 3)
1. Policy engine chain
    - **Permit** all principals to perform `get-menu` action
    - **Permit** all principals to perform `create-order` action 
        - ONLY WHEN they have `gateway/create_order` scope in JWT
    - **Forbid** all principals to perform `create-order` action 
        - ONLY WHEN `pizzaId==5` (forbid ordering pineapple pizza 🚫🍍🍕). 

Let's get started!

## Step 1: Upgrade to two Cognito clients

1. In the previous module, you used a single Cognito client that had the `gateway/invoke` scope. In this module you replace it with **two clients** with different scopes:

    - **client1** - has only `gateway/get_menu` scope. It can view the menu but cannot place orders
    - **client2** - has both `gateway/get_menu` and `gateway/create_order` scopes - full access

1. Open `terraform/cognito-module4.tf` and **uncomment the entire file**. This file defines two new clients - `client1` and `client2`. Note that each client has its own scope configuration:

    ```hcl
    resource "aws_cognito_user_pool_client" "client1" {
        allowed_oauth_scopes = ["gateway/get_menu"]
        ...REDACTED...
    }

    resource "aws_cognito_user_pool_client" "client2" {
        allowed_oauth_scopes = ["gateway/get_menu", "gateway/create_order"]
        ...REDACTED...
    }
    ```

## Step 2: Add scope validation to the Gateway authorizer configuration

Edit `terraform/gateway.tf`. Inside of the `awscc_bedrockagentcore_gateway` resource update `allowed_scopes` to `["gateway/get_menu"]`
    
This is what the `awscc_bedrockagentcore_gateway` resource should look like after update:

```hcl
resource "awscc_bedrockagentcore_gateway" "pizza_shop" {
    name          = "${local.project_name}"
    description   = "MCP gateway for the pizza shop ordering tools"
    role_arn      = aws_iam_role.gateway.arn
    protocol_type = "MCP"

    authorizer_type = "CUSTOM_JWT"

    authorizer_configuration = {
        custom_jwt_authorizer = {
            discovery_url  = local.cognito_discovery_url
            allowed_scopes = ["gateway/get_menu"] # <- Updated value
        }
    }

    ...REDACTED...
```

**allowed_scopes** here means "the token must contain AT LEAST `gateway/get_menu` scope" to pass the JWT check. The `gateway/create_order` scope restriction will be enforced later by a Cedar policy.

## Step 3: Attach the Policy Engine to AgentCore Gateway

1. The Policy Engine resource is already defined at the top of `terraform/gateway-policies.tf`. 

    ```hcl
    resource "awscc_bedrockagentcore_policy_engine" "pizza_shop" {
        name = local.project_name_underscore
    }
    ```

1. Open `terraform/gateway.tf` and uncomment the `policy_engine_configuration` block inside the gateway resource:

    ```hcl
    policy_engine_configuration = {
        arn  = awscc_bedrockagentcore_policy_engine.pizza_shop.policy_engine_arn
        mode = "ENFORCE"
    }
    ```

    > Note the `mode` configuration property. It supports two options: `"LOG_ONLY"`to observe policy decisions in CloudWatch without blocking requests and `"ENFORCE"` once you are confident in your policies.

## Step 4: Deploy

Run he follwoing command in VS Code Terminal:

```bash
make redeploy-gateway
```

This deploys the changes you've implemented in previous steps - new Cognito clients, Policy Engine, and updates the gateway configuration.

Once deployment completes - let's start testing!

## Step 5: Confirm default deny

By default, Policy Engine implements `deny_all` approach. Requests are denied unless explicitly permitted. Since you still haven't defined any `permit` policies, the expected result of this test is not being able to invoke the gateway. 

1. Get a token for either client and try to list tools:

    ```bash
    make get-client1-token
    make list-tools
    ```

    Expected response:

    ```json
    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "tools": []
        }
    }
    ```

    The Policy Engine is active, but you did not create any permit policies yet - as a result, nothing is visible. 

2. Try calling a tool directly by running the following command: 

    ```bash
    make get-menu
    ```

    Expected response:

    ```json
    {
        "jsonrpc": "2.0",
        "id": 1,
        "error": {
            "code": -32002,
            "message": "Tool Execution Denied: Tool call not allowed due to policy enforcement [No policy applies to the request (denied by default).]"
        }
    }
    ```

## Step 6: Add permit_all (for illustration purposes only)

Before writing targeted policies, start with a wide-open `permit_all` just to confirm the Policy Engine is wired up correctly and traffic can flow. This policy allows every principal to call any action on any gateway resource.

1. Open `terraform/gateway-policies.tf` and uncomment the `permit_all` policy resource (lines 6-16):

    ```hcl
    # Module 4 - Step 6: Permit all (illustration only - overly permissive)
    resource "awscc_bedrockagentcore_policy" "permit_all" {
        definition = {
            cedar = {
                statement = "permit(principal, action, resource is AgentCore::Gateway);"
            }
        }
    }
    ```

2. Run the following command to deploy the updated policy configuration:

    ```bash
    make deploy-infra
    ```

    Wait for deployment to complete. 

3. Test the deployed configuration by running following commands one by one:

    ```bash
    make list-tools
    make get-menu
    ```

    With `permit_all` policy these tests are working again! 
    
However this `permit_all` is definitely overly permissive. Let's start tightening the security. 

## Step 7: Permit by tool

Let's narrow the access. Instead of allowing everything, let's explicitly permit only the `get-menu` tool. This means `create-order` is still denied for everyone - regardless of their token scopes (you'll fix it later).

1. Edit `terraform/gateway-policies.tf` and comment out (or delete) the `permit_all` policy resource (lines 6-16)

1. Uncomment `allow_get_menu` policy resource (lines 19-35). Note that this policy only permits access when action equals a very specific tool name:

    ```hcl
    permit(
        principal,
        action == AgentCore::Action::"get-menu___get-menu",
        resource == AgentCore::Gateway::"<gateway_arn>"
    );
    ```

1. Deploy your updates by running the following command in VS Code Terminal:

    ```bash
    make deploy-infra
    ```

1. Once deployed, test the new configuration by running

    ```bash
    make list-tools
    ```

    Expected result: ℹ️ The returned list only contains a single `get-menu` tool. The gateway is not returning `create-orders` tool because there's no access policy allowing you to use it. 

1. Try getting the pizza menu

    ```bash
    make get-menu
    ```

    Expected result: ✅ request successfully completes since you've created a `permit` policy for `get-menu` tool. Now this tool can be accessed by clients. 

1. Try to order pizza by running

    ```bash
    make create-order pizzaId=1
    ```

    Expected result: ❌ denied. You haven't created any `permit` policies for the `create-order` tool, so the default `deny_all` policy is still being applied. 

## Step 8: Scope-based permit for create-order

This is where Cedar and OAuth2 scopes work together! Let's create a policy that permits calling the `create-order` tool only when the caller's token contains a `gateway/create_order` scope. 

> Reminder: `client1` has only `get_menu` scope and will be denied.  `client2` has both scopes and will be allowed.

1. Edit `terraform/gateway-policies.tf` and uncomment the `allow_create_order_with_scope` policy resource (lines 38-58):

    ```hcl
    permit(
        principal,
        action == AgentCore::Action::"create-order___create-order",
        resource == AgentCore::Gateway::"<gateway_arn>"
    )
    when {
        principal.hasTag("scope") &&
        principal.getTag("scope") like "*gateway/create_order*"
    };
    ```

    Note the `when` condition. The `principal.getTag("scope")` reads the `scope` claim from the validated JWT. The `like` operator checks if the string contains `gateway/create_order`.

1. Deploy your updates by running:

    ```bash
    make deploy-infra
    ```

1. Test with `client1` (has `get_menu` scope only):

    ```bash
    make get-client1-token
    make create-order pizzaId=1
    ```

    Expected result: ❌ denied. `client1` does not have the `gateway/create_order` scope, so the `when` condition is not satisfied.

1. Test with `client2` (has both scopes):

    ```bash
    make get-client2-token
    make create-order pizzaId=1
    ```

    Expected result: ✅ order succeeds. `client2` carries the `gateway/create_order` scope, so the policy permits the call.

`client1` and `client2` now have different capabilities based on their JWT scopes, enforced at the policy layer.

But can you apply access policies not just based on JWT scopes and tool names, but even more fine-grained - based on tool invocation arguments? Let's see how you can do it!

## Step 9: Forbid pineapple pizza 🚫🍍🍕

This step demonstrates what scopes alone can never do: make a decision based on the actual tool arguments. The `forbid_pineapple` policy inspects `context.input.pizzaId` and blocks any order for pizza #5 (Pineapple Deluxe) - regardless of who is calling or what scopes they have. Even `client2` with full access will not be able order a pineapple pizza once this policy is applied.

1. Edit `terraform/gateway-policies.tf` and uncomment the `forbid_pineapple` policy resource (lines 61-80):

    ```hcl
    forbid(
        principal,
        action == AgentCore::Action::"create-order___create-order",
        resource == AgentCore::Gateway::"<gateway_arn>"
    )
    when {
        context.input.pizzaId == 5
    };
    ```

    Note the `when` condition. The`context.input` contains the tool arguments that were passed from the MCP client. This allows policies to make decisions based on the actual data being sent, not just who is calling.

1. Run the following command in VS Code Terminal to deploy your updates:

    ```bash
    make deploy-infra
    ```

1. Get a `client2` token (the only client allowed to create orders) and try ordering a Four Cheese pizza (pizzaId=3):

    ```bash
    make get-client2-token
    make create-order pizzaId=3
    ```

    Expected result: ✅ Four Cheese order succeeds. `client2` has the right scope and `pizzaId` does not equal `5`.

1. Now try ordering the pineapple pizza:

    ```bash
    make create-order pizzaId=5
    ```

    Expected response:

    ```json
    {
        "jsonrpc": "2.0",
        "id": 1,
        "error": {
            "code": -32002,
            "message": "Tool Execution Denied: Tool call not allowed due to policy enforcement [Policy evaluation denied due to forbid_pineapple-XXXXXXXXXX]"
        }
    }
    ```

    Expected result: ❌ the tool call was denied by the policy engine. The `forbid` policy matches `pizzaId=5` and blocks the request even though `allow_create_order_with_scope` policy would permit it. Remember - **Forbid always wins.**

## Congratulations!

Your gateway now enforces fine-grained authorization using Cedar policies.

- **Policy Engine** evaluates policies before every tool invocation
- **`permit` by action** controls which tools are accessible at all
- **`permit` with scope conditions** ties permissions to JWT claims
- **`forbid` with `context.input`** enforces business rules on tool arguments

This is what you've gradually implemented in this module:

| Step | Policies active | client1 (get_menu only) | client2 (get_menu + create_order) |
|---|---|---|---|
| 5 | None (engine on, no policies) | All denied | All denied |
| 6 | permit_all | Full access | Full access |
| 7 | allow_get_menu | Menu only | Menu only |
| 8 | allow_get_menu + allow_create_order_with_scope | Menu only | Menu + Orders |
| 9 | above + forbid_pineapple | Menu only | Menu + Orders (no pizza #5) |

## Next step

Head to [Module 5](m05-interceptors.md) to add a Lambda interceptor that can inspect and transform requests and responses.
