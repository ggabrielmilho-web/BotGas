# Prompt para Gerar Dataset de Fine-Tuning - GasBot

## Contexto do Sistema

Você vai gerar um dataset de treinamento para fine-tuning do GPT-4.1-mini que será usado em um chatbot de delivery de gás via WhatsApp (GasBot).

### Objetivo do Modelo Fine-Tuned

O modelo fine-tuned será um **MessageExtractor** - sua única função é extrair informações estruturadas de mensagens de clientes brasileiros que pedem gás via WhatsApp.

### Domínio de Negócio

- **Produtos**: Distribuidora de gás e água mineral
  - **Botijões de Gás (GLP)**: P5 (5kg), P8 (8kg), P13 (13kg), P20 (20kg), P45 (45kg)
  - **Galão de Água**: 20 litros (retornável)
- **Canal**: WhatsApp (mensagens informais, sem pontuação, com erros de digitação)
- **Clientes**:
  - Residencial: P5, P8, P13, Galão 20L
  - Comercial/Industrial: P20, P45
- **Região**: Brasil (português brasileiro coloquial)

---

## Formato de Saída Esperado (JSONL)

Cada linha do arquivo `.jsonl` deve conter **um único objeto JSON** com esta estrutura:

```json
{
  "messages": [
    {"role": "system", "content": "Você é um extrator de informações para pedidos de gás via WhatsApp. Analise a mensagem do cliente e extraia: produto/quantidade, endereço completo, forma de pagamento, e metadados adicionais (urgência, troco, complemento)."},
    {"role": "user", "content": "MENSAGEM DO CLIENTE AQUI"},
    {"role": "assistant", "tool_calls": [
      {
        "id": "call_123",
        "type": "function",
        "function": {
          "name": "extract_order_info",
          "arguments": "{\"product\": {\"name\": \"Botijão P13\", \"quantity\": 1, \"confidence\": 0.95}, \"address\": {\"street\": \"Rua X\", \"number\": \"123\", \"neighborhood\": \"Centro\", \"complement\": null, \"reference\": null, \"confidence\": 0.90}, \"payment\": {\"method\": \"pix\", \"change_for\": null, \"confidence\": 0.85}, \"metadata\": {\"is_urgent\": false, \"has_complement\": false, \"has_change_request\": false, \"customer_tone\": \"polite\"}}"
        }
      }
    ]}
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "extract_order_info",
        "description": "Extrai informações estruturadas de uma mensagem de pedido de gás",
        "parameters": {
          "type": "object",
          "properties": {
            "product": {
              "type": "object",
              "properties": {
                "name": {"type": "string", "description": "Nome do produto (P5, P8, P13, P20, P45, Galão 20L)"},
                "quantity": {"type": "integer", "description": "Quantidade solicitada (1-10)"},
                "confidence": {"type": "number", "description": "Confiança da extração (0.0-1.0)"}
              }
            },
            "address": {
              "type": "object",
              "properties": {
                "street": {"type": "string", "description": "Nome da rua/avenida"},
                "number": {"type": "string", "description": "Número do endereço"},
                "neighborhood": {"type": "string", "description": "Bairro"},
                "complement": {"type": "string", "description": "Complemento (apto, bloco, casa)"},
                "reference": {"type": "string", "description": "Ponto de referência"},
                "confidence": {"type": "number", "description": "Confiança da extração (0.0-1.0)"}
              }
            },
            "payment": {
              "type": "object",
              "properties": {
                "method": {"type": "string", "enum": ["pix", "dinheiro", "cartao", "unknown"], "description": "Forma de pagamento"},
                "change_for": {"type": "number", "description": "Valor para troco (se dinheiro)"},
                "confidence": {"type": "number", "description": "Confiança da extração (0.0-1.0)"}
              }
            },
            "metadata": {
              "type": "object",
              "properties": {
                "is_urgent": {"type": "boolean", "description": "Cliente indicou urgência"},
                "has_complement": {"type": "boolean", "description": "Endereço tem complemento"},
                "has_change_request": {"type": "boolean", "description": "Cliente pediu troco"},
                "customer_tone": {"type": "string", "enum": ["polite", "neutral", "urgent", "informal"], "description": "Tom da mensagem"}
              }
            }
          },
          "required": ["product", "address", "payment", "metadata"]
        }
      }
    }
  ]
}
```

---

## Regras para Geração dos Exemplos

### 1. Variação Linguística (Português Brasileiro Coloquial)

