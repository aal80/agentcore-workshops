import boto3
import base64
import json

AGENT_RUNTIME_ARN_FILE = "../../tmp/agent_runtime_arn.txt"
AGENT_RUNTIME_ARN = open(AGENT_RUNTIME_ARN_FILE).read().strip()

def invoke_remote_agent(prompt: str) -> str:
    client = boto3.client("bedrock-agentcore")
    payload = json.dumps({"prompt": prompt})
    response = client.invoke_agent_runtime(
        agentRuntimeArn=AGENT_RUNTIME_ARN,
        payload=payload,
        contentType="application/json",
    )
    raw = response["response"].read()
    return raw.decode() if isinstance(raw, bytes) else raw

def run():
    print("-" * 20)
    print("Welcome to the AwesomeCorp Customer Support Agent (remote)")
    print(f"AgentCore Runtime ARN: {AGENT_RUNTIME_ARN}")
    while True:
        print("\n" + "-" * 20)
        prompt = input("User prompt (type 'exit' to quit): ").strip()

        if prompt.lower() == "exit":
            break
        if not prompt:
            continue

        print("Sending prompt to the agent running on AgentCore...")
        response = invoke_remote_agent(prompt)
        print(f"\n{response}")

if __name__ == "__main__":
    run()
