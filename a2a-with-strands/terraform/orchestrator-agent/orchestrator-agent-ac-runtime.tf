variable "project_name" {}
variable "region" {}
variable "cognito_client_id" {}
variable "cognito_client_secret" {}
variable "cognito_discovery_url" {}
variable "cognito_token_endpoint" {}
variable "ecr_repo_name" {}
variable "ecr_repo_url" {}
variable "weather_agent_runtime_url" {}
variable "shopping_agent_runtime_url" {}

data "aws_ecr_image" "agent" {
  repository_name = var.ecr_repo_name
  image_tag       = "latest"
}

locals {
  project_name_underscore = replace(var.project_name, "-", "_")
  agent_ecr_uri           = "${var.ecr_repo_url}@${data.aws_ecr_image.agent.image_digest}"
}

resource "aws_iam_role" "orchestrator_agent" {
  name = "${var.project_name}-orchestrator-agent"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = "sts:AssumeRole"
      Principal = {
        Service = "bedrock-agentcore.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "orchestrator_agent" {
  role = aws_iam_role.orchestrator_agent.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          # To subscribe to Bedrock Models
          "aws-marketplace:Subscribe",
          "aws-marketplace:ViewSubscriptions",
          "aws-marketplace:Unsubscribe",

          # To invoke Bedrock Models
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",

          # To pull images from ECR
          "ecr:GetAuthorizationToken",
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer",

          # To send telemetry to CloudWatch
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams",
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords",
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_bedrockagentcore_agent_runtime" "orchestrator_agent" {
  agent_runtime_name = "${local.project_name_underscore}_orchestrator_agent"
  role_arn           = aws_iam_role.orchestrator_agent.arn

  agent_runtime_artifact {
    container_configuration {
      container_uri = local.agent_ecr_uri
    }
  }
  environment_variables = {
    WEATHER_AGENT_RUNTIME_URL  = var.weather_agent_runtime_url
    SHOPPING_AGENT_RUNTIME_URL = var.shopping_agent_runtime_url
    COGNITO_TOKEN_ENDPOINT     = var.cognito_token_endpoint
    COGNITO_CLIENT_ID          = var.cognito_client_id
    COGNITO_CLIENT_SECRET      = var.cognito_client_secret
  }

  network_configuration {
    network_mode = "PUBLIC"
  }
}

locals {
  orchestrator_agent_runtime_arn_encoded = replace(aws_bedrockagentcore_agent_runtime.orchestrator_agent.agent_runtime_arn, "/", "%2F")
  orchestrator_agent_runtime_url         = "https://bedrock-agentcore.${var.region}.amazonaws.com/runtimes/${local.orchestrator_agent_runtime_arn_encoded}/invocations/"
}

resource "local_file" "orchestrator_agent_runtime_url" {
  content  = local.orchestrator_agent_runtime_url
  filename = "${path.root}/../tmp/orchestrator_agent_runtime_url.txt"
}

resource "local_file" "orchestrator_agent_runtime_arn" {
  content  = aws_bedrockagentcore_agent_runtime.orchestrator_agent.agent_runtime_arn
  filename = "${path.root}/../tmp/orchestrator_agent_runtime_arn.txt"
}
