"""
Módulo de Utilitários
=====================

Funções utilitárias para o PIIGuardian, incluindo:
- Manipulação de texto
- Formatação de saída
- Logging configurável
- Helpers diversos
"""

import re
import json
import hashlib
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from datetime import datetime
import logging
from functools import wraps
import time


# ============================================================================
# CONFIGURAÇÃO DE LOGGING
# ============================================================================

def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Configura logging para o PIIGuardian.
    
    Args:
        level: Nível de logging (DEBUG, INFO, WARNING, ERROR)
        log_file: Arquivo para salvar logs (opcional)
        format_string: Formato customizado de log (opcional)
        
    Returns:
        Logger configurado
    """
    if format_string is None:
        format_string = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    
    # Configura logger raiz
    logger = logging.getLogger("piiguardian")
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove handlers existentes
    logger.handlers.clear()
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(format_string))
    logger.addHandler(console_handler)
    
    # Handler para arquivo (se especificado)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(format_string))
        logger.addHandler(file_handler)
    
    return logger


# ============================================================================
# MANIPULAÇÃO DE TEXTO
# ============================================================================

def normalize_text(text: str) -> str:
    """
    Normaliza texto para processamento.
    
    - Remove espaços extras
    - Normaliza quebras de linha
    - Remove caracteres de controle
    
    Args:
        text: Texto original
        
    Returns:
        Texto normalizado
    """
    if not text:
        return ""
    
    # Remove caracteres de controle (exceto newline e tab)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    
    # Normaliza quebras de linha
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Remove espaços extras (mantém quebras de linha)
    lines = text.split('\n')
    lines = [' '.join(line.split()) for line in lines]
    text = '\n'.join(lines)
    
    return text.strip()


def mask_pii(text: str, entities: List[Dict], mask_char: str = '*') -> str:
    """
    Mascara dados pessoais no texto.
    
    Args:
        text: Texto original
        entities: Lista de entidades detectadas
        mask_char: Caractere para mascaramento
        
    Returns:
        Texto com dados pessoais mascarados
    """
    if not entities:
        return text
    
    # Ordena entidades por posição (decrescente) para não afetar índices
    sorted_entities = sorted(entities, key=lambda x: x.get('start', 0), reverse=True)
    
    result = text
    for entity in sorted_entities:
        start = entity.get('start', 0)
        end = entity.get('end', 0)
        value = entity.get('value', '')
        
        if start >= 0 and end > start:
            # Cria máscara mantendo alguns caracteres visíveis
            if len(value) > 4:
                masked = value[:2] + mask_char * (len(value) - 4) + value[-2:]
            else:
                masked = mask_char * len(value)
            
            result = result[:start] + masked + result[end:]
    
    return result


def anonymize_text(text: str, entities: List[Dict]) -> str:
    """
    Anonimiza texto substituindo dados pessoais por placeholders.
    
    Args:
        text: Texto original
        entities: Lista de entidades detectadas
        
    Returns:
        Texto anonimizado
    """
    if not entities:
        return text
    
    # Mapeamento de tipos para placeholders
    placeholders = {
        'CPF': '[CPF_REMOVIDO]',
        'CNPJ': '[CNPJ_REMOVIDO]',
        'TELEFONE': '[TELEFONE_REMOVIDO]',
        'CELULAR': '[CELULAR_REMOVIDO]',
        'EMAIL': '[EMAIL_REMOVIDO]',
        'CEP': '[CEP_REMOVIDO]',
        'NOME_PESSOA': '[NOME_REMOVIDO]',
        'ENDERECO': '[ENDERECO_REMOVIDO]',
        'RG': '[RG_REMOVIDO]',
        'DATA_NASCIMENTO': '[DATA_REMOVIDA]',
    }
    
    # Ordena por posição (decrescente)
    sorted_entities = sorted(entities, key=lambda x: x.get('start', 0), reverse=True)
    
    result = text
    for entity in sorted_entities:
        start = entity.get('start', 0)
        end = entity.get('end', 0)
        entity_type = entity.get('type', 'UNKNOWN').replace('_CONTEXTUAL', '')
        
        placeholder = placeholders.get(entity_type, f'[{entity_type}_REMOVIDO]')
        
        if start >= 0 and end > start:
            result = result[:start] + placeholder + result[end:]
    
    return result


def extract_numbers(text: str) -> List[str]:
    """
    Extrai todas as sequências numéricas do texto.
    
    Args:
        text: Texto para análise
        
    Returns:
        Lista de sequências numéricas encontradas
    """
    # Remove formatação comum mas mantém grupos
    pattern = r'\b[\d\.\-\s/()]+\b'
    matches = re.findall(pattern, text)
    
    # Filtra apenas sequências com pelo menos 4 dígitos
    result = []
    for match in matches:
        digits = re.sub(r'\D', '', match)
        if len(digits) >= 4:
            result.append(match.strip())
    
    return result


# ============================================================================
# FORMATAÇÃO DE SAÍDA
# ============================================================================

def format_result_json(result: Dict, indent: int = 2) -> str:
    """
    Formata resultado como JSON legível.
    
    Args:
        result: Dicionário de resultado
        indent: Indentação do JSON
        
    Returns:
        String JSON formatada
    """
    return json.dumps(result, indent=indent, ensure_ascii=False, default=str)


def format_result_table(result: Dict) -> str:
    """
    Formata resultado como tabela ASCII.
    
    Args:
        result: Dicionário de resultado
        
    Returns:
        String com tabela formatada
    """
    lines = []
    
    # Cabeçalho
    lines.append("+" + "-"*78 + "+")
    lines.append(f"| {'RESULTADO DA DETECÇÃO':^76} |")
    lines.append("+" + "-"*78 + "+")
    
    # Status
    status = "⚠️  DADOS PESSOAIS DETECTADOS" if result.get('has_pii') else "✅ NENHUM DADO PESSOAL"
    lines.append(f"| Status: {status:<67} |")
    lines.append("+" + "-"*78 + "+")
    
    # Entidades
    entities = result.get('entities', [])
    if entities:
        lines.append(f"| {'TIPO':<20} | {'VALOR':<30} | {'CONF.':<8} | {'MÉTODO':<12} |")
        lines.append("+" + "-"*78 + "+")
        
        for entity in entities:
            tipo = entity.get('type', 'N/A')[:20]
            valor = entity.get('value', 'N/A')[:30]
            conf = f"{entity.get('confidence', 0):.0%}"
            metodo = entity.get('detection_method', 'N/A')[:12]
            
            lines.append(f"| {tipo:<20} | {valor:<30} | {conf:<8} | {metodo:<12} |")
    
    lines.append("+" + "-"*78 + "+")
    
    # Sumário
    summary = result.get('summary', {})
    total = summary.get('total_entities', 0)
    by_type = summary.get('by_type', {})
    
    lines.append(f"| Total: {total} entidade(s) | Por tipo: {str(by_type)[:50]:<50} |")
    lines.append("+" + "-"*78 + "+")
    
    return "\n".join(lines)


def format_result_markdown(result: Dict) -> str:
    """
    Formata resultado como Markdown.
    
    Args:
        result: Dicionário de resultado
        
    Returns:
        String Markdown formatada
    """
    lines = []
    
    # Título
    lines.append("# Resultado da Detecção de Dados Pessoais")
    lines.append("")
    
    # Status
    if result.get('has_pii'):
        lines.append(f"**⚠️ Status:** Dados pessoais detectados")
    else:
        lines.append(f"**✅ Status:** Nenhum dado pessoal identificado")
    lines.append("")
    
    # Entidades
    entities = result.get('entities', [])
    if entities:
        lines.append("## Entidades Detectadas")
        lines.append("")
        lines.append("| Tipo | Valor | Confiança | Método |")
        lines.append("|------|-------|-----------|--------|")
        
        for entity in entities:
            tipo = entity.get('type', 'N/A')
            valor = f"`{entity.get('value', 'N/A')}`"
            conf = f"{entity.get('confidence', 0):.0%}"
            metodo = entity.get('detection_method', 'N/A')
            
            lines.append(f"| {tipo} | {valor} | {conf} | {metodo} |")
        
        lines.append("")
    
    # Sumário
    summary = result.get('summary', {})
    lines.append("## Sumário")
    lines.append("")
    lines.append(f"- **Total de entidades:** {summary.get('total_entities', 0)}")
    lines.append(f"- **Por tipo:** {summary.get('by_type', {})}")
    
    # Metadata
    metadata = result.get('metadata', {})
    if metadata:
        lines.append("")
        lines.append("## Metadados")
        lines.append("")
        lines.append(f"- **Tempo de processamento:** {metadata.get('processing_time_ms', 0):.2f}ms")
        lines.append(f"- **Modo:** {metadata.get('mode', 'N/A')}")
    
    return "\n".join(lines)


# ============================================================================
# HELPERS DIVERSOS
# ============================================================================

def generate_hash(text: str) -> str:
    """
    Gera hash SHA-256 do texto.
    
    Args:
        text: Texto para hash
        
    Returns:
        Hash hexadecimal
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def chunk_text(text: str, max_length: int = 512, overlap: int = 50) -> List[str]:
    """
    Divide texto em chunks para processamento de textos longos.
    
    Args:
        text: Texto a ser dividido
        max_length: Tamanho máximo de cada chunk
        overlap: Sobreposição entre chunks
        
    Returns:
        Lista de chunks
    """
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + max_length
        
        # Tenta quebrar em espaço ou pontuação
        if end < len(text):
            # Procura último espaço antes do limite
            last_space = text.rfind(' ', start, end)
            if last_space > start + max_length // 2:
                end = last_space
        
        chunks.append(text[start:end].strip())
        start = end - overlap
    
    return chunks


