import logging
import os
import time
import asyncio
import httpx
from uuid import uuid4
from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.types import Message, Part, Role, TextPart
from strands import Agent, tool
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from fastapi import HTTPException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# This agent's own AgentCore runtime URL (used for the A2A agent card)
runtime_url = os.environ.get("AGENTCORE_RUNTIME_URL", "http://127.0.0.1:9000/")

WEATHER_AGENT_URL = os.environ.get("WEATHER_AGENT_RUNTIME_URL", "")
SHOPPING_AGENT_URL = os.environ.get("SHOPPING_AGENT_RUNTIME_URL", "")
COGNITO_TOKEN_ENDPOINT = os.environ.get("COGNITO_TOKEN_ENDPOINT", "")
COGNITO_CLIENT_ID = os.environ.get("COGNITO_CLIENT_ID", "")
COGNITO_CLIENT_SECRET = os.environ.get("COGNITO_CLIENT_SECRET", "")

logger.info(f"WEATHER_AGENT_URL={WEATHER_AGENT_URL}")
logger.info(f"SHOPPING_AGENT_URL={SHOPPING_AGENT_URL}")
logger.info(f"COGNITO_TOKEN_ENDPOINT={COGNITO_TOKEN_ENDPOINT}")
logger.info(f"COGNITO_CLIENT_ID={COGNITO_CLIENT_ID}")
logger.info(f"COGNITO_CLIENT_SECRET={COGNITO_CLIENT_SECRET[:2]}...REDACTED...")

_httpx_client = None
_token_cache: dict = {"token": "", "expires_at": 0.0}
_weather_agent_card = None
_shopping_agent_card = None

