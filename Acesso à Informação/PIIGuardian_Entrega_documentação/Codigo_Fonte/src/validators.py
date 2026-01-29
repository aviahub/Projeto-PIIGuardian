"""
Módulo de Validadores Matemáticos
=================================

Este módulo contém validadores matemáticos para documentos brasileiros,
garantindo que os dados detectados sejam válidos segundo as regras oficiais.

Classes:
    - CPFValidator: Validação matemática de CPF
    - CNPJValidator: Validação matemática de CNPJ
    - PhoneValidator: Validação de telefones brasileiros
    - EmailValidator: Validação de formato de email
"""

import re
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Resultado de uma validação."""
    is_valid: bool
    confidence: float
    message: str
    cleaned_value: Optional[str] = None


class CPFValidator:
    """
    Validador matemático de CPF brasileiro.
    
    O CPF (Cadastro de Pessoas Físicas) é composto por 11 dígitos,
    onde os dois últimos são dígitos verificadores calculados
    através de um algoritmo específico.
    
    Algoritmo de validação:
    1. Multiplica os 9 primeiros dígitos por pesos decrescentes (10 a 2)
    2. Soma os produtos e calcula o resto da divisão por 11
    3. Se resto < 2, primeiro dígito verificador = 0
    4. Se resto >= 2, primeiro dígito verificador = 11 - resto
    5. Repete o processo com 10 dígitos para o segundo verificador
    
    Exemplo:
        >>> validator = CPFValidator()
        >>> result = validator.validate("123.456.789-09")
        >>> print(result.is_valid)
        True
    """
    
    # CPFs conhecidamente inválidos (sequências repetidas)
    INVALID_CPFS = {
        "00000000000", "11111111111", "22222222222", "33333333333",
        "44444444444", "55555555555", "66666666666", "77777777777",
        "88888888888", "99999999999"
    }
    
    @staticmethod
    def clean(cpf: str) -> str:
        """Remove caracteres não numéricos do CPF."""
        return re.sub(r'\D', '', cpf)
    
    @staticmethod
    def format(cpf: str) -> str:
        """Formata CPF no padrão XXX.XXX.XXX-XX."""
        cleaned = CPFValidator.clean(cpf)
        if len(cleaned) == 11:
            return f"{cleaned[:3]}.{cleaned[3:6]}.{cleaned[6:9]}-{cleaned[9:]}"
        return cpf
    
    def validate(self, cpf: str) -> ValidationResult:
        """
        Valida um CPF usando o algoritmo oficial.
        
        Args:
            cpf: String contendo o CPF (com ou sem formatação)
            
        Returns:
            ValidationResult com o resultado da validação
        """
        cleaned = self.clean(cpf)
        
        # Verifica comprimento
        if len(cleaned) != 11:
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                message=f"CPF deve ter 11 dígitos, encontrado: {len(cleaned)}"
            )
        
        # Verifica se são todos dígitos
        if not cleaned.isdigit():
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                message="CPF deve conter apenas dígitos"
            )
        
        # Verifica sequências inválidas
        if cleaned in self.INVALID_CPFS:
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                message="CPF com sequência inválida (dígitos repetidos)"
            )
        
        # Calcula primeiro dígito verificador
        digits = [int(d) for d in cleaned]
        
        sum_first = sum(d * w for d, w in zip(digits[:9], range(10, 1, -1)))
        expected_first = (sum_first * 10 % 11) % 10
        
        if expected_first != digits[9]:
            return ValidationResult(
                is_valid=False,
                confidence=0.3,
                message=f"Primeiro dígito verificador inválido: esperado {expected_first}, encontrado {digits[9]}",
                cleaned_value=cleaned
            )
        
        # Calcula segundo dígito verificador
        sum_second = sum(d * w for d, w in zip(digits[:10], range(11, 1, -1)))
        expected_second = (sum_second * 10 % 11) % 10
        
        if expected_second != digits[10]:
            return ValidationResult(
                is_valid=False,
                confidence=0.3,
                message=f"Segundo dígito verificador inválido: esperado {expected_second}, encontrado {digits[10]}",
                cleaned_value=cleaned
            )
        
        return ValidationResult(
            is_valid=True,
            confidence=0.98,
            message="CPF válido - dígitos verificadores conferem",
            cleaned_value=cleaned
        )
    
    def calculate_check_digits(self, cpf_base: str) -> Tuple[int, int]:
        """
        Calcula os dígitos verificadores para uma base de CPF.
        
        Args:
            cpf_base: Os 9 primeiros dígitos do CPF
            
        Returns:
            Tupla com os dois dígitos verificadores
        """
        cleaned = self.clean(cpf_base)[:9]
        if len(cleaned) != 9:
            raise ValueError("Base do CPF deve ter 9 dígitos")
        
        digits = [int(d) for d in cleaned]
        
        # Primeiro dígito
        sum_first = sum(d * w for d, w in zip(digits, range(10, 1, -1)))
        first_digit = (sum_first * 10 % 11) % 10
        
        # Segundo dígito
        digits.append(first_digit)
        sum_second = sum(d * w for d, w in zip(digits, range(11, 1, -1)))
        second_digit = (sum_second * 10 % 11) % 10
        
        return first_digit, second_digit


class CNPJValidator:
    """
    Validador matemático de CNPJ brasileiro.
    
    O CNPJ (Cadastro Nacional de Pessoa Jurídica) é composto por 14 dígitos,
    onde os dois últimos são dígitos verificadores.
    
    Formato: XX.XXX.XXX/XXXX-XX
    """
    
    # Pesos para cálculo dos dígitos verificadores
    WEIGHTS_FIRST = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    WEIGHTS_SECOND = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    
    # CNPJs conhecidamente inválidos
    INVALID_CNPJS = {
        "00000000000000", "11111111111111", "22222222222222",
        "33333333333333", "44444444444444", "55555555555555",
        "66666666666666", "77777777777777", "88888888888888",
        "99999999999999"
    }
    
    @staticmethod
    def clean(cnpj: str) -> str:
        """Remove caracteres não numéricos do CNPJ."""
        return re.sub(r'\D', '', cnpj)
    
    @staticmethod
    def format(cnpj: str) -> str:
        """Formata CNPJ no padrão XX.XXX.XXX/XXXX-XX."""
        cleaned = CNPJValidator.clean(cnpj)
        if len(cleaned) == 14:
            return f"{cleaned[:2]}.{cleaned[2:5]}.{cleaned[5:8]}/{cleaned[8:12]}-{cleaned[12:]}"
        return cnpj
    
    def validate(self, cnpj: str) -> ValidationResult:
        """
        Valida um CNPJ usando o algoritmo oficial.
        
        Args:
            cnpj: String contendo o CNPJ (com ou sem formatação)
            
        Returns:
            ValidationResult com o resultado da validação
        """
        cleaned = self.clean(cnpj)
        
        # Verifica comprimento
        if len(cleaned) != 14:
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                message=f"CNPJ deve ter 14 dígitos, encontrado: {len(cleaned)}"
            )
        
        # Verifica se são todos dígitos
        if not cleaned.isdigit():
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                message="CNPJ deve conter apenas dígitos"
            )
        
        # Verifica sequências inválidas
        if cleaned in self.INVALID_CNPJS:
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                message="CNPJ com sequência inválida (dígitos repetidos)"
            )
        
        digits = [int(d) for d in cleaned]
        
        # Calcula primeiro dígito verificador
        sum_first = sum(d * w for d, w in zip(digits[:12], self.WEIGHTS_FIRST))
        remainder = sum_first % 11
        expected_first = 0 if remainder < 2 else 11 - remainder
        
        if expected_first != digits[12]:
            return ValidationResult(
                is_valid=False,
                confidence=0.3,
                message=f"Primeiro dígito verificador inválido",
                cleaned_value=cleaned
            )
        
        # Calcula segundo dígito verificador
        sum_second = sum(d * w for d, w in zip(digits[:13], self.WEIGHTS_SECOND))
        remainder = sum_second % 11
        expected_second = 0 if remainder < 2 else 11 - remainder
        
        if expected_second != digits[13]:
            return ValidationResult(
                is_valid=False,
                confidence=0.3,
                message=f"Segundo dígito verificador inválido",
                cleaned_value=cleaned
            )
        
        return ValidationResult(
            is_valid=True,
            confidence=0.98,
            message="CNPJ válido - dígitos verificadores conferem",
            cleaned_value=cleaned
        )


class PhoneValidator:
    """
    Validador de telefones brasileiros.
    
    Formatos aceitos:
    - Fixo: (XX) XXXX-XXXX ou XX XXXX-XXXX
    - Celular: (XX) 9XXXX-XXXX ou XX 9XXXX-XXXX
    - Com DDI: +55 (XX) 9XXXX-XXXX
    
    DDDs válidos do Brasil: 11-99 (exceto algumas faixas reservadas)
    """
    
    # DDDs válidos no Brasil
    VALID_DDDS = {
        # São Paulo
        11, 12, 13, 14, 15, 16, 17, 18, 19,
        # Rio de Janeiro / Espírito Santo
        21, 22, 24, 27, 28,
        # Minas Gerais
        31, 32, 33, 34, 35, 37, 38,
        # Paraná / Santa Catarina
        41, 42, 43, 44, 45, 46, 47, 48, 49,
        # Rio Grande do Sul
        51, 53, 54, 55,
        # Centro-Oeste
        61, 62, 63, 64, 65, 66, 67, 68, 69,
        # Nordeste
        71, 73, 74, 75, 77, 79,
        81, 82, 83, 84, 85, 86, 87, 88, 89,
        # Norte
        91, 92, 93, 94, 95, 96, 97, 98, 99
    }
    
    @staticmethod
    def clean(phone: str) -> str:
        """Remove caracteres não numéricos do telefone."""
        return re.sub(r'\D', '', phone)
    
    def validate(self, phone: str) -> ValidationResult:
        """
        Valida um número de telefone brasileiro.
        
        Args:
            phone: String contendo o telefone (com ou sem formatação)
            
        Returns:
            ValidationResult com o resultado da validação
        """
        cleaned = self.clean(phone)
        
        # Remove DDI se presente
        if cleaned.startswith('55') and len(cleaned) > 11:
            cleaned = cleaned[2:]
        
        # Verifica comprimento (10 para fixo, 11 para celular)
        if len(cleaned) not in [10, 11]:
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                message=f"Telefone deve ter 10 ou 11 dígitos, encontrado: {len(cleaned)}"
            )
        
        # Extrai DDD
        ddd = int(cleaned[:2])
        
        # Valida DDD
        if ddd not in self.VALID_DDDS:
            return ValidationResult(
                is_valid=False,
                confidence=0.4,
                message=f"DDD {ddd} não é válido no Brasil",
                cleaned_value=cleaned
            )
        
        # Valida celular (deve começar com 9)
        if len(cleaned) == 11:
            if cleaned[2] != '9':
                return ValidationResult(
                    is_valid=False,
                    confidence=0.5,
                    message="Celular com 11 dígitos deve ter terceiro dígito = 9",
                    cleaned_value=cleaned
                )
        
        # Verifica se não são todos iguais
        if len(set(cleaned[2:])) == 1:
            return ValidationResult(
                is_valid=False,
                confidence=0.2,
                message="Telefone com dígitos repetidos",
                cleaned_value=cleaned
            )
        
        phone_type = "celular" if len(cleaned) == 11 else "fixo"
        
        return ValidationResult(
            is_valid=True,
            confidence=0.90,
            message=f"Telefone {phone_type} válido - DDD {ddd}",
            cleaned_value=cleaned
        )


class EmailValidator:
    """
    Validador de endereços de email.
    
    Valida formato e estrutura básica do email, verificando:
    - Presença de @ e domínio
    - TLDs válidos
    - Caracteres permitidos
    """
    
    # TLDs comuns válidos
    COMMON_TLDS = {
        'com', 'com.br', 'org', 'org.br', 'net', 'net.br', 'gov', 'gov.br',
        'edu', 'edu.br', 'mil', 'mil.br', 'info', 'biz', 'io', 'co',
        'br', 'pt', 'us', 'uk', 'de', 'fr', 'es', 'it', 'jp', 'cn'
    }
    
    # Regex para validação básica de email
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    def validate(self, email: str) -> ValidationResult:
        """
        Valida um endereço de email.
        
        Args:
            email: String contendo o email
            
        Returns:
            ValidationResult com o resultado da validação
        """
        email = email.strip().lower()
        
        # Verifica formato básico
        if not self.EMAIL_PATTERN.match(email):
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                message="Formato de email inválido"
            )
        
        # Separa local e domínio
        try:
            local, domain = email.rsplit('@', 1)
        except ValueError:
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                message="Email deve conter exatamente um @"
            )
        
        # Verifica comprimento do local
        if len(local) > 64:
            return ValidationResult(
                is_valid=False,
                confidence=0.3,
                message="Parte local do email muito longa (máximo 64 caracteres)"
            )
        
        # Verifica comprimento do domínio
        if len(domain) > 255:
            return ValidationResult(
                is_valid=False,
                confidence=0.3,
                message="Domínio do email muito longo (máximo 255 caracteres)"
            )
        
        # Verifica TLD
        tld = domain.split('.')[-1]
        if len(tld) < 2:
            return ValidationResult(
                is_valid=False,
                confidence=0.3,
                message="TLD do email inválido"
            )
        
        # Verifica domínios brasileiros comuns
        confidence = 0.95 if any(domain.endswith(f'.{t}') for t in self.COMMON_TLDS) else 0.85
        
        return ValidationResult(
            is_valid=True,
            confidence=confidence,
            message="Email com formato válido",
            cleaned_value=email
        )


class CEPValidator:
    """
    Validador de CEP brasileiro.
    
    O CEP (Código de Endereçamento Postal) tem 8 dígitos no formato XXXXX-XXX.
    Os primeiros dígitos indicam a região:
    - 0: São Paulo capital
    - 1: São Paulo interior
    - 2: Rio de Janeiro e Espírito Santo
    - 3: Minas Gerais
    - 4: Bahia e Sergipe
    - 5: Pernambuco, Alagoas, Paraíba, Rio Grande do Norte
    - 6: Ceará, Piauí, Maranhão, Pará, Amazonas, Acre, Amapá, Roraima
    - 7: Goiás, Tocantins, Mato Grosso, Mato Grosso do Sul, Distrito Federal
    - 8: Paraná e Santa Catarina
    - 9: Rio Grande do Sul
    """
    
    @staticmethod
    def clean(cep: str) -> str:
        """Remove caracteres não numéricos do CEP."""
        return re.sub(r'\D', '', cep)
    
    @staticmethod
    def format(cep: str) -> str:
        """Formata CEP no padrão XXXXX-XXX."""
        cleaned = CEPValidator.clean(cep)
        if len(cleaned) == 8:
            return f"{cleaned[:5]}-{cleaned[5:]}"
        return cep
    
    def validate(self, cep: str) -> ValidationResult:
        """
        Valida um CEP brasileiro.
        
        Args:
            cep: String contendo o CEP (com ou sem formatação)
            
        Returns:
            ValidationResult com o resultado da validação
        """
        cleaned = self.clean(cep)
        
        # Verifica comprimento
        if len(cleaned) != 8:
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                message=f"CEP deve ter 8 dígitos, encontrado: {len(cleaned)}"
            )
        
        # Verifica se são todos dígitos
        if not cleaned.isdigit():
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                message="CEP deve conter apenas dígitos"
            )
        
        # Verifica sequências inválidas
        if len(set(cleaned)) == 1:
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                message="CEP com dígitos repetidos"
            )
        
        # Verifica faixa válida (00000-000 a 99999-999)
        first_digit = int(cleaned[0])
        regions = {
            0: "São Paulo - Capital",
            1: "São Paulo - Interior",
            2: "Rio de Janeiro / Espírito Santo",
            3: "Minas Gerais",
            4: "Bahia / Sergipe",
            5: "Nordeste (PE, AL, PB, RN)",
            6: "Norte/Nordeste (CE, PI, MA, PA, AM, AC, AP, RR)",
            7: "Centro-Oeste (GO, TO, MT, MS, DF)",
            8: "Sul (PR, SC)",
            9: "Rio Grande do Sul"
        }
        
        region = regions.get(first_digit, "Região desconhecida")
        
        return ValidationResult(
            is_valid=True,
            confidence=0.85,
            message=f"CEP válido - Região: {region}",
            cleaned_value=cleaned
        )
