provider "aws" {
  region = var.aws_region
}

resource "aws_vpc" "unstructured" {
  cidr_block = var.vpc_cidr
  tags = {
    Name = "${var.project_name}-${var.env_name}-vpc"
  }
  enable_dns_hostnames = true
}

resource "aws_subnet" "unstructured_public" {
  vpc_id = aws_vpc.unstructured.id
  cidr_block = var.public_subnet_cidr
  availability_zone = var.availability_zone
  tags = {
    Name = "${var.project_name}-${var.env_name}-public-subnet"
  }
}

resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.unstructured.id
  tags = {
    Name = "${var.project_name}-${var.env_name}-igw"
  }
}

resource "aws_route_table" "unstructured_public" {
  vpc_id = aws_vpc.unstructured.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gw.id
  }
  tags = {
    Name = "${var.project_name}-${var.env_name}-public-rt"
  }
}

resource "aws_route_table_association" "unstructured_public" {
  subnet_id      = aws_subnet.unstructured_public.id
  route_table_id = aws_route_table.unstructured_public.id
}

resource "aws_security_group" "unstructured_ec2_sg" {
  name   = "${var.project_name}-${var.env_name}-ec2-sg"
  vpc_id = aws_vpc.unstructured.id
  ingress {
    description      = "Allow SSH"
    from_port        = 22
    to_port          = 22
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }
  ingress {
    description      = "Allow HTTP"
    from_port        = 80
    to_port          = 80
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }
  ingress {
    description      = "Allow HTTPS"
    from_port        = 443
    to_port          = 443
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }
  ingress {
    description      = "Allow Jaeger"
    from_port        = 4317
    to_port          = 16686
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }
  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }
  tags = {
    Name = "${var.project_name}-${var.env_name}-ec2-sg"
  }
}

resource "aws_instance" "unstructured_ec2_instance" {
  ami           = var.aws_ami
  instance_type = var.instance_type
  availability_zone = var.availability_zone
  vpc_security_group_ids = [aws_security_group.unstructured_ec2_sg.id]
  subnet_id      = aws_subnet.unstructured_public.id
  root_block_device {
    volume_size = 600
    volume_type = "gp3"
  }
  key_name = "agentric-dev"
  tags = {
    Name = "${var.project_name}-${var.env_name}-ec2"
  }
}

resource "aws_eip" "unstructured_ec2_eip" {
  instance = aws_instance.unstructured_ec2_instance.id
}

output "instance_unstructured_public_ip" {
  value = aws_eip.unstructured_ec2_eip.public_ip
}

output "instance_unstructured_public_hostname" {
  value = aws_eip.unstructured_ec2_eip.public_dns
}

resource "aws_route53_record" "unstructured_claims_dev_record" {
  zone_id = var.hosted_zone_id
  name    = "${var.env_name}.${var.project_name}.agentricai.co"
  type    = "A"
  ttl     = 300
  records = [aws_eip.unstructured_ec2_eip.public_ip]
}

output "dns_record" {
  value = aws_route53_record.unstructured_claims_dev_record.fqdn
}

terraform {
  backend "s3" {

  }
}