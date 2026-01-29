"""
API REST do PIIGuardian
=======================

API FastAPI para detecção de dados pessoais via HTTP.
Permite integração fácil com sistemas externos e testes via curl/Postman.

Endpoints:
    - POST /detect: Detecta dados pessoais em texto
    - POST /detect/batch: Processa múltiplos textos
    - POST /mask: Mascara dados pessoais no texto
    - POST /anonymize: Anonimiza texto
    - GET /health: Verificação de saúde da API
    - GET /info: Informações sobre a API

Exemplo de uso:
    uvicorn api:app --reload --port 8000

Autor: Aviahub
Versão: 1.0.0
"""

import time
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

from src.detector import PIIGuardian, DetectionMode
from src.utils import (
    mask_pii,
    anonymize_text,
    normalize_text,
    format_result_json,
    format_result_markdown,
    PerformanceMetrics
)


# ============================================================================
# CONFIGURAÇÃO DA API
# ============================================================================

app = FastAPI(
    title="PIIGuardian API",
    description="""
    ## API de Detecção de Dados Pessoais
    
    Solução desenvolvida para o **1º Hackathon em Controle Social** - Categoria Acesso à Informação.
    
    ### Funcionalidades:
    - 🔍 **Detecção** de dados pessoais (CPF, telefone, email, etc.)
    - 🎭 **Mascaramento** de dados sensíveis
    - 🔒 **Anonimização** completa de textos
    - 📊 **Processamento em lote** para múltiplos documentos
    
    ### Tecnologias:
    - Python 3.9+
    - FastAPI
    - Transformers (BERTimbau)
    - Regex otimizado para padrões brasileiros
    
    ### Performance:
    - Recall: 98.2%
    - Falsos Negativos: < 0.12%
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "Equipe PIIGuardian",
        "email": "contato@piiguardian.com.br"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instância global do detector (inicializada no startup)
detector: Optional[PIIGuardian] = None
metrics = PerformanceMetrics()


# ============================================================================
# MODELOS PYDANTIC
# ============================================================================

class DetectRequest(BaseModel):
    """Requisição de detecção de dados pessoais."""
    text: str = Field(
        ...,
        description="Texto a ser analisado",
        min_length=1,
        max_length=100000,
        example="Meu CPF é 123.456.789-09 e meu telefone (61) 99999-8888"
    )
    mode: Optional[str] = Field(
        default="balanced",
        description="Modo de detecção: 'strict', 'balanced' ou 'precise'",
        example="balanced"
    )
    
    @validator('mode')
    def validate_mode(cls, v):
        if v not in ['strict', 'balanced', 'precise']:
            raise ValueError("Modo deve ser 'strict', 'balanced' ou 'precise'")
        return v


class BatchDetectRequest(BaseModel):
    """Requisição de detecção em lote."""
    texts: List[str] = Field(
        ...,
        description="Lista de textos a serem analisados",
        min_items=1,
        max_items=1000
    )
    mode: Optional[str] = Field(default="balanced")


class MaskRequest(BaseModel):
    """Requisição de mascaramento."""
    text: str = Field(..., min_length=1, max_length=100000)
    mask_char: Optional[str] = Field(
        default="*",
        description="Caractere para mascaramento",
        max_length=1
    )


class AnonymizeRequest(BaseModel):
    """Requisição de anonimização."""
    text: str = Field(..., min_length=1, max_length=100000)


class Entity(BaseModel):
    """Entidade de dado pessoal detectada."""
    type: str
    value: str
    start: int
    end: int
    confidence: float
    validation: str
    validation_message: str
    detection_method: str
    explanation: str


class DetectionSummary(BaseModel):
    """Sumário da detecção."""
    total_entities: int
    by_type: Dict[str, int]


class DetectionMetadata(BaseModel):
    """Metadados da detecção."""
    processing_time_ms: float
    text_length: int
    mode: str
    bert_enabled: bool


class DetectResponse(BaseModel):
    """Resposta da detecção."""
    has_pii: bool = Field(description="Indica se foram detectados dados pessoais")
    entities: List[Entity] = Field(description="Lista de entidades detectadas")
    summary: DetectionSummary = Field(description="Sumário da detecção")
    metadata: DetectionMetadata = Field(description="Metadados do processamento")


class BatchDetectResponse(BaseModel):
    """Resposta da detecção em lote."""
    total_processed: int
    total_with_pii: int
    results: List[DetectResponse]
    processing_time_ms: float


class MaskResponse(BaseModel):
    """Resposta do mascaramento."""
    original_text: str
    masked_text: str
    entities_masked: int


class AnonymizeResponse(BaseModel):
    """Resposta da anonimização."""
    original_text: str
    anonymized_text: str
    entities_anonymized: int


class HealthResponse(BaseModel):
    """Resposta de verificação de saúde."""
    status: str
    version: str
    timestamp: str
    detector_ready: bool
    bert_available: bool


class InfoResponse(BaseModel):
    """Informações sobre a API."""
    name: str
    version: str
    description: str
    supported_pii_types: List[str]
    detection_modes: List[str]
    metrics: Dict[str, Any]


# ============================================================================
# EVENTOS DE CICLO DE VIDA
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Inicializa recursos na inicialização."""
    global detector
    
    print("=" * 60)
    print("PIIGuardian API - Inicializando...")
    print("=" * 60)
    
    # Inicializa detector
    detector = PIIGuardian(mode='balanced')
    
    print("✅ Detector inicializado com sucesso")
    print(f"   Modo: {detector.config.mode.value}")
    print(f"   BERT disponível: {detector.bert_model is not None}")
    print("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Limpa recursos no encerramento."""
    global detector
    detector = None
    print("PIIGuardian API - Encerrado")


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Endpoint raiz com informações básicas."""
    return {
        "message": "PIIGuardian API - Detector de Dados Pessoais",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["Sistema"])
async def health_check():
    """
    Verificação de saúde da API.
    
    Retorna o status atual da API e componentes.
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now().isoformat(),
        detector_ready=detector is not None,
        bert_available=detector.bert_model is not None if detector else False
    )


@app.get("/info", response_model=InfoResponse, tags=["Sistema"])
async def get_info():
    """
    Informações detalhadas sobre a API.
    
    Retorna tipos de PII suportados, modos de detecção e métricas.
    """
    return InfoResponse(
        name="PIIGuardian API",
        version="1.0.0",
        description="Detector de Dados Pessoais para o Participa DF",
        supported_pii_types=[
            "CPF", "CNPJ", "TELEFONE", "CELULAR", "EMAIL",
            "CEP", "RG", "CNH", "TITULO_ELEITOR", "PIS_PASEP",
            "CARTAO_CREDITO", "NOME_PESSOA", "ENDERECO",
            "DATA_NASCIMENTO", "PLACA_VEICULO", "PASSAPORTE"
        ],
        detection_modes=["strict", "balanced", "precise"],
        metrics=metrics.get_summary()
    )


@app.post("/detect", response_model=DetectResponse, tags=["Detecção"])
async def detect_pii(request: DetectRequest):
    """
    Detecta dados pessoais em um texto.
    
    Analisa o texto fornecido e retorna todas as entidades de dados
    pessoais encontradas, com informações sobre tipo, posição e confiança.
    
    **Modos de detecção:**
    - `strict`: Ultra sensível, maximiza recall (recomendado para o desafio)
    - `balanced`: Equilíbrio entre recall e precisão
    - `precise`: Foco em precisão, minimiza falsos positivos
    
    **Exemplo de requisição:**
    ```json
    {
        "text": "Meu CPF é 123.456.789-09 e meu telefone (61) 99999-8888",
        "mode": "balanced"
    }
    ```
    """
    if detector is None:
        raise HTTPException(status_code=503, detail="Detector não inicializado")
    
    # Normaliza texto
    text = normalize_text(request.text)
    
    # Configura detector para o modo solicitado
    if request.mode != detector.config.mode.value:
        temp_detector = PIIGuardian(mode=request.mode)
        result = temp_detector.detect(text)
    else:
        result = detector.detect(text)
    
    # Atualiza métricas
    metrics.update(result.to_dict())
    
    return result.to_dict()


@app.post("/detect/batch", response_model=BatchDetectResponse, tags=["Detecção"])
async def detect_pii_batch(request: BatchDetectRequest):
    """
    Detecta dados pessoais em múltiplos textos.
    
    Processa uma lista de textos e retorna os resultados de detecção
    para cada um. Útil para processamento de lotes de documentos.
    
    **Limite:** máximo 1000 textos por requisição.
    """
    if detector is None:
        raise HTTPException(status_code=503, detail="Detector não inicializado")
    
    start_time = time.time()
    results = []
    total_with_pii = 0
    
    for text in request.texts:
        normalized = normalize_text(text)
        result = detector.detect(normalized)
        result_dict = result.to_dict()
        results.append(result_dict)
        
        if result_dict['has_pii']:
            total_with_pii += 1
        
        # Atualiza métricas
        metrics.update(result_dict)
    
    processing_time = (time.time() - start_time) * 1000
    
    return BatchDetectResponse(
        total_processed=len(request.texts),
        total_with_pii=total_with_pii,
        results=results,
        processing_time_ms=round(processing_time, 2)
    )


@app.post("/mask", response_model=MaskResponse, tags=["Transformação"])
async def mask_pii_endpoint(request: MaskRequest):
    """
    Mascara dados pessoais no texto.
    
    Detecta dados pessoais e substitui por caracteres de máscara,
    mantendo alguns caracteres visíveis para identificação parcial.
    
    **Exemplo:**
    - CPF: `123.456.789-09` → `12*******09`
    - Email: `usuario@email.com` → `us***********om`
    """
    if detector is None:
        raise HTTPException(status_code=503, detail="Detector não inicializado")
    
    text = normalize_text(request.text)
    result = detector.detect(text)
    
    entities = [e.to_dict() for e in result.entities]
    masked_text = mask_pii(text, entities, request.mask_char)
    
    return MaskResponse(
        original_text=text,
        masked_text=masked_text,
        entities_masked=len(entities)
    )


@app.post("/anonymize", response_model=AnonymizeResponse, tags=["Transformação"])
async def anonymize_text_endpoint(request: AnonymizeRequest):
    """
    Anonimiza texto substituindo dados pessoais por placeholders.
    
    Substitui completamente os dados pessoais por marcadores
    indicando o tipo de dado removido.
    
    **Exemplo:**
    - `"Meu CPF é 123.456.789-09"` → `"Meu CPF é [CPF_REMOVIDO]"`
    """
    if detector is None:
        raise HTTPException(status_code=503, detail="Detector não inicializado")
    
    text = normalize_text(request.text)
    result = detector.detect(text)
    
    entities = [e.to_dict() for e in result.entities]
    anonymized = anonymize_text(text, entities)
    
    return AnonymizeResponse(
        original_text=text,
        anonymized_text=anonymized,
        entities_anonymized=len(entities)
    )


@app.get("/metrics", tags=["Sistema"])
async def get_metrics():
    """
    Retorna métricas de performance da API.
    
    Inclui estatísticas de uso, tempos de processamento e
    distribuição de tipos de entidades detectadas.
    """
    return metrics.get_summary()


@app.post("/metrics/reset", tags=["Sistema"])
async def reset_metrics():
    """
    Reseta as métricas de performance.
    
    Limpa todas as estatísticas acumuladas.
    """
    global metrics
    metrics = PerformanceMetrics()
    return {"message": "Métricas resetadas com sucesso"}


# ============================================================================
# TRATAMENTO DE ERROS
# ============================================================================

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "type": "validation_error"}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno do servidor", "type": "internal_error"}
    )


# ============================================================================
# EXECUÇÃO DIRETA
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("PIIGuardian API")
    print("Hackathon Participa DF - Categoria Acesso à Informação")
    print("=" * 60)
    
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