def timing_decorator(func):
    """Decorator para medir tempo de execução."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = (time.time() - start) * 1000
        logging.debug(f"{func.__name__} executado em {elapsed:.2f}ms")
        return result
    return wrapper


def load_json_file(file_path: Union[str, Path]) -> Dict:
    """
    Carrega arquivo JSON.
    
    Args:
        file_path: Caminho do arquivo
        
    Returns:
        Dicionário com conteúdo do arquivo
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_file(data: Dict, file_path: Union[str, Path], indent: int = 2):
    """
    Salva dados em arquivo JSON.
    
    Args:
        data: Dicionário a ser salvo
        file_path: Caminho do arquivo
        indent: Indentação do JSON
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False, default=str)


def get_file_stats(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Obtém estatísticas de um arquivo.
    
    Args:
        file_path: Caminho do arquivo
        
    Returns:
        Dicionário com estatísticas
    """
    path = Path(file_path)
    
    if not path.exists():
        return {'exists': False}
    
    stat = path.stat()
    
    return {
        'exists': True,
        'size_bytes': stat.st_size,
        'size_kb': round(stat.st_size / 1024, 2),
        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
        'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
    }


class PerformanceMetrics:
    """Classe para rastrear métricas de performance."""
    
    def __init__(self):
        self.metrics = {
            'total_texts': 0,
            'total_entities': 0,
            'total_time_ms': 0,
            'by_type': {},
            'true_positives': 0,
            'false_positives': 0,
            'false_negatives': 0,
        }
    
    def update(self, result: Dict, expected: Optional[Dict] = None):
        """Atualiza métricas com novo resultado."""
        self.metrics['total_texts'] += 1
        self.metrics['total_entities'] += len(result.get('entities', []))
        self.metrics['total_time_ms'] += result.get('metadata', {}).get('processing_time_ms', 0)
        
        for entity in result.get('entities', []):
            entity_type = entity.get('type', 'UNKNOWN')
            self.metrics['by_type'][entity_type] = self.metrics['by_type'].get(entity_type, 0) + 1
    
    def calculate_scores(self) -> Dict[str, float]:
        """Calcula métricas de avaliação."""
        tp = self.metrics['true_positives']
        fp = self.metrics['false_positives']
        fn = self.metrics['false_negatives']
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            'precision': round(precision, 4),
            'recall': round(recall, 4),
            'f1_score': round(f1, 4),
            'false_negatives': fn,
            'false_positives': fp,
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Retorna sumário das métricas."""
        avg_time = (
            self.metrics['total_time_ms'] / self.metrics['total_texts']
            if self.metrics['total_texts'] > 0 else 0
        )
        
        return {
            'total_texts_processed': self.metrics['total_texts'],
            'total_entities_detected': self.metrics['total_entities'],
            'average_time_ms': round(avg_time, 2),
            'entities_by_type': self.metrics['by_type'],
            **self.calculate_scores()
        }
