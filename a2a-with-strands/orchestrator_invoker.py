import base64
import json
from pathlib import Path
import boto3

AWS_REGION = Path("tmp/aws_region.txt").read_text().strip()
client = boto3.client("bedrock-agentcore", region_name=AWS_REGION)

RUNTIME_ARN = Path("tmp/orchestrator_agent_runtime_arn.txt").read_text().strip()
print(f"> RUNTIME_ARN={RUNTIME_ARN}")


PROMPT_TEXT="Find me running shoes for a marathon in Seattle next week"
PROMPT_JSON = json.dumps({"prompt":PROMPT_TEXT})
PROMPT_BASE64 = base64.b64encode(PROMPT_JSON.encode()).decode()

print(f"> Invoking with prompt: {PROMPT_TEXT}")
input("Press ENTER to start...")

response = client.invoke_agent_runtime(
    agentRuntimeArn=RUNTIME_ARN,
    payload=PROMPT_JSON,
    contentType="application/json"
)

if "text/event-stream" in response.get("contentType", ""):
    print("handling response stream")

    for line in response["response"].iter_lines(chunk_size=10):
        if line:
            line = line.decode('utf-8')
            if line.startswith("data:"):
                line = line[6:]
                print(line)

elif response.get("contentType") =="application/json":
    for chunk in response.get("response", []):
        print(chunk)

else:
    print(response)
