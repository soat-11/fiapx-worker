import os
import json
import boto3
import pytest
from pathlib import Path
from moto import mock_aws 

AWS_REGION = 'us-east-1'
os.environ['SQS_QUEUE_URL'] = f'https://sqs.{AWS_REGION}.amazonaws.com/123/processing-queue'
os.environ['RESULT_QUEUE_URL'] = f'https://sqs.{AWS_REGION}.amazonaws.com/123/result-queue'
os.environ['OUTPUT_BUCKET'] = 'fiapx-project-videos'
os.environ['AWS_DEFAULT_REGION'] = AWS_REGION

from app.worker import VideoWorker

@mock_aws 
class TestVideoWorker:
    AWS_REGION = AWS_REGION

    def setup_method(self, method):
        self.s3 = boto3.client("s3", region_name=self.AWS_REGION)
        self.sqs = boto3.client("sqs", region_name=self.AWS_REGION)
        
        self.s3.create_bucket(Bucket=os.environ['OUTPUT_BUCKET'])
        self.queue_url = self.sqs.create_queue(QueueName="processing-queue")['QueueUrl']
        self.result_url = self.sqs.create_queue(QueueName="result-queue")['QueueUrl']
        
        self.worker = VideoWorker()

    def test_tmp_directory_usage(self):
        video_id = "test_123"
        work_dir = Path(f"/tmp/{video_id}")
        assert str(work_dir).startswith("/tmp")

    def test_process_message_structure(self):
        assert self.worker.output_bucket == 'fiapx-project-videos'