**Produtos de Gás** podem ser referidos como:
- **P5 (5kg)**: "p5", "5kg", "botijao pequeno", "botija pequena", "mini botijão"
- **P8 (8kg)**: "p8", "8kg", "botijão de 8"
- **P13 (13kg)**: "gas", "gás", "botijao", "botijão", "p13", "13kg", "botija", "butijão", "bujão" (MAIS COMUM)
- **P20 (20kg)**: "p20", "20kg", "botijão de 20", "gas de 20"
- **P45 (45kg)**: "p45", "45kg", "botijão grande", "botijao industrial", "botija de 45"
- **Galão de Água**: "galao", "galão", "agua", "água", "galao de agua", "20 litros", "20L"

**Exemplos de mensagens**:
- "um gas", "1 gas", "quero gas", "preciso de gas", "manda um gas" (sempre assume P13 se não especificar)
- "quero um p45", "preciso de 2 botijao de 45kg", "manda um industrial"
- "1 galao de agua", "2 galão", "quero agua"
- "um p5 e um galao", "quero gas p13 e agua"

**Endereço** pode vir em diversos formatos:
- "rua x 123 centro"
- "av joao batista numero 45 jardim"
- "na rua y n 78 bairro z"
- "rua abc, 12, centro"
- "avenida xyz 456 apt 301"
- Sem pontuação, com abreviações (r., av., n., num.)

**Pagamento**:
- PIX: "pix", "no pix", "via pix", "pagamento pix"
- Dinheiro: "dinheiro", "din", "espécie", "cash", "troco pra 100", "tenho 50"
- Cartão: "cartao", "cartão", "debito", "débito", "credito", "crédito"

**Urgência**:
- "urgente", "rapido", "rápido", "preciso hoje", "to sem gas", "acabou o gas"

**Complemento**:
- "apto 302", "ap 12", "casa 3", "bloco b", "fundos", "em cima da padaria"

### 2. Tipos de Mensagens a Gerar

#### Tipo A: Mensagem Simples (35% dos exemplos)
Cliente menciona apenas produto, sem endereço/pagamento.

**Exemplos**:
- "quero um gas" (P13 implícito)
- "preciso de 2 botijao de 45kg" (P45 explícito)
- "manda um p13 pra mim"
- "1 galao de agua"
- "quero 2 gas e 1 galao"

#### Tipo B: Mensagem Completa em Uma Linha (30% dos exemplos)
Cliente envia produto + endereço + pagamento tudo junto.

**Exemplos**:
- "quero 1 gas na rua x 123 centro pix"
- "manda 2 botijao de 45kg av y 456 jardim dinheiro troco pra 100"
- "preciso de gas rua z numero 78 apto 12 cartao"
- "1 p13 e 2 galao agua rua abc 45 centro pix"

#### Tipo C: Mensagem com Endereço Parcial (20% dos exemplos)
Cliente menciona produto + endereço incompleto.

**Exemplos**:
- "1 gas rua x 45 centro"
- "quero gas av joao batista 12"
- "2 p45 na rua y centro numero 89"
- "galao de agua rua z 34"

#### Tipo D: Mensagens com Extras (10% dos exemplos)
Urgência, troco, complemento, referências.

**Exemplos**:
- "urgente preciso de gas rua x 12 centro pix"
- "2 gas rua y 34 apto 201 dinheiro troco pra 50"
- "quero gas av z 67 em frente a padaria cartao"
- "URGENTE 1 p45 industrial rua abc 12 pix"

#### Tipo E: Pedidos Múltiplos (5% dos exemplos)
Cliente pede múltiplos produtos diferentes.

**Exemplos**:
- "quero 1 gas e 2 galao de agua"
- "manda 2 p13 e 1 p45 rua x 45 centro pix"
- "preciso de 1 botijao e 3 galao"
- "1 gas p13 e 1 galao agua rua y 78 pix"

### 3. Variações de Escrita

- **Sem pontuação**: "quero gas rua x 12 centro pix"
- **Com erros**: "botijao", "butijão", "avenida joao batista" (sem acento)
- **Abreviações**: "av", "r.", "n.", "ap", "bl", "num"
- **Maiúsculas/minúsculas**: "QUERO GAS", "quero gas", "Quero Gas"
- **Números por extenso**: "um gas", "dois botijao"

### 4. Valores de Confidence

