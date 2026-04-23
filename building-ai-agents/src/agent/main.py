from tools.return_policy import get_return_policy
from tools.product_info import get_product_info
from tools.web_search import search_web
from system_prompt import SYSTEM_PROMPT
from strands.models import BedrockModel
from strands import Agent

# Uncomment when asked in Module 2
# from tools.tech_support import get_technical_support

# Uncomment when asked in Module 3
# from memory_config import session_manager

# Initialize the Bedrock model (Amazon Nova 2 Lite)
model = BedrockModel(model_id="global.amazon.nova-2-lite-v1:0", temperature=0.3)

# Create the customer support agent with all tools
agent = Agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[
        get_product_info,       # Tool 1: Simple product information lookup
        get_return_policy,      # Tool 2: Simple return policy lookup
        search_web,             # Tool 3: Access the web for updated information

        # Uncomment when asked in Module 2
        # get_technical_support,  # Tool 4: Technical support & troubleshooting
    ],

    # Uncomment when asked in Module 3
    # session_manager=session_manager,
)

print("✅ Customer Support Agent created successfully!")

# Used for local testing only
if __name__ == "__main__":
    agent("How can you help me?")
    # agent("My headphones are broken, what's the return policy?")
    # agent("My headphones are broken, I need technical support")
    # agent("My MacBook Pro overheating during video editing, what's the return policy?")
    # agent("What was my previous problem?")
