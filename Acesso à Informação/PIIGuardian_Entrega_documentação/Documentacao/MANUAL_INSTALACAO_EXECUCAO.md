# Manual de Instalação e Execução

## PIIGuardian - Detector de Dados Pessoais

**Versão:** 1.0.0  
**Desenvolvedor:** Aviahub  
**Hackathon:** 1º Hackathon em Controle Social da CGDF

---

## Índice

1. [Requisitos do Sistema](#1-requisitos-do-sistema)
2. [Instalação](#2-instalação)
3. [Execução](#3-execução)
4. [Exemplos de Uso](#4-exemplos-de-uso)
5. [API REST](#5-api-rest)
6. [Solução de Problemas](#6-solução-de-problemas)

---

## 1. Requisitos do Sistema

### 1.1 Hardware Mínimo

| Componente | Mínimo | Recomendado |
|------------|--------|-------------|
| Processador | 2 cores | 4+ cores |
| Memória RAM | 2 GB | 4 GB |
| Espaço em Disco | 500 MB | 1 GB |

### 1.2 Software

| Software | Versão | Obrigatório |
|----------|--------|-------------|
| Python | 3.9 ou superior | Sim |
| pip | 21.0 ou superior | Sim |
| Git | 2.0 ou superior | Recomendado |

### 1.3 Sistemas Operacionais Suportados

- Windows 10/11
- Ubuntu 20.04+
- macOS 11+

---

## 2. Instalação

### 2.1 Passo 1: Obter o Código

**Opção A - Via Git (Recomendado):**
```bash
git clone https://github.com/aviahub/Projeto-PIIGuardian.git
cd Projeto-PIIGuardian
```

**Opção B - Download Manual:**
1. Acesse: https://github.com/aviahub/Projeto-PIIGuardian
2. Clique em "Code" > "Download ZIP"
3. Extraia o arquivo
4. Abra o terminal na pasta extraída

### 2.2 Passo 2: Criar Ambiente Virtual

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

> **Nota:** O prompt deve mostrar `(venv)` indicando que o ambiente está ativo.

### 2.3 Passo 3: Instalar Dependências

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Tempo estimado:** 2-5 minutos (dependendo da conexão)

### 2.4 Passo 4: Verificar Instalação

```bash
python main.py --text "Teste com CPF 123.456.789-09"
```

**Saída esperada:**
```json
{
  "tem_dados_pessoais": true,
  "entidades": [
    {
      "tipo": "CPF",
      "valor": "123.456.789-09",
      "confianca": 0.98
    }
  ]
}
```

---

## 3. Execução

### 3.1 Modo Interativo

O modo mais simples para testes manuais:

```bash
python main.py
```

O sistema aguardará entrada de texto e retornará a análise em tempo real.

**Exemplo de sessão:**
```
============================================================
PIIGuardian - Detector de Dados Pessoais
Desenvolvido por Aviahub para o Hackathon CGDF
============================================================

Digite 'sair' para encerrar.

📝 Digite o texto para análise:
> Meu nome é João Silva, CPF 123.456.789-09

----------------------------------------
🔍 RESULTADO DA ANÁLISE
----------------------------------------
⚠️  CLASSIFICAÇÃO: NÃO PÚBLICO
📊 Dados pessoais encontrados: 2

📋 Entidades detectadas:
   • NOME: João Silva (confiança: 89%)
   • CPF: 123.456.789-09 (confiança: 98%)
----------------------------------------
```

### 3.2 Linha de Comando (Texto Direto)

Para análise rápida de um texto específico:

```bash
python main.py --text "Texto para análise aqui"
```

**Com modo específico:**
```bash
python main.py --text "Texto" --mode strict
```

### 3.3 Processar Arquivo JSON

Para processar múltiplos pedidos de um arquivo:

```bash
python main.py --file entrada.json --output saida.json
```

**Formato do arquivo de entrada (entrada.json):**
```json
{
  "pedidos": [
    {"id": 1, "texto": "Primeiro pedido..."},
    {"id": 2, "texto": "Segundo pedido..."}
  ]
}
```

**Ou formato simplificado:**
```json
[
  {"id": 1, "texto": "Primeiro pedido..."},
  {"id": 2, "texto": "Segundo pedido..."}
]
```

### 3.4 Iniciar API REST

Para disponibilizar o detector como serviço web:

```bash
python main.py --api --port 8000
```

**Ou diretamente com uvicorn:**
```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

A API estará disponível em: http://localhost:8000

---

## 4. Exemplos de Uso

### 4.1 Exemplo 1: Detecção Básica

**Comando:**
```bash
python main.py --text "O solicitante de CPF 123.456.789-09 requer informações"
```

**Saída:**
```json
{
  "tem_dados_pessoais": true,
  "entidades": [
    {
      "tipo": "CPF",
      "valor": "123.456.789-09",
      "inicio": 24,
      "fim": 38,
      "confianca": 0.98
    }
  ],
  "total_entidades": 1,
  "modo": "balanced"
}
```

### 4.2 Exemplo 2: Múltiplos Tipos de Dados

**Comando:**
```bash
python main.py --text "João Silva, CPF 123.456.789-09, tel (61) 99999-8888, email joao@email.com"
```

**Saída:**
```json
{
  "tem_dados_pessoais": true,
  "entidades": [
    {"tipo": "NOME", "valor": "João Silva", "confianca": 0.89},
    {"tipo": "CPF", "valor": "123.456.789-09", "confianca": 0.98},
    {"tipo": "TELEFONE", "valor": "(61) 99999-8888", "confianca": 0.96},
    {"tipo": "EMAIL", "valor": "joao@email.com", "confianca": 0.95}
  ],
  "total_entidades": 4,
  "modo": "balanced"
}
```

### 4.3 Exemplo 3: Texto sem Dados Pessoais

**Comando:**
```bash
python main.py --text "Solicito informações sobre o horário de funcionamento do órgão"
```

**Saída:**
```json
{
  "tem_dados_pessoais": false,
  "entidades": [],
  "total_entidades": 0,
  "modo": "balanced"
}
```

### 4.4 Exemplo 4: Processamento em Lote

**Criar arquivo de teste (teste.json):**
```json
[
  {"id": 1, "texto": "Pedido sem dados pessoais"},
  {"id": 2, "texto": "Meu CPF é 123.456.789-09"},
  {"id": 3, "texto": "Email: teste@email.com, tel: 61999998888"}
]
```

**Comando:**
```bash
python main.py --file teste.json --output resultado.json
```

**Arquivo de saída (resultado.json):**
```json
[
  {"id": 1, "tem_dados_pessoais": false, "classificacao": "PUBLICO", "entidades": []},
  {"id": 2, "tem_dados_pessoais": true, "classificacao": "NAO_PUBLICO", "entidades": [{"tipo": "CPF", "valor": "123.456.789-09", "confianca": 0.98}]},
  {"id": 3, "tem_dados_pessoais": true, "classificacao": "NAO_PUBLICO", "entidades": [{"tipo": "EMAIL", "valor": "teste@email.com", "confianca": 0.95}, {"tipo": "TELEFONE", "valor": "61999998888", "confianca": 0.94}]}
]
```

---

## 5. API REST

### 5.1 Iniciar o Servidor

```bash
python main.py --api --port 8000
```

### 5.2 Endpoints Disponíveis

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | /detect | Detectar PII em texto |
| POST | /detect/batch | Processar múltiplos textos |
| POST | /mask | Mascarar dados pessoais |
| GET | /health | Verificar status do servidor |
| GET | /docs | Documentação interativa (Swagger) |

### 5.3 Exemplo: Requisição de Detecção

**Usando curl:**
```bash
curl -X POST "http://localhost:8000/detect" \
     -H "Content-Type: application/json" \
     -d '{"text": "Meu CPF é 123.456.789-09"}'
```

**Usando Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/detect",
    json={"text": "Meu CPF é 123.456.789-09"}
)
print(response.json())
```

**Resposta:**
```json
{
  "has_pii": true,
  "entities": [
    {
      "type": "CPF",
      "value": "123.456.789-09",
      "start": 11,
      "end": 25,
      "confidence": 0.98
    }
  ],
  "processing_time_ms": 12.5
}
```

### 5.4 Documentação Interativa

Acesse http://localhost:8000/docs para a documentação Swagger com interface para testar todos os endpoints.

---

## 6. Solução de Problemas

### 6.1 Erro: "Python não encontrado"

**Solução:**
1. Verifique se Python está instalado: `python --version`
2. Se não estiver, baixe em: https://www.python.org/downloads/
3. Marque "Add Python to PATH" durante a instalação

### 6.2 Erro: "pip não encontrado"

**Solução:**
```bash
python -m ensurepip --upgrade
```

### 6.3 Erro ao Instalar Dependências

**Solução:**
```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt --no-cache-dir
```

### 6.4 Erro: "ModuleNotFoundError"

**Solução:**
1. Verifique se o ambiente virtual está ativo (deve mostrar `(venv)`)
2. Reinstale as dependências:
```bash
pip install -r requirements.txt
```

### 6.5 API Não Inicia

**Verificar:**
1. Porta 8000 pode estar em uso. Tente outra porta:
```bash
python main.py --api --port 8001
```

2. Verifique se uvicorn está instalado:
```bash
pip install uvicorn
```

### 6.6 BERT Não Disponível

Se aparecer "BERT disponível: False", o sistema funcionará apenas com regex (recall ~85%).

**Para habilitar BERT:**
```bash
pip install torch transformers
```

---

## Comandos de Referência Rápida

| Ação | Comando |
|------|---------|
| Modo interativo | `python main.py` |
| Analisar texto | `python main.py --text "texto"` |
| Processar arquivo | `python main.py --file entrada.json --output saida.json` |
| Iniciar API | `python main.py --api` |
| Modo strict | `python main.py --text "texto" --mode strict` |
| Executar testes | `python -m pytest tests/ -v` |
| Ver ajuda | `python main.py --help` |

---

**Aviahub**  
Janeiro de 2026

*Manual elaborado para o 1º Hackathon em Controle Social da CGDF*