- **Alta confiança (0.90-0.99)**: Informação explícita e clara
- **Média confiança (0.70-0.89)**: Informação implícita mas dedutível
- **Baixa confiança (0.50-0.69)**: Informação ambígua ou incompleta
- **Muito baixa (<0.50)**: Informação ausente ou não mencionada

**Exemplo**:
- "quero 1 gas" → product.confidence = 0.95 (explícito)
- "manda um pra mim" → product.confidence = 0.60 (implícito, contexto necessário)
- Endereço não mencionado → address.confidence = 0.0

### 5. Metadados

- **is_urgent**: true se mensagem contém "urgente", "rapido", "to sem gas", "acabou"
- **has_complement**: true se endereço tem "apto", "bloco", "casa", "fundos"
- **has_change_request**: true se menciona "troco pra X", "tenho X reais"
- **customer_tone**:
  - "polite": "por favor", "obrigado", "😊"
  - "urgent": "urgente", "rapido", caps lock
  - "informal": gírias, abreviações extremas
  - "neutral": tom padrão

---

## Exemplos de Treinamento

### Exemplo 1: Mensagem Simples
```json
{"messages": [{"role": "system", "content": "Você é um extrator de informações para pedidos de gás via WhatsApp. Analise a mensagem do cliente e extraia: produto/quantidade, endereço completo, forma de pagamento, e metadados adicionais."}, {"role": "user", "content": "quero um gas"}, {"role": "assistant", "tool_calls": [{"id": "call_001", "type": "function", "function": {"name": "extract_order_info", "arguments": "{\"product\": {\"name\": \"Botijão P13\", \"quantity\": 1, \"confidence\": 0.95}, \"address\": {\"street\": null, \"number\": null, \"neighborhood\": null, \"complement\": null, \"reference\": null, \"confidence\": 0.0}, \"payment\": {\"method\": \"unknown\", \"change_for\": null, \"confidence\": 0.0}, \"metadata\": {\"is_urgent\": false, \"has_complement\": false, \"has_change_request\": false, \"customer_tone\": \"neutral\"}}"}}]}], "tools": [{"type": "function", "function": {"name": "extract_order_info", "description": "Extrai informações estruturadas de uma mensagem de pedido de gás", "parameters": {"type": "object", "properties": {"product": {"type": "object", "properties": {"name": {"type": "string"}, "quantity": {"type": "integer"}, "confidence": {"type": "number"}}}, "address": {"type": "object", "properties": {"street": {"type": "string"}, "number": {"type": "string"}, "neighborhood": {"type": "string"}, "complement": {"type": "string"}, "reference": {"type": "string"}, "confidence": {"type": "number"}}}, "payment": {"type": "object", "properties": {"method": {"type": "string", "enum": ["pix", "dinheiro", "cartao", "unknown"]}, "change_for": {"type": "number"}, "confidence": {"type": "number"}}}, "metadata": {"type": "object", "properties": {"is_urgent": {"type": "boolean"}, "has_complement": {"type": "boolean"}, "has_change_request": {"type": "boolean"}, "customer_tone": {"type": "string", "enum": ["polite", "neutral", "urgent", "informal"]}}}}, "required": ["product", "address", "payment", "metadata"]}}}]}
```

### Exemplo 2: Mensagem Completa
```json
{"messages": [{"role": "system", "content": "Você é um extrator de informações para pedidos de gás via WhatsApp. Analise a mensagem do cliente e extraia: produto/quantidade, endereço completo, forma de pagamento, e metadados adicionais."}, {"role": "user", "content": "manda 1 gas na rua joao batista 45 centro pix"}, {"role": "assistant", "tool_calls": [{"id": "call_002", "type": "function", "function": {"name": "extract_order_info", "arguments": "{\"product\": {\"name\": \"Botijão P13\", \"quantity\": 1, \"confidence\": 0.98}, \"address\": {\"street\": \"Rua João Batista\", \"number\": \"45\", \"neighborhood\": \"Centro\", \"complement\": null, \"reference\": null, \"confidence\": 0.92}, \"payment\": {\"method\": \"pix\", \"change_for\": null, \"confidence\": 0.95}, \"metadata\": {\"is_urgent\": false, \"has_complement\": false, \"has_change_request\": false, \"customer_tone\": \"neutral\"}}"}}]}], "tools": [{"type": "function", "function": {"name": "extract_order_info", "description": "Extrai informações estruturadas de uma mensagem de pedido de gás", "parameters": {"type": "object", "properties": {"product": {"type": "object", "properties": {"name": {"type": "string"}, "quantity": {"type": "integer"}, "confidence": {"type": "number"}}}, "address": {"type": "object", "properties": {"street": {"type": "string"}, "number": {"type": "string"}, "neighborhood": {"type": "string"}, "complement": {"type": "string"}, "reference": {"type": "string"}, "confidence": {"type": "number"}}}, "payment": {"type": "object", "properties": {"method": {"type": "string", "enum": ["pix", "dinheiro", "cartao", "unknown"]}, "change_for": {"type": "number"}, "confidence": {"type": "number"}}}, "metadata": {"type": "object", "properties": {"is_urgent": {"type": "boolean"}, "has_complement": {"type": "boolean"}, "has_change_request": {"type": "boolean"}, "customer_tone": {"type": "string", "enum": ["polite", "neutral", "urgent", "informal"]}}}}, "required": ["product", "address", "payment", "metadata"]}}}]}
```

