variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "instance_type" {
  type    = string
  default = "t3.micro"
}

variable "key_name" {
  type        = string
  description = "Name for the aws_key_pair resource"
}

variable "public_key_path" {
  type        = string
  description = "Path to your public SSH key (e.g. /tmp/deploy_key.pub)"
}

variable "private_key_path" {
  type        = string
  description = "Path to your private SSH key (used in ssh_command output)"
  default     = "~/.ssh/id_rsa"
}

variable "github_repo" {
  type        = string
  description = "GitHub repository URL for the project (https://github.com/you/repo.git)"
}

variable "app_port" {
  type    = number
  default = 8000
}

variable "ssh_allow_cidr" {
  type    = string
  default = "0.0.0.0/0"
}

# optional: allow pipeline to pass AWS creds (fetched from Vault)
variable "aws_access_key_id" {
  type    = string
  default = ""
  sensitive = true
}

variable "aws_secret_access_key" {
  type    = string
  default = ""
  sensitive = true
}