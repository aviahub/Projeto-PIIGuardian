"""
Testes Unitários dos Validadores
================================

Testes para validadores matemáticos de CPF, CNPJ, telefone, etc.

Executar:
    pytest tests/test_validators.py -v
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.validators import (
    CPFValidator,
    CNPJValidator,
    PhoneValidator,
    EmailValidator,
    CEPValidator,
    ValidationResult
)


# ============================================================================
# TESTES DO VALIDADOR DE CPF
# ============================================================================

class TestCPFValidator:
    """Testes do validador de CPF."""
    
    @pytest.fixture
    def validator(self):
        return CPFValidator()
    
    # CPFs válidos conhecidos
    VALID_CPFS = [
        "529.982.247-25",
        "52998224725",
        "123.456.789-09",
        "000.000.001-91",
    ]
    
    # CPFs inválidos
    INVALID_CPFS = [
        "111.111.111-11",  # Sequência repetida
        "222.222.222-22",
        "123.456.789-00",  # Dígitos verificadores errados
        "12345678900",
        "123",             # Muito curto
        "123456789012",    # Muito longo
        "abc.def.ghi-jk",  # Não numérico
    ]
    
    @pytest.mark.parametrize("cpf", VALID_CPFS)
    def test_valid_cpf(self, validator, cpf):
        """Testa CPFs válidos."""
        result = validator.validate(cpf)
        assert result.is_valid, f"CPF deveria ser válido: {cpf}"
        assert result.confidence >= 0.9
    
    @pytest.mark.parametrize("cpf", INVALID_CPFS)
    def test_invalid_cpf(self, validator, cpf):
        """Testa CPFs inválidos."""
        result = validator.validate(cpf)
        assert not result.is_valid, f"CPF deveria ser inválido: {cpf}"
    
    def test_clean_cpf(self, validator):
        """Testa limpeza de CPF."""
        assert validator.clean("123.456.789-09") == "12345678909"
        assert validator.clean("123 456 789 09") == "12345678909"
        assert validator.clean("12345678909") == "12345678909"
    
    def test_format_cpf(self, validator):
        """Testa formatação de CPF."""
        assert validator.format("12345678909") == "123.456.789-09"
        assert validator.format("123.456.789-09") == "123.456.789-09"
    
    def test_calculate_check_digits(self, validator):
        """Testa cálculo dos dígitos verificadores."""
        # Base: 529982247, dígitos: 2 e 5
        first, second = validator.calculate_check_digits("529982247")
        assert first == 2
        assert second == 5


# ============================================================================
# TESTES DO VALIDADOR DE CNPJ
# ============================================================================

class TestCNPJValidator:
    """Testes do validador de CNPJ."""
    
    @pytest.fixture
    def validator(self):
        return CNPJValidator()
    
    VALID_CNPJS = [
        "11.222.333/0001-81",
        "11222333000181",
    ]
    
    INVALID_CNPJS = [
        "11.111.111/1111-11",
        "00.000.000/0000-00",
        "12.345.678/0001-00",
        "123",
    ]
    
    @pytest.mark.parametrize("cnpj", VALID_CNPJS)
    def test_valid_cnpj(self, validator, cnpj):
        """Testa CNPJs válidos."""
        result = validator.validate(cnpj)
        assert result.is_valid, f"CNPJ deveria ser válido: {cnpj}"
    
    @pytest.mark.parametrize("cnpj", INVALID_CNPJS)
    def test_invalid_cnpj(self, validator, cnpj):
        """Testa CNPJs inválidos."""
        result = validator.validate(cnpj)
        assert not result.is_valid, f"CNPJ deveria ser inválido: {cnpj}"
    
    def test_clean_cnpj(self, validator):
        """Testa limpeza de CNPJ."""
        assert validator.clean("11.222.333/0001-81") == "11222333000181"
    
    def test_format_cnpj(self, validator):
        """Testa formatação de CNPJ."""
        assert validator.format("11222333000181") == "11.222.333/0001-81"


# ============================================================================
# TESTES DO VALIDADOR DE TELEFONE
# ============================================================================

class TestPhoneValidator:
    """Testes do validador de telefone."""
    
    @pytest.fixture
    def validator(self):
        return PhoneValidator()
    
    VALID_PHONES = [
        "(11) 99999-8888",
        "11999998888",
        "(61) 3456-7890",
        "6134567890",
        "+55 11 99999-8888",
    ]
    
    INVALID_PHONES = [
        "1234567",          # Muito curto
        "123456789012345",  # Muito longo
        "(00) 99999-8888",  # DDD inválido
    ]
    
    @pytest.mark.parametrize("phone", VALID_PHONES)
    def test_valid_phone(self, validator, phone):
        """Testa telefones válidos."""
        result = validator.validate(phone)
        assert result.is_valid, f"Telefone deveria ser válido: {phone}"
    
    @pytest.mark.parametrize("phone", INVALID_PHONES)
    def test_invalid_phone(self, validator, phone):
        """Testa telefones inválidos."""
        result = validator.validate(phone)
        assert not result.is_valid, f"Telefone deveria ser inválido: {phone}"
    
    def test_clean_phone(self, validator):
        """Testa limpeza de telefone."""
        assert validator.clean("(11) 99999-8888") == "11999998888"
        assert validator.clean("+55 11 99999-8888") == "5511999998888"


# ============================================================================
# TESTES DO VALIDADOR DE EMAIL
# ============================================================================

class TestEmailValidator:
    """Testes do validador de email."""
    
    @pytest.fixture
    def validator(self):
        return EmailValidator()
    
    VALID_EMAILS = [
        "usuario@exemplo.com",
        "usuario.nome@empresa.com.br",
        "user123@dominio.org",
        "nome_sobrenome@gov.br",
        "a@b.co",
    ]
    
    INVALID_EMAILS = [
        "usuario",
        "usuario@",
        "@dominio.com",
        "usuario@dominio",
        "usuario @dominio.com",
        "",
    ]
    
    @pytest.mark.parametrize("email", VALID_EMAILS)
    def test_valid_email(self, validator, email):
        """Testa emails válidos."""
        result = validator.validate(email)
        assert result.is_valid, f"Email deveria ser válido: {email}"
    
    @pytest.mark.parametrize("email", INVALID_EMAILS)
    def test_invalid_email(self, validator, email):
        """Testa emails inválidos."""
        result = validator.validate(email)
        assert not result.is_valid, f"Email deveria ser inválido: {email}"


# ============================================================================
# TESTES DO VALIDADOR DE CEP
# ============================================================================

class TestCEPValidator:
    """Testes do validador de CEP."""
    
    @pytest.fixture
    def validator(self):
        return CEPValidator()
    
    VALID_CEPS = [
        "70000-000",
        "70000000",
        "01310-100",
        "01310100",
    ]
    
    INVALID_CEPS = [
        "1234567",     # Muito curto
        "123456789",   # Muito longo
        "00000000",    # Pode ser aceito ou não
        "abcdefgh",    # Não numérico
    ]
    
    @pytest.mark.parametrize("cep", VALID_CEPS)
    def test_valid_cep(self, validator, cep):
        """Testa CEPs válidos."""
        result = validator.validate(cep)
        assert result.is_valid, f"CEP deveria ser válido: {cep}"
    
    def test_clean_cep(self, validator):
        """Testa limpeza de CEP."""
        assert validator.clean("70000-000") == "70000000"
    
    def test_format_cep(self, validator):
        """Testa formatação de CEP."""
        assert validator.format("70000000") == "70000-000"


# ============================================================================
# TESTES DE RESULTADO DE VALIDAÇÃO
# ============================================================================

class TestValidationResult:
    """Testes do objeto ValidationResult."""
    
    def test_result_attributes(self):
        """Testa atributos do resultado."""
        result = ValidationResult(
            is_valid=True,
            confidence=0.95,
            message="Validação OK",
            cleaned_value="12345678909"
        )
        
        assert result.is_valid == True
        assert result.confidence == 0.95
        assert result.message == "Validação OK"
        assert result.cleaned_value == "12345678909"
    
    def test_result_defaults(self):
        """Testa valores padrão do resultado."""
        result = ValidationResult(
            is_valid=False,
            confidence=0.0,
            message="Erro"
        )
        
        assert result.cleaned_value is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
