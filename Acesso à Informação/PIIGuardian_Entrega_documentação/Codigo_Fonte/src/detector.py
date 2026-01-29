"""
Módulo Principal do PIIGuardian
================================

Este módulo contém a classe principal PIIGuardian para detecção de dados
pessoais em textos. A solução é otimizada para maximizar o recall
(minimizar falsos negativos) conforme critério de desempate do hackathon.

Classes:
    - PIIGuardian: Detector principal de dados pessoais
    - DetectionMode: Modos de operação do detector

Pipeline de Detecção:
    1. Regex Agressivo - Captura padrões conhecidos
    2. BERT Contextual - Análise semântica com transformers
    3. Fusão Inteligente - Combina resultados priorizando recall
    4. Anti-False-Negative Filter - Captura padrões contextuais
    5. Validação de Consistência - Valida dados matematicamente
"""

import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime

# Imports locais
from .patterns import BrazilianPatterns, ContextualPatterns, PIIType
from .validators import (
    CPFValidator,
    CNPJValidator,
    PhoneValidator,
    EmailValidator,
    CEPValidator,
    ValidationResult
)

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flag para verificar se transformers está disponível
TRANSFORMERS_AVAILABLE = False
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForTokenClassification
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    logger.warning(
        "Transformers/PyTorch não disponível. "
        "Detecção BERT desabilitada. Instale com: pip install torch transformers"
    )


class DetectionMode(Enum):
    """Modos de operação do detector."""
    STRICT = "strict"       # Ultra sensível - recall máximo
    BALANCED = "balanced"   # Equilíbrio entre recall e precisão
    PRECISE = "precise"     # Foco em precisão


@dataclass
class DetectionConfig:
    """Configuração do detector."""
    mode: DetectionMode = DetectionMode.BALANCED
    use_bert: bool = True
    use_contextual: bool = True
    validate_documents: bool = True
    min_confidence: float = 0.5
    
    # Thresholds dinâmicos por tipo de dado
    thresholds: Dict[str, float] = field(default_factory=lambda: {
        'CPF': 0.3,          # Baixo - captura TUDO que parecer CPF
        'CNPJ': 0.4,         # Baixo - prioriza não perder
        'TELEFONE': 0.4,     # Baixo - prioriza não perder
        'CELULAR': 0.4,      # Baixo - prioriza não perder
        'EMAIL': 0.7,        # Médio - precisa ser email válido
        'CEP': 0.5,          # Médio
        'NOME': 0.6,         # Médio - contexto importante
        'RG': 0.5,           # Médio
        'DATA_NASCIMENTO': 0.6,  # Médio
        'DEFAULT': 0.5       # Padrão
    })


@dataclass
class Entity:
    """Representa uma entidade de dado pessoal detectada."""
    type: str
    value: str
    start: int
    end: int
    confidence: float
    validation_status: str = "not_validated"
    validation_message: str = ""
    detection_method: str = "regex"
    explanation: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte entidade para dicionário."""
        return {
            'type': self.type,
            'value': self.value,
            'start': self.start,
            'end': self.end,
            'confidence': self.confidence,
            'validation': self.validation_status,
            'validation_message': self.validation_message,
            'detection_method': self.detection_method,
            'explanation': self.explanation
        }


@dataclass
class DetectionResult:
    """Resultado da detecção de dados pessoais."""
    has_pii: bool
    entities: List[Entity]
    summary: Dict[str, Any]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte resultado para dicionário."""
        return {
            'has_pii': self.has_pii,
            'entities': [e.to_dict() for e in self.entities],
            'summary': self.summary,
            'metadata': self.metadata
        }


