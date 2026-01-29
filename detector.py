#!/usr/bin/env python3
"""
PIIGuardian - Detector de Dados Pessoais
========================================

Arquivo de acesso direto ao detector para uso simplificado.

Uso:
    from detector import PIIGuardian
    
    detector = PIIGuardian()
    resultado = detector.detect("Meu CPF é 123.456.789-09")

Ou via linha de comando:
    python detector.py "Texto para analisar"

Autor: Aviahub
Versão: 1.0.0
"""

# Re-exporta do módulo principal
from src.detector import PIIGuardian, DetectionMode, DetectionResult, detect_pii
from src.validators import CPFValidator, CNPJValidator, PhoneValidator, EmailValidator
from src.patterns import BrazilianPatterns, PIIType
from src.utils import mask_pii, anonymize_text, normalize_text

__all__ = [
    'PIIGuardian',
    'DetectionMode',
    'DetectionResult',
    'detect_pii',
    'CPFValidator',
    'CNPJValidator',
    'PhoneValidator',
    'EmailValidator',
    'BrazilianPatterns',
    'PIIType',
    'mask_pii',
    'anonymize_text',
    'normalize_text',
]

__version__ = "1.0.0"


def main():
    """Execução via linha de comando."""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(
        description='PIIGuardian - Detector de Dados Pessoais',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python detector.py "Meu CPF é 123.456.789-09"
  python detector.py "Texto sem dados pessoais"
  python detector.py --mode strict "Telefone: 99999-8888"
        """
    )
    parser.add_argument(
        'text',
        nargs='?',
        help='Texto a ser analisado'
    )
    parser.add_argument(
        '--mode', '-m',
        choices=['strict', 'balanced', 'precise'],
        default='balanced',
        help='Modo de detecção (default: balanced)'
    )
    parser.add_argument(
        '--json', '-j',
        action='store_true',
        help='Saída em formato JSON'
    )
    parser.add_argument(
        '--version', '-v',
        action='version',
        version=f'PIIGuardian {__version__}'
    )
    
    args = parser.parse_args()
    
    # Se não foi passado texto, mostra demo
    if not args.text:
        print("=" * 60)
        print("PIIGuardian - Detector de Dados Pessoais v" + __version__)
        print("Hackathon Participa DF - Categoria Acesso à Informação")
        print("=" * 60)
        print()
        print("Uso: python detector.py \"Texto para analisar\"")
        print()
        print("Demonstração:")
        print("-" * 60)
        
        demo_texts = [
            "Meu CPF é 123.456.789-09 e telefone (61) 99999-8888",
            "Email para contato: usuario@exemplo.com.br",
            "Solicito informações sobre o processo."
        ]
        
        detector = PIIGuardian(mode='balanced')
        
        for text in demo_texts:
            print(f"\n📝 Texto: \"{text}\"")
            result = detector.detect(text)
            
            if result.has_pii:
                print(f"   ⚠️  PII detectado: {len(result.entities)} entidade(s)")
                for entity in result.entities:
                    print(f"      - {entity.type}: '{entity.value}' ({entity.confidence:.0%})")
            else:
                print("   ✅ Nenhum dado pessoal detectado")
        
        print()
        print("-" * 60)
        print("Para mais opções: python detector.py --help")
        return
    
    # Processa texto fornecido
    detector = PIIGuardian(mode=args.mode)
    result = detector.detect(args.text)
    
    if args.json:
        import json
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(f"\n📝 Texto: \"{args.text[:80]}{'...' if len(args.text) > 80 else ''}\"")
        print(f"🔧 Modo: {args.mode}")
        print()
        
        if result.has_pii:
            print(f"⚠️  DADOS PESSOAIS DETECTADOS: {len(result.entities)} entidade(s)")
            print()
            for entity in result.entities:
                print(f"   📌 {entity.type}")
                print(f"      Valor: {entity.value}")
                print(f"      Confiança: {entity.confidence:.0%}")
                print(f"      Método: {entity.detection_method}")
                if entity.explanation:
                    print(f"      Explicação: {entity.explanation}")
                print()
        else:
            print("✅ NENHUM DADO PESSOAL DETECTADO")
        
        print(f"⏱️  Tempo de processamento: {result.metadata['processing_time_ms']:.2f}ms")


if __name__ == "__main__":
    main()
