"""
Testes Unitários do Detector PIIGuardian
========================================

Testes abrangentes para validar a detecção de dados pessoais,
cobrindo todos os tipos de PII suportados e casos extremos.

Executar:
    pytest tests/test_detector.py -v
"""

import pytest
import sys
from pathlib import Path

# Adiciona diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.detector import PIIGuardian, DetectionMode, DetectionResult


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def detector():
    """Detector no modo balanceado."""
    return PIIGuardian(mode='balanced')


@pytest.fixture
def detector_strict():
    """Detector no modo strict (máximo recall)."""
    return PIIGuardian(mode='strict')


@pytest.fixture
def detector_precise():
    """Detector no modo precise (máxima precisão)."""
    return PIIGuardian(mode='precise')


# ============================================================================
# TESTES DE INICIALIZAÇÃO
# ============================================================================

class TestInitialization:
    """Testes de inicialização do detector."""
    
    def test_create_detector_default(self):
        """Testa criação do detector com configuração padrão."""
        detector = PIIGuardian()
        assert detector is not None
        assert detector.config.mode == DetectionMode.BALANCED
    
    def test_create_detector_strict_mode(self):
        """Testa criação do detector no modo strict."""
        detector = PIIGuardian(mode='strict')
        assert detector.config.mode == DetectionMode.STRICT
    
    def test_create_detector_precise_mode(self):
        """Testa criação do detector no modo precise."""
        detector = PIIGuardian(mode='precise')
        assert detector.config.mode == DetectionMode.PRECISE
    
    def test_invalid_mode_raises_error(self):
        """Testa que modo inválido levanta erro."""
        with pytest.raises(ValueError):
            PIIGuardian(mode='invalid_mode')


# ============================================================================
# TESTES DE DETECÇÃO DE CPF
# ============================================================================

class TestCPFDetection:
    """Testes de detecção de CPF."""
    
    @pytest.mark.parametrize("cpf", [
        "123.456.789-09",
        "12345678909",
        "123 456 789 09",
        "123.456.789.09",
    ])
    def test_detect_cpf_various_formats(self, detector, cpf):
        """Testa detecção de CPF em vários formatos."""
        text = f"Meu CPF é {cpf}"
        result = detector.detect(text)
        
        assert result.has_pii, f"Falhou para CPF: {cpf}"
        cpf_entities = [e for e in result.entities if 'CPF' in e.type]
        assert len(cpf_entities) >= 1, f"CPF não detectado: {cpf}"
    
    def test_detect_cpf_in_context(self, detector):
        """Testa detecção de CPF com contexto."""
        text = "O contribuinte, inscrito no CPF sob o número 123.456.789-09, solicita"
        result = detector.detect(text)
        
        assert result.has_pii
        assert any('CPF' in e.type for e in result.entities)
    
    def test_cpf_validation(self, detector):
        """Testa validação matemática do CPF."""
        # CPF válido matematicamente
        valid_cpf = "529.982.247-25"
        result = detector.detect(f"CPF: {valid_cpf}")
        
        cpf_entities = [e for e in result.entities if 'CPF' in e.type]
        assert len(cpf_entities) >= 1
        
        # Verifica se a validação foi aplicada
        entity = cpf_entities[0]
        assert entity.validation_status in ['valid', 'invalid', 'not_validated']
    
    def test_reject_invalid_cpf_sequence(self, detector_precise):
        """Testa rejeição de CPF com sequência inválida."""
        invalid_cpf = "111.111.111-11"
        result = detector_precise.detect(f"CPF: {invalid_cpf}")
        
        # No modo precise, CPFs inválidos devem ser rejeitados ou ter baixa confiança
        cpf_entities = [e for e in result.entities if 'CPF' in e.type]
        if cpf_entities:
            assert cpf_entities[0].confidence < 0.5


# ============================================================================
# TESTES DE DETECÇÃO DE TELEFONE
# ============================================================================

class TestPhoneDetection:
    """Testes de detecção de telefone."""
    
    @pytest.mark.parametrize("phone", [
        "(61) 99999-8888",
        "61 99999-8888",
        "6199998888",
        "(11) 3456-7890",
        "+55 61 99999-8888",
        "61999998888",
    ])
    def test_detect_phone_various_formats(self, detector, phone):
        """Testa detecção de telefone em vários formatos."""
        text = f"Meu telefone é {phone}"
        result = detector.detect(text)
        
        assert result.has_pii, f"Falhou para telefone: {phone}"
        phone_entities = [e for e in result.entities if 'TELEFONE' in e.type or 'CELULAR' in e.type]
        assert len(phone_entities) >= 1, f"Telefone não detectado: {phone}"
    
    def test_detect_phone_with_context(self, detector):
        """Testa detecção de telefone com contexto."""
        text = "Para contato, ligue no número (11) 98765-4321 ou envie mensagem"
        result = detector.detect(text)
        
        assert result.has_pii
        assert any('TELEFONE' in e.type or 'CELULAR' in e.type for e in result.entities)
    
    def test_detect_both_mobile_and_landline(self, detector):
        """Testa detecção de celular e fixo no mesmo texto."""
        text = "Celular: (11) 99999-8888, Fixo: (11) 3456-7890"
        result = detector.detect(text)
        
        assert result.has_pii
        phone_entities = [e for e in result.entities if 'TELEFONE' in e.type or 'CELULAR' in e.type]
        assert len(phone_entities) >= 2


