import os
import uuid
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig, RetrievalConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager
from logger import get_logger

l = get_logger("memory_config")

MEMORY_ID = os.environ.get("MEMORY_ID")
ACTOR_ID = "customer-123"   # In production this comes from the authenticated user identity
l.info(f"ℹ️ MEMORY_ID={MEMORY_ID}")

memory_config = AgentCoreMemoryConfig(
    memory_id=MEMORY_ID,
    session_id=str(uuid.uuid4()),
    actor_id=ACTOR_ID,
    retrieval_config={
        "support/customer/{actorId}/semantic/":     RetrievalConfig(top_k=3, relevance_score=0.2),
        "support/customer/{actorId}/preferences/":  RetrievalConfig(top_k=3, relevance_score=0.2),
    }
)

session_manager = AgentCoreMemorySessionManager(memory_config)
l.info("✅ session_manager ready")