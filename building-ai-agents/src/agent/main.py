from tools.return_policy import get_return_policy
from tools.product_info import get_product_info
from system_prompt import SYSTEM_PROMPT
from strands.models import BedrockModel
from strands import Agent
from tools.tech_support import get_technical_support
from memory_config import session_manager
from mcp_client import mcp_tools_list

model = BedrockModel(model_id="us.anthropic.claude-haiku-4-5-20251001-v1:0", temperature=0.3)

agent = Agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[
        get_product_info,
        get_return_policy,

        # Uncomment when instructed in Module 2
        # get_technical_support,  
        
        # Uncomment when instructed in Module 4
        # mcp_tools_list
    ],

    # Uncomment when instructed in Module 3
    # session_manager=session_manager,
)

print("✅ Customer Support Agent created successfully!")

# Used for local testing only
if __name__ == "__main__":

    # Prompts for Module 1
    agent("How can you help me?")
    # agent("Tell me what you know about headphones?")
    # agent("My headphones are broken, what's the return policy?")

    # Prompts for Module 2 - uncomment when instructed
    # agent("My headphones are broken, I need technical support")

    # Prompts for Module 3 - uncomment when instructed
    # agent("My MacBook Pro overheating during video editing, what's the return policy?")
    # agent("What was my previous problem?")

    # Prompts for Module 4 - uncomment when instructed
    # agent("I have a Gaming Console Pro. My warranty serial number is MNO33333333. Am I covered?")
