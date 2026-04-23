from tools.return_policy import get_return_policy
from tools.product_info import get_product_info
from tools.web_search import search_web
# from tools.tech_support import get_technical_support
from system_prompt import SYSTEM_PROMPT
from strands.models import BedrockModel
from strands import Agent

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

        # Below tool will be added in Module 2
        # get_technical_support,  # Tool 4: Technical support & troubleshooting
    ],
)

print("✅ Customer Support Agent created successfully!")

# Used for local testing only
if __name__ == "__main__":
    agent("How can you help me?")
    # agent("My headphones are broken, what's the return policy?")
    # agent("My headphones are broken, I need technical support")
