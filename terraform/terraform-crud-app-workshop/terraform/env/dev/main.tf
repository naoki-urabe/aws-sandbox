module "vpc" {
    source = "../../modules/vpc"
    name = var.name
    cidr_block = var.cidr_block
}