async def get_bearer_token() -> str:
    """Fetch a Cognito client_credentials bearer token, with in-memory caching."""
    if time.time() < _token_cache["expires_at"] - 120:
        return _token_cache["token"]

    if not all([COGNITO_TOKEN_ENDPOINT, COGNITO_CLIENT_ID, COGNITO_CLIENT_SECRET]):
        logger.warning(
            "Cognito credentials not configured; proceeding without bearer token"
        )
        return ""

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            COGNITO_TOKEN_ENDPOINT,
            data={
                "grant_type": "client_credentials",
                "client_id": COGNITO_CLIENT_ID,
                "client_secret": COGNITO_CLIENT_SECRET,
                "scope": "resource/read",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        data = resp.json()

    _token_cache["token"] = data["access_token"]
    _token_cache["expires_at"] = time.time() + data.get("expires_in", 3600)
    logger.info("Bearer token refreshed")
    return _token_cache["token"]


async def go():
    await discover_agents()
    # resp = await send_message_to_agent(_weather_agent_card, "how can you help me?")
    resp = await send_message_to_weather_agent("Seattle", "tomorrow")
    logger.info(resp)


async def get_httpx_client():
    global _httpx_client
    logger.info("> get_httpx_client")

    if _httpx_client == None:
        logger.info(" | creating a new client")
        _httpx_client = httpx.AsyncClient(
            timeout=httpx.Timeout(120, connect=5.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        )

    bearer_token = await get_bearer_token()
    logger.info(f" | bearer_token=={bearer_token[:10]}....")
    request_headers = {"Authorization": f"Bearer {bearer_token}"}

    _httpx_client.headers.update(request_headers)
    return _httpx_client


async def discover_agents():
    logger.info("> discover_agents")
    global _weather_agent_card
    global _shopping_agent_card

    httpx_client = await get_httpx_client()

    logger.info("Retrieving Agent cards...")
    weather_agent_resolver = A2ACardResolver(
        httpx_client=httpx_client, base_url=WEATHER_AGENT_URL
    )
    _weather_agent_card = await weather_agent_resolver.get_agent_card()

    shopping_agent_resolver = A2ACardResolver(
        httpx_client=httpx_client, base_url=SHOPPING_AGENT_URL
    )
    _shopping_agent_card = await shopping_agent_resolver.get_agent_card()

    logger.info("Agent cards retrieved")


async def send_message_to_agent(agent_card, message_text):
    logger.info(f"> send_message_to_agent text={message_text}")
    httpx_client = await get_httpx_client()

    a2a_config = ClientConfig(httpx_client=httpx_client, streaming=False)
    a2a_factory = ClientFactory(a2a_config)
    a2a_client = a2a_factory.create(agent_card)

    message = Message(
        kind="message",
        role=Role.user,
        parts=[Part(TextPart(kind="text", text=message_text))],
        message_id=uuid4().hex,
    )

    logger.info("Sending the message...")
    try:
        async for event in a2a_client.send_message(message):
            # logger.info(event)
            task, _ = event
            text = task.artifacts[0].parts[0].root.text
            logger.info(f"> agent_response={text}")
            return text
    except Exception as e:
        logger.exception(f"send_message failed: {e}")
        raise


@tool
async def send_message_to_weather_agent(location: str, timeframe: str):
    """
    Retrieves weather for {location} and {timeframe}, for example "What's the weather tomorrow in Seattle"
    """
    logger.info(
        f">send_message_to_weather_agent location={location} timeframe={timeframe}"
    )

    if _weather_agent_card == None:
        await discover_agents()

    return await send_message_to_agent(
        _weather_agent_card,
        f"Summarize weather for {location} for {timeframe} in less than 10 words",
    )

@tool
async def send_message_to_shopping_agent(weather_conditions: str, item: str):
    """
    Recommends products to buy given weather conditions and a specific item request.
    For example: weather_conditions="rainy and cold, 45F", item="running shoes for a marathon"
    """
    logger.info(
        f">send_message_to_shopping_agent weather_conditions={weather_conditions} item={item}"
    )

    if _shopping_agent_card == None:
        await discover_agents()

    message = (
        f"Weather conditions: {weather_conditions}\nThe user is looking for: {item}"
    )
    return await send_message_to_agent(_shopping_agent_card, message)


system_prompt = """You are a personal weather-to-wardrobe and outdoor gear assistant.

For every request:
1. Extract the location and time frame from the user's prompt (e.g. "Seattle next week", "London tomorrow")
2. Call get_weather with that location and time frame to fetch conditions or a forecast
3. Call get_shopping_recommendations with:
   - weather_description: the weather result from step 2
   - item_request: the specific item or activity from the user's prompt, if any
     (e.g. "running shoes for a marathon", "jacket for hiking", "outfit for a wedding")
     Leave item_request empty only if the user asked for general clothing recommendations
4. Present a concise combined response: weather summary followed by product recommendations

Keep responses practical and to the point.
"""

logger.info("Initializing Strands Agent...")
agent = Agent(
    system_prompt=system_prompt,
    tools=[send_message_to_weather_agent, send_message_to_shopping_agent],
    name="Orchestrator Agent",
    description="Orchestrates weather and shopping agents to recommend weather-appropriate clothing and gear.",
)
logger.info("Strands Agent initialized")

logger.info("Initializing BedrockAgentCoreApp...")
app = BedrockAgentCoreApp()
logger.info("BedrockAgentCoreApp initialized")

@app.entrypoint
async def invoke_agent(payload, context):
    logger.info(">invoke_agent")
    try:
        prompt = payload.get("prompt", "")
        if not prompt:
            raise HTTPException(status_code=200, detail="No prompt provided")

        logger.info(f"prompt={prompt[:50]}...")

        async with asyncio.timeout(120):
            agent_stream = agent.stream_async(prompt=prompt)
            async for event in agent_stream:
                if ("message" in event) or ("event" in event and "metadata" in event["event"]):
                    logger.info(event)
                    yield event
               
    except asyncio.TimeoutError:
        logger.error("Operation timed out")
        yield {"error": "Request timed out after 120 seconds"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        yield {"error": f"Processing failed: {str(e)}"}


if __name__ == "__main__":
    logger.info("Starting...")
    app.run(host="0.0.0.0", port=8080)
