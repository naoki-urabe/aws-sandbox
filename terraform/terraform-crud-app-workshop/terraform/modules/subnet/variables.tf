variable "name" {
    type = string
}

variable "vpc_id" {
    type = string
}

variable "subnet_cidr_block" {
    default = "10.0.0.0/24"
}