### Exemplo 3: Mensagem com Troco
```json
{"messages": [{"role": "system", "content": "Você é um extrator de informações para pedidos de gás via WhatsApp. Analise a mensagem do cliente e extraia: produto/quantidade, endereço completo, forma de pagamento, e metadados adicionais."}, {"role": "user", "content": "2 botijao rua x 78 centro dinheiro troco pra 100"}, {"role": "assistant", "tool_calls": [{"id": "call_003", "type": "function", "function": {"name": "extract_order_info", "arguments": "{\"product\": {\"name\": \"Botijão P13\", \"quantity\": 2, \"confidence\": 0.96}, \"address\": {\"street\": \"Rua X\", \"number\": \"78\", \"neighborhood\": \"Centro\", \"complement\": null, \"reference\": null, \"confidence\": 0.90}, \"payment\": {\"method\": \"dinheiro\", \"change_for\": 100.0, \"confidence\": 0.98}, \"metadata\": {\"is_urgent\": false, \"has_complement\": false, \"has_change_request\": true, \"customer_tone\": \"neutral\"}}"}}]}], "tools": [{"type": "function", "function": {"name": "extract_order_info", "description": "Extrai informações estruturadas de uma mensagem de pedido de gás", "parameters": {"type": "object", "properties": {"product": {"type": "object", "properties": {"name": {"type": "string"}, "quantity": {"type": "integer"}, "confidence": {"type": "number"}}}, "address": {"type": "object", "properties": {"street": {"type": "string"}, "number": {"type": "string"}, "neighborhood": {"type": "string"}, "complement": {"type": "string"}, "reference": {"type": "string"}, "confidence": {"type": "number"}}}, "payment": {"type": "object", "properties": {"method": {"type": "string", "enum": ["pix", "dinheiro", "cartao", "unknown"]}, "change_for": {"type": "number"}, "confidence": {"type": "number"}}}, "metadata": {"type": "object", "properties": {"is_urgent": {"type": "boolean"}, "has_complement": {"type": "boolean"}, "has_change_request": {"type": "boolean"}, "customer_tone": {"type": "string", "enum": ["polite", "neutral", "urgent", "informal"]}}}}, "required": ["product", "address", "payment", "metadata"]}}}]}
```

### Exemplo 4: Mensagem Urgente com Complemento
```json
{"messages": [{"role": "system", "content": "Você é um extrator de informações para pedidos de gás via WhatsApp. Analise a mensagem do cliente e extraia: produto/quantidade, endereço completo, forma de pagamento, e metadados adicionais."}, {"role": "user", "content": "URGENTE preciso de gas av y 123 apto 302 cartao"}, {"role": "assistant", "tool_calls": [{"id": "call_004", "type": "function", "function": {"name": "extract_order_info", "arguments": "{\"product\": {\"name\": \"Botijão P13\", \"quantity\": 1, \"confidence\": 0.93}, \"address\": {\"street\": \"Avenida Y\", \"number\": \"123\", \"neighborhood\": null, \"complement\": \"Apto 302\", \"reference\": null, \"confidence\": 0.88}, \"payment\": {\"method\": \"cartao\", \"change_for\": null, \"confidence\": 0.94}, \"metadata\": {\"is_urgent\": true, \"has_complement\": true, \"has_change_request\": false, \"customer_tone\": \"urgent\"}}"}}]}], "tools": [{"type": "function", "function": {"name": "extract_order_info", "description": "Extrai informações estruturadas de uma mensagem de pedido de gás", "parameters": {"type": "object", "properties": {"product": {"type": "object", "properties": {"name": {"type": "string"}, "quantity": {"type": "integer"}, "confidence": {"type": "number"}}}, "address": {"type": "object", "properties": {"street": {"type": "string"}, "number": {"type": "string"}, "neighborhood": {"type": "string"}, "complement": {"type": "string"}, "reference": {"type": "string"}, "confidence": {"type": "number"}}}, "payment": {"type": "object", "properties": {"method": {"type": "string", "enum": ["pix", "dinheiro", "cartao", "unknown"]}, "change_for": {"type": "number"}, "confidence": {"type": "number"}}}, "metadata": {"type": "object", "properties": {"is_urgent": {"type": "boolean"}, "has_complement": {"type": "boolean"}, "has_change_request": {"type": "boolean"}, "customer_tone": {"type": "string", "enum": ["polite", "neutral", "urgent", "informal"]}}}}, "required": ["product", "address", "payment", "metadata"]}}}]}
```

