#!/usr/bin/env python3
"""Script para testar especificamente o Redis storage do rate limiting."""

import asyncio
import redis.asyncio as redis
import time
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.rate_limiting import RedisRateLimitStorage


async def test_redis_storage():
    """Testar funcionalidades do Redis storage."""
    
    print("🧪 Teste do Redis Storage para Rate Limiting")
    print("="*50)
    
    # Configurar Redis
    redis_url = "redis://localhost:6379/0"
    redis_client = redis.Redis.from_url(redis_url, decode_responses=False)
    
    try:
        # Testar conexão
        await redis_client.ping()
        print("✅ Conexão Redis estabelecida")
    except Exception as e:
        print(f"❌ Erro de conexão Redis: {str(e)}")
        return
    
    # Criar storage
    storage = RedisRateLimitStorage(redis_client, "test_rate_limit")
    
    client_ip = "192.168.1.100"
    current_time = time.time()
    
    print(f"\n🔍 Testando storage para IP: {client_ip}")
    
    # Teste 1: Adicionar requisições
    print("\n1️⃣ Adicionando requisições...")
    for i in range(5):
        request_time = current_time - (4 - i) * 10  # 40, 30, 20, 10, 0 segundos atrás
        await storage.add_client_request(client_ip, request_time)
        print(f"   Adicionada requisição {i+1} em {request_time}")
    
    # Teste 2: Obter requisições recentes
    print("\n2️⃣ Obtendo requisições dos últimos 30 segundos...")
    window_start = current_time - 30
    recent_requests = await storage.get_client_requests(client_ip, window_start)
    print(f"   Requisições encontradas: {len(recent_requests)}")
    for req_time in recent_requests:
        age = current_time - req_time
        print(f"   - Requisição há {age:.1f} segundos")
    
    # Teste 3: Obter requisições dos últimos 60 segundos
    print("\n3️⃣ Obtendo requisições dos últimos 60 segundos...")
    window_start = current_time - 60
    recent_requests = await storage.get_client_requests(client_ip, window_start)
    print(f"   Requisições encontradas: {len(recent_requests)}")
    
    # Teste 4: Testar múltiplos IPs
    print("\n4️⃣ Testando múltiplos IPs...")
    test_ips = ["192.168.1.101", "192.168.1.102", "10.0.0.1"]
    
    for ip in test_ips:
        for i in range(3):
            request_time = current_time - i * 5
            await storage.add_client_request(ip, request_time)
        print(f"   Adicionadas 3 requisições para {ip}")
    
    # Teste 5: Obter estatísticas
    print("\n5️⃣ Obtendo estatísticas...")
    stats = await storage.get_stats()
    print(f"   Total de clientes: {stats.get('total_clients', 0)}")
    print(f"   Total de requisições: {stats.get('total_requests', 0)}")
    
    # Teste 6: Limpeza de entradas antigas
    print("\n6️⃣ Testando limpeza de entradas antigas...")
    cutoff_time = current_time - 25  # Remover requisições mais antigas que 25 segundos
    removed_count = await storage.cleanup_old_entries(cutoff_time)
    print(f"   Entradas removidas: {removed_count}")
    
    # Verificar após limpeza
    recent_requests = await storage.get_client_requests(client_ip, current_time - 60)
    print(f"   Requisições restantes para {client_ip}: {len(recent_requests)}")
    
    # Teste 7: Verificar TTL das chaves
    print("\n7️⃣ Verificando TTL das chaves...")
    for ip in [client_ip] + test_ips:
        key = storage._get_client_key(ip)
        ttl = await redis_client.ttl(key)
        if ttl > 0:
            print(f"   TTL para {ip}: {ttl} segundos")
        else:
            print(f"   TTL para {ip}: sem TTL ou chave expirada")
    
    # Teste 8: Performance test
    print("\n8️⃣ Teste de performance...")
    performance_ip = "192.168.1.200"
    
    start_time = time.time()
    for i in range(100):
        request_time = current_time + i * 0.1
        await storage.add_client_request(performance_ip, request_time)
    add_time = time.time() - start_time
    
    start_time = time.time()
    for i in range(100):
        await storage.get_client_requests(performance_ip, current_time - 60)
    get_time = time.time() - start_time
    
    print(f"   Tempo para adicionar 100 requisições: {add_time:.3f}s")
    print(f"   Tempo para obter 100 consultas: {get_time:.3f}s")
    print(f"   Requisições/segundo (add): {100/add_time:.1f}")
    print(f"   Consultas/segundo (get): {100/get_time:.1f}")
    
    # Limpeza final
    print("\n🧹 Limpeza final...")
    final_cutoff = current_time - 1
    final_removed = await storage.cleanup_old_entries(final_cutoff)
    print(f"   Entradas finais removidas: {final_removed}")
    
    # Estatísticas finais
    final_stats = await storage.get_stats()
    print(f"\n📊 Estatísticas finais:")
    print(f"   Total de clientes: {final_stats.get('total_clients', 0)}")
    print(f"   Total de requisições: {final_stats.get('total_requests', 0)}")
    
    await redis_client.close()
    print("\n✅ Teste do Redis storage concluído com sucesso!")


