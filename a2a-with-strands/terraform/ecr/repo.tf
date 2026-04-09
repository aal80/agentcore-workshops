variable "repo_name" {}

resource "aws_ecr_repository" "this" {
  name = "${var.repo_name}"
}

output "url" {
    value = aws_ecr_repository.this.repository_url
}

output "name" {
    value = aws_ecr_repository.this.name
}

resource "local_file" "repo" {
    content = aws_ecr_repository.this.name
    filename = "${path.root}/../tmp/ecr_repo_name_${var.repo_name}.txt"
}