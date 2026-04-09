# resource "aws_cloudwatch_log_group" "orchestrator_agent" {
#   name              = "/aws/vendedlogs/agentcore/orchestrator-agent/applogs"
#   retention_in_days = 7
# }

# resource "aws_cloudwatch_log_delivery_source" "orchestrator_agent" {
#   name         = "${var.project_name}-orchestrator-agent-app-logs"
#   log_type     = "APPLICATION_LOGS"
#   resource_arn = aws_bedrockagentcore_agent_runtime.orchestrator_agent.agent_runtime_arn
# }

# resource "aws_cloudwatch_log_delivery_destination" "orchestrator_agent" {
#   name = "${var.project_name}-orchestrator-agent-dst"

#   delivery_destination_type = "CWL"
#   delivery_destination_configuration {
#     destination_resource_arn = aws_cloudwatch_log_group.orchestrator_agent.arn
#   }

#   output_format = "json"
# }

# resource "aws_cloudwatch_log_delivery" "orchestrator_agent" {
#   delivery_source_name     = aws_cloudwatch_log_delivery_source.orchestrator_agent.name
#   delivery_destination_arn = aws_cloudwatch_log_delivery_destination.orchestrator_agent.arn
# }
