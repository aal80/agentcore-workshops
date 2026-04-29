# --- Module 2: Uncomment to deploy the Knowledge Base
module "knowledge_base" {
  source = "./knowledge_base"
  project_name = local.project_name
  region = data.aws_region.current.region
}

# --- Module 3: Uncomment to deploy AgentCore Memory
module "memory" {
  source = "./memory"
  project_name = local.project_name
  region = data.aws_region.current.region
}

# --- Module 4: Uncomment to deploy AgentCore Gateway
module "gateway" {
  source       = "./gateway"
  project_name = local.project_name
  region       = data.aws_region.current.region
}

# --- Module 5: Uncomment to deploy AgentCore Runtime infrastructure (ECR + IAM role)
module "runtime" {
  source       = "./runtime"
  project_name = local.project_name
  region       = data.aws_region.current.region
  ecr_repo_name = aws_ecr_repository.agent.name
  ecr_repo_url = aws_ecr_repository.agent.repository_url
  agentcore_memory_id = module.memory.memory_id
  tech_support_knowledgebase_id = module.knowledge_base.kb_id
}
