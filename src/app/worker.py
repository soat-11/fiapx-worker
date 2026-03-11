import boto3
import json
import os
import shutil
from pathlib import Path
from s3_manager import S3Manager
from processor import VideoProcessor
import traceback

class VideoWorker:
    def __init__(self):
        self.sqs = boto3.client('sqs')
        self.queue_url = os.environ['SQS_QUEUE_URL']
        self.result_queue_url = os.environ['RESULT_QUEUE_URL']
        self.output_bucket = os.environ['OUTPUT_BUCKET']
        self.s3_mgr = S3Manager()
        self.processor = VideoProcessor()

    def run(self):
        print(f"[*] Worker ativo ouvindo a fila: {self.queue_url}")
        while True:
            try:
                response = self.sqs.receive_message(
                    QueueUrl=self.queue_url,
                    MaxNumberOfMessages=1,
                    WaitTimeSeconds=20
                )

                if 'Messages' in response:
                    for msg in response['Messages']:
                        print(f"[DEBUG] Mensagem bruta recebida: {msg['Body']}", flush=True)
                        try:
                            self.process_message(msg)
                        except Exception as e:
                            print(f"[ERRO] Falha no processamento: {str(e)}")
                            traceback.print_exc()
            except Exception as e:
                print(f"[ERRO CRÍTICO] Falha no loop do SQS: {str(e)}")

    def process_message(self, msg):
        # O body agora é o JSON direto que você enviou
        data = json.loads(msg['Body'])
        
        # Extração direta conforme o seu formato
        video_id = data.get('videoId')
        bucket = data.get('inputBucket')
        key = data.get('inputKey')

        if not all([video_id, bucket, key]):
            print(f"[!] Mensagem inválida ou incompleta: {data}")
            self.sqs.delete_message(QueueUrl=self.queue_url, ReceiptHandle=msg['ReceiptHandle'])
            return

        print(f"[*] Iniciando processamento do vídeo ID: {video_id} (Path: {key})")
        
        # Setup de diretórios temporários usando o videoId para evitar colisões
        work_dir = Path(f"/tmp/{video_id}")
        frames_dir = work_dir / "frames"
        
        if work_dir.exists(): shutil.rmtree(work_dir)
        frames_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # 1. Download (Usando o bucket e key que vieram na mensagem)
            video_local = str(work_dir / "input_video.mp4")
            self.s3_mgr.download_video(bucket, key, video_local)
            print(f"[1/4] Download concluído: {key}")

            # 2. FFmpeg (Fatiamento)
            self.processor.extract_frames(video_local, str(frames_dir))
            print("[2/4] Fatiamento concluído.")

            # 3. Zip
            zip_local = str(work_dir / f"{video_id}.zip")
            self.processor.create_zip(str(frames_dir), zip_local)
            print("[3/4] Zip criado.")

            output_key = f"zips/{video_id}.zip"
            print(f"[*] Fazendo upload de: {zip_local} para s3://{self.output_bucket}/{output_key}")
            self.s3_mgr.upload_zip(zip_local, self.output_bucket, output_key)
            print(f"[4/4] Upload concluído para: {output_key}")

            # Sucesso: Notifica a fila de resultado e remove do SQS
            self.notify_result(video_id, output_key, "DONE")
            self.sqs.delete_message(QueueUrl=self.queue_url, ReceiptHandle=msg['ReceiptHandle'])
            print(f"[OK] Processo finalizado para o vídeo {video_id}.")

        finally:
            # Limpeza obrigatória do /tmp para não encher o disco do Fargate
            if work_dir.exists():
                shutil.rmtree(work_dir)

    def notify_result(self, video_id, output_key, status):
        # Enviando o videoId de volta para o Orchestrator saber qual linha atualizar no banco
        result = {
            "videoId": video_id,            
            "outputKey": output_key,
            "status": status
        }
        self.sqs.send_message(QueueUrl=self.result_queue_url, MessageBody=json.dumps(result))

if __name__ == "__main__":
    worker = VideoWorker()
    worker.run()