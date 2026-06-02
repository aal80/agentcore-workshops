# --- Module 6: Uncomment to add outbound identity (Token Vault + Credential Providers)
#
# variable "cognito_client_id" {
#   type      = string
#   sensitive = true
#   ephemeral = true
# }
#
# variable "cognito_client_secret" {
#   type      = string
#   sensitive = true
#   ephemeral = true
# }
#
# variable "cognito_discovery_url" {
#   type = string
# }
#
# resource "aws_bedrockagentcore_workload_identity" "pizza_agent" {
#   name = local.project_name
# }
#
# resource "aws_bedrockagentcore_oauth2_credential_provider" "cognito" {
#   name                       = "${local.project_name}-cognito"
#   credential_provider_vendor = "CustomOauth2"
#
#   oauth2_provider_config {
#     custom_oauth2_provider_config {
#       client_id_wo                  = var.cognito_client_id
#       client_secret_wo              = var.cognito_client_secret
#       client_credentials_wo_version = 1
#       oauth_discovery {
#         discovery_url = var.cognito_discovery_url
#       }
#     }
#   }
# }
#
# resource "local_file" "workload_identity_name" {
#   content  = aws_bedrockagentcore_workload_identity.pizza_agent.name
#   filename = "${path.root}/../tmp/workload_identity_name.txt"
# }
#
# resource "local_file" "credential_provider_name" {
#   content  = aws_bedrockagentcore_oauth2_credential_provider.cognito.name
#   filename = "${path.root}/../tmp/credential_provider_name.txt"
# }
#
# output "workload_identity_name" {
#   value = aws_bedrockagentcore_workload_identity.pizza_agent.name
# }
#
# output "credential_provider_name" {
#   value = aws_bedrockagentcore_oauth2_credential_provider.cognito.name
# }
