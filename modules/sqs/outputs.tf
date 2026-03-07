output "queue_url_upload_video" {
  value = aws_sqs_queue.upload_video.id
}
output "queue_arn_upload_video" {
  value = aws_sqs_queue.upload_video.arn
}

output "queue_url_processing_video" {
  value = aws_sqs_queue.processing_video.id
}
output "queue_arn_processing_video" {
  value = aws_sqs_queue.processing_video.arn
}

output "queue_url_concluded_video" {
  value = aws_sqs_queue.concluded_video.id
}
output "queue_arn_concluded_video" {
  value = aws_sqs_queue.concluded_video.arn
}

output "queue_url_email_notification" {
  value = aws_sqs_queue.email_notification.id
}
output "queue_arn_email_notification" {
  value = aws_sqs_queue.email_notification.arn
}