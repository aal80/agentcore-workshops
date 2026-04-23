# Module 2: Adding a Knowledge Base

In Module 1 you built an agent with tools that return hardcoded mock data. In this module you'll replace that with a real **Bedrock Knowledge Base** backed by S3 vector storage, so the `get_technical_support` tool can answer questions from actual documentation.

By the end of this module your agent will:
- Query a Bedrock Knowledge Base for technical support questions
- Use Amazon Titan Embed v2 to perform semantic search over 6 documentation files
- Automatically sync documents from S3 on every `terraform apply`

## Architecture

The knowledge base infrastructure consists of:

| Resource | Purpose |
|---|---|
| S3 bucket (`*-kb-source`) | Stores the source documentation files |
| S3 vector bucket + index | Stores the vector embeddings (S3 Vectors) |
| Bedrock Knowledge Base | Orchestrates retrieval using Titan Embed v2 |
| Bedrock Data Source | Links the S3 bucket to the KB with fixed-size chunking |
| `null_resource` | Triggers ingestion sync after every deploy |

## Step 1: Deploy the Knowledge Base infrastructure

Open [terraform/workshop.tf](terraform/workshop.tf) and uncomment the `knowledge_base` module:

```hcl
module "knowledge_base" {
  source       = "./knowledge_base"
  project_name = local.project_name
  region       = data.aws_region.current.region
}
```

Then deploy:

```bash
make deploy-infra
```

This will:
1. Create an S3 source bucket and upload the 6 documentation files from [knowledge-base/](knowledge-base/)
2. Create an S3 vector bucket and index (1024 dimensions, cosine similarity, float32)
3. Create the Bedrock Knowledge Base using Amazon Titan Embed v2
4. Start an ingestion job to embed and index all documents
5. Write the Knowledge Base ID to `tmp/tech_support_kb_id.txt`

Ingestion takes 1-2 minutes. You can check the status with:

```bash
aws bedrock-agent list-ingestion-jobs \
  --knowledge-base-id $(cat tmp/tech_support_kb_id.txt) \
  --data-source-id <data-source-id>
```

## Step 2: Verify the Knowledge Base is working

Once ingestion completes, run a test query to confirm documents were indexed:

```bash
aws bedrock-agent-runtime retrieve \
  --knowledge-base-id $(cat tmp/tech_support_kb_id.txt) \
  --retrieval-query '{"text": "how do I fix Wi-Fi connection problems"}' \
  --retrieval-configuration '{"vectorSearchConfiguration": {"numberOfResults": 3}}'
```

You should get back scored text chunks from your documents. An empty result means ingestion hasn't finished yet.

## Step 3: Enable the `get_technical_support` tool

Open [src/agent/tools/tech_support.py](src/agent/tools/tech_support.py). The tool reads the KB ID from the `TECH_SUPPORT_KB_ID` environment variable at import time:

```python
import os
import boto3
from strands.tools import tool
from strands_tools import retrieve

TECH_SUPPORT_KB_ID = os.environ.get("TECH_SUPPORT_KB_ID")
if not TECH_SUPPORT_KB_ID:
    raise ValueError("TECH_SUPPORT_KB_ID environment variable is not set.")

@tool
def get_technical_support(issue_description: str) -> str:
    try:
        region = boto3.Session().region_name
        tool_use = {
            "toolUseId": "tech_support_query",
            "input": {
                "text": issue_description,
                "knowledgeBaseId": TECH_SUPPORT_KB_ID,
                "region": region,
                "numberOfResults": 3,
                "score": 0.4,
            },
        }
        result = retrieve.retrieve(tool_use)
        if result["status"] == "success":
            return result["content"][0]["text"]
        else:
            return f"Unable to access technical support documentation. Error: {result['content'][0]['text']}"
    except Exception as e:
        return f"Unable to access technical support documentation. Error: {str(e)}"
```

Now open [src/agent/main.py](src/agent/main.py) and uncomment the `get_technical_support` tool:

```python
agent = Agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[
        get_product_info,
        get_return_policy,
        search_web,
        get_technical_support,  # <-- uncomment this line
    ],
)
```

Also update the test prompt at the bottom to exercise the new tool:

```python
if __name__ == "__main__":
    # agent("How can you help me?")
    # agent("My headphones are broken, what's the return policy?")
    agent("My headphones are broken, I need technical support")
```

## Step 4: Run the agent

`make test-agent-locally` automatically reads `tmp/tech_support_kb_id.txt` and passes it as the `TECH_SUPPORT_KB_ID` environment variable:

```bash
make test-agent-locally
```

This time the agent will invoke `get_technical_support` and return content retrieved from the Knowledge Base:

```
Tool #1: get_technical_support

Based on our technical documentation, here are steps to troubleshoot your headphones:

WARRANTY COVERAGE
- Manufacturing defects - Full coverage
- Normal wear and tear - Not covered
...

SERVICE OPTIONS
- In-warranty repairs - Free parts and labor
...
```

The agent is now answering from real documentation rather than hardcoded strings.

## How it works under the hood

1. The agent receives the user's message and decides `get_technical_support` is the right tool
2. The tool calls `bedrock-agent-runtime retrieve` with the issue description as the query text
3. Bedrock embeds the query using Titan Embed v2 and performs a vector similarity search against the S3 index
4. The top 3 matching chunks (above score threshold 0.4) are returned
5. The agent uses those chunks to compose a response

## Congratulations!

You've integrated a real Bedrock Knowledge Base into your agent!

- Source documents live in S3 and are automatically synced on every `terraform apply`
- Semantic search finds relevant content even when the query wording doesn't exactly match the docs
- The KB ID is injected via environment variable — no hardcoded values in code

Current limitations to address in the next modules:

- The agent still has no memory — it doesn't remember previous conversations
- Tools are embedded in the agent app and aren't reusable across agents
- Running locally only — not scalable or observable
- No authentication or authorization
