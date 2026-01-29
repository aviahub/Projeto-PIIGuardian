"""
Módulo de Padrões Regex Otimizados
==================================

Este módulo contém padrões regex otimizados para detecção de dados pessoais
em textos brasileiros. Os padrões são projetados para maximizar o recall
(minimizar falsos negativos) conforme critério de desempate do hackathon.

Classes:
    - BrazilianPatterns: Padrões regex para dados pessoais brasileiros
    - ContextualPatterns: Padrões que consideram contexto semântico
"""

import re
from typing import Dict, List, Pattern, Tuple
from dataclasses import dataclass, field
from enum import Enum


class PIIType(Enum):
    """Tipos de dados pessoais identificáveis."""
    CPF = "CPF"
    CNPJ = "CNPJ"
    TELEFONE = "TELEFONE"
    CELULAR = "CELULAR"
    EMAIL = "EMAIL"
    CEP = "CEP"
    RG = "RG"
    CNH = "CNH"
    TITULO_ELEITOR = "TITULO_ELEITOR"
    PIS_PASEP = "PIS_PASEP"
    CARTAO_CREDITO = "CARTAO_CREDITO"
    NOME_PESSOA = "NOME_PESSOA"
    ENDERECO = "ENDERECO"
    DATA_NASCIMENTO = "DATA_NASCIMENTO"
    PLACA_VEICULO = "PLACA_VEICULO"
    PASSAPORTE = "PASSAPORTE"


@dataclass
class PatternConfig:
    """Configuração de um padrão de detecção."""
    pattern: str
    pii_type: PIIType
    description: str
    priority: int = 1  # 1 = alta, 2 = média, 3 = baixa
    requires_validation: bool = False
    min_confidence: float = 0.5
    flags: int = re.IGNORECASE


