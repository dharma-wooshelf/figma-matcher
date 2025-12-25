provider "aws" {
  region = var.aws_region

  # if pipeline passes credentials via variables, use them; otherwise provider will fall back to environment variables or instance profile
  access_key = var.aws_access_key_id != "" ? var.aws_access_key_id : null
  secret_key = var.aws_secret_access_key != "" ? var.aws_secret_access_key : null
}