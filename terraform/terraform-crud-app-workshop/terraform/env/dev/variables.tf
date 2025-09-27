variable "cidr_block" {
  default = "10.0.0.0/16"
}

variable "vpc_name" {
  type = string
}

variable "subnet_name" {
  type = string
}

variable "subnet_cidr_block" {
  default = "10.0.0.0/24"
}