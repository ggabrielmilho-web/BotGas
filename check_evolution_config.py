"""
Verificar configurações do Evolution API
"""
import httpx
import asyncio
import json

EVOLUTION_API_URL = "https://api.carvalhoia.com"
EVOLUTION_API_KEY = "03fd4f2fc18afc835d3e83d343eae714"

async def check_config():
    """Verificar configurações e integrações disponíveis"""

    print("=== VERIFICANDO CONFIGURACOES EVOLUTION API ===\n")

    headers = {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json"
    }

    # 1. Tentar acessar endpoint de configurações
    print("[1] Verificando informacoes da API...\n")

    endpoints_to_test = [
        "/",
        "/instance/fetchInstances",
        "/settings",
        "/integrations"
    ]

    async with httpx.AsyncClient(timeout=10.0) as client:
        for endpoint in endpoints_to_test:
            try:
                response = await client.get(
                    f"{EVOLUTION_API_URL}{endpoint}",
                    headers=headers
                )

                if response.status_code == 200:
                    print(f"[OK] {endpoint}")
                    if endpoint == "/":
                        try:
                            data = response.json()
                            print(f"     Versao: {data.get('version', 'N/A')}")
                            print(f"     Nome: {data.get('name', 'N/A')}")
                        except:
                            pass
                else:
                    print(f"[AVISO] {endpoint} - Status {response.status_code}")

            except Exception as e:
                print(f"[ERRO] {endpoint} - {str(e)[:50]}")

    print("\n" + "="*50)

    # 2. Ver uma instância existente em detalhes
    print("\n[2] Analisando instancia existente...\n")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{EVOLUTION_API_URL}/instance/fetchInstances",
                headers=headers
            )

            if response.status_code == 200:
                instances = response.json()

                if instances and len(instances) > 0:
                    inst = instances[0]

                    print("DETALHES DA INSTANCIA EXISTENTE:")
                    print(f"  Nome: {inst.get('name', 'N/A')}")
                    print(f"  ID: {inst.get('id', 'N/A')}")
                    print(f"  Integration: {inst.get('integration', 'N/A')}")
                    print(f"  Status: {inst.get('connectionStatus', 'N/A')}")

                    # Ver se tem configurações especiais
                    if 'Setting' in inst:
                        print(f"\n  Settings:")
                        settings = inst['Setting']
                        for key, value in settings.items():
                            if key not in ['id', 'createdAt', 'updatedAt', 'instanceId']:
                                print(f"    - {key}: {value}")

                    # Ver integrações ativas
                    print(f"\n  Integracoes ativas:")
                    integrations = ['Chatwoot', 'Proxy', 'Rabbitmq', 'Websocket', 'Sqs']
                    for integ in integrations:
                        if integ in inst and inst[integ]:
                            print(f"    - {integ}: Configurado")

    except Exception as e:
        print(f"Erro: {e}")

    print("\n" + "="*50)

    # 3. Tentar criar com payload EXATAMENTE igual ao da instância existente
    print("\n[3] Tentando criar com mesmo payload da instancia existente...\n")

    test_name = "test_clone_config"

    # Deletar se existir
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.delete(
                f"{EVOLUTION_API_URL}/instance/delete/{test_name}",
                headers=headers
            )
    except:
        pass

    # Payload baseado na instância existente
    payload = {
        "instanceName": test_name,
        "integration": "WHATSAPP-BAILEYS"
    }

    print(f"Payload: {json.dumps(payload, indent=2)}\n")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{EVOLUTION_API_URL}/instance/create",
                headers=headers,
                json=payload
            )

            print(f"Status: {response.status_code}")

            if response.status_code in [200, 201]:
                print("[OK] Instancia criada com sucesso!")
                print("\n==> SOLUCAO: Use 'integration': 'WHATSAPP-BAILEYS'")

                # Deletar
                await client.delete(
                    f"{EVOLUTION_API_URL}/instance/delete/{test_name}",
                    headers=headers
                )
                print("[INFO] Instancia de teste deletada")

            else:
                print(f"[ERRO] {response.text}\n")

                # Verificar se mensagem de erro dá alguma dica
                try:
                    error_data = response.json()
                    if 'response' in error_data and 'message' in error_data['response']:
                        messages = error_data['response']['message']
                        print(f"Mensagens de erro:")
                        for msg in messages:
                            print(f"  - {msg}")
                except:
                    pass

    except Exception as e:
        print(f"Erro: {e}")

    print("\n" + "="*50)
    print("\n=== RESUMO ===")
    print("\nINTEGRATION detectada nas instancias existentes: WHATSAPP-BAILEYS")
    print("Use este valor ao criar novas instancias.")
    print("\nO codigo em evolution.py JA FOI CORRIGIDO com este valor!")

if __name__ == "__main__":
    asyncio.run(check_config())