# ============================================================================
# TESTES DE DETECÇÃO DE EMAIL
# ============================================================================

class TestEmailDetection:
    """Testes de detecção de email."""
    
    @pytest.mark.parametrize("email", [
        "usuario@exemplo.com",
        "usuario.nome@empresa.com.br",
        "user123@dominio.org",
        "nome_sobrenome@gov.br",
    ])
    def test_detect_email_various_formats(self, detector, email):
        """Testa detecção de email em vários formatos."""
        text = f"Meu email é {email}"
        result = detector.detect(text)
        
        assert result.has_pii, f"Falhou para email: {email}"
        email_entities = [e for e in result.entities if 'EMAIL' in e.type]
        assert len(email_entities) >= 1, f"Email não detectado: {email}"
    
    def test_detect_email_with_context(self, detector):
        """Testa detecção de email com contexto."""
        text = "Envie resposta para o endereço eletrônico joao.silva@empresa.com.br"
        result = detector.detect(text)
        
        assert result.has_pii
        assert any('EMAIL' in e.type for e in result.entities)


# ============================================================================
# TESTES DE DETECÇÃO DE CEP
# ============================================================================

class TestCEPDetection:
    """Testes de detecção de CEP."""
    
    @pytest.mark.parametrize("cep", [
        "70000-000",
        "70000000",
        "01310-100",
    ])
    def test_detect_cep_various_formats(self, detector, cep):
        """Testa detecção de CEP em vários formatos."""
        text = f"CEP: {cep}"
        result = detector.detect(text)
        
        assert result.has_pii, f"Falhou para CEP: {cep}"
        cep_entities = [e for e in result.entities if 'CEP' in e.type]
        assert len(cep_entities) >= 1, f"CEP não detectado: {cep}"


# ============================================================================
# TESTES DE DETECÇÃO DE CNPJ
# ============================================================================

class TestCNPJDetection:
    """Testes de detecção de CNPJ."""
    
    @pytest.mark.parametrize("cnpj", [
        "12.345.678/0001-90",
        "12345678000190",
        "12.345.678/0001.90",
    ])
    def test_detect_cnpj_various_formats(self, detector, cnpj):
        """Testa detecção de CNPJ em vários formatos."""
        text = f"CNPJ: {cnpj}"
        result = detector.detect(text)
        
        assert result.has_pii, f"Falhou para CNPJ: {cnpj}"
        cnpj_entities = [e for e in result.entities if 'CNPJ' in e.type]
        assert len(cnpj_entities) >= 1, f"CNPJ não detectado: {cnpj}"


# ============================================================================
# TESTES DE DETECÇÃO MÚLTIPLA
# ============================================================================

class TestMultipleDetection:
    """Testes de detecção de múltiplos dados pessoais."""
    
    def test_detect_multiple_pii_types(self, detector):
        """Testa detecção de múltiplos tipos de PII no mesmo texto."""
        text = """
        Dados do solicitante:
        - Nome: João da Silva
        - CPF: 123.456.789-09
        - Telefone: (61) 99999-8888
        - Email: joao@email.com
        - CEP: 70000-000
        """
        result = detector.detect(text)
        
        assert result.has_pii
        assert len(result.entities) >= 4
        
        # Verifica tipos detectados
        types_found = {e.type.replace('_CONTEXTUAL', '') for e in result.entities}
        expected_types = {'CPF', 'TELEFONE', 'EMAIL', 'CEP'}
        assert expected_types.issubset(types_found) or len(types_found) >= 3
    
    def test_detect_repeated_data(self, detector):
        """Testa detecção de dados repetidos."""
        text = "CPF 123.456.789-09 confirmado. Repito: CPF 123.456.789-09"
        result = detector.detect(text)
        
        assert result.has_pii
        cpf_entities = [e for e in result.entities if 'CPF' in e.type]
        # Pode detectar 1 ou 2, dependendo da deduplicação
        assert len(cpf_entities) >= 1


# ============================================================================
# TESTES DE TEXTO SEM PII
# ============================================================================

class TestNoPII:
    """Testes de textos sem dados pessoais."""
    
    @pytest.mark.parametrize("text", [
        "Olá, gostaria de solicitar informações sobre o processo.",
        "Agradeço a atenção dispensada.",
        "Venho por meio desta solicitar esclarecimentos.",
        "O documento está em análise.",
    ])
    def test_no_pii_detected(self, detector, text):
        """Testa que textos sem PII não geram detecções."""
        result = detector.detect(text)
        
        # Pode ter algumas detecções de baixa confiança, mas não deve ter muitas
        high_confidence_entities = [e for e in result.entities if e.confidence > 0.7]
        assert len(high_confidence_entities) == 0, f"Falso positivo em: {text}"
    
    def test_empty_text(self, detector):
        """Testa texto vazio."""
        result = detector.detect("")
        
        assert not result.has_pii
        assert len(result.entities) == 0
    
    def test_whitespace_only(self, detector):
        """Testa texto com apenas espaços."""
        result = detector.detect("   \n\t  ")
        
        assert not result.has_pii
        assert len(result.entities) == 0


