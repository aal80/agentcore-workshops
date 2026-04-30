define get-vars
	@echo "> get-vars"
	$(eval AWS_ACCOUNT_ID := $(shell cat ./tmp/aws_account_id.txt))
	$(eval AWS_REGION := $(shell cat ./tmp/aws_region.txt))
	$(info > AWS_ACCOUNT_ID=$(AWS_ACCOUNT_ID))
	$(info > AWS_REGION=$(AWS_REGION))
endef

deploy-infra:
	@echo "Running terraform apply"
	cd terraform && \
	terraform init && \
	terraform apply --auto-approve

destroy:
	@echo "Destroying everything..."
	cd terraform && terraform destroy
	rm -rf tmp

test-vars:
	$(call get-vars)

install-qemu:
	@echo "> Installing QEMU"
	docker run --privileged --rm tonistiigi/binfmt --install arm64
	ls /proc/sys/fs/binfmt_misc/qemu-aarch64
	mount | grep binfmt_misc

login-to-ecr:
	$(call get-vars)
	@echo "> Logging in into ECR..."
	docker logout "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
	aws ecr get-login-password | docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

test-agent-locally:
	@echo "Testing agent locally..."
	$(eval TECH_SUPPORT_KB_ID := $(shell cat ./tmp/tech_support_kb_id.txt))
	$(eval MEMORY_ID := $(shell cat ./tmp/memory_id.txt))
	$(eval GATEWAY_URL := $(shell cat ./tmp/gateway_url.txt))
	$(eval COGNITO_CLIENT_ID := $(shell cat ./tmp/cognito_client_id.txt))
	$(eval COGNITO_CLIENT_SECRET_ARN := $(shell cat ./tmp/cognito_client_secret_arn.txt))
	$(eval COGNITO_TOKEN_ENDPOINT := $(shell cat ./tmp/cognito_token_endpoint.txt))
	$(eval COGNITO_SCOPE := $(shell cat ./tmp/cognito_scope.txt))
	
	
	cd src/agent && \
		TECH_SUPPORT_KB_ID=$(TECH_SUPPORT_KB_ID) \
		MEMORY_ID=$(MEMORY_ID) \
		GATEWAY_URL=$(GATEWAY_URL) \
		COGNITO_CLIENT_ID=$(COGNITO_CLIENT_ID) \
		COGNITO_CLIENT_SECRET_ARN=$(COGNITO_CLIENT_SECRET_ARN) \
		COGNITO_TOKEN_ENDPOINT=$(COGNITO_TOKEN_ENDPOINT) \
		COGNITO_SCOPE=$(COGNITO_SCOPE) \
		uv run agent.py

get-cognito-access-token:
	@echo "Getting a new access token..."
	$(eval COGNITO_TOKEN_ENDPOINT := $(shell cat ./tmp/cognito_token_endpoint.txt))
	$(eval COGNITO_SCOPE := $(shell cat ./tmp/cognito_scope.txt))
	$(eval COGNITO_CLIENT_ID := $(shell cat ./tmp/cognito_client_id.txt))
	$(eval COGNITO_CLIENT_SECRET_ARN := $(shell cat ./tmp/cognito_client_secret_arn.txt))
	$(eval COGNITO_CLIENT_SECRET := $(shell aws secretsmanager get-secret-value \
		--secret-id $(COGNITO_CLIENT_SECRET_ARN) \
		--query SecretString --output text))

	$(info > COGNITO_TOKEN_ENDPOINT=$(COGNITO_TOKEN_ENDPOINT))
	$(info > COGNITO_CLIENT_ID=$(COGNITO_CLIENT_ID))
	$(info > COGNITO_CLIENT_SECRET=$(shell echo $(COGNITO_CLIENT_SECRET) | cut -c1-3).....)
	$(info > COGNITO_SCOPE=$(COGNITO_SCOPE))

	$(eval ACCESS_TOKEN := $(shell curl -s -X POST $(COGNITO_TOKEN_ENDPOINT) \
		-H "Content-Type: application/x-www-form-urlencoded" \
		-d "grant_type=client_credentials&client_id=$(COGNITO_CLIENT_ID)&client_secret=$(COGNITO_CLIENT_SECRET)&scope=$(COGNITO_SCOPE)" \
		| jq -r '.access_token'))
	@echo ""
	@echo "Retrieved access token: $(ACCESS_TOKEN)"
# 	@echo $(ACCESS_TOKEN) > ./tmp/access_token.txt
# 	@echo ""
# 	@echo "Token saved to ./tmp/access_token.txt"

test-gateway:
	@echo "Getting a list of tools from the gateway..."
	$(eval ACCESS_TOKEN := $(shell cat ./tmp/access_token.txt))
	$(eval GATEWAY_URL := $(shell cat ./tmp/gateway_url.txt))
	
	$(info > ACCESS_TOKEN=$(shell echo $(ACCESS_TOKEN) | cut -c1-10).....)
	$(info > GATEWAY_URL=$(GATEWAY_URL))

	curl -s -X POST $(GATEWAY_URL) \
		-H "Content-Type: application/json" \
		-H "Authorization: Bearer $(ACCESS_TOKEN)" \
		-d '{"jsonrpc":"2.0","id":"1","method":"tools/list","params":{}}' \
		| jq .


### MODULE 5: AgentCore Runtime -----

build-and-push-agent:
	@echo "> Building agent container image..."
	$(call get-vars)
	$(eval ECR_REPO_URL := $(shell cat ./tmp/ecr_repo_url.txt))
	cd src/agent && \
		docker buildx build \
			--platform linux/arm64 \
			--no-cache \
			--load \
			-t "$(ECR_REPO_URL):latest" \
			.

	@echo "> Pushing agent image to ECR..."
	docker push "$(ECR_REPO_URL):latest"


# test-orchestrator:
# 	python3 orchestrator_invoker.py
# 	$(eval RUNTIME_AGENT_ARN := $(shell cat ./tmp/orchestrator_agent_runtime_arn.txt))
# 	$(info > RUNTIME_AGENT_ARN=$(RUNTIME_AGENT_ARN))

# 	$(eval PROMPT := Find me running shoes for a marathon in Seattle next week)
# 	$(eval PAYLOAD := $(shell echo '{"prompt":"$(PROMPT)"}' | base64))
	
# 	@echo ""
# 	@echo "Testing with prompt: $(PROMPT)"
# 	@printf "Press ENTER to start..."; read _
# 	aws bedrock-agentcore invoke-agent-runtime \
#   		--agent-runtime-arn "$(RUNTIME_AGENT_ARN)" \
# 		--payload "$(PAYLOAD)" \
# 		--content-type "application/json" \
# 		tmp/invoke_output.txt \
# 		--no-cli-pager

# 	@echo "> Invocation output:"
# 	@cat tmp/invoke_output.txt



