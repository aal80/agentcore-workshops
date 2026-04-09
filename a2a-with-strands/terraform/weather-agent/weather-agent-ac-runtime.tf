variable "project_name" {}
variable "region" {}
variable "cognito_client_id" {}
variable "cognito_discovery_url" {}

locals {
    project_name_underscore = replace(var.project_name, "-", "_")
}

resource "aws_iam_role" "weather_agent" {
  name = "${var.project_name}-weather-agent"

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

resource "aws_iam_role_policy" "weather_agent" {
  role = aws_iam_role.weather_agent.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams",
          "ecr:GetAuthorizationToken",
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer",
          "xray:PutTraceSegments", 
          "xray:PutTelemetryRecords"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_bedrockagentcore_agent_runtime" "weather_agent" {
  agent_runtime_name = "${local.project_name_underscore}_weather_agent"
  role_arn           = aws_iam_role.weather_agent.arn

  agent_runtime_artifact {
    container_configuration {
      container_uri = local.weather_agent_ecr_uri
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
  weather_agent_runtime_arn_encoded = replace(aws_bedrockagentcore_agent_runtime.weather_agent.agent_runtime_arn, "/", "%2F")
  weather_agent_runtime_url = "https://bedrock-agentcore.${var.region}.amazonaws.com/runtimes/${local.weather_agent_runtime_arn_encoded}/invocations/"
}

output "runtime_url" {
  value = local.weather_agent_runtime_url
}

resource "local_file" "weather_agent_runtime_url" {
  content  = local.weather_agent_runtime_url
  filename = "${path.root}/../tmp/weather_agent_runtime_url.txt"
}