### Exemplo 5: Mensagem com Referência
```json
{"messages": [{"role": "system", "content": "Você é um extrator de informações para pedidos de gás via WhatsApp. Analise a mensagem do cliente e extraia: produto/quantidade, endereço completo, forma de pagamento, e metadados adicionais."}, {"role": "user", "content": "quero gas rua z 56 em frente a padaria sao jose pix por favor"}, {"role": "assistant", "tool_calls": [{"id": "call_005", "type": "function", "function": {"name": "extract_order_info", "arguments": "{\"product\": {\"name\": \"Botijão P13\", \"quantity\": 1, \"confidence\": 0.95}, \"address\": {\"street\": \"Rua Z\", \"number\": \"56\", \"neighborhood\": null, \"complement\": null, \"reference\": \"Em frente à padaria São José\", \"confidence\": 0.89}, \"payment\": {\"method\": \"pix\", \"change_for\": null, \"confidence\": 0.96}, \"metadata\": {\"is_urgent\": false, \"has_complement\": false, \"has_change_request\": false, \"customer_tone\": \"polite\"}}"}}]}], "tools": [{"type": "function", "function": {"name": "extract_order_info", "description": "Extrai informações estruturadas de uma mensagem de pedido de gás", "parameters": {"type": "object", "properties": {"product": {"type": "object", "properties": {"name": {"type": "string"}, "quantity": {"type": "integer"}, "confidence": {"type": "number"}}}, "address": {"type": "object", "properties": {"street": {"type": "string"}, "number": {"type": "string"}, "neighborhood": {"type": "string"}, "complement": {"type": "string"}, "reference": {"type": "string"}, "confidence": {"type": "number"}}}, "payment": {"type": "object", "properties": {"method": {"type": "string", "enum": ["pix", "dinheiro", "cartao", "unknown"]}, "change_for": {"type": "number"}, "confidence": {"type": "number"}}}, "metadata": {"type": "object", "properties": {"is_urgent": {"type": "boolean"}, "has_complement": {"type": "boolean"}, "has_change_request": {"type": "boolean"}, "customer_tone": {"type": "string", "enum": ["polite", "neutral", "urgent", "informal"]}}}}, "required": ["product", "address", "payment", "metadata"]}}}]}
```

### Exemplo 6: Botijão P45 (Industrial)
```json
{"messages": [{"role": "system", "content": "Você é um extrator de informações para pedidos de gás via WhatsApp. Analise a mensagem do cliente e extraia: produto/quantidade, endereço completo, forma de pagamento, e metadados adicionais."}, {"role": "user", "content": "preciso de 2 botijao de 45kg rua comercial 234 centro cartao"}, {"role": "assistant", "tool_calls": [{"id": "call_006", "type": "function", "function": {"name": "extract_order_info", "arguments": "{\"product\": {\"name\": \"Botijão P45\", \"quantity\": 2, \"confidence\": 0.98}, \"address\": {\"street\": \"Rua Comercial\", \"number\": \"234\", \"neighborhood\": \"Centro\", \"complement\": null, \"reference\": null, \"confidence\": 0.91}, \"payment\": {\"method\": \"cartao\", \"change_for\": null, \"confidence\": 0.95}, \"metadata\": {\"is_urgent\": false, \"has_complement\": false, \"has_change_request\": false, \"customer_tone\": \"neutral\"}}"}}]}], "tools": [{"type": "function", "function": {"name": "extract_order_info", "description": "Extrai informações estruturadas de uma mensagem de pedido de gás", "parameters": {"type": "object", "properties": {"product": {"type": "object", "properties": {"name": {"type": "string"}, "quantity": {"type": "integer"}, "confidence": {"type": "number"}}}, "address": {"type": "object", "properties": {"street": {"type": "string"}, "number": {"type": "string"}, "neighborhood": {"type": "string"}, "complement": {"type": "string"}, "reference": {"type": "string"}, "confidence": {"type": "number"}}}, "payment": {"type": "object", "properties": {"method": {"type": "string", "enum": ["pix", "dinheiro", "cartao", "unknown"]}, "change_for": {"type": "number"}, "confidence": {"type": "number"}}}, "metadata": {"type": "object", "properties": {"is_urgent": {"type": "boolean"}, "has_complement": {"type": "boolean"}, "has_change_request": {"type": "boolean"}, "customer_tone": {"type": "string", "enum": ["polite", "neutral", "urgent", "informal"]}}}}, "required": ["product", "address", "payment", "metadata"]}}}]}
```

