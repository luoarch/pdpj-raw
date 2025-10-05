#!/usr/bin/env python3
"""
Script para criar bucket S3 para documentos PDPJ.
"""

import boto3
import sys
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import os

# Carregar variáveis de ambiente
load_dotenv()

def create_s3_bucket():
    """Cria o bucket S3 para documentos PDPJ."""
    
    # Configurações
    bucket_name = os.getenv('S3_BUCKET_NAME', 'pdpj-documents-br')
    region = os.getenv('AWS_REGION', 'sa-east-1')
    
    print(f"🪣 Criando bucket S3: {bucket_name}")
    print(f"🌎 Região: {region}")
    
    try:
        # Criar cliente S3
        s3_client = boto3.client(
            's3',
            region_name=region,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        # Verificar se bucket já existe
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            print(f"✅ Bucket {bucket_name} já existe!")
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                print(f"📦 Bucket não encontrado, criando...")
            elif error_code == '403':
                print(f"❌ Acesso negado ao bucket {bucket_name}")
                return False
            else:
                print(f"❌ Erro ao verificar bucket: {e}")
                return False
        
        # Criar bucket
        if region == 'us-east-1':
            # us-east-1 não precisa de LocationConstraint
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            # Outras regiões precisam especificar LocationConstraint
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': region}
            )
        
        print(f"✅ Bucket {bucket_name} criado com sucesso!")
        
        # Configurar CORS para permitir acesso web
        cors_configuration = {
            'CORSRules': [
                {
                    'AllowedHeaders': ['*'],
                    'AllowedMethods': ['GET', 'HEAD'],
                    'AllowedOrigins': ['*'],
                    'ExposeHeaders': ['ETag'],
                    'MaxAgeSeconds': 3000
                }
            ]
        }
        
        s3_client.put_bucket_cors(Bucket=bucket_name, CORSConfiguration=cors_configuration)
        print("✅ CORS configurado para o bucket")
        
        # Configurar versionamento
        s3_client.put_bucket_versioning(
            Bucket=bucket_name,
            VersioningConfiguration={'Status': 'Enabled'}
        )
        print("✅ Versionamento habilitado")
        
        # Configurar política de ciclo de vida (opcional)
        try:
            lifecycle_config = {
                'Rules': [
                    {
                        'ID': 'DeleteOldVersions',
                        'Status': 'Enabled',
                        'NoncurrentVersionExpiration': {
                            'NoncurrentDays': 30
                        }
                    }
                ]
            }
            
            s3_client.put_bucket_lifecycle_configuration(
                Bucket=bucket_name,
                LifecycleConfiguration=lifecycle_config
            )
            print("✅ Política de ciclo de vida configurada")
        except Exception as e:
            print(f"⚠️  Aviso: Não foi possível configurar ciclo de vida: {e}")
            print("✅ Bucket criado sem política de ciclo de vida")
        
        return True
        
    except ClientError as e:
        print(f"❌ Erro ao criar bucket: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def test_bucket_access():
    """Testa acesso ao bucket criado."""
    bucket_name = os.getenv('S3_BUCKET_NAME', 'pdpj-documents-br')
    
    try:
        s3_client = boto3.client(
            's3',
            region_name=os.getenv('AWS_REGION', 'sa-east-1'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        # Listar objetos no bucket
        response = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
        print(f"✅ Acesso ao bucket {bucket_name} confirmado")
        
        # Testar upload de arquivo de teste
        test_key = 'test/connection-test.txt'
        test_content = 'Teste de conexão com bucket S3 - PDPJ API'
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key=test_key,
            Body=test_content.encode('utf-8'),
            ContentType='text/plain'
        )
        print("✅ Upload de teste realizado com sucesso")
        
        # Limpar arquivo de teste
        s3_client.delete_object(Bucket=bucket_name, Key=test_key)
        print("✅ Arquivo de teste removido")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar bucket: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Criando bucket S3 para PDPJ Process API")
    print("=" * 50)
    
    # Criar bucket
    if create_s3_bucket():
        print("\n🧪 Testando acesso ao bucket...")
        test_bucket_access()
        print("\n🎉 Configuração S3 concluída com sucesso!")
        print(f"📋 Bucket: {os.getenv('S3_BUCKET_NAME', 'pdpj-documents-br')}")
        print(f"🌎 Região: {os.getenv('AWS_REGION', 'sa-east-1')}")
    else:
        print("\n❌ Falha na criação do bucket")
        sys.exit(1)
