variable "project_name" {
  default = "stock-intelligence"
}
variable "environment" {
  default = "prod"
}
variable "aws_region" {
  default = "us-east-1"
}
variable "db_username" {
  sensitive = true
}
variable "db_password" {
  sensitive = true
}
