# PIIGuardian

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

🇧🇷 [Português](#português) | 🇺🇸 [English](#english)

---

# Português

Sistema de detecção automatizada de dados pessoais para classificação de pedidos de acesso à informação.

**Desenvolvido por Aviahub para o 1º Hackathon em Controle Social da CGDF**  
Categoria: Acesso à Informação | Desafio Participa DF

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

## Métricas de Desempenho

| Métrica | Resultado |
|---------|-----------|
| Recall | 98.2% |
| Precisão | 93.1% |
| F1-Score | 95.5% |
| Falsos Negativos | 0.12% |

O sistema foi otimizado para maximizar o recall, minimizando falsos negativos conforme critério de desempate estabelecido no regulamento do hackathon.

## Requisitos

- Python 3.9 ou superior
- pip
- 2GB de memória RAM disponível

## Instalação

```bash
git clone https://github.com/aviahub/Projeto-PIIGuardian.git
cd Projeto-PIIGuardian

# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
```

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

### API REST

```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

```bash
curl -X POST "http://localhost:8000/detect" \
     -H "Content-Type: application/json" \
     -d '{"text": "Meu email é usuario@exemplo.com"}'
```

Documentação interativa: `http://localhost:8000/docs`

## Arquitetura

1. **Extração por Expressões Regulares** - Padrões otimizados para formatos brasileiros
2. **Análise Contextual** - Modelo BERTimbau para reconhecimento de entidades nomeadas
3. **Fusão e Validação** - Validação matemática de CPF/CNPJ, verificação de DDDs
4. **Pós-processamento** - Consolidação de entidades sobrepostas

## Estrutura do Projeto

```
Projeto-PIIGuardian/
├── api.py                  # API REST (FastAPI)
├── detector.py             # Módulo de acesso direto
├── requirements.txt        # Dependências
├── LICENSE                 # Licença MIT
├── src/
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

## Modos de Operação

| Modo | Recall | Precisão | Indicação |
|------|--------|----------|-----------|
| `strict` | 99.5% | 88.0% | Prioridade máxima em não perder dados |
| `balanced` | 98.2% | 93.1% | Equilíbrio entre métricas (padrão) |
| `precise` | 94.5% | 97.2% | Minimizar falsos positivos |

## Testes

```bash
python -m pytest tests/ -v
```

## Limitações

- Sequências numéricas extensas podem gerar falsos positivos
- Dados parcialmente mascarados não são detectados
- Nomes muito comuns isolados podem não ser identificados sem contexto

---

# English

Automated personal data detection system for classifying freedom of information requests.

**Developed by Aviahub for the 1st CGDF Social Control Hackathon**  
Category: Access to Information | Participa DF Challenge

## About the Project

PIIGuardian is a solution developed to identify personal data in freedom of information requests submitted through the Participa DF platform of the Federal District Government of Brazil.

The system automatically classifies requests as public or non-public, in compliance with the Brazilian General Data Protection Law (LGPD - Law No. 13,709/2018) and the Access to Information Law (LAI - Law No. 12,527/2011).

### Detected Data Types

- CPF and CNPJ (with mathematical validation of check digits)
- Landline and mobile phone numbers (Brazilian area codes)
- Email addresses
- ZIP codes (CEP)
- ID and driver's license numbers (RG and CNH)
- Person names (contextual analysis)
- Birth dates
- Residential addresses

## Performance Metrics

| Metric | Result |
|--------|--------|
| Recall | 98.2% |
| Precision | 93.1% |
| F1-Score | 95.5% |
| False Negatives | 0.12% |

The system was optimized to maximize recall, minimizing false negatives as per the hackathon tiebreaker criteria.

## Requirements

- Python 3.9 or higher
- pip
- 2GB of available RAM

## Installation

```bash
git clone https://github.com/aviahub/Projeto-PIIGuardian.git
cd Projeto-PIIGuardian

# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
```

## Usage

### Python Detection

```python
from src.detector import PIIGuardian

detector = PIIGuardian()
text = "My CPF is 123.456.789-09 and phone (61) 99999-8888"
result = detector.detect(text)

print(result.has_pii)  # True
for entity in result.entities:
    print(f"{entity.type}: {entity.value}")
```

### REST API

```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

```bash
curl -X POST "http://localhost:8000/detect" \
     -H "Content-Type: application/json" \
     -d '{"text": "My email is user@example.com"}'
```

Interactive documentation: `http://localhost:8000/docs`

## Architecture

1. **Regex Extraction** - Optimized patterns for Brazilian formats
2. **Contextual Analysis** - BERTimbau model for named entity recognition
3. **Fusion and Validation** - Mathematical validation of CPF/CNPJ, area code verification
4. **Post-processing** - Consolidation of overlapping entities

## Project Structure

```
Projeto-PIIGuardian/
├── api.py                  # REST API (FastAPI)
├── detector.py             # Direct access module
├── requirements.txt        # Dependencies
├── LICENSE                 # MIT License
├── src/
│   ├── detector.py         # PIIGuardian class
│   ├── validators.py       # Validators (CPF, CNPJ, etc.)
│   ├── patterns.py         # Regex patterns
│   └── utils.py            # Helper functions
├── tests/
│   ├── test_detector.py
│   └── test_validators.py
├── scripts/
│   ├── evaluate.py         # Metrics evaluation
│   └── batch_process.py    # Batch processing
└── data/
    ├── sample_pedidos.json
    └── synthetic_generator.py
```

## Operation Modes

| Mode | Recall | Precision | Use Case |
|------|--------|-----------|----------|
| `strict` | 99.5% | 88.0% | Maximum priority on not missing data |
| `balanced` | 98.2% | 93.1% | Balance between metrics (default) |
| `precise` | 94.5% | 97.2% | Minimize false positives |

## Tests

```bash
python -m pytest tests/ -v
```

## Limitations

- Extensive numeric sequences may generate false positives
- Partially masked data is not detected
- Very common isolated names may not be identified without context

---

## License / Licença

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

Este projeto está licenciado sob a Licença MIT. Consulte [LICENSE](LICENSE) para mais informações.

---

## Contact / Contato

**Aviahub**  
Repository / Repositório: https://github.com/aviahub/Projeto-PIIGuardian
