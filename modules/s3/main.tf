resource "aws_s3_bucket" "lambda" {
  bucket = "${var.project_name}-lambdas"
}

resource "aws_s3_bucket" "uploads" {
  bucket = "${var.project_name}-video-raw"
}

resource "aws_s3_bucket" "processed" {
  bucket = "${var.project_name}-video-concluded"
}

# Bloqueio de acesso público (Boa prática de segurança)
resource "aws_s3_bucket_public_access_block" "block_uploads" {
  bucket = aws_s3_bucket.uploads.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}