data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

resource "aws_key_pair" "deployer" {
  key_name   = var.key_name
  public_key = file(var.public_key_path)
}

resource "aws_security_group" "sg" {
  name        = "${var.key_name}-sg"
  description = "Allow SSH and app port"

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.ssh_allow_cidr]
  }

  ingress {
    description = "App port"
    from_port   = var.app_port
    to_port     = var.app_port
    protocol    = "tcp"
    cidr_blocks = [var.ssh_allow_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# NEW: store deployment secret in AWS Secrets Manager (optional - only created when aws_deploy_secret provided)
resource "aws_secretsmanager_secret" "deploy" {
  count = var.aws_deploy_secret != "" ? 1 : 0
  name  = var.aws_deploy_secret_name
  description = "Deployment secret for figma-web-matcher"
  tags = {
    ManagedBy = "terraform"
    Project   = "figma-web-matcher"
  }
}

resource "aws_secretsmanager_secret_version" "deploy_version" {
  count       = var.aws_deploy_secret != "" ? 1 : 0
  secret_id   = aws_secretsmanager_secret.deploy[0].id
  secret_string = var.aws_deploy_secret
}

resource "aws_instance" "web" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.deployer.key_name
  vpc_security_group_ids = [aws_security_group.sg.id]
  associate_public_ip_address = true

  user_data = <<-EOF
              #!/bin/bash
              set -e
              export DEBIAN_FRONTEND=noninteractive
              apt-get update
              apt-get install -y python3 python3-venv python3-pip git
              cd /home/ubuntu
              if [ ! -d app ]; then
                git clone "${var.github_repo}" app
              else
                cd app && git pull
              fi
              cd app
              python3 -m venv .venv
              . .venv/bin/activate
              pip install --upgrade pip
              pip install -r requirements.txt || true
              nohup .venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port ${var.app_port} --log-level info > /home/ubuntu/app/uvicorn.log 2>&1 &
              EOF

  tags = {
    Name = "figma-web-matcher"
  }
}