### Exemplo 7: Galão de Água
```json
{"messages": [{"role": "system", "content": "Você é um extrator de informações para pedidos de gás via WhatsApp. Analise a mensagem do cliente e extraia: produto/quantidade, endereço completo, forma de pagamento, e metadados adicionais."}, {"role": "user", "content": "quero 3 galao de agua"}, {"role": "assistant", "tool_calls": [{"id": "call_007", "type": "function", "function": {"name": "extract_order_info", "arguments": "{\"product\": {\"name\": \"Galão 20L\", \"quantity\": 3, \"confidence\": 0.97}, \"address\": {\"street\": null, \"number\": null, \"neighborhood\": null, \"complement\": null, \"reference\": null, \"confidence\": 0.0}, \"payment\": {\"method\": \"unknown\", \"change_for\": null, \"confidence\": 0.0}, \"metadata\": {\"is_urgent\": false, \"has_complement\": false, \"has_change_request\": false, \"customer_tone\": \"neutral\"}}"}}]}], "tools": [{"type": "function", "function": {"name": "extract_order_info", "description": "Extrai informações estruturadas de uma mensagem de pedido de gás", "parameters": {"type": "object", "properties": {"product": {"type": "object", "properties": {"name": {"type": "string"}, "quantity": {"type": "integer"}, "confidence": {"type": "number"}}}, "address": {"type": "object", "properties": {"street": {"type": "string"}, "number": {"type": "string"}, "neighborhood": {"type": "string"}, "complement": {"type": "string"}, "reference": {"type": "string"}, "confidence": {"type": "number"}}}, "payment": {"type": "object", "properties": {"method": {"type": "string", "enum": ["pix", "dinheiro", "cartao", "unknown"]}, "change_for": {"type": "number"}, "confidence": {"type": "number"}}}, "metadata": {"type": "object", "properties": {"is_urgent": {"type": "boolean"}, "has_complement": {"type": "boolean"}, "has_change_request": {"type": "boolean"}, "customer_tone": {"type": "string", "enum": ["polite", "neutral", "urgent", "informal"]}}}}, "required": ["product", "address", "payment", "metadata"]}}}]}
```

### Exemplo 8: Pedido Múltiplo (extrai apenas primeiro produto)
```json
{"messages": [{"role": "system", "content": "Você é um extrator de informações para pedidos de gás via WhatsApp. Analise a mensagem do cliente e extraia: produto/quantidade, endereço completo, forma de pagamento, e metadados adicionais."}, {"role": "user", "content": "quero 1 gas e 2 galao de agua rua silva 89 jardim pix"}, {"role": "assistant", "tool_calls": [{"id": "call_008", "type": "function", "function": {"name": "extract_order_info", "arguments": "{\"product\": {\"name\": \"Botijão P13\", \"quantity\": 1, \"confidence\": 0.95}, \"address\": {\"street\": \"Rua Silva\", \"number\": \"89\", \"neighborhood\": \"Jardim\", \"complement\": null, \"reference\": null, \"confidence\": 0.90}, \"payment\": {\"method\": \"pix\", \"change_for\": null, \"confidence\": 0.96}, \"metadata\": {\"is_urgent\": false, \"has_complement\": false, \"has_change_request\": false, \"customer_tone\": \"neutral\"}}"}}]}], "tools": [{"type": "function", "function": {"name": "extract_order_info", "description": "Extrai informações estruturadas de uma mensagem de pedido de gás", "parameters": {"type": "object", "properties": {"product": {"type": "object", "properties": {"name": {"type": "string"}, "quantity": {"type": "integer"}, "confidence": {"type": "number"}}}, "address": {"type": "object", "properties": {"street": {"type": "string"}, "number": {"type": "string"}, "neighborhood": {"type": "string"}, "complement": {"type": "string"}, "reference": {"type": "string"}, "confidence": {"type": "number"}}}, "payment": {"type": "object", "properties": {"method": {"type": "string", "enum": ["pix", "dinheiro", "cartao", "unknown"]}, "change_for": {"type": "number"}, "confidence": {"type": "number"}}}, "metadata": {"type": "object", "properties": {"is_urgent": {"type": "boolean"}, "has_complement": {"type": "boolean"}, "has_change_request": {"type": "boolean"}, "customer_tone": {"type": "string", "enum": ["polite", "neutral", "urgent", "informal"]}}}}, "required": ["product", "address", "payment", "metadata"]}}}]}
```

