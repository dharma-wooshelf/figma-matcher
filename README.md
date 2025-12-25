# Figma ↔ Web Matcher (Python)

## Run Backend
pip install -r requirements.txt
uvicorn backend.main:app --reload 

## Open UI
Open frontend/index.html in browser

## GitHub Actions / Terraform
- Workflow added: .github/workflows/terraform.yml
- On push to branches dev/qa/prod the workflow runs terraform validate + plan.
- To apply, use "Run workflow" (manual dispatch) from Actions and select the branch; apply will fetch secrets from Vault and run terraform apply.
- Required GitHub Secrets:
  - VAULT_ADDR
  - VAULT_ROLE_ID
  - VAULT_SECRET_ID
- Store your deployment secrets in Vault at secret/data/figma-web-matcher/ci:
  - AWS_ACCESS_KEY_ID
  - AWS_SECRET_ACCESS_KEY
  - TF_PUB_KEY
  - TF_VAR_key_name
  - TF_VAR_github_repo
  - TF_VAR_app_port (optional)
  - TF_VAR_aws_region (optional)

This is an MVP scaffold; review and tighten environment protections before using in production.
