"""
PIIGuardian - Detector de Dados Pessoais para o Participa DF
============================================================

Solução desenvolvida para o 1º Hackathon em Controle Social
Categoria: Acesso à Informação

Este módulo fornece ferramentas para detecção automática de dados pessoais
em textos, classificando-os conforme a LGPD (Lei Geral de Proteção de Dados).

Módulos:
    - detector: Classe principal PIIGuardian para detecção de PII
    - validators: Validadores matemáticos para CPF, CNPJ, etc.
    - patterns: Padrões regex otimizados para dados brasileiros
    - utils: Funções utilitárias

Exemplo de uso:
    >>> from src.detector import PIIGuardian
    >>> detector = PIIGuardian()
    >>> resultado = detector.detect("Meu CPF é 123.456.789-09")
    >>> print(resultado['has_pii'])
    True

Autor: Aviahub
Versão: 1.0.0
Licença: MIT
"""

__version__ = "1.0.0"
__author__ = "Aviahub"
__license__ = "MIT"

from .detector import PIIGuardian
from .validators import CPFValidator, CNPJValidator, PhoneValidator
from .patterns import BrazilianPatterns

__all__ = [
    "PIIGuardian",
    "CPFValidator",
    "CNPJValidator",
    "PhoneValidator",
    "BrazilianPatterns",
]