### Exemplo 9: Botijão P5 (Pequeno)
```json
{"messages": [{"role": "system", "content": "Você é um extrator de informações para pedidos de gás via WhatsApp. Analise a mensagem do cliente e extraia: produto/quantidade, endereço completo, forma de pagamento, e metadados adicionais."}, {"role": "user", "content": "tem botijao pequeno? quero um p5"}, {"role": "assistant", "tool_calls": [{"id": "call_009", "type": "function", "function": {"name": "extract_order_info", "arguments": "{\"product\": {\"name\": \"Botijão P5\", \"quantity\": 1, \"confidence\": 0.94}, \"address\": {\"street\": null, \"number\": null, \"neighborhood\": null, \"complement\": null, \"reference\": null, \"confidence\": 0.0}, \"payment\": {\"method\": \"unknown\", \"change_for\": null, \"confidence\": 0.0}, \"metadata\": {\"is_urgent\": false, \"has_complement\": false, \"has_change_request\": false, \"customer_tone\": \"informal\"}}"}}]}], "tools": [{"type": "function", "function": {"name": "extract_order_info", "description": "Extrai informações estruturadas de uma mensagem de pedido de gás", "parameters": {"type": "object", "properties": {"product": {"type": "object", "properties": {"name": {"type": "string"}, "quantity": {"type": "integer"}, "confidence": {"type": "number"}}}, "address": {"type": "object", "properties": {"street": {"type": "string"}, "number": {"type": "string"}, "neighborhood": {"type": "string"}, "complement": {"type": "string"}, "reference": {"type": "string"}, "confidence": {"type": "number"}}}, "payment": {"type": "object", "properties": {"method": {"type": "string", "enum": ["pix", "dinheiro", "cartao", "unknown"]}, "change_for": {"type": "number"}, "confidence": {"type": "number"}}}, "metadata": {"type": "object", "properties": {"is_urgent": {"type": "boolean"}, "has_complement": {"type": "boolean"}, "has_change_request": {"type": "boolean"}, "customer_tone": {"type": "string", "enum": ["polite", "neutral", "urgent", "informal"]}}}}, "required": ["product", "address", "payment", "metadata"]}}}]}
```

### Exemplo 10: Galão de Água com Endereço Completo
```json
{"messages": [{"role": "system", "content": "Você é um extrator de informações para pedidos de gás via WhatsApp. Analise a mensagem do cliente e extraia: produto/quantidade, endereço completo, forma de pagamento, e metadados adicionais."}, {"role": "user", "content": "manda 2 galao agua av paulista 1500 apto 45 dinheiro"}, {"role": "assistant", "tool_calls": [{"id": "call_010", "type": "function", "function": {"name": "extract_order_info", "arguments": "{\"product\": {\"name\": \"Galão 20L\", \"quantity\": 2, \"confidence\": 0.96}, \"address\": {\"street\": \"Avenida Paulista\", \"number\": \"1500\", \"neighborhood\": null, \"complement\": \"Apto 45\", \"reference\": null, \"confidence\": 0.91}, \"payment\": {\"method\": \"dinheiro\", \"change_for\": null, \"confidence\": 0.95}, \"metadata\": {\"is_urgent\": false, \"has_complement\": true, \"has_change_request\": false, \"customer_tone\": \"neutral\"}}"}}]}], "tools": [{"type": "function", "function": {"name": "extract_order_info", "description": "Extrai informações estruturadas de uma mensagem de pedido de gás", "parameters": {"type": "object", "properties": {"product": {"type": "object", "properties": {"name": {"type": "string"}, "quantity": {"type": "integer"}, "confidence": {"type": "number"}}}, "address": {"type": "object", "properties": {"street": {"type": "string"}, "number": {"type": "string"}, "neighborhood": {"type": "string"}, "complement": {"type": "string"}, "reference": {"type": "string"}, "confidence": {"type": "number"}}}, "payment": {"type": "object", "properties": {"method": {"type": "string", "enum": ["pix", "dinheiro", "cartao", "unknown"]}, "change_for": {"type": "number"}, "confidence": {"type": "number"}}}, "metadata": {"type": "object", "properties": {"is_urgent": {"type": "boolean"}, "has_complement": {"type": "boolean"}, "has_change_request": {"type": "boolean"}, "customer_tone": {"type": "string", "enum": ["polite", "neutral", "urgent", "informal"]}}}}, "required": ["product", "address", "payment", "metadata"]}}}]}
```

