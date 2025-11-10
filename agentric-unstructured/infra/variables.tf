variable "project_name" {
  description = "Project name for resource tagging"
  type        = string
  default     = "unstructured"
}

variable "env_name" {
  description = "Environment name (dev/staging/prod)"
  type        = string
  default = "unstable"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-southeast-2"
}

variable "aws_ami" {
  description = "EC2 AMI ID to use"
  type        = string
  default     = "ami-0279a86684f669718"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.large"
}

variable "hosted_zone_id" {
  description = "Route53 Hosted Zone ID"
  type        = string
  default     = "Z0185298QNBZO5YYZD9L"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "Public subnet CIDR block"
  type        = string
  default     = "10.0.1.0/24"
}

variable "availability_zone" {
  description = "Availability Zone"
  type        = string
  default     = "ap-southeast-2a"
}

variable "tf_state_bucket" {
  description = "Terraform state S3 bucket name"
  type        = string
  default     = "agentric-tf"
}
