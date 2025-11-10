
# Infrastructure and CI/CD Documentation

## Infrastructure Overview

This project uses **Terraform** to provision AWS resources and **Docker** for deployment. The infrastructure is defined in the `infra/` directory and managed via GitHub Actions workflows.

### Key Components

1. **AWS Resources**:
   - VPC with public subnet in `ap-southeast-2a`
   - EC2 instance (`t2.large` with 600GB GP3 volume)
   - Internet Gateway and Route Table
   - Security Group allowing:
     - SSH (22)
     - HTTP (80) and HTTPS (443)
     - Jaeger tracing (4317-16686)
   - Elastic IP and Route53 DNS record for `claims.dev.agentricai.co`

2. **Variables**:
   - Defined in [infra/variables.tf](infra/variables.tf:1)
   - Configurable parameters:
     - AWS region
     - EC2 AMI ID
     - Instance type
     - Route53 Hosted Zone ID

3. **Deployment Target**:
   - Single EC2 instance with Docker Compose
   - Environment variables configured via `.env.docker` file

## CI/CD Workflows

All workflows are triggered from `.github/workflows/` and use the same base steps for infrastructure provisioning:

### 1. **Deploy to EC2** (`deploy-ec2.yml`)
- **Trigger**: Push to `main` branch or manual dispatch
- **Steps**:
  1. Checkout code
  2. Setup Terraform and AWS credentials
  3. Initialize and apply Terraform in `./infra`
  4. Deploy via SSH and Docker:
     - Clean existing deployment
     - Transfer code to EC2
     - Install Docker and dependencies
     - Run `docker compose up -d --build`

### 2. **Factory Reset** (`factory-reset.yml`)
- **Trigger**: Manual dispatch only
- **Purpose**: Full infrastructure reset
- **Steps**:
  1. Terraform destroy followed by re-apply
  2. Full Docker stack rebuild on EC2
  3. Ensures clean state for development

### 3. **Reset DB and Redeploy** (`deploy-clean-db.yml`)
- **Trigger**: Manual dispatch
- **Steps**:
  1. Terraform apply (skip if infrastructure unchanged)
  2. Stop and remove existing Docker containers
  3. Rebuild and redeploy with fresh database
  4. Preserves infrastructure but resets application state

## Security and Secrets

- AWS credentials stored in GitHub Secrets:
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
- SSH key for EC2 access stored in:
  - `SSH_PRIVATE_KEY`
- Sensitive environment variables:
### Pre-CI/CD Configuration Requirements

#### GitHub Setup
1. **Create Secrets in GitHub Repository**:
   - Add `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` for AWS authentication
   - Store EC2 SSH private key in `SSH_PRIVATE_KEY` secret
   - Add `AGENT_API_KEY` for application-level authentication

#### AWS Setup
1. **IAM User Permissions**:
   - Create IAM user with:
     - AmazonEC2FullAccess
     - IAMFullAccess
     - AmazonRoute53FullAccess
     - AmazonS3FullAccess
   - Generate and store access keys securely

2. **Network Configuration**:
   - Ensure Route53 Hosted Zone exists for `claims.dev.agentricai.co`
   - Verify VPC/Subnet configuration matches `variables.tf` parameters
   - Confirm Security Group allows:
     - SSH access from GitHub Actions IP range
     - HTTPS access from 0.0.0.0/0

3. **EC2 Instance Preparation**:
   - Create and register SSH key pair
   - Configure Instance Profile with necessary permissions
   - Set up Docker prerequisites on the instance
  - `AGENT_API_KEY`