async def test_redis_connection_variations():
    """Testar diferentes configurações de conexão Redis."""
    
    print("\n🔌 Teste de Configurações de Conexão Redis")
    print("="*50)
    
    configs = [
        {"url": "redis://localhost:6379/0", "name": "Redis local padrão"},
        {"url": "redis://localhost:6379/1", "name": "Redis local DB 1"},
        {"url": "redis://localhost:6379/2", "name": "Redis local DB 2"},
    ]
    
    for config in configs:
        print(f"\nTestando: {config['name']}")
        print(f"URL: {config['url']}")
        
        try:
            redis_client = redis.Redis.from_url(config['url'], decode_responses=False)
            await redis_client.ping()
            print("✅ Conexão bem-sucedida")
            
            # Testar storage
            storage = RedisRateLimitStorage(redis_client, "connection_test")
            await storage.add_client_request("test_ip", time.time())
            stats = await storage.get_stats()
            print(f"✅ Storage funcional - clientes: {stats.get('total_clients', 0)}")
            
            await redis_client.close()
            
        except Exception as e:
            print(f"❌ Erro: {str(e)}")


async def test_redis_error_handling():
    """Testar tratamento de erros do Redis."""
    
    print("\n⚠️ Teste de Tratamento de Erros Redis")
    print("="*50)
    
    # Teste com Redis inexistente
    print("\n1️⃣ Testando com Redis inexistente...")
    try:
        redis_client = redis.Redis(host="localhost", port=9999, decode_responses=False)
        storage = RedisRateLimitStorage(redis_client, "error_test")
        
        # Tentar operações que devem falhar
        requests = await storage.get_client_requests("test_ip", time.time() - 60)
        print(f"   get_client_requests retornou: {requests}")
        
        await storage.add_client_request("test_ip", time.time())
        print("   add_client_request executado")
        
    except Exception as e:
        print(f"   ❌ Erro esperado: {str(e)}")
    
    # Teste com URL inválida
    print("\n2️⃣ Testando com URL inválida...")
    try:
        redis_client = redis.Redis.from_url("redis://invalid-host:6379/0", decode_responses=False)
        storage = RedisRateLimitStorage(redis_client, "error_test")
        
        stats = await storage.get_stats()
        print(f"   get_stats retornou: {stats}")
        
    except Exception as e:
        print(f"   ❌ Erro esperado: {str(e)}")


async def main():
    """Função principal."""
    try:
        await test_redis_storage()
        await test_redis_connection_variations()
        await test_redis_error_handling()
        
    except KeyboardInterrupt:
        print("\n⚠️ Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
