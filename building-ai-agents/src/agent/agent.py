
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
from strands.models import BedrockModel
from tools.return_policy import get_return_policy
from tools.product_info import get_product_info
from tools.tech_support import get_technical_support
from system_prompt import SYSTEM_PROMPT
from memory_config import session_manager
import asyncio
from logger import get_logger
from mcp_client import mcp_tools_list
import os

l = get_logger("agent")

model = BedrockModel(model_id="us.anthropic.claude-haiku-4-5-20251001-v1:0", temperature=0.3)

tools = [
    get_return_policy, 
    get_product_info, 
    get_technical_support,
    mcp_tools_list
]

agent = Agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=tools,
    session_manager=session_manager,
)

app = BedrockAgentCoreApp()
@app.entrypoint
async def invoke(payload, _context=None):
    user_prompt = payload.get("prompt", "Hey there!")

    l.info(f"ℹ️ user_prompt={user_prompt}")

    response = agent(user_prompt)
    response_text = response.message["content"][0]["text"]

    # l.info(f"response_text={response_text}")

    return response_text

def run_locally():
    print("-" * 20)
    print("Welcome to the AwesomeCorp Customer Support Agent")
    while True:
        print("\n" + "-" * 20)
        prompt = input("User prompt (type 'exit' to quit): ").strip()
        if prompt.lower() == "exit":
            break
        if not prompt:
            continue
        asyncio.run(invoke({"prompt": prompt}))

if __name__ == "__main__":
    # print("===" * 20)
    # for k, v in sorted(os.environ.items()):
    #     print(f"  {k}={v}")
    # print("===" * 20)
    if os.environ.get("AGENTCORE_RUNTIME_URL"):
        print("Running on AgentCore, starting server...")
        app.run()
    else:
        print("Running locally...")
        run_locally()

