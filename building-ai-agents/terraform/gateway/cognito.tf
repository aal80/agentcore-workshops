resource "aws_cognito_user_pool" "gateway" {
  name = "${var.project_name}-gateway"
}

resource "aws_cognito_user_pool_domain" "gateway" {
  domain       = "${var.project_name}-gw"
  user_pool_id = aws_cognito_user_pool.gateway.id
}

resource "aws_cognito_resource_server" "gateway" {
  name         = "gateway"
  identifier   = "gateway"
  user_pool_id = aws_cognito_user_pool.gateway.id

  scope {
    scope_name        = "read"
    scope_description = "Read access to gateway tools"
  }
}

resource "aws_cognito_user_pool_client" "gateway" {
  name         = "${var.project_name}-gw-client"
  user_pool_id = aws_cognito_user_pool.gateway.id

  generate_secret                      = true
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["client_credentials"]
  allowed_oauth_scopes                 = [local.cognito_scope]
  supported_identity_providers         = ["COGNITO"]
  depends_on                           = [aws_cognito_resource_server.gateway]
}

locals {
  cognito_discovery_url  = "https://cognito-idp.${var.region}.amazonaws.com/${aws_cognito_user_pool.gateway.id}/.well-known/openid-configuration"
  cognito_token_endpoint = "https://${var.project_name}-gw.auth.${var.region}.amazoncognito.com/oauth2/token"
  cognito_scope = "gateway/read"
}

resource "aws_secretsmanager_secret" "cognito_client_secret" {
  name                    = "${var.project_name}/gateway/cognito-client-secret"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "cognito_client_secret" {
  secret_id     = aws_secretsmanager_secret.cognito_client_secret.id
  secret_string = aws_cognito_user_pool_client.gateway.client_secret
}


resource "local_file" "cognito_token_endpoint" {
  content  = local.cognito_token_endpoint
  filename = "${path.root}/../tmp/cognito_token_endpoint.txt"
}

resource "local_file" "cognito_client_id" {
  content  = aws_cognito_user_pool_client.gateway.id
  filename = "${path.root}/../tmp/cognito_client_id.txt"
}

resource "local_file" "cognito_client_secret_arn" {
  content  = aws_secretsmanager_secret.cognito_client_secret.arn
  filename = "${path.root}/../tmp/cognito_client_secret_arn.txt"
}

resource "local_file" "cognito_scope" {
  content  = local.cognito_scope
  filename = "${path.root}/../tmp/cognito_scope.txt"
}

