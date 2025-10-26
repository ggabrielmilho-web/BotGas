"""
Testes para MessageExtractor - Validação da extração de informações

Testa a capacidade do modelo fine-tuned de extrair:
- Produtos (nome, quantidade, confiança)
- Endereços (rua, número, bairro, complemento, referência)
- Pagamento (método, troco)
- Metadados (urgência, tom do cliente)
"""
import sys
from pathlib import Path
import pytest

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.agents.message_extractor import MessageExtractor


@pytest.fixture
def extractor():
    """Fixture que cria uma instância do MessageExtractor"""
    return MessageExtractor()


@pytest.mark.asyncio
async def test_simple_message(extractor):
    """
    Teste: mensagem simples solicitando apenas um produto

    Entrada: "quero um gas"
    Esperado:
    - Produto identificado como Botijão P13 (padrão)
    - Quantidade = 1
    - Alta confiança no produto (>0.8)
    - Baixa confiança em endereço (<0.3)
    - Pagamento desconhecido
    """
    result = await extractor.extract("quero um gas")

    assert result["product"]["name"] in ["Botijão P13", "P13"], \
        f"Produto esperado: Botijão P13, recebido: {result['product']['name']}"
    assert result["product"]["quantity"] == 1, \
        f"Quantidade esperada: 1, recebida: {result['product']['quantity']}"
    assert result["product"]["confidence"] > 0.8, \
        f"Confiança do produto deve ser > 0.8, recebida: {result['product']['confidence']}"
    assert result["address"]["confidence"] < 0.3, \
        f"Confiança do endereço deve ser < 0.3, recebida: {result['address']['confidence']}"
    assert result["payment"]["method"] == "unknown", \
        f"Método de pagamento esperado: unknown, recebido: {result['payment']['method']}"


@pytest.mark.asyncio
async def test_complete_message(extractor):
    """
    Teste: mensagem completa com produto, endereço e pagamento

    Entrada: "manda 1 gas na rua joao batista 45 centro pix"
    Esperado:
    - Produto: Botijão P13
    - Quantidade: 1
    - Endereço completo extraído
    - Pagamento: pix
    """
    result = await extractor.extract("manda 1 gas na rua joao batista 45 centro pix")

    # Validar produto
    assert result["product"]["name"] in ["Botijão P13", "P13"], \
        f"Produto esperado: Botijão P13, recebido: {result['product']['name']}"
    assert result["product"]["quantity"] == 1

    # Validar endereço
    assert result["address"]["street"] is not None, "Rua não foi extraída"
    assert "joão batista" in result["address"]["street"].lower() or "joao batista" in result["address"]["street"].lower(), \
        f"Rua esperada: João Batista, recebida: {result['address']['street']}"
    assert result["address"]["number"] == "45", \
        f"Número esperado: 45, recebido: {result['address']['number']}"
    assert result["address"]["neighborhood"] is not None, "Bairro não foi extraído"
    assert "centro" in result["address"]["neighborhood"].lower(), \
        f"Bairro esperado: Centro, recebido: {result['address']['neighborhood']}"

    # Validar pagamento
    assert result["payment"]["method"] == "pix", \
        f"Método de pagamento esperado: pix, recebido: {result['payment']['method']}"


@pytest.mark.asyncio
async def test_with_change(extractor):
    """
    Teste: mensagem com pagamento em dinheiro e troco

    Entrada: "2 p45 rua y 78 dinheiro troco pra 100"
    Esperado:
    - Produto: Botijão P45
    - Quantidade: 2
    - Pagamento: dinheiro
    - Troco para: 100.0
    """
    result = await extractor.extract("2 p45 rua y 78 dinheiro troco pra 100")

    # Validar produto
    assert result["product"]["name"] in ["Botijão P45", "P45"], \
        f"Produto esperado: Botijão P45, recebido: {result['product']['name']}"
    assert result["product"]["quantity"] == 2, \
        f"Quantidade esperada: 2, recebida: {result['product']['quantity']}"

    # Validar pagamento
    assert result["payment"]["method"] == "dinheiro", \
        f"Método de pagamento esperado: dinheiro, recebido: {result['payment']['method']}"
    assert result["payment"]["change_for"] == 100.0, \
        f"Troco esperado: 100.0, recebido: {result['payment']['change_for']}"

    # Validar metadata
    assert result["metadata"]["has_change_request"] == True, \
        "has_change_request deveria ser True"


