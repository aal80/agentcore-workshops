variable "ecr_repo_prefix" {}

locals {
  shopping_agent_ecr_uri = "${data.aws_ecr_repository.shopping_agent.repository_url}@${data.aws_ecr_image.shopping_agent.image_digest}"
}

data "aws_ecr_repository" "shopping_agent" {
  name = "${var.ecr_repo_prefix}-shopping-agent"
}

data "aws_ecr_image" "shopping_agent" {
  repository_name = data.aws_ecr_repository.shopping_agent.name
  image_tag = "latest"
}

# output "shopping_agent_ecr_uri" {
#   value = local.shopping_agent_ecr_uri
# }