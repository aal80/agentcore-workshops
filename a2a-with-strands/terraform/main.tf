data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

resource "random_string" "prefix" {
  length  = 4
  special = false
  upper   = false
  numeric = false
}

locals {
  prefix             = random_string.prefix.id
  project_name_short = "a2a-workshop"
  project_name       = "${local.prefix}-${local.project_name_short}"
}

module "cognito" {
  source       = "./cognito"
  project_name = local.project_name
  region       = data.aws_region.current.region
}

# module "weather_agent" {
#   source                = "./weather-agent"
#   project_name          = local.project_name
#   region                = data.aws_region.current.region
#   ecr_repo_prefix       = local.project_name_short
#   cognito_client_id     = module.cognito.client_id
#   cognito_discovery_url = module.cognito.discovery_url
# }

# module "shopping_agent" {
#   source                = "./shopping-agent"
#   project_name          = local.project_name
#   region                = data.aws_region.current.region
#   ecr_repo_prefix       = local.project_name_short
#   cognito_client_id     = module.cognito.client_id
#   cognito_discovery_url = module.cognito.discovery_url
# }

# module "orchestrator_agent" {
#   source                 = "./orchestrator-agent"
#   project_name           = local.project_name
#   region                 = data.aws_region.current.region
#   ecr_repo_prefix        = local.project_name_short
#   cognito_client_id      = module.cognito.client_id
#   cognito_client_secret  = module.cognito.client_secret
#   cognito_discovery_url  = module.cognito.discovery_url
#   cognito_token_endpoint = module.cognito.token_endpoint
#   weather_agent_runtime_url = module.weather_agent.runtime_url
#   shopping_agent_runtime_url = module.shopping_agent.runtime_url
# }
