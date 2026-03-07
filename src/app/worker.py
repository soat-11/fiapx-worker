import boto3
import json
import os
import shutil
from pathlib import Path
from s3_manager import S3Manager
from processor import VideoProcessor

class VideoWorker:
    def __init__(self):
        self.sqs = boto3.client('sqs')
        self.queue_url = os.environ['SQS_QUEUE_URL']
        self.result_queue_url = os.environ['RESULT_QUEUE_URL']
        self.output_bucket = os.environ['OUTPUT_BUCKET']
        self.s3_mgr = S3Manager()
        self.processor = VideoProcessor()

    def run(self):
        print(f"[*] Worker ativo ouvindo a fila {self.queue_url}")
        while True:
            response = self.sqs.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=20 # Long Polling
            )

            if 'Messages' in response:
                for msg in response['Messages']:
                    self.process_message(msg)

    def process_message(self, msg):
        body = json.loads(msg['Body'])
        # Tratando evento vindo direto do S3 ou mensagem customizada
        records = body.get('Records', [])
        
        for record in records:
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            
            # Setup de pastas temporárias
            task_id = Path(key).stem
            work_dir = Path(f"/tmp/{task_id}")
            frames_dir = work_dir / "frames"
            frames_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                video_local = self.s3_mgr.download_video(bucket, key, str(work_dir / "input.mp4"))
                self.processor.extract_frames(video_local, str(frames_dir))
                
                zip_local = self.processor.create_zip(str(frames_dir), str(work_dir / f"{task_id}.zip"))
                s3_uri = self.s3_mgr.upload_zip(self.output_bucket, f"processed/{task_id}.zip", zip_local)
                
                self.notify_result(key, s3_uri, "SUCCESS")
                self.sqs.delete_message(QueueUrl=self.queue_url, ReceiptHandle=msg['ReceiptHandle'])
                print(f"[OK] {key} processado com sucesso.")

            except Exception as e:
                print(f"[ERRO] Falha ao processar {key}: {e}")
                self.notify_result(key, None, "ERROR")
            finally:
                if work_dir.exists():
                    shutil.rmtree(work_dir)

    def notify_result(self, original_key, s3_uri, status):
        result = {
            "original_file": original_key,
            "zip_url": s3_uri,
            "status": status
        }
        self.sqs.send_message(QueueUrl=self.result_queue_url, MessageBody=json.dumps(result))

if __name__ == "__main__":
    worker = VideoWorker()
    worker.run()