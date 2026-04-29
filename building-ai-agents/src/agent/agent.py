
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

l = get_logger("agent")

model = BedrockModel(model_id="us.anthropic.claude-haiku-4-5-20251001-v1:0", temperature=0.3)

tools = [
    get_return_policy, 
    get_product_info, 
    
    # Uncomment when instructed in Module 2
    get_technical_support

    # Uncomment when instructed in Module 4
    # mcp_tools_list
]

app = BedrockAgentCoreApp()  
@app.entrypoint  
async def invoke(payload, context=None):
    user_prompt = payload.get("prompt", "Hey there!")
    actor_id   = payload.get("actor_id", "customer-123")
    session_id = context.session_id if context else str(__import__("uuid").uuid4())

    l.info(f"ℹ️ user_prompt={user_prompt}")

    agent = Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=tools,
    
        # Uncomment when instructed in Module 3
        session_manager=session_manager,
    )
    response = agent(user_prompt)
    response_text = response.message["content"][0]["text"]

    # l.info(f"response_text={response_text}")

    return response_text

if __name__ == "__main__":
    
    # Prompts for Module 1
    prompt = "How can you help me?"
    # prompt = "Tell me what you know about headphones?"
    # prompt = "My headphones are broken, what's the return policy?"

    # Prompts for Module 2 - uncomment when instructed
    # prompt = "My wireless headphones are not turning on, I need technical support"

    # Prompts for Module 3 - uncomment when instructed
    # prompt = "My MacBook Pro overheating during video editing, what's the return policy?"
    # prompt = "What was my previous problem?"

    # Prompts for Module 4 - uncomment when instructed
    # prompt = "I have a Gaming Console Pro. My warranty serial number is MNO33333333. Am I covered?"

    asyncio.run(invoke({"prompt":prompt}))

    # You'll need this in Module 5 - uncomment when instructed
    # app.run()

