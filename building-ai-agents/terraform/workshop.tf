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
