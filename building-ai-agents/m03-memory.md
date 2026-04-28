# Module 3: Personalizing the Agent with Memory

In Module 2 your agent gained the ability to answer technical questions using grounded facts stored in the Bedrock Knowledge Base. But it still has no memory — every conversation starts from scratch. Ask it "what laptop did I ask about last time?" and it has no idea.

In this module you'll add **Amazon Bedrock AgentCore Memory** so the agent can remember customer preferences and past interactions across sessions.

## How AgentCore Memory works

AgentCore Memory is a managed service that sits between your agent and the conversation history. It organizes memory into two tiers:

- **Short-term memory (STM)** — the current session's conversation, stored immediately after each exchange
- **Long-term memory (LTM)** — persistent patterns and facts, extracted asynchronously from STM (takes 20-30 seconds) and organized by namespace using vector embeddings for semantic retrieval

Memory is organized into **strategies** that define what kind of information to store and where, for example:

| Strategy | What it captures | Example |
|---|---|---|
| `USER_PREFERENCE` | Behavioral patterns, preferences, habits | "prefers ThinkPad, budget under $1200" |
| `SEMANTIC` | Factual information from conversations | "MacBook Pro order #MB-78432 under warranty" |

Each customer's memories are isolated using **namespaces** with `{actorId}` as a placeholder — so `support/customer/{actorId}/preferences/` becomes a unique memory space per customer ID at runtime.

When the agent starts a conversation, `AgentCoreMemorySessionManager` automatically:
1. Retrieves relevant memories from both namespaces and injects them into the context
2. Stores the new conversation as an event for future LTM processing

## Architecture

| Resource | Purpose |
|---|---|
| `aws_bedrockagentcore_memory` | Memory store with USER_PREFERENCE + SEMANTIC strategies |
| IAM role | Allows Bedrock to invoke models for LTM extraction |
| `tmp/memory_id.txt` | Written by Terraform for local testing |

## Step 1: Before enabling memory

Before you add memory capabilities to your agent, let's examine the problem. 

Update `main.py` so only the prompt asking about overheating will be active, as shown below:

```python
if __name__ == "__main__":
    # Other questions
    agent("My new MacBook Pro overheating during video editing, what's the return policy?")
    # agent("what was my previous problem?")
```

```bash
make test-agent-locally
```

Then switch to the follow-up prompt and run again:

```python
if __name__ == "__main__":
    # Other questions
    # agent("My new MacBook Pro overheating during video editing, what's the return policy?")
    agent("what was my previous problem?")
```

```bash
make test-agent-locally
```

The agent has no idea what you're referring to:
```
I don't have access to your previous conversation history, so I can't see what your previous problem was. 

To help you effectively, could you please share some details about:
- What product or issue you're currently facing
- Any specific symptoms or errors you're experiencing
- When the problem started
```

It starts each run completely fresh. This is the limitation we're fixing.

## Step 2: Deploy the Memory infrastructure

Open [terraform/workshop.tf](terraform/workshop.tf) and uncomment the `memory` module:

```hcl
module "memory" {
  source       = "./memory"
  project_name = local.project_name
  region       = data.aws_region.current.region
}
```

Then deploy:

```bash
make deploy-infra
```

This creates the AgentCore Memory store with two strategies configured and writes the Memory ID to `tmp/memory_id.txt`.

Verify it was created in the AWS Console:

1. Open the [Amazon Bedrock AgentCore console](https://console.aws.amazon.com/bedrock-agentcore/)
2. In the left navigation, go to **Build → Memory**
3. You should see `<prefix>-building-ai-agents-customer-support` with status **Active**

## Step 3: Update the agent to use memory

The memory configuration is already isolated in [src/agent/memory_config.py](src/agent/memory_config.py). Examine this file to understand what's being configured:

```python
import os
import uuid
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig, RetrievalConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager

MEMORY_ID = os.environ.get("MEMORY_ID")
ACTOR_ID = "customer-123"   # In production this comes from the authenticated user identity

memory_config = AgentCoreMemoryConfig(
    memory_id=MEMORY_ID,
    session_id=str(uuid.uuid4()),
    actor_id=ACTOR_ID,
    retrieval_config={
        "support/customer/{actorId}/semantic/":    RetrievalConfig(top_k=3, relevance_score=0.2),
        "support/customer/{actorId}/preferences/": RetrievalConfig(top_k=3, relevance_score=0.2),
    }
)

session_manager = AgentCoreMemorySessionManager(memory_config)
```

Now open [src/agent/main.py](src/agent/main.py). The memory integration is already wired in but commented out. Uncomment the marked line:

```python
agent = Agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[...],

    # Uncomment when asked in Module 3
    session_manager=session_manager,        # <-- uncomment this line
)
```

The only change to the agent is swapping in `AgentCoreMemorySessionManager` via `session_manager`. Everything else — tools, model, system prompt — stays the same.

## Step 4: Repeat the test with memory enabled

Repeat the same two runs from Step 1.

**First run** — same prompt, now with memory enabled:

```python
if __name__ == "__main__":
    # Other questions
    agent("My new MacBook Pro overheating during video editing, what's the return policy?")
    # agent("what was my previous problem?")
```

```bash
make test-agent-locally
```

The agent answers as before, but this time the conversation is stored in the Short-term Memory. AgentCore asynchronously extracts it into Long-term memory — wait ~30 seconds before the next run.

**Second run** — switch back to the follow-up:

```python
if __name__ == "__main__":
    # Other questions
    # agent("My new MacBook Pro overheating during video editing, what's the return policy?")
    agent("what was my previous problem?")
```

```bash
make test-agent-locally
```

This time the agent recalls the MacBook Pro overheating issue from the previous session — without you mentioning it. 

```
Based on the context, your previous problem was **overheating issues with your MacBook Pro specifically during video editing**. 

Since you mentioned this is a new MacBook Pro that you use for video editing work, overheating during intensive tasks like video editing is a common concern, especially when rendering large files or using demanding software.
```

That's memory persistance and retrieval in action!

## How it works under the hood

1. `AgentCoreMemorySessionManager` queries both memory namespaces for context relevant to the incoming message
1. Retrieved memories are injected into the conversation context before the LLM sees the prompt
1. The LLM composes a response informed by the customer's history
1. After the response, the new exchange is stored as an STM event
1. AgentCore asynchronously processes STM events into LTM strategies (preferences + semantic facts)

## Congratulations!

Your agent now remembers customers across sessions!

- **USER_PREFERENCE** strategy captures behavioral patterns like preferred brands and budget constraints
- **SEMANTIC** strategy stores factual details like order numbers and product issues
- Memories are **per-customer** — `{actorId}` namespaces ensure complete isolation between users
- The session manager is the only change to the agent code — tools and model are unaffected

In the next module you'll learn how to use AgentCore Gateway to securely share tools across multiple agents: [Module 4: Scale with Gateway & Identity](./m04-gateway.md).
