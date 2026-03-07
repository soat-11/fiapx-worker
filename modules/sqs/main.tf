resource "aws_sqs_queue" "upload_video" {
  name                      = "${var.project_name}-upload-videos-queue"
  message_retention_seconds = 86400 # 1 dia
  visibility_timeout_seconds = 600 # 10 min para o Python fatiar o vídeo
  
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.upload_video_dlq.arn
    maxReceiveCount     = 5
  })
}

resource "aws_sqs_queue" "upload_video_dlq" {
  name = "${var.project_name}-upload-videos-queue-dlq"
}

resource "aws_sqs_queue" "processing_video" {
  name                      = "${var.project_name}-processing-videos-queue"
  message_retention_seconds = 86400 # 1 dia
  visibility_timeout_seconds = 600 # 10 min para o Python fatiar o vídeo
  
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.processing_video_dlq.arn
    maxReceiveCount     = 5
  })
}

resource "aws_sqs_queue" "processing_video_dlq" {
  name = "${var.project_name}-processing-videos-queue-dlq"
}

resource "aws_sqs_queue" "concluded_video" {
  name                      = "${var.project_name}-concluded-videos-queue"
  message_retention_seconds = 86400 # 1 dia
  visibility_timeout_seconds = 600 # 10 min para o Python fatiar o vídeo
  
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.concluded_video_dlq.arn
    maxReceiveCount     = 5
  })
}

resource "aws_sqs_queue" "concluded_video_dlq" {
  name = "${var.project_name}-concluded-videos-queue-dlq"
}

resource "aws_sqs_queue" "email_notification" {
  name                      = "${var.project_name}-email-notifications-queue"
  message_retention_seconds = 86400 # 1 dia
  visibility_timeout_seconds = 600 
  
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.email_notification_dlq.arn
    maxReceiveCount     = 5
  })
}

resource "aws_sqs_queue" "email_notification_dlq" {
  name = "${var.project_name}-email-notifications-queue-dlq"
}
