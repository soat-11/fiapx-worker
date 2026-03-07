output "bucket_id" {
  value = aws_s3_bucket.lambda.id
}

output "upload_bucket_id" {
  value = aws_s3_bucket.uploads.id
}

output "processed_bucket_id" {
  value = aws_s3_bucket.processed.id
}