@pytest.mark.asyncio
async def test_water_gallon(extractor):
    """
    Teste: solicitação de galão de água

    Entrada: "quero 3 galao de agua"
    Esperado:
    - Produto: Galão 20L
    - Quantidade: 3
    """
    result = await extractor.extract("quero 3 galao de agua")

    assert result["product"]["name"] in ["Galão 20L", "Galão", "galao"], \
        f"Produto esperado: Galão 20L, recebido: {result['product']['name']}"
    assert result["product"]["quantity"] == 3, \
        f"Quantidade esperada: 3, recebida: {result['product']['quantity']}"


@pytest.mark.asyncio
async def test_multiple_products(extractor):
    """
    Teste: múltiplos produtos na mesma mensagem

    Entrada: "quero 1 gas e 2 galão"
    Esperado:
    - Deve extrair apenas o primeiro produto (Botijão P13)
    - Quantidade: 1

    Nota: Sistema atual processa um produto por vez
    """
    result = await extractor.extract("quero 1 gas e 2 galão")

    # Deve extrair apenas o primeiro produto
    assert result["product"]["name"] in ["Botijão P13", "P13"], \
        f"Produto esperado: Botijão P13, recebido: {result['product']['name']}"
    assert result["product"]["quantity"] == 1, \
        f"Quantidade esperada: 1, recebida: {result['product']['quantity']}"


@pytest.mark.asyncio
async def test_urgent_message(extractor):
    """
    Teste: mensagem com urgência explícita

    Entrada: "URGENTE preciso de gas rua x 12 centro pix"
    Esperado:
    - metadata.is_urgent = True
    - metadata.customer_tone = "urgent"
    """
    result = await extractor.extract("URGENTE preciso de gas rua x 12 centro pix")

    assert result["metadata"]["is_urgent"] == True, \
        f"is_urgent esperado: True, recebido: {result['metadata']['is_urgent']}"
    assert result["metadata"]["customer_tone"] == "urgent", \
        f"customer_tone esperado: urgent, recebido: {result['metadata']['customer_tone']}"


@pytest.mark.asyncio
async def test_polite_message(extractor):
    """
    Teste: mensagem educada com 'por favor'

    Entrada: "quero gas rua z 56 pix por favor"
    Esperado:
    - metadata.customer_tone = "polite"
    """
    result = await extractor.extract("quero gas rua z 56 pix por favor")

    assert result["metadata"]["customer_tone"] == "polite", \
        f"customer_tone esperado: polite, recebido: {result['metadata']['customer_tone']}"


@pytest.mark.asyncio
async def test_with_complement(extractor):
    """
    Teste: endereço com complemento

    Entrada: "1 gas rua abc 100 apto 302 pix"
    Esperado:
    - Complemento extraído: "apto 302" ou similar
    - metadata.has_complement = True
    """
    result = await extractor.extract("1 gas rua abc 100 apto 302 pix")

    assert result["address"]["complement"] is not None, \
        "Complemento deveria ter sido extraído"
    assert "302" in str(result["address"]["complement"]), \
        f"Complemento esperado conter '302', recebido: {result['address']['complement']}"
    assert result["metadata"]["has_complement"] == True, \
        f"has_complement esperado: True, recebido: {result['metadata']['has_complement']}"


@pytest.mark.asyncio
async def test_different_product_sizes(extractor):
    """
    Teste: diferentes tamanhos de botijão

    Testa a capacidade de identificar P5, P8, P13, P20, P45
    """
    test_cases = [
        ("quero 1 p5", "P5"),
        ("manda um p8", "P8"),
        ("preciso de 1 p13", "P13"),
        ("1 p20 por favor", "P20"),
        ("quero um p45", "P45"),
    ]

    for message, expected_product in test_cases:
        result = await extractor.extract(message)
        assert expected_product in result["product"]["name"], \
            f"Para '{message}': esperado {expected_product} no nome, recebido: {result['product']['name']}"


@pytest.mark.asyncio
async def test_payment_methods(extractor):
    """
    Teste: diferentes métodos de pagamento

    Testa identificação de pix, dinheiro, cartao
    """
    test_cases = [
        ("1 gas pix", "pix"),
        ("1 gas dinheiro", "dinheiro"),
        ("1 gas cartao", "cartao"),
        ("1 gas cartão", "cartao"),
    ]

    for message, expected_method in test_cases:
        result = await extractor.extract(message)
        assert result["payment"]["method"] == expected_method, \
            f"Para '{message}': esperado {expected_method}, recebido: {result['payment']['method']}"


def run_all_tests():
    """Função auxiliar para rodar todos os testes"""
    print("=" * 60)
    print("🧪 GASBOT - MESSAGE EXTRACTOR TESTS")
    print("=" * 60)
    print("\nPara rodar os testes, execute:")
    print("cd backend")
    print("pytest tests/test_message_extractor.py -v")
    print("\nOu rode um teste específico:")
    print("pytest tests/test_message_extractor.py::test_simple_message -v")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