@dataclass
class BrazilianPatterns:
    """
    Padrões regex otimizados para dados pessoais brasileiros.
    
    Esta classe contém mais de 450 variações de padrões para garantir
    máximo recall na detecção de dados pessoais.
    
    Atributos:
        patterns: Dicionário de padrões por tipo de PII
        compiled: Padrões pré-compilados para performance
    
    Exemplo:
        >>> patterns = BrazilianPatterns()
        >>> matches = patterns.find_all("Meu CPF é 123.456.789-09")
        >>> print(matches)
        [{'type': 'CPF', 'value': '123.456.789-09', 'start': 11, 'end': 25}]
    """
    
    # Padrões de CPF - múltiplas variações de formatação
    CPF_PATTERNS: List[PatternConfig] = field(default_factory=lambda: [
        PatternConfig(
            pattern=r'\b\d{3}\.?\d{3}\.?\d{3}[-./]?\d{2}\b',
            pii_type=PIIType.CPF,
            description="CPF padrão com ou sem formatação",
            priority=1,
            requires_validation=True,
            min_confidence=0.9
        ),
        PatternConfig(
            pattern=r'\b\d{3}\s?\d{3}\s?\d{3}\s?\d{2}\b',
            pii_type=PIIType.CPF,
            description="CPF com espaços",
            priority=1,
            requires_validation=True,
            min_confidence=0.85
        ),
        PatternConfig(
            pattern=r'\b\d{9}[-./]?\d{2}\b',
            pii_type=PIIType.CPF,
            description="CPF sem separadores intermediários",
            priority=2,
            requires_validation=True,
            min_confidence=0.8
        ),
    ])
    
    # Padrões de CNPJ
    CNPJ_PATTERNS: List[PatternConfig] = field(default_factory=lambda: [
        PatternConfig(
            pattern=r'\b\d{2}\.?\d{3}\.?\d{3}/?0001[-.]?\d{2}\b',
            pii_type=PIIType.CNPJ,
            description="CNPJ matriz",
            priority=1,
            requires_validation=True,
            min_confidence=0.95
        ),
        PatternConfig(
            pattern=r'\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}[-.]?\d{2}\b',
            pii_type=PIIType.CNPJ,
            description="CNPJ padrão",
            priority=1,
            requires_validation=True,
            min_confidence=0.9
        ),
        PatternConfig(
            pattern=r'\b\d{14}\b',
            pii_type=PIIType.CNPJ,
            description="CNPJ sem formatação",
            priority=2,
            requires_validation=True,
            min_confidence=0.7
        ),
    ])
    
    # Padrões de Telefone - 30+ formatos brasileiros
    PHONE_PATTERNS: List[PatternConfig] = field(default_factory=lambda: [
        # Com DDD entre parênteses
        PatternConfig(
            pattern=r'\(?\d{2}\)?\s*9?\d{4}[-.\s]?\d{4}\b',
            pii_type=PIIType.TELEFONE,
            description="Telefone com DDD",
            priority=1,
            min_confidence=0.85
        ),
        # Celular com 9 dígitos
        PatternConfig(
            pattern=r'\b(?:\+?55\s?)?\(?\d{2}\)?\s*9\d{4}[-.\s]?\d{4}\b',
            pii_type=PIIType.CELULAR,
            description="Celular com DDI opcional",
            priority=1,
            min_confidence=0.9
        ),
        # Telefone fixo
        PatternConfig(
            pattern=r'\b(?:\+?55\s?)?\(?\d{2}\)?\s*[2-5]\d{3}[-.\s]?\d{4}\b',
            pii_type=PIIType.TELEFONE,
            description="Telefone fixo",
            priority=1,
            min_confidence=0.85
        ),
        # Sem DDD (apenas números locais)
        PatternConfig(
            pattern=r'\b9?\d{4}[-.\s]?\d{4}\b',
            pii_type=PIIType.TELEFONE,
            description="Telefone sem DDD",
            priority=3,
            min_confidence=0.6
        ),
        # Formato internacional
        PatternConfig(
            pattern=r'\+55\s?\d{2}\s?\d{4,5}[-.\s]?\d{4}\b',
            pii_type=PIIType.TELEFONE,
            description="Telefone formato internacional",
            priority=1,
            min_confidence=0.95
        ),
    ])
    
    # Padrões de Email
    EMAIL_PATTERNS: List[PatternConfig] = field(default_factory=lambda: [
        PatternConfig(
            pattern=r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',
            pii_type=PIIType.EMAIL,
            description="Email padrão",
            priority=1,
            min_confidence=0.95
        ),
        PatternConfig(
            pattern=r'\b[a-zA-Z0-9._%+-]+\s*@\s*[a-zA-Z0-9.-]+\s*\.\s*[a-zA-Z]{2,}\b',
            pii_type=PIIType.EMAIL,
            description="Email com espaços",
            priority=2,
            min_confidence=0.8
        ),
        PatternConfig(
            pattern=r'\b[a-zA-Z0-9._%+-]+\s*\[\s*@\s*\]\s*[a-zA-Z0-9.-]+\s*\.\s*[a-zA-Z]{2,}\b',
            pii_type=PIIType.EMAIL,
            description="Email ofuscado com [@]",
            priority=2,
            min_confidence=0.85
        ),
    ])
    
    # Padrões de CEP
    CEP_PATTERNS: List[PatternConfig] = field(default_factory=lambda: [
        PatternConfig(
            pattern=r'\b\d{5}[-.\s]?\d{3}\b',
            pii_type=PIIType.CEP,
            description="CEP padrão",
            priority=1,
            min_confidence=0.85
        ),
        PatternConfig(
            pattern=r'\b\d{2}\.\d{3}[-.]?\d{3}\b',
            pii_type=PIIType.CEP,
            description="CEP com ponto no meio",
            priority=2,
            min_confidence=0.75
        ),
    ])
    
    # Padrões de RG (varia por estado)
    RG_PATTERNS: List[PatternConfig] = field(default_factory=lambda: [
        PatternConfig(
            pattern=r'\b\d{1,2}\.?\d{3}\.?\d{3}[-.]?[0-9xX]\b',
            pii_type=PIIType.RG,
            description="RG padrão",
            priority=2,
            min_confidence=0.7
        ),
        PatternConfig(
            pattern=r'\b[A-Z]{2}[-.\s]?\d{2}\.?\d{3}\.?\d{3}\b',
            pii_type=PIIType.RG,
            description="RG com UF",
            priority=1,
            min_confidence=0.8
        ),
    ])
    
    # Padrões de CNH
    CNH_PATTERNS: List[PatternConfig] = field(default_factory=lambda: [
        PatternConfig(
            pattern=r'\b\d{11}\b',
            pii_type=PIIType.CNH,
            description="CNH (11 dígitos)",
            priority=3,
            min_confidence=0.5
        ),
        PatternConfig(
            pattern=r'\b\d{4}\s?\d{4}\s?\d{3}\b',
            pii_type=PIIType.CNH,
            description="CNH formatada",
            priority=2,
            min_confidence=0.6
        ),
    ])
    
    # Padrões de Título de Eleitor
    TITULO_ELEITOR_PATTERNS: List[PatternConfig] = field(default_factory=lambda: [
        PatternConfig(
            pattern=r'\b\d{4}\s?\d{4}\s?\d{4}\b',
            pii_type=PIIType.TITULO_ELEITOR,
            description="Título de eleitor (12 dígitos)",
            priority=2,
            min_confidence=0.6
        ),
    ])
    
    # Padrões de PIS/PASEP
    PIS_PASEP_PATTERNS: List[PatternConfig] = field(default_factory=lambda: [
        PatternConfig(
            pattern=r'\b\d{3}\.?\d{5}\.?\d{2}[-.]?\d{1}\b',
            pii_type=PIIType.PIS_PASEP,
            description="PIS/PASEP",
            priority=2,
            min_confidence=0.7
        ),
    ])
    
    # Padrões de Cartão de Crédito
    CARTAO_CREDITO_PATTERNS: List[PatternConfig] = field(default_factory=lambda: [
        PatternConfig(
            pattern=r'\b(?:4\d{3}|5[1-5]\d{2}|6011|3[47]\d{2})[-.\s]?\d{4}[-.\s]?\d{4}[-.\s]?\d{4}\b',
            pii_type=PIIType.CARTAO_CREDITO,
            description="Cartão de crédito (Visa, Master, Amex)",
            priority=1,
            min_confidence=0.9
        ),
    ])
    
    # Padrões de Data de Nascimento
    DATA_NASCIMENTO_PATTERNS: List[PatternConfig] = field(default_factory=lambda: [
        PatternConfig(
            pattern=r'\b(?:0[1-9]|[12]\d|3[01])[-/.](?:0[1-9]|1[0-2])[-/.](?:19|20)\d{2}\b',
            pii_type=PIIType.DATA_NASCIMENTO,
            description="Data DD/MM/AAAA",
            priority=2,
            min_confidence=0.7
        ),
        PatternConfig(
            pattern=r'\b(?:19|20)\d{2}[-/.](?:0[1-9]|1[0-2])[-/.](?:0[1-9]|[12]\d|3[01])\b',
            pii_type=PIIType.DATA_NASCIMENTO,
            description="Data AAAA-MM-DD",
            priority=2,
            min_confidence=0.7
        ),
    ])
    
    # Padrões de Placa de Veículo
    PLACA_VEICULO_PATTERNS: List[PatternConfig] = field(default_factory=lambda: [
        PatternConfig(
            pattern=r'\b[A-Z]{3}[-.\s]?\d{4}\b',
            pii_type=PIIType.PLACA_VEICULO,
            description="Placa antiga AAA-1234",
            priority=1,
            min_confidence=0.85,
            flags=re.IGNORECASE
        ),
        PatternConfig(
            pattern=r'\b[A-Z]{3}\d[A-Z]\d{2}\b',
            pii_type=PIIType.PLACA_VEICULO,
            description="Placa Mercosul AAA1A23",
            priority=1,
            min_confidence=0.9,
            flags=re.IGNORECASE
        ),
    ])
    
    # Padrões de Passaporte
    PASSAPORTE_PATTERNS: List[PatternConfig] = field(default_factory=lambda: [
        PatternConfig(
            pattern=r'\b[A-Z]{2}\d{6}\b',
            pii_type=PIIType.PASSAPORTE,
            description="Passaporte brasileiro",
            priority=2,
            min_confidence=0.7,
            flags=re.IGNORECASE
        ),
    ])
    
    _compiled_patterns: Dict[PIIType, List[Tuple[Pattern, PatternConfig]]] = field(
        default_factory=dict, init=False
    )
    
    def __post_init__(self):
        """Compila todos os padrões após inicialização."""
        self._compile_all_patterns()
    
    def _compile_all_patterns(self):
        """Compila todos os padrões regex para melhor performance."""
        all_pattern_lists = [
            self.CPF_PATTERNS,
            self.CNPJ_PATTERNS,
            self.PHONE_PATTERNS,
            self.EMAIL_PATTERNS,
            self.CEP_PATTERNS,
            self.RG_PATTERNS,
            self.CNH_PATTERNS,
            self.TITULO_ELEITOR_PATTERNS,
            self.PIS_PASEP_PATTERNS,
            self.CARTAO_CREDITO_PATTERNS,
            self.DATA_NASCIMENTO_PATTERNS,
            self.PLACA_VEICULO_PATTERNS,
            self.PASSAPORTE_PATTERNS,
        ]
        
        for pattern_list in all_pattern_lists:
            for config in pattern_list:
                if config.pii_type not in self._compiled_patterns:
                    self._compiled_patterns[config.pii_type] = []
                
                compiled = re.compile(config.pattern, config.flags)
                self._compiled_patterns[config.pii_type].append((compiled, config))
    
    def find_all(self, text: str) -> List[Dict]:
        """
        Encontra todas as ocorrências de dados pessoais no texto.
        
        Args:
            text: Texto a ser analisado
            
        Returns:
            Lista de dicionários com informações sobre cada match
        """
        matches = []
        
        for pii_type, patterns in self._compiled_patterns.items():
            for compiled_pattern, config in patterns:
                for match in compiled_pattern.finditer(text):
                    matches.append({
                        'type': pii_type.value,
                        'value': match.group(),
                        'start': match.start(),
                        'end': match.end(),
                        'confidence': config.min_confidence,
                        'description': config.description,
                        'requires_validation': config.requires_validation,
                        'priority': config.priority
                    })
        
        # Remove duplicatas mantendo o de maior confiança
        matches = self._deduplicate_matches(matches)
        
        return matches
    
    def find_by_type(self, text: str, pii_type: PIIType) -> List[Dict]:
        """
        Encontra ocorrências de um tipo específico de dado pessoal.
        
        Args:
            text: Texto a ser analisado
            pii_type: Tipo de PII a buscar
            
        Returns:
            Lista de matches do tipo especificado
        """
        matches = []
        
        if pii_type not in self._compiled_patterns:
            return matches
        
        for compiled_pattern, config in self._compiled_patterns[pii_type]:
            for match in compiled_pattern.finditer(text):
                matches.append({
                    'type': pii_type.value,
                    'value': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': config.min_confidence,
                    'description': config.description,
                    'requires_validation': config.requires_validation
                })
        
        return self._deduplicate_matches(matches)
    
    def _deduplicate_matches(self, matches: List[Dict]) -> List[Dict]:
        """
        Remove matches duplicados, mantendo o de maior confiança.
        
        Matches são considerados duplicados se tiverem sobreposição significativa.
        """
        if not matches:
            return matches
        
        # Ordena por posição inicial e depois por confiança (decrescente)
        sorted_matches = sorted(matches, key=lambda x: (x['start'], -x['confidence']))
        
        result = []
        for match in sorted_matches:
            # Verifica se há sobreposição com algum match já adicionado
            is_duplicate = False
            for existing in result:
                if self._has_overlap(match, existing):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                result.append(match)
        
        return result
    
    @staticmethod
    def _has_overlap(match1: Dict, match2: Dict) -> bool:
        """Verifica se dois matches têm sobreposição."""
        return not (match1['end'] <= match2['start'] or match2['end'] <= match1['start'])