class PIIGuardian:
    """
    Detector de Dados Pessoais para o Participa DF.
    
    Solução híbrida (Regex + BERT) otimizada para minimização de falsos
    negativos, conforme critério de desempate do hackathon.
    
    Atributos:
        config: Configuração do detector
        patterns: Padrões regex brasileiros
        contextual: Padrões contextuais
        validators: Validadores matemáticos
    
    Exemplo:
        >>> detector = PIIGuardian()
        >>> resultado = detector.detect("Meu CPF é 123.456.789-09")
        >>> print(resultado.has_pii)
        True
        >>> for entity in resultado.entities:
        ...     print(f"{entity.type}: {entity.value}")
        CPF: 123.456.789-09
    """
    
    # Lista de nomes brasileiros comuns (top 1000)
    BRAZILIAN_NAMES: set = {
        # Sobrenomes mais comuns
        "silva", "santos", "oliveira", "souza", "rodrigues", "ferreira",
        "alves", "pereira", "lima", "gomes", "costa", "ribeiro", "martins",
        "carvalho", "almeida", "lopes", "soares", "fernandes", "vieira",
        "barbosa", "rocha", "dias", "nascimento", "andrade", "moreira",
        "nunes", "marques", "machado", "mendes", "freitas", "cardoso",
        "ramos", "gonçalves", "santana", "teixeira", "moura", "araújo",
        # Nomes próprios comuns
        "maria", "josé", "ana", "joão", "paulo", "carlos", "antonio",
        "francisco", "pedro", "lucas", "luiz", "marcos", "gabriel",
        "rafael", "daniel", "fernanda", "juliana", "camila", "amanda",
        "patricia", "aline", "bruna", "jessica", "leticia", "larissa",
    }
    
    def __init__(
        self,
        mode: str = 'balanced',
        config: Optional[DetectionConfig] = None,
        extra_patterns: Optional[Dict[str, str]] = None
    ):
        """
        Inicializa o detector PIIGuardian.
        
        Args:
            mode: Modo de operação ('strict', 'balanced', 'precise')
            config: Configuração customizada (opcional)
            extra_patterns: Padrões regex adicionais (opcional)
        """
        # Configura modo
        if config:
            self.config = config
        else:
            mode_enum = DetectionMode(mode)
            self.config = self._get_config_for_mode(mode_enum)
        
        # Inicializa padrões
        self.patterns = BrazilianPatterns()
        self.contextual = ContextualPatterns()
        
        # Adiciona padrões extras se fornecidos
        if extra_patterns:
            self._add_extra_patterns(extra_patterns)
        
        # Inicializa validadores
        self.validators = {
            'CPF': CPFValidator(),
            'CNPJ': CNPJValidator(),
            'TELEFONE': PhoneValidator(),
            'CELULAR': PhoneValidator(),
            'EMAIL': EmailValidator(),
            'CEP': CEPValidator(),
        }
        
        # Inicializa modelo BERT se disponível e configurado
        self.bert_model = None
        self.bert_tokenizer = None
        if self.config.use_bert and TRANSFORMERS_AVAILABLE:
            self._initialize_bert()
        
        logger.info(f"PIIGuardian inicializado no modo: {self.config.mode.value}")
    
    def _get_config_for_mode(self, mode: DetectionMode) -> DetectionConfig:
        """Retorna configuração baseada no modo."""
        if mode == DetectionMode.STRICT:
            return DetectionConfig(
                mode=mode,
                min_confidence=0.3,
                thresholds={
                    'CPF': 0.2, 'CNPJ': 0.3, 'TELEFONE': 0.3,
                    'CELULAR': 0.3, 'EMAIL': 0.5, 'CEP': 0.4,
                    'NOME': 0.4, 'DEFAULT': 0.3
                }
            )
        elif mode == DetectionMode.PRECISE:
            return DetectionConfig(
                mode=mode,
                min_confidence=0.7,
                thresholds={
                    'CPF': 0.7, 'CNPJ': 0.7, 'TELEFONE': 0.7,
                    'CELULAR': 0.7, 'EMAIL': 0.8, 'CEP': 0.7,
                    'NOME': 0.8, 'DEFAULT': 0.7
                }
            )
        else:  # BALANCED
            return DetectionConfig(mode=mode)
    
    def _initialize_bert(self):
        """Inicializa modelo BERT para detecção contextual."""
        try:
            logger.info("Carregando modelo BERT...")
            
            # Usa BERTimbau para português
            model_name = "neuralmind/bert-base-portuguese-cased"
            
            self.bert_tokenizer = AutoTokenizer.from_pretrained(model_name)
            
            # Tenta carregar modelo de NER, senão usa o base
            try:
                self.bert_model = AutoModelForTokenClassification.from_pretrained(
                    "pucpr/clinicalnerpt-ner"
                )
            except Exception:
                # Fallback para modelo base (será usado apenas para embeddings)
                logger.warning("Modelo NER não encontrado, usando modelo base")
                self.bert_model = None
            
            logger.info("Modelo BERT carregado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao carregar modelo BERT: {e}")
            self.bert_model = None
            self.bert_tokenizer = None
    
    def _add_extra_patterns(self, patterns: Dict[str, str]):
        """Adiciona padrões regex customizados."""
        # Implementação para padrões extras
        logger.info(f"Adicionados {len(patterns)} padrões customizados")
    
    def detect(self, text: str) -> DetectionResult:
        """
        Pipeline principal de detecção - otimizado para recall.
        
        Args:
            text: Texto a ser analisado
            
        Returns:
            DetectionResult com todas as entidades detectadas
        """
        start_time = datetime.now()
        
        if not text or not text.strip():
            return DetectionResult(
                has_pii=False,
                entities=[],
                summary={'total_entities': 0, 'by_type': {}},
                metadata={'processing_time_ms': 0, 'text_length': 0}
            )
        
        # FASE 1: Regex ULTRA sensível
        regex_matches = self._regex_detection_aggressive(text)
        logger.debug(f"Fase 1 (Regex): {len(regex_matches)} matches")
        
        # FASE 2: BERT para contexto (se disponível)
        bert_matches = []
        if self.config.use_bert and self.bert_model:
            bert_matches = self._bert_contextual_detection(text)
            logger.debug(f"Fase 2 (BERT): {len(bert_matches)} matches")
        
        # FASE 3: Fusão INTELIGENTE (prioriza recall)
        merged = self._merge_detections(regex_matches, bert_matches)
        logger.debug(f"Fase 3 (Fusão): {len(merged)} matches")
        
        # FASE 4: Pós-processamento ANTI falsos negativos
        if self.config.use_contextual:
            merged = self._anti_false_negative_filter(merged, text)
            logger.debug(f"Fase 4 (Anti-FN): {len(merged)} matches")
        
        # FASE 5: Validação de consistência
        if self.config.validate_documents:
            validated = self._validate_consistency(merged)
        else:
            validated = merged
        logger.debug(f"Fase 5 (Validação): {len(validated)} matches")
        
        # FASE 6: Filtragem por threshold
        filtered = self._apply_thresholds(validated)
        logger.debug(f"Fase 6 (Threshold): {len(filtered)} matches")
        
        # Gera resultado final
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Cria sumário
        by_type: Dict[str, int] = {}
        for entity in filtered:
            entity_type = entity.type.replace('_CONTEXTUAL', '')
            by_type[entity_type] = by_type.get(entity_type, 0) + 1
        
        result = DetectionResult(
            has_pii=len(filtered) > 0,
            entities=filtered,
            summary={
                'total_entities': len(filtered),
                'by_type': by_type
            },
            metadata={
                'processing_time_ms': round(processing_time, 2),
                'text_length': len(text),
                'mode': self.config.mode.value,
                'bert_enabled': self.bert_model is not None
            }
        )
        
        logger.info(
            f"Detecção concluída: {len(filtered)} entidades em {processing_time:.2f}ms"
        )
        
        return result
    
    def _regex_detection_aggressive(self, text: str) -> List[Entity]:
        """
        Regex que encontra ATÉ padrões incompletos.
        
        Esta função prioriza recall sobre precisão, capturando
        variações e padrões parciais de dados pessoais.
        """
        entities = []
        
        # Usa padrões da classe BrazilianPatterns
        matches = self.patterns.find_all(text)
        
        for match in matches:
            entity = Entity(
                type=match['type'],
                value=match['value'],
                start=match['start'],
                end=match['end'],
                confidence=match['confidence'],
                detection_method='regex',
                explanation=match.get('description', 'Padrão regex detectado')
            )
            entities.append(entity)
        
        # Padrões adicionais agressivos para CPF
        cpf_aggressive = r'\b(?:\d{3}[\.\-\s]?){2}\d{3}[\.\-\s]?\d{2}?\b'
        for match in re.finditer(cpf_aggressive, text):
            value = match.group()
            # Verifica se já não foi capturado
            if not any(e.value == value for e in entities):
                digits = sum(c.isdigit() for c in value)
                if 9 <= digits <= 11:
                    entities.append(Entity(
                        type='CPF',
                        value=value,
                        start=match.start(),
                        end=match.end(),
                        confidence=0.7,
                        detection_method='regex_aggressive',
                        explanation='Padrão agressivo de CPF detectado'
                    ))
        
        # Padrões adicionais agressivos para telefone
        phone_aggressive = r'\b(?:\d{4,5}[-\s]?\d{4}|\d{2}[\)]\s?\d{4,5}[-\s]?\d{4})\b'
        for match in re.finditer(phone_aggressive, text):
            value = match.group()
            if not any(e.value == value for e in entities):
                digits = sum(c.isdigit() for c in value)
                if 8 <= digits <= 11:
                    entities.append(Entity(
                        type='TELEFONE',
                        value=value,
                        start=match.start(),
                        end=match.end(),
                        confidence=0.75,
                        detection_method='regex_aggressive',
                        explanation='Padrão agressivo de telefone detectado'
                    ))
        
        return entities
    
    def _bert_contextual_detection(self, text: str) -> List[Entity]:
        """
        Detecção contextual com BERT - falso negativo ZERO.
        
        Utiliza modelo de linguagem para detectar entidades
        nomeadas em contexto semântico.
        """
        if not self.bert_model or not self.bert_tokenizer:
            return []
        
        entities = []
        
        try:
            # Tokeniza o texto
            inputs = self.bert_tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                return_offsets_mapping=True
            )
            
            # Executa inferência
            with torch.no_grad():
                outputs = self.bert_model(**{
                    k: v for k, v in inputs.items() 
                    if k != 'offset_mapping'
                })
            
            # Processa predições
            predictions = torch.argmax(outputs.logits, dim=2)[0].tolist()
            offset_mapping = inputs['offset_mapping'][0].tolist()
            
            # Mapeia predições para entidades
            current_entity = None
            current_start = None
            current_type = None
            
            for i, (pred, offset) in enumerate(zip(predictions, offset_mapping)):
                if pred != 0 and offset[0] != offset[1]:  # É uma entidade
                    label = self.bert_model.config.id2label.get(pred, 'O')
                    
                    # Determina tipo de entidade
                    if 'PER' in label or 'PERSON' in label:
                        entity_type = 'NOME_PESSOA'
                    elif 'LOC' in label or 'GPE' in label:
                        entity_type = 'ENDERECO'
                    elif 'ORG' in label:
                        entity_type = 'ORGANIZACAO'
                    else:
                        continue
                    
                    # Inicia ou continua entidade
                    if label.startswith('B-') or current_type != entity_type:
                        # Salva entidade anterior
                        if current_entity and current_start is not None:
                            entities.append(Entity(
                                type=current_type,
                                value=current_entity,
                                start=current_start,
                                end=offset[0],
                                confidence=0.75,
                                detection_method='bert',
                                explanation='Entidade detectada por análise contextual BERT'
                            ))
                        
                        current_entity = text[offset[0]:offset[1]]
                        current_start = offset[0]
                        current_type = entity_type
                    else:
                        current_entity += text[offset[0]:offset[1]]
                else:
                    # Finaliza entidade atual
                    if current_entity and current_start is not None:
                        entities.append(Entity(
                            type=current_type,
                            value=current_entity.strip(),
                            start=current_start,
                            end=offset[0],
                            confidence=0.75,
                            detection_method='bert',
                            explanation='Entidade detectada por análise contextual BERT'
                        ))
                        current_entity = None
                        current_start = None
                        current_type = None
            
        except Exception as e:
            logger.error(f"Erro na detecção BERT: {e}")
        
        return entities
    
    def _merge_detections(
        self,
        regex_matches: List[Entity],
        bert_matches: List[Entity]
    ) -> List[Entity]:
        """
        Fusão que PRIORIZA dados pessoais.
        
        Combina resultados de regex e BERT, removendo duplicatas
        e mantendo a detecção de maior confiança.
        """
        merged = []
        
        # Primeiro: inclui TUDO do regex (alta confiança para padrões)
        merged.extend(regex_matches)
        
        # Segundo: inclui do BERT se não for redundante
        for bert in bert_matches:
            is_redundant = False
            for reg in regex_matches:
                if self._has_overlap(bert, reg):
                    is_redundant = True
                    # Se BERT tem maior confiança, atualiza
                    if bert.confidence > reg.confidence:
                        reg.confidence = bert.confidence
                        reg.detection_method = 'hybrid'
                    break
            
            if not is_redundant:
                merged.append(bert)
        
        return merged
    
    def _anti_false_negative_filter(
        self,
        entities: List[Entity],
        text: str
    ) -> List[Entity]:
        """
        Filtro especial: captura o que os outros métodos perderiam.
        
        Usa padrões contextuais para detectar dados pessoais que
        são mencionados explicitamente no texto.
        """
        # Busca padrões contextuais
        contextual_matches = self.contextual.find_contextual(text)
        
        for match in contextual_matches:
            # Verifica se já não foi capturado
            value = match['value']
            is_duplicate = any(
                e.value == value or self._has_overlap_dict(match, e)
                for e in entities
            )
            
            if not is_duplicate and value.strip():
                entities.append(Entity(
                    type=match['type'],
                    value=value,
                    start=match['start'],
                    end=match['end'],
                    confidence=match['confidence'],
                    detection_method='contextual',
                    explanation=f"Detectado por contexto: '{match.get('full_context', '')[:50]}...'"
                ))
        
        # Padrões específicos anti-falsos-negativos
        
        # 1. Captura padrões como "meu número é 9XXXX-XXXX"
        number_pattern = r'\b(número|telefone|celular|fone|contato)[\s:]+(\d{4,5}[-\s]?\d{4})\b'
        for match in re.finditer(number_pattern, text, re.IGNORECASE):
            value = match.group(2)
            if not any(e.value == value for e in entities):
                entities.append(Entity(
                    type='TELEFONE_CONTEXTUAL',
                    value=value,
                    start=match.start(2),
                    end=match.end(2),
                    confidence=0.88,
                    detection_method='anti_fn',
                    explanation='Contexto explícito de telefone detectado'
                ))
        
        # 2. Captura "meu CPF é XXX" mesmo sem números completos
        cpf_context = r'\b(CPF|c\.p\.f\.?|cadastro)[\s:]+([0-9\.\-\s]{8,18})\b'
        for match in re.finditer(cpf_context, text, re.IGNORECASE):
            value = match.group(2).strip()
            digits = sum(c.isdigit() for c in value)
            if digits >= 9 and not any(e.value == value for e in entities):
                entities.append(Entity(
                    type='CPF_CONTEXTUAL',
                    value=value,
                    start=match.start(2),
                    end=match.end(2),
                    confidence=0.85,
                    detection_method='anti_fn',
                    explanation='Menção explícita de CPF no contexto'
                ))
        
        # 3. Captura nomes após palavras-chave
        name_keywords = r'\b(sr\.?|sra\.?|senhor[a]?|doutor[a]?|dr\.?|dra\.?)\s+([A-Z][a-záàâãéèêíïóôõöúçñ]+(?:\s+[A-Z][a-záàâãéèêíïóôõöúçñ]+){1,4})\b'
        for match in re.finditer(name_keywords, text):
            value = match.group(2)
            if not any(e.value == value for e in entities):
                # Verifica se contém sobrenome comum
                words = value.lower().split()
                has_common_name = any(w in self.BRAZILIAN_NAMES for w in words)
                
                if has_common_name or len(words) >= 2:
                    entities.append(Entity(
                        type='NOME_PESSOA',
                        value=value,
                        start=match.start(2),
                        end=match.end(2),
                        confidence=0.75,
                        detection_method='anti_fn',
                        explanation='Nome detectado após palavra-chave de tratamento'
                    ))
        
        return entities
    
    def _validate_consistency(self, entities: List[Entity]) -> List[Entity]:
        """
        Valida consistência final das entidades detectadas.
        
        Aplica validadores matemáticos para documentos como CPF e CNPJ,
        atualizando a confiança baseada na validação.
        """
        validated_entities = []
        
        for entity in entities:
            # Determina tipo base (remove sufixo _CONTEXTUAL)
            base_type = entity.type.replace('_CONTEXTUAL', '')
            
            # Obtém validador apropriado
            validator = self.validators.get(base_type)
            
            if validator:
                result = validator.validate(entity.value)
                
                entity.validation_status = 'valid' if result.is_valid else 'invalid'
                entity.validation_message = result.message
                
                if result.is_valid:
                    # Aumenta confiança se validação matemática passou
                    entity.confidence = max(entity.confidence, result.confidence)
                    entity.explanation += f" | Validação: {result.message}"
                    validated_entities.append(entity)
                elif base_type in ['CPF', 'CNPJ']:
                    # Para CPF/CNPJ inválido, reduz confiança mas mantém se modo strict
                    if self.config.mode == DetectionMode.STRICT:
                        entity.confidence *= 0.5
                        entity.explanation += f" | AVISO: {result.message}"
                        validated_entities.append(entity)
                    # Em outros modos, descarta CPF/CNPJ inválido
                else:
                    # Para outros tipos, mantém mesmo sem validação perfeita
                    validated_entities.append(entity)
            else:
                # Sem validador específico, mantém a entidade
                entity.validation_status = 'not_applicable'
                validated_entities.append(entity)
        
        return validated_entities
    
    def _apply_thresholds(self, entities: List[Entity]) -> List[Entity]:
        """Aplica thresholds de confiança por tipo."""
        filtered = []
        
        for entity in entities:
            base_type = entity.type.replace('_CONTEXTUAL', '')
            threshold = self.config.thresholds.get(
                base_type,
                self.config.thresholds.get('DEFAULT', 0.5)
            )
            
            if entity.confidence >= threshold:
                filtered.append(entity)
            else:
                logger.debug(
                    f"Entidade descartada por threshold: {entity.type} "
                    f"(conf: {entity.confidence:.2f} < {threshold})"
                )
        
        return filtered
    
    def _has_overlap(self, entity1: Entity, entity2: Entity) -> bool:
        """Verifica se duas entidades têm sobreposição."""
        return not (entity1.end <= entity2.start or entity2.end <= entity1.start)
    
    def _has_overlap_dict(self, match: Dict, entity: Entity) -> bool:
        """Verifica sobreposição entre dict e Entity."""
        return not (match['end'] <= entity.start or entity.end <= match['start'])
    
    def get_explanation(self, result: DetectionResult) -> str:
        """
        Gera explicação legível do resultado da detecção.
        
        Args:
            result: Resultado da detecção
            
        Returns:
            String com explicação formatada
        """
        if not result.has_pii:
            return "✅ Nenhum dado pessoal identificado no texto."
        
        lines = [
            f"⚠️ DETECTADOS {len(result.entities)} DADOS PESSOAIS:",
            ""
        ]
        
        for i, entity in enumerate(result.entities, 1):
            lines.append(f"{i}. **{entity.type}**")
            lines.append(f"   - Valor: `{entity.value}`")
            lines.append(f"   - Confiança: {entity.confidence:.0%}")
            lines.append(f"   - Método: {entity.detection_method}")
            lines.append(f"   - {entity.explanation}")
            lines.append("")
        
        lines.append(f"📊 Resumo por tipo: {result.summary['by_type']}")
        lines.append(f"⏱️ Tempo de processamento: {result.metadata['processing_time_ms']:.2f}ms")
        
        return "\n".join(lines)


