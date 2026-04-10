variable "project_name" {}
variable "region" {}
variable "cognito_client_id" {}
variable "cognito_discovery_url" {}
variable "ecr_repo_name" {}
variable "ecr_repo_url" {}

data "aws_ecr_image" "agent" {
  repository_name = var.ecr_repo_name
  image_tag       = "latest"
}

locals {
  project_name_underscore = replace(var.project_name, "-", "_")
  agent_ecr_uri           = "${var.ecr_repo_url}@${data.aws_ecr_image.agent.image_digest}"
}

resource "aws_iam_role" "shopping_agent" {
  name = "${var.project_name}-shopping-agent"

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

resource "aws_iam_role_policy" "shopping_agent" {
  role = aws_iam_role.shopping_agent.id
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

resource "aws_bedrockagentcore_agent_runtime" "shopping_agent" {
  agent_runtime_name = "${local.project_name_underscore}_shopping_agent"
  role_arn           = aws_iam_role.shopping_agent.arn

  agent_runtime_artifact {
    container_configuration {
      container_uri = local.agent_ecr_uri
    }
  }

  authorizer_configuration {
    custom_jwt_authorizer {
      discovery_url   = var.cognito_discovery_url
      allowed_clients = [var.cognito_client_id]
    }
  }

  network_configuration {
    network_mode = "PUBLIC"
  }

  protocol_configuration {
    server_protocol = "A2A"
  }
}

locals {
  shopping_agent_runtime_arn_encoded = replace(aws_bedrockagentcore_agent_runtime.shopping_agent.agent_runtime_arn, "/", "%2F")
  shopping_agent_runtime_url         = "https://bedrock-agentcore.${var.region}.amazonaws.com/runtimes/${local.shopping_agent_runtime_arn_encoded}/invocations/"
}

output "runtime_url" {
  value = local.shopping_agent_runtime_url
}


resource "local_file" "shopping_agent_runtime_url" {
  content  = local.shopping_agent_runtime_url
  filename = "${path.root}/../tmp/shopping_agent_runtime_url.txt"
}