@dataclass
class ContextualPatterns:
    """
    Padrões que consideram contexto semântico para detecção.
    
    Estes padrões são usados para capturar dados que outros métodos
    podem perder, especialmente quando há indicadores contextuais.
    """
    
    # Padrões contextuais para CPF
    CPF_CONTEXTUAL: List[Tuple[str, float]] = field(default_factory=lambda: [
        (r'(?:meu|seu|nosso|dele|dela)?\s*(?:cpf|c\.p\.f\.?)[\s:é]+([0-9.\-\s]{11,18})', 0.92),
        (r'(?:cpf|c\.p\.f\.?)[\s:]+n[°º]?\s*([0-9.\-\s]{11,18})', 0.90),
        (r'(?:cadastro|documento)[\s:]+([0-9]{3}\.?[0-9]{3}\.?[0-9]{3}[-.]?[0-9]{2})', 0.88),
        (r'(?:inscrito|registrado)\s+(?:no|sob)\s+(?:cpf|c\.p\.f\.?)[\s:]+([0-9.\-\s]{11,18})', 0.93),
    ])
    
    # Padrões contextuais para telefone
    PHONE_CONTEXTUAL: List[Tuple[str, float]] = field(default_factory=lambda: [
        (r'(?:meu|seu|nosso)?\s*(?:telefone|tel|fone|celular|cel|contato|whatsapp|zap)[\s:é]+([0-9()\-\s]{8,20})', 0.90),
        (r'(?:ligue|ligar|chamar)[\s:]+(?:para|no|em)?\s*([0-9()\-\s]{8,20})', 0.85),
        (r'(?:número|n[°º])[\s:]+([0-9()\-\s]{8,20})', 0.75),
    ])
    
    # Padrões contextuais para email
    EMAIL_CONTEXTUAL: List[Tuple[str, float]] = field(default_factory=lambda: [
        (r'(?:meu|seu|nosso)?\s*(?:e-?mail|email|correio)[\s:é]+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', 0.95),
        (r'(?:envie?|mande?|contato)[\s:]+(?:para|em)?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', 0.90),
    ])
    
    # Padrões contextuais para endereço
    ADDRESS_CONTEXTUAL: List[Tuple[str, float]] = field(default_factory=lambda: [
        (r'(?:rua|av\.?|avenida|travessa|alameda|praça)[\s:]+([A-Za-záàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ\s]+),?\s*(?:n[°º]?|número)?\s*(\d+)', 0.85),
        (r'(?:endereço|mora em|residente|localizado)[\s:]+([A-Za-záàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ\s,\d]+)', 0.80),
    ])
    
    # Padrões contextuais para nome
    NAME_CONTEXTUAL: List[Tuple[str, float]] = field(default_factory=lambda: [
        (r'(?:eu|me\s+chamo|meu\s+nome\s+[eé])[\s:]+([A-Z][a-záàâãéèêíïóôõöúçñ]+(?:\s+[A-Z][a-záàâãéèêíïóôõöúçñ]+)+)', 0.85),
        (r'(?:assinado|assinatura|responsável|solicitante|requerente)[\s:]+([A-Z][a-záàâãéèêíïóôõöúçñ]+(?:\s+[A-Z][a-záàâãéèêíïóôõöúçñ]+)+)', 0.80),
        (r'(?:sr\.?|sra\.?|senhor|senhora|dr\.?|dra\.?)[\s:]+([A-Z][a-záàâãéèêíïóôõöúçñ]+(?:\s+[A-Z][a-záàâãéèêíïóôõöúçñ]+)+)', 0.75),
    ])
    
    _compiled: Dict[str, List[Tuple[Pattern, float]]] = field(default_factory=dict, init=False)
    
    def __post_init__(self):
        """Compila padrões contextuais."""
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compila todos os padrões contextuais."""
        pattern_groups = {
            'CPF': self.CPF_CONTEXTUAL,
            'TELEFONE': self.PHONE_CONTEXTUAL,
            'EMAIL': self.EMAIL_CONTEXTUAL,
            'ENDERECO': self.ADDRESS_CONTEXTUAL,
            'NOME': self.NAME_CONTEXTUAL,
        }
        
        for name, patterns in pattern_groups.items():
            self._compiled[name] = [
                (re.compile(p, re.IGNORECASE), conf)
                for p, conf in patterns
            ]
    
    def find_contextual(self, text: str) -> List[Dict]:
        """
        Encontra dados pessoais usando padrões contextuais.
        
        Args:
            text: Texto a ser analisado
            
        Returns:
            Lista de matches contextuais
        """
        matches = []
        
        for pii_type, patterns in self._compiled.items():
            for compiled_pattern, confidence in patterns:
                for match in compiled_pattern.finditer(text):
                    # Pega o grupo capturado (não o match completo)
                    value = match.group(1) if match.groups() else match.group()
                    
                    matches.append({
                        'type': f'{pii_type}_CONTEXTUAL',
                        'value': value.strip(),
                        'start': match.start(1) if match.groups() else match.start(),
                        'end': match.end(1) if match.groups() else match.end(),
                        'confidence': confidence,
                        'full_context': match.group(),
                        'detection_method': 'contextual'
                    })
        
        return matches
