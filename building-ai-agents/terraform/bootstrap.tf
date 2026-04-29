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
  project_name_short = "building-ai-agents"
  project_name       = "${local.prefix}-${local.project_name_short}"
}

resource "aws_ecr_repository" "agent" {
  name = "${local.project_name}"
  force_delete = true
}

resource "local_file" "aws_region"{
    content = data.aws_region.current.region
    filename = "${path.root}/../tmp/aws_region.txt"
}

resource "local_file" "aws_account_id"{
    content = data.aws_caller_identity.current.account_id
    filename = "${path.root}/../tmp/aws_account_id.txt"
}

resource "local_file" "ecr_repo_url"{
    content = aws_ecr_repository.agent.repository_url
    filename = "${path.root}/../tmp/ecr_repo_url.txt"
}
