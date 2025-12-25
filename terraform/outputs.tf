output "public_ip" {
  description = "Public IPv4 address of the EC2 instance"
  value       = aws_instance.web.public_ip
}

output "public_dns" {
  description = "Public DNS of the EC2 instance"
  value       = aws_instance.web.public_dns
}

output "ssh_command" {
  description = "ssh command to connect (uses private_key_path variable)"
  value       = "ssh -i ${var.private_key_path} ubuntu@${aws_instance.web.public_ip}"
}

output "app_url" {
  description = "URL to reach the app"
  value       = "http://${aws_instance.web.public_ip}:${var.app_port}"
}

# NEW: output the ARN of the created secret (sensitive)
output "aws_deploy_secret_arn" {
  description = "ARN of the Secrets Manager secret created for deployment (if any)"
  value       = length(aws_secretsmanager_secret.deploy) > 0 ? aws_secretsmanager_secret.deploy[0].arn : ""
  sensitive   = true
}