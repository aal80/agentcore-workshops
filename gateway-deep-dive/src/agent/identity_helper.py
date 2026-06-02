import asyncio
import requests
import os
import boto3
from logger import get_logger

l = get_logger(__name__)

CREDENTIAL_PROVIDER_NAME = os.environ.get("CREDENTIAL_PROVIDER_NAME")

try:
    from bedrock_agentcore.services.identity import IdentityClient
    region = boto3.session.Session().region_name
    identity_client = IdentityClient(region)
except Exception as e:
    identity_client = None
    l.warning(f"IdentityClient not available: {e}")


def get_token() -> str | None:
    if CREDENTIAL_PROVIDER_NAME:
        return _get_token_from_token_vault()
    else:
        return _get_token_from_cognito_endpoint()


def _get_token_from_cognito_endpoint() -> str | None:
    l.info("> _get_token_from_cognito_endpoint")
    client_id     = os.environ.get("COGNITO_CLIENT_ID")
    client_secret = os.environ.get("COGNITO_CLIENT_SECRET")
    token_endpoint = os.environ.get("COGNITO_TOKEN_ENDPOINT")
    scope         = os.environ.get("COGNITO_SCOPE")

    if not all([client_id, client_secret, token_endpoint, scope]):
        l.warning("⚠️ Cognito env vars not set — gateway tools disabled")
        return None

    l.info(f"COGNITO_CLIENT_ID={client_id}")
    l.info(f"COGNITO_TOKEN_ENDPOINT={token_endpoint}")
    l.info(f"COGNITO_SCOPE={scope}")

    response = requests.post(
        token_endpoint,
        data={
            "grant_type":    "client_credentials",
            "client_id":     client_id,
            "client_secret": client_secret,
            "scope":         scope,
        },
    )
    response.raise_for_status()
    return response.json()["access_token"]


def _get_token_from_token_vault() -> str | None:
    l.info("> _get_token_from_token_vault")
    if not identity_client:
        l.warning("⚠️ IdentityClient not available")
        return None

    workload_name = os.environ.get("WORKLOAD_ID_NAME")
    scope         = os.environ.get("COGNITO_SCOPE", "gateway/invoke")

    if not workload_name:
        l.warning("⚠️ WORKLOAD_ID_NAME not set")
        return None

    l.info(f"WORKLOAD_ID_NAME={workload_name}")
    l.info(f"CREDENTIAL_PROVIDER_NAME={CREDENTIAL_PROVIDER_NAME}")

    workload_response = identity_client.get_workload_access_token(
        workload_name=workload_name
    )
    workload_token = workload_response["workloadAccessToken"]
    l.info(f"workload_token={workload_token[:10]}...REDACTED")

    access_token = asyncio.run(identity_client.get_token(
        provider_name=CREDENTIAL_PROVIDER_NAME,
        scopes=[scope],
        auth_flow="M2M",
        agent_identity_token=workload_token,
    ))
    l.info(f"access_token={access_token[:10]}...REDACTED")
    return access_token