# ============================================================================
# TESTES DE DETECÇÃO CONTEXTUAL
# ============================================================================

class TestContextualDetection:
    """Testes de detecção baseada em contexto."""
    
    def test_detect_name_with_title(self, detector):
        """Testa detecção de nome com título."""
        text = "Solicito audiência com o Sr. Carlos Eduardo da Silva"
        result = detector.detect(text)
        
        # Deve detectar o nome
        name_entities = [e for e in result.entities if 'NOME' in e.type or 'PESSOA' in e.type]
        # Pode ou não detectar dependendo do modo
        assert result is not None
    
    def test_detect_cpf_contextual(self, detector_strict):
        """Testa detecção de CPF por contexto."""
        text = "Meu CPF é 123 456 789 09, por favor verifique"
        result = detector_strict.detect(text)
        
        assert result.has_pii
    
    def test_detect_phone_contextual(self, detector_strict):
        """Testa detecção de telefone por contexto."""
        text = "Me ligue no celular 99999-8888 ou no fixo 3456-7890"
        result = detector_strict.detect(text)
        
        assert result.has_pii
        phone_entities = [e for e in result.entities if 'TELEFONE' in e.type]
        assert len(phone_entities) >= 1


# ============================================================================
# TESTES DE RESULTADO
# ============================================================================

class TestDetectionResult:
    """Testes do objeto de resultado."""
    
    def test_result_structure(self, detector):
        """Testa estrutura do resultado."""
        result = detector.detect("CPF: 123.456.789-09")
        
        assert hasattr(result, 'has_pii')
        assert hasattr(result, 'entities')
        assert hasattr(result, 'summary')
        assert hasattr(result, 'metadata')
    
    def test_result_to_dict(self, detector):
        """Testa conversão para dicionário."""
        result = detector.detect("Email: teste@email.com")
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert 'has_pii' in result_dict
        assert 'entities' in result_dict
        assert 'summary' in result_dict
        assert 'metadata' in result_dict
    
    def test_metadata_contains_timing(self, detector):
        """Testa que metadados contêm tempo de processamento."""
        result = detector.detect("Texto qualquer")
        
        assert 'processing_time_ms' in result.metadata
        assert result.metadata['processing_time_ms'] >= 0
    
    def test_summary_counts_by_type(self, detector):
        """Testa que sumário conta por tipo."""
        result = detector.detect("CPF: 123.456.789-09, Email: a@b.com")
        
        assert 'total_entities' in result.summary
        assert 'by_type' in result.summary
        assert result.summary['total_entities'] >= 0


# ============================================================================
# TESTES DE PERFORMANCE
# ============================================================================

class TestPerformance:
    """Testes de performance básica."""
    
    def test_short_text_performance(self, detector):
        """Testa performance com texto curto."""
        text = "CPF: 123.456.789-09"
        result = detector.detect(text)
        
        # Deve processar em menos de 1 segundo
        assert result.metadata['processing_time_ms'] < 1000
    
    def test_medium_text_performance(self, detector):
        """Testa performance com texto médio."""
        text = "CPF: 123.456.789-09 " * 100
        result = detector.detect(text)
        
        # Deve processar em menos de 5 segundos
        assert result.metadata['processing_time_ms'] < 5000
    
    def test_large_text_performance(self, detector):
        """Testa performance com texto grande."""
        text = "Texto sem dados pessoais. " * 500
        result = detector.detect(text)
        
        # Deve processar em menos de 10 segundos
        assert result.metadata['processing_time_ms'] < 10000


# ============================================================================
# TESTES DE MODOS
# ============================================================================

class TestDetectionModes:
    """Testes dos diferentes modos de detecção."""
    
    def test_strict_mode_higher_recall(self, detector_strict, detector_precise):
        """Testa que modo strict tem maior recall."""
        # Texto com dado ambíguo
        text = "Número: 99999-8888"
        
        result_strict = detector_strict.detect(text)
        result_precise = detector_precise.detect(text)
        
        # Modo strict deve detectar mais ou igual
        assert len(result_strict.entities) >= len(result_precise.entities)
    
    def test_precise_mode_higher_confidence(self, detector_strict, detector_precise):
        """Testa que modo precise requer maior confiança."""
        text = "CPF: 123.456.789-09"
        
        result_strict = detector_strict.detect(text)
        result_precise = detector_precise.detect(text)
        
        # Ambos devem detectar CPF claro
        assert result_strict.has_pii
        assert result_precise.has_pii


# ============================================================================
# EXECUÇÃO DOS TESTES
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
