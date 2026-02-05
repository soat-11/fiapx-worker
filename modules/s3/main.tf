resource "aws_s3_bucket" "lambda_artifacts" {
  bucket = "fiapx-lambda-artifacts"
}

resource "aws_s3_bucket_public_access_block" "artifacts_block" {
  bucket = aws_s3_bucket.lambda_artifacts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}