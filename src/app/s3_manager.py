import boto3
import os

class S3Manager:
    def __init__(self):
        self.s3 = boto3.client('s3')

    def download_video(self, bucket, key, download_path):
        print(f"[S3] Baixando {key} de {bucket}...")
        self.s3.download_file(bucket, key, download_path)
        return download_path

    def upload_zip(self, bucket, key, file_path):
        print(f"[S3] Enviando resultado para {bucket}/{key}...")
        self.s3.upload_file(file_path, bucket, key)
        return f"s3://{bucket}/{key}"