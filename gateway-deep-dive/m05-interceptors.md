# Module 5: Adding interceptors

AgentCore Gateway can invoke a **Lambda interceptor** on every request and/or response, giving you a programmable hook to inspect, transform, enrich, or block traffic — without changing your tool Lambdas.

## Architecture

In this module you will implement the following architecture:

![](./images/m05-arch.png)

## What interceptors can do

| Use case | Request or Response? |
|---|---|
| Validate custom headers | REQUEST |
| Log or audit tool calls | REQUEST or RESPONSE |
| Inject context into tool arguments | REQUEST |
| Short-circuit with a synthetic response | REQUEST |
| Enrich or redact tool output | RESPONSE |
| Add metadata (currency, units, timestamp) | RESPONSE |

## How it works

When an interceptor is configured, Gateway invokes your interceptor Lambda **before** forwarding the request to the tool Lambda (REQUEST) and/or **after** receiving the tool response (RESPONSE).

```
curl / agent
    │
    ▼
Gateway receives MCP call
    │
    ├─► Interceptor Lambda (REQUEST)
    │       │
    │       └─► returns transformedGatewayRequest  ← Gateway uses this
    │
    ├─► Tool Lambda (get-menu / create-order)
    │
    ├─► Interceptor Lambda (RESPONSE)
    │       │
    │       └─► returns transformedGatewayResponse ← Gateway sends this to caller
    │
    ▼
MCP response to caller
```

If the interceptor's REQUEST response includes a `transformedGatewayResponse`, Gateway uses that as the final response and **skips the tool Lambda entirely** — useful for caching or access denial.

## Interceptor event format

Your interceptor Lambda receives an event with this structure:

**REQUEST** (before tool Lambda):
```json
{
  "interceptorInputVersion": "1.0",
  "mcp": {
    "gatewayRequest": {
      "path": "/mcp",
      "httpMethod": "POST",
      "headers": { "authorization": "Bearer ...", "mcp-session-id": "..." },
      "body": {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
          "name": "create-order___create-order",
          "arguments": { "pizzaId": 5 }
        }
      }
    },
    "gatewayResponse": null
  }
}
```

**RESPONSE** (after tool Lambda):
```json
{
  "interceptorInputVersion": "1.0",
  "mcp": {
    "gatewayRequest": { ... },
    "gatewayResponse": {
      "statusCode": 200,
      "body": {
        "jsonrpc": "2.0",
        "result": {
          "content": [{ "type": "text", "text": "{\"orderId\":\"ORD-123\",\"item\":\"Margherita\",\"total\":12.99}" }]
        }
      }
    }
  }
}
```

Your interceptor returns either a `transformedGatewayRequest` (for REQUEST) or a `transformedGatewayResponse` (for RESPONSE).

## The two interceptor variants

Open `src/lambdas/interceptor/`. There are two handler files:

**`index.js` (pass-through)** — logs the event and returns everything unchanged. Use this to understand what the gateway sends to the interceptor without modifying any traffic.

**`index2.js` (mutating)** — demonstrates two transformations:
- **REQUEST**: if `pizzaId === 5` (Pineapple Deluxe), rewrites it to `pizzaId = 1` (Margherita)
- **RESPONSE**: adds `"currency": "USD"` to every `create-order` response

## Step 1: Enable the interceptor Lambda

Open `terraform/lambdas.tf` and **uncomment the interceptor Lambda block** (the `Module 5` section at the bottom of the file).

## Step 2: Attach the interceptor to the gateway

Open `terraform/gateway.tf`. Find the `interceptor_configuration` block inside the gateway resource and **uncomment it**:

```hcl
interceptor_configuration {
  interception_points = ["REQUEST", "RESPONSE"]
  interceptor {
    lambda {
      arn = aws_lambda_function.interceptor.arn
    }
  }
  input_configuration {
    pass_request_headers = true
  }
}
```

`pass_request_headers = true` makes the original HTTP headers (including `Authorization`) available to your interceptor Lambda. Leave it `false` if you do not need headers to reduce payload size.

## Step 3: Deploy

```bash
make deploy-infra
```

This packages and deploys the interceptor Lambda, then updates the gateway. The gateway will use `index.handler` (pass-through) by default.

Let's start testing!

## Step 4: Observe the pass-through interceptor

Place an order and watch the interceptor log in CloudWatch:

```bash
make create-order pizzaId=2
```

Open the [CloudWatch console](https://console.aws.amazon.com/cloudwatch/), go to **Log groups**, find `/aws/lambda/<prefix>-pizza-gateway-interceptor`, and open the latest log stream. You should see the full REQUEST and RESPONSE events logged by `console.log`.

The response from the MCP call should be unchanged — you ordered Pepperoni and got Pepperoni.

## Step 5: Switch to the mutating interceptor

1. Open `terraform/lambdas.tf`, find the `aws_lambda_function` `"interceptor"` resource, and change:
    ```hcl
    handler = "index.handler"
    ```
    to:
    ```hcl
    handler = "index2.handler"
    ```

2. Redeploy:
    ```bash
    make deploy-infra
    ```

3. Order Pineapple Deluxe (id=5):
    ```bash
    make create-order pizzaId=5
    ```

    Expected response (note: `item` is now Margherita, not Pineapple Deluxe, and `currency` is present):

    ```json
    {
      "orderId": "ORDER-...",
      "date": "2026-...",
      "item": "Margherita",
      "total": 12.99,
      "currency": "USD"
    }
    ```

The interceptor silently swapped your order and enriched the response — the tool Lambda itself was never changed.

## How it works under the hood

1. Gateway receives the `tools/call` request for `create-order` with `pizzaId=5`
2. Gateway invokes the interceptor Lambda with `interception_points = "REQUEST"`
3. The interceptor sees `pizzaId=5` and rewrites it to `pizzaId=1` in its `transformedGatewayRequest`
4. Gateway forwards the **modified** request to the create-order Lambda
5. Lambda returns `{ item: "Margherita", total: 12.99, ... }`
6. Gateway invokes the interceptor Lambda with `interception_points = "RESPONSE"`
7. The interceptor adds `"currency": "USD"` to the response
8. Gateway returns the **enriched** response to the caller

## Congratulations!

You have added a programmable request/response interceptor to your gateway.

- **Pass-through (`index.handler`)** — observe without modifying
- **Mutating (`index2.handler`)** — rewrite inputs and enrich outputs
- The tool Lambdas themselves were never touched

## Next step

Head to [Module 6](m06-outbound-identity.md) to replace plaintext Cognito credentials with AgentCore's secure Token Vault.
