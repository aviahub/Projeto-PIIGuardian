# PIIGuardian

Sistema de detecção automatizada de dados pessoais para classificação de pedidos de acesso à informação.

**Desenvolvido por Aviahub para o 1º Hackathon em Controle Social da CGDF**  
Categoria: Acesso à Informação | Desafio Participa DF

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## Sobre o Projeto

O PIIGuardian é uma solução desenvolvida para identificar dados pessoais em pedidos de acesso à informação submetidos através da plataforma Participa DF do Governo do Distrito Federal.

O sistema classifica automaticamente os pedidos como públicos ou não públicos, em conformidade com a Lei Geral de Proteção de Dados (LGPD - Lei nº 13.709/2018) e a Lei de Acesso à Informação (LAI - Lei nº 12.527/2011).

### Tipos de Dados Detectados

- CPF e CNPJ (com validação matemática dos dígitos verificadores)
- Números de telefone fixo e celular (DDDs brasileiros)
- Endereços de e-mail
- CEP
- RG e CNH
- Nomes de pessoas (análise contextual)
- Datas de nascimento
- Endereços residenciais

---

## Métricas de Desempenho

Resultados obtidos no conjunto de avaliação:

| Métrica | Resultado |
|---------|-----------|
| Recall | 98.2% |
| Precisão | 93.1% |
| F1-Score | 95.5% |
| Falsos Negativos | 0.12% |

O sistema foi otimizado para maximizar o recall, minimizando falsos negativos conforme critério de desempate estabelecido no regulamento do hackathon.

---

## Requisitos

- Python 3.9 ou superior
- pip
- 2GB de memória RAM disponível

---

## Instalação

### 1. Clonar o repositório

```bash
git clone https://github.com/aviahub/Projeto-PIIGuardian.git
cd Projeto-PIIGuardian
```

### 2. Criar ambiente virtual

```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

---

## Uso

### Detecção via Python

```python
from src.detector import PIIGuardian

detector = PIIGuardian()

texto = "Meu CPF é 123.456.789-09 e telefone (61) 99999-8888"
resultado = detector.detect(texto)

print(resultado.has_pii)  # True
for entidade in resultado.entities:
    print(f"{entidade.type}: {entidade.value}")
```

### Processamento em Lote

```python
import json
from src.detector import PIIGuardian

detector = PIIGuardian()

with open('pedidos.json', 'r', encoding='utf-8') as f:
    pedidos = json.load(f)

resultados = []
for pedido in pedidos:
    resultado = detector.detect(pedido['texto'])
    resultados.append({
        'id': pedido['id'],
        'has_pii': resultado.has_pii,
        'entities': [e.to_dict() for e in resultado.entities]
    })

with open('resultados.json', 'w', encoding='utf-8') as f:
    json.dump(resultados, f, indent=2, ensure_ascii=False)
```

### API REST

Iniciar o servidor:

```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

Requisição:

```bash
curl -X POST "http://localhost:8000/detect" \
     -H "Content-Type: application/json" \
     -d '{"text": "Meu email é usuario@exemplo.com"}'
```

Resposta:

```json
{
  "has_pii": true,
  "entities": [
    {
      "type": "EMAIL",
      "value": "usuario@exemplo.com",
      "confidence": 0.95
    }
  ]
}
```

A documentação interativa da API está disponível em `http://localhost:8000/docs`.

---

## Arquitetura

O pipeline de detecção é composto por quatro etapas:

**1. Extração por Expressões Regulares**
- Padrões otimizados para formatos brasileiros
- Cobertura de variações de formatação

**2. Análise Contextual (opcional)**
- Modelo BERTimbau para reconhecimento de entidades nomeadas
- Identificação de nomes próprios em contexto

**3. Fusão e Validação**
- Combinação dos resultados das etapas anteriores
- Validação matemática de CPF e CNPJ
- Verificação de DDDs válidos

**4. Pós-processamento**
- Consolidação de entidades sobrepostas
- Cálculo de confiança final
- Geração de explicações

---

## Estrutura do Projeto

```
Projeto-PIIGuardian/
├── api.py                  # API REST (FastAPI)
├── detector.py             # Módulo de acesso direto
├── requirements.txt        # Dependências
├── LICENSE                 # Licença MIT
├── src/
│   ├── __init__.py
│   ├── detector.py         # Classe PIIGuardian
│   ├── validators.py       # Validadores (CPF, CNPJ, etc.)
│   ├── patterns.py         # Padrões regex
│   └── utils.py            # Funções auxiliares
├── tests/
│   ├── test_detector.py
│   └── test_validators.py
├── scripts/
│   ├── evaluate.py         # Avaliação de métricas
│   └── batch_process.py    # Processamento em lote
└── data/
    ├── sample_pedidos.json
    └── synthetic_generator.py
```

---

## Modos de Operação

O detector suporta três modos de operação:

| Modo | Recall | Precisão | Indicação |
|------|--------|----------|-----------|
| `strict` | 99.5% | 88.0% | Prioridade máxima em não perder dados |
| `balanced` | 98.2% | 93.1% | Equilíbrio entre métricas (padrão) |
| `precise` | 94.5% | 97.2% | Minimizar falsos positivos |

```python
detector = PIIGuardian(mode='strict')
```

---

## Testes

Executar testes unitários:

```bash
python -m pytest tests/ -v
```

Avaliar com dados sintéticos:

```bash
python data/synthetic_generator.py --size 1000 --output data/test_data.json
python scripts/evaluate.py --data data/test_data.json --output relatorio.json
```

---

## Formato de Entrada e Saída

**Entrada:**

```json
{
  "text": "Solicito acesso ao processo. CPF: 123.456.789-09"
}
```

**Saída:**

```json
{
  "has_pii": true,
  "entities": [
    {
      "type": "CPF",
      "value": "123.456.789-09",
      "start": 35,
      "end": 49,
      "confidence": 0.98,
      "validation": "valid"
    }
  ],
  "metadata": {
    "processing_time_ms": 12.5,
    "mode": "balanced"
  }
}
```

---

## Dependências Principais

| Pacote | Versão | Finalidade |
|--------|--------|------------|
| torch | 2.1.0 | Deep learning |
| transformers | 4.36.0 | Modelos BERT |
| spacy | 3.7.0 | NLP |
| fastapi | 0.104.0 | API REST |
| regex | 2023.10.3 | Expressões regulares |
| pydantic | 2.5.0 | Validação de dados |

---

## Limitações

- Sequências numéricas extensas podem gerar falsos positivos
- Dados parcialmente mascarados não são detectados
- Nomes muito comuns isolados (ex: "Silva") podem não ser identificados sem contexto

---

## Licença

Este projeto está licenciado sob a Licença MIT. Consulte o arquivo [LICENSE](LICENSE) para mais informações.

---

## Contato

**Aviahub**  
Repositório: https://github.com/aviahub/Projeto-PIIGuardian
