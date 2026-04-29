import os
import boto3
import requests
from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp import MCPClient
import logging

logging.getLogger("mcp_client").setLevel(logging.INFO)
l = logging.getLogger("mcp_client")

GATEWAY_URL = os.environ.get("GATEWAY_URL")
COGNITO_CLIENT_ID = os.environ.get("COGNITO_CLIENT_ID")
COGNITO_CLIENT_SECRET_ARN = os.environ.get("COGNITO_CLIENT_SECRET_ARN")
COGNITO_TOKEN_ENDPOINT = os.environ.get("COGNITO_TOKEN_ENDPOINT")
COGNITO_SCOPE = os.environ.get("COGNITO_SCOPE")

l.info(f"mcp_client :: GATEWAY_URL={GATEWAY_URL}")
l.info(f"mcp_client :: COGNITO_CLIENT_ID={COGNITO_CLIENT_ID}")
l.info(f"mcp_client :: COGNITO_CLIENT_SECRET_ARN={COGNITO_CLIENT_SECRET_ARN}")
l.info(f"mcp_client :: COGNITO_TOKEN_ENDPOINT={COGNITO_TOKEN_ENDPOINT}")
l.info(f"mcp_client :: COGNITO_SCOPE={COGNITO_SCOPE}")

_required = [GATEWAY_URL, COGNITO_CLIENT_ID, COGNITO_CLIENT_SECRET_ARN, COGNITO_TOKEN_ENDPOINT, COGNITO_SCOPE]

if not all(_required):
    l.info("⚠️ mcp_client :: one or more required env vars are missing — Gateway tools disabled")
    mcp_tools_list = []
else:
    sm = boto3.client("secretsmanager")
    cognito_client_secret = sm.get_secret_value(SecretId=COGNITO_CLIENT_SECRET_ARN)["SecretString"]
    l.info(f"mcp_client :: cognito_client_secret={cognito_client_secret[:2]}.....")

    def _get_gateway_token() -> str:
        response = requests.post(
            COGNITO_TOKEN_ENDPOINT,
            data={
                "grant_type":    "client_credentials",
                "client_id":     COGNITO_CLIENT_ID,
                "client_secret": cognito_client_secret,
                "scope":         COGNITO_SCOPE,
            },
        )
        response.raise_for_status()
        return response.json()["access_token"]

    gateway_token = _get_gateway_token()
    l.info(f"ℹ️ mcp_client :: gateway_token={gateway_token[:10]}.....")

    mcp_client = MCPClient(lambda: streamablehttp_client(
        GATEWAY_URL,
        headers={"Authorization": f"Bearer {gateway_token}"}
    ))

    mcp_client.start()
    mcp_tools_list = mcp_client.list_tools_sync()

l.info("✅ mcp_client ready")