---

## Tarefa: Gerar 300 Exemplos

Por favor, gere **300 exemplos de treinamento** seguindo estas especificações:

### Distribuição:
- **105 exemplos** (35%): Tipo A - Mensagem Simples (produtos variados: P5, P8, P13, P20, P45, Galão)
- **90 exemplos** (30%): Tipo B - Mensagem Completa
- **60 exemplos** (20%): Tipo C - Endereço Parcial
- **30 exemplos** (10%): Tipo D - Mensagens com Extras
- **15 exemplos** (5%): Tipo E - Pedidos Múltiplos

### Distribuição de Produtos nos Exemplos:
- **P13 (13kg)**: 60% dos exemplos (produto mais comum - residencial)
- **Galão 20L**: 20% dos exemplos (muito comum em conjunto com gás)
- **P45 (45kg)**: 10% dos exemplos (comercial/industrial)
- **P5 (5kg)**: 5% dos exemplos (menos comum)
- **P8 (8kg)**: 3% dos exemplos (menos comum)
- **P20 (20kg)**: 2% dos exemplos (raro)

### Requisitos de Qualidade:
1. **Variação linguística alta**: Nunca repita a mesma estrutura de frase
2. **Erros de digitação realistas**: 20% dos exemplos devem conter erros típicos
3. **Diversidade de nomes**: Use nomes de ruas brasileiras reais e variados
4. **Confidence scores realistas**: Ajuste conforme clareza da informação
5. **Metadados coerentes**: Tom da mensagem deve refletir o conteúdo

### Formato de Entrega:
- Arquivo `.jsonl` onde **cada linha é um JSON completo** (sem quebras de linha no JSON)
- Use **aspas duplas** (") em todo o JSON (não use aspas simples)
- Valide que cada linha é um JSON válido
- Nome do arquivo: `gasbot-finetuning-dataset.jsonl`

### Validação Final:
Após gerar, valide que:
- [ ] Arquivo tem exatamente 300 linhas
- [ ] Cada linha é um JSON válido
- [ ] Todos os JSONs seguem o schema exato do exemplo
- [ ] Há diversidade linguística (sem repetições)
- [ ] Confidence scores fazem sentido
- [ ] Metadados estão coerentes

---

## Observações Importantes

1. **NÃO inclua contexto de conversa anterior** - cada exemplo é uma mensagem isolada
2. **NÃO use emojis nas mensagens dos clientes** (exceto casos raros de cortesia)
3. **Sempre normalize endereços** no output: "rua x" → "Rua X", "av" → "Avenida"
4. **Quantidade padrão é 1** se não especificada
5. **Normalização de Produtos no Output**:
   - "gas", "gás", "botijão" SEM especificação → "Botijão P13" (assume padrão residencial)
   - "p5", "5kg", "botijão pequeno" → "Botijão P5"
   - "p8", "8kg" → "Botijão P8"
   - "p13", "13kg", "botijão" → "Botijão P13"
   - "p20", "20kg" → "Botijão P20"
   - "p45", "45kg", "botijão grande", "industrial" → "Botijão P45"
   - "galao", "água", "galão de água" → "Galão 20L"
6. **Pedidos Múltiplos**: Se cliente pede "1 gas e 2 galão", extraia APENAS o primeiro produto mencionado ("Botijão P13"). O sistema GasBot processa um produto por vez.
7. **Use null para campos não mencionados** (não use strings vazias)
8. **Confidence = 0.0** para informações completamente ausentes

---

## Começe a Geração Agora

Por favor, gere o arquivo `gasbot-finetuning-dataset.jsonl` com 300 exemplos seguindo todas as especificações acima.
