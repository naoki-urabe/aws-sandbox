module "vpc" {
    source = "../../modules/vpc"
    name = var.vpc_name
    cidr_block = var.cidr_block
}

module "subnet" {
    source = "../../modules/subnet"
    vpc_id = module.vpc.vpc_id
    name = var.subnet_name
    subnet_cidr_block = var.subnet_cidr_block
}