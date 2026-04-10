# Module 6 - Cleanup

## Destroy all AWS resources

> You can skip this step if you're using an AWS-provided account for this workshop. 

```bash
make destroy
```

Runs `terraform destroy` and removes `./tmp/`. Deletes all AWS resources: Cognito, AgentCore runtimes, IAM roles, CloudWatch log groups.

## Workshop Table Of Contents

1. [Overview](README.md) - Overview, architecture, understanding the protocols.
1. [Prerequisites & Setup](02-prereqs.md) — Install dependencies, QEMU, bootstrap infrastructure, deploy Cognito
2. [Weather Agent](03-weather-agent.md) — Build, deploy, and test the Weather sub-agent
3. [Shopping Agent](04-shopping-agent.md) — Build, deploy, and test the Shopping sub-agent
4. [Orchestrator Agent](05-orchestrator-agent.md) — Build, deploy, and test the Orchestrator + observability & troubleshooting
5. [Cleanup](06-cleanup.md) — Destroy all AWS resources