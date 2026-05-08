terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket = "stock-intelligence-tfstate"
    key    = "prod/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
}

# ──────────────────────────────────────────────
# VPC
# ──────────────────────────────────────────────
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.project_name}-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway     = true
  single_nat_gateway     = false
  one_nat_gateway_per_az = true
  enable_dns_hostnames   = true
  enable_dns_support     = true

  tags = local.tags
}

# ──────────────────────────────────────────────
# EKS Cluster
# ──────────────────────────────────────────────
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = "${var.project_name}-cluster"
  cluster_version = "1.29"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  eks_managed_node_groups = {
    general = {
      instance_types = ["t3.large"]
      min_size       = 2
      max_size       = 10
      desired_size   = 3
    }
    ml_workloads = {
      instance_types = ["c5.2xlarge"]
      min_size       = 1
      max_size       = 5
      desired_size   = 2
      labels = { workload = "ml" }
      taints = [{ key = "ml-only", value = "true", effect = "NO_SCHEDULE" }]
    }
  }

  tags = local.tags
}

# ──────────────────────────────────────────────
# RDS PostgreSQL
# ──────────────────────────────────────────────
resource "aws_db_instance" "postgres" {
  identifier        = "${var.project_name}-postgres"
  engine            = "postgres"
  engine_version    = "15.4"
  instance_class    = "db.t3.medium"
  allocated_storage = 100
  storage_encrypted = true

  db_name  = "stock_db"
  username = var.db_username
  password = var.db_password

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  backup_retention_period = 7
  skip_final_snapshot     = false
  final_snapshot_identifier = "${var.project_name}-final-snapshot"
  deletion_protection     = true

  tags = local.tags
}

resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-db-subnet"
  subnet_ids = module.vpc.private_subnets
  tags       = local.tags
}

# ──────────────────────────────────────────────
# ElastiCache Redis
# ──────────────────────────────────────────────
resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "${var.project_name}-redis"
  description                = "Redis cache for stock platform"
  node_type                  = "cache.t3.medium"
  num_cache_clusters         = 2
  port                       = 6379
  subnet_group_name          = aws_elasticache_subnet_group.main.name
  security_group_ids         = [aws_security_group.redis.id]
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  automatic_failover_enabled = true

  tags = local.tags
}

resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.project_name}-cache-subnet"
  subnet_ids = module.vpc.private_subnets
  tags       = local.tags
}

# ──────────────────────────────────────────────
# S3 — Data Lake
# ──────────────────────────────────────────────
resource "aws_s3_bucket" "data_lake" {
  bucket        = "${var.project_name}-data-lake-${var.environment}"
  force_destroy = false
  tags          = local.tags
}

resource "aws_s3_bucket_versioning" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}

# ──────────────────────────────────────────────
# Security Groups
# ──────────────────────────────────────────────
resource "aws_security_group" "rds" {
  name   = "${var.project_name}-rds-sg"
  vpc_id = module.vpc.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = module.vpc.private_subnets_cidr_blocks
  }
  tags = local.tags
}

resource "aws_security_group" "redis" {
  name   = "${var.project_name}-redis-sg"
  vpc_id = module.vpc.vpc_id

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = module.vpc.private_subnets_cidr_blocks
  }
  tags = local.tags
}

# ──────────────────────────────────────────────
# Locals
# ──────────────────────────────────────────────
locals {
  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}
