variable "ecr_repo_prefix" {}

locals {
  orchestrator_agent_ecr_uri = "${data.aws_ecr_repository.orchestrator_agent.repository_url}@${data.aws_ecr_image.orchestrator_agent.image_digest}"
}

data "aws_ecr_repository" "orchestrator_agent" {
  name = "${var.ecr_repo_prefix}-orchestrator-agent"
}

data "aws_ecr_image" "orchestrator_agent" {
  repository_name = data.aws_ecr_repository.orchestrator_agent.name
  image_tag = "latest"
}

# output "shopping_agent_ecr_uri" {
#   value = local.shopping_agent_ecr_uri
# }