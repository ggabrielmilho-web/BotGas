"""
Debug Evolution API - Ver estrutura esperada
"""
import httpx
import asyncio
import json

EVOLUTION_API_URL = "https://api.carvalhoia.com"
EVOLUTION_API_KEY = "03fd4f2fc18afc835d3e83d343eae714"

async def debug_evolution():
    """Debug detalhado do Evolution API"""

    print("=== DEBUG EVOLUTION API ===\n")

    headers = {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json"
    }

    # 1. Ver instâncias existentes COMPLETAS
    print("[1] Buscando instancias existentes (estrutura completa)...\n")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{EVOLUTION_API_URL}/instance/fetchInstances",
                headers=headers
            )

            if response.status_code == 200:
                instances = response.json()
                print(f"Total de instancias: {len(instances)}\n")

                if instances:
                    # Mostrar primeira instância COMPLETA
                    print("=== ESTRUTURA DA PRIMEIRA INSTANCIA ===")
                    print(json.dumps(instances[0], indent=2, ensure_ascii=False))
                    print("\n" + "="*50 + "\n")

                    # Extrair campos importantes
                    if 'instance' in instances[0]:
                        inst = instances[0]['instance']
                        print("CAMPOS IMPORTANTES:")
                        print(f"  - instanceName: {inst.get('instanceName')}")
                        print(f"  - state: {inst.get('state')}")
                        print(f"  - integration: {inst.get('integration')}")
                        print(f"  - webhook: {inst.get('webhook')}")
                        print(f"  - webhookByEvents: {inst.get('webhookByEvents')}")

                        # Ver se tem integration configurada
                        integration = inst.get('integration')
                        if integration:
                            print(f"\n  INTEGRATION configurada: {integration}")
                        else:
                            print(f"\n  INTEGRATION: Nao configurada (None)")

            else:
                print(f"Erro: {response.status_code}")
                print(response.text)

    except Exception as e:
        print(f"Erro: {e}")

    print("\n" + "="*50)

    # 2. Testar diferentes payloads de criação
    print("\n[2] Testando diferentes payloads de criacao...\n")

    test_instance_name = "test_debug_gasbot"

    # Deletar se existir
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.delete(
                f"{EVOLUTION_API_URL}/instance/delete/{test_instance_name}",
                headers=headers
            )
            print("Instancia antiga deletada (se existia)\n")
    except:
        pass

    # TESTE 1: Payload mínimo
    print("TESTE 1: Payload minimo")
    payload1 = {
        "instanceName": test_instance_name,
    }
    print(f"Payload: {json.dumps(payload1, indent=2)}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{EVOLUTION_API_URL}/instance/create",
                headers=headers,
                json=payload1
            )

            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:500]}\n")

    except Exception as e:
        print(f"Erro: {e}\n")

    # TESTE 2: Com integration = "WHATSAPP-BAILEYS"
    print("\nTESTE 2: Com integration WHATSAPP-BAILEYS")
    payload2 = {
        "instanceName": test_instance_name,
        "integration": "WHATSAPP-BAILEYS",
        "qrcode": True
    }
    print(f"Payload: {json.dumps(payload2, indent=2)}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{EVOLUTION_API_URL}/instance/create",
                headers=headers,
                json=payload2
            )

            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:500]}\n")

            if response.status_code in [200, 201]:
                print("[OK] Instancia criada com sucesso!")

                # Deletar logo em seguida
                await client.delete(
                    f"{EVOLUTION_API_URL}/instance/delete/{test_instance_name}",
                    headers=headers
                )
                print("[INFO] Instancia de teste deletada\n")

    except Exception as e:
        print(f"Erro: {e}\n")

    # TESTE 3: Sem integration (deixar API escolher)
    print("\nTESTE 3: Sem campo integration (deixar default)")
    payload3 = {
        "instanceName": test_instance_name,
        "qrcode": True,
        "webhook": "http://localhost:8000/webhook"
    }
    print(f"Payload: {json.dumps(payload3, indent=2)}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{EVOLUTION_API_URL}/instance/create",
                headers=headers,
                json=payload3
            )

            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:500]}\n")

            if response.status_code in [200, 201]:
                print("[OK] Instancia criada com sucesso!")

                # Deletar logo em seguida
                await client.delete(
                    f"{EVOLUTION_API_URL}/instance/delete/{test_instance_name}",
                    headers=headers
                )
                print("[INFO] Instancia de teste deletada\n")

    except Exception as e:
        print(f"Erro: {e}\n")

    # TESTE 4: Com integration = "WHATSAPP-WEB"
    print("\nTESTE 4: Com integration WHATSAPP-WEB")
    payload4 = {
        "instanceName": test_instance_name,
        "integration": "WHATSAPP-WEB",
        "qrcode": True
    }
    print(f"Payload: {json.dumps(payload4, indent=2)}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{EVOLUTION_API_URL}/instance/create",
                headers=headers,
                json=payload4
            )

            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:500]}\n")

            if response.status_code in [200, 201]:
                print("[OK] Instancia criada com sucesso!")

                # Deletar logo em seguida
                await client.delete(
                    f"{EVOLUTION_API_URL}/instance/delete/{test_instance_name}",
                    headers=headers
                )
                print("[INFO] Instancia de teste deletada\n")

    except Exception as e:
        print(f"Erro: {e}\n")

    print("="*50)
    print("\n=== FIM DO DEBUG ===")

if __name__ == "__main__":
    asyncio.run(debug_evolution())
