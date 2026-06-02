terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.47"
    }
    awscc = {
      source  = "hashicorp/awscc"
      version = "~> 1.86"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.9"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.9"
    }
  }
}

provider "aws" {}

provider "awscc" {}