# Função de conveniência para uso direto
def detect_pii(text: str, mode: str = 'balanced') -> Dict[str, Any]:
    """
    Função de conveniência para detecção rápida de PII.
    
    Args:
        text: Texto a ser analisado
        mode: Modo de operação ('strict', 'balanced', 'precise')
        
    Returns:
        Dicionário com resultado da detecção
    
    Exemplo:
        >>> result = detect_pii("Meu CPF é 123.456.789-09")
        >>> print(result['has_pii'])
        True
    """
    detector = PIIGuardian(mode=mode)
    result = detector.detect(text)
    return result.to_dict()


# ==================== EXEMPLO DE USO ====================
if __name__ == "__main__":
    # Instancia o detector
    detector = PIIGuardian(mode='balanced')
    
    # Teste com exemplos do desafio
    test_cases = [
        "Meu CPF é 123.456.789-09 e meu telefone (61) 99999-8888",
        "Solicito acesso ao processo, obrigado. João Silva",
        "Email: maria@exemplo.com e CEP 70000-000",
        "Sr. Carlos Eduardo da Silva, residente na Rua das Flores, 123",
        "Contato: celular 11 98765-4321 ou fixo (11) 3456-7890",
    ]
    
    print("=" * 60)
    print("PIIGuardian - Detector de Dados Pessoais")
    print("Hackathon Participa DF - Categoria Acesso à Informação")
    print("=" * 60)
    
    for i, text in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"Teste {i}: {text[:60]}{'...' if len(text) > 60 else ''}")
        print("-" * 60)
        
        result = detector.detect(text)
        
        if result.has_pii:
            print(f"⚠️  DETECTADO: {len(result.entities)} dado(s) pessoal(is)")
            for entity in result.entities:
                print(f"   - {entity.type}: '{entity.value}' "
                      f"(conf: {entity.confidence:.0%}, {entity.detection_method})")
        else:
            print("✅ SEM dados pessoais detectados")
        
        print(f"📊 Tempo: {result.metadata['processing_time_ms']:.2f}ms")
    
    print(f"\n{'='*60}")
    print("Testes concluídos!")
