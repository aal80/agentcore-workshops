data "aws_ecr_image" "agent" {
  repository_name = var.ecr_repo_name
  image_tag       = "latest"
}


locals {
  project_name_underscore = replace(var.project_name, "-", "_")
  agent_ecr_uri           = "${var.ecr_repo_url}@${data.aws_ecr_image.agent.image_digest}"
}


resource "aws_iam_role" "agent" {
  name = "${var.project_name}-agent"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "bedrock-agentcore.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "agent" {
  role = aws_iam_role.agent.id
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

          # To use Bederock Knowledge Base and AgentCore Memory
          "bedrock:*",
          "bedrock-agentcore:*",
          
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

resource "aws_bedrockagentcore_agent_runtime" "agent" {
  agent_runtime_name = "${local.project_name_underscore}_agent"
  role_arn           = aws_iam_role.agent.arn

  agent_runtime_artifact {
    container_configuration {
      container_uri = local.agent_ecr_uri
    }
  }

  environment_variables = {
    "MEMORY_ID" = var.agentcore_memory_id
    "TECH_SUPPORT_KB_ID"=var.tech_support_knowledgebase_id
  }

  network_configuration {
    network_mode = "PUBLIC"
  }
}

locals {
  agent_runtime_arn = aws_bedrockagentcore_agent_runtime.agent.agent_runtime_arn
  agent_runtime_arn_encoded = replace(local.agent_runtime_arn, "/", "%2F")
  agent_runtime_url         = "https://bedrock-agentcore.${var.region}.amazonaws.com/runtimes/${local.agent_runtime_arn_encoded}/invocations/"
}

output "runtime_url" {
  value = local.agent_runtime_url
}

output "runtime_arn" {
  value = aws_bedrockagentcore_agent_runtime.agent
}

resource "local_file" "agent_runtime_url" {
  content  = local.agent_runtime_url
  filename = "${path.root}/../tmp/agent_runtime_url.txt"
}

resource "local_file" "agent_runtime_arn" {
  content  = local.agent_runtime_arn
  filename = "${path.root}/../tmp/agent_runtime_arn.txt"
}

