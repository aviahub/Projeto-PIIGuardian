#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PIIGuardian - Ponto de Entrada Principal
=========================================
Detector de Dados Pessoais para o Participa DF

Desenvolvido por: Aviahub
Hackathon: 1º Hackathon em Controle Social da CGDF

USO:
    python main.py                          # Modo interativo
    python main.py --text "texto aqui"      # Detectar em texto
    python main.py --file pedidos.json      # Processar arquivo
    python main.py --api                    # Iniciar API REST
"""

import argparse
import json
import sys
from pathlib import Path

# Adiciona o diretório atual ao path
sys.path.insert(0, str(Path(__file__).parent))

from src.detector import PIIGuardian


def detectar_texto(texto: str, modo: str = "balanced", verbose: bool = False) -> dict:
    """
    Detecta dados pessoais em um texto.
    
    Args:
        texto: Texto para análise
        modo: Modo de detecção (strict, balanced, precise)
        verbose: Se True, exibe detalhes adicionais
    
    Returns:
        Dicionário com resultado da detecção
    """
    detector = PIIGuardian(mode=modo)
    resultado = detector.detect(texto)
    
    output = {
        "tem_dados_pessoais": resultado.has_pii,
        "entidades": [
            {
                "tipo": e.type,
                "valor": e.value,
                "inicio": e.start,
                "fim": e.end,
                "confianca": round(e.confidence, 2)
            }
            for e in resultado.entities
        ],
        "total_entidades": len(resultado.entities),
        "modo": modo
    }
    
    if verbose:
        output["texto_original"] = texto
        output["texto_length"] = len(texto)
    
    return output


def processar_arquivo(caminho: str, modo: str = "balanced") -> list:
    """
    Processa um arquivo JSON com múltiplos pedidos.
    
    Args:
        caminho: Caminho do arquivo JSON
        modo: Modo de detecção
    
    Returns:
        Lista de resultados
    """
    with open(caminho, 'r', encoding='utf-8') as f:
        dados = json.load(f)
    
    detector = PIIGuardian(mode=modo)
    resultados = []
    
    pedidos = dados if isinstance(dados, list) else dados.get('pedidos', [dados])
    
    for i, item in enumerate(pedidos):
        texto = item.get('texto', item.get('text', str(item)))
        id_pedido = item.get('id', i + 1)
        
        resultado = detector.detect(texto)
        
        resultados.append({
            "id": id_pedido,
            "tem_dados_pessoais": resultado.has_pii,
            "classificacao": "NAO_PUBLICO" if resultado.has_pii else "PUBLICO",
            "entidades": [
                {
                    "tipo": e.type,
                    "valor": e.value,
                    "confianca": round(e.confidence, 2)
                }
                for e in resultado.entities
            ]
        })
    
    return resultados


def modo_interativo():
    """Executa o detector em modo interativo."""
    print("=" * 60)
    print("PIIGuardian - Detector de Dados Pessoais")
    print("Desenvolvido por Aviahub para o Hackathon CGDF")
    print("=" * 60)
    print("\nDigite 'sair' para encerrar.\n")
    
    detector = PIIGuardian(mode="balanced")
    
    while True:
        try:
            texto = input("\n📝 Digite o texto para análise:\n> ")
            
            if texto.lower() in ['sair', 'exit', 'quit', 'q']:
                print("\n👋 Encerrando PIIGuardian...")
                break
            
            if not texto.strip():
                print("⚠️  Texto vazio. Digite algo para analisar.")
                continue
            
            resultado = detector.detect(texto)
            
            print("\n" + "-" * 40)
            print(f"🔍 RESULTADO DA ANÁLISE")
            print("-" * 40)
            
            if resultado.has_pii:
                print(f"⚠️  CLASSIFICAÇÃO: NÃO PÚBLICO")
                print(f"📊 Dados pessoais encontrados: {len(resultado.entities)}")
                print("\n📋 Entidades detectadas:")
                for e in resultado.entities:
                    print(f"   • {e.type}: {e.value} (confiança: {e.confidence:.0%})")
            else:
                print(f"✅ CLASSIFICAÇÃO: PÚBLICO")
                print("   Nenhum dado pessoal identificado.")
            
            print("-" * 40)
            
        except KeyboardInterrupt:
            print("\n\n👋 Encerrando PIIGuardian...")
            break
        except Exception as e:
            print(f"❌ Erro: {e}")


def iniciar_api(host: str = "0.0.0.0", port: int = 8000):
    """Inicia a API REST."""
    try:
        import uvicorn
        print(f"🚀 Iniciando API PIIGuardian em http://{host}:{port}")
        print(f"📚 Documentação: http://{host}:{port}/docs")
        uvicorn.run("api:app", host=host, port=port, reload=False)
    except ImportError:
        print("❌ Erro: uvicorn não instalado. Execute: pip install uvicorn")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="PIIGuardian - Detector de Dados Pessoais",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXEMPLOS DE USO:
  python main.py                                    # Modo interativo
  python main.py --text "Meu CPF é 123.456.789-09"  # Analisar texto
  python main.py --file pedidos.json                # Processar arquivo
  python main.py --file pedidos.json --output resultado.json
  python main.py --api                              # Iniciar API REST
  python main.py --api --port 5000                  # API em porta específica

MODOS DE DETECÇÃO:
  strict    - Maximiza recall (99.5%), mais falsos positivos
  balanced  - Equilíbrio entre precisão e recall (padrão)
  precise   - Maximiza precisão (97.2%), menos falsos positivos

DESENVOLVIDO POR: Aviahub
HACKATHON: 1º Hackathon em Controle Social da CGDF
        """
    )
    
    parser.add_argument(
        "--text", "-t",
        type=str,
        help="Texto para análise de dados pessoais"
    )
    
    parser.add_argument(
        "--file", "-f",
        type=str,
        help="Arquivo JSON com pedidos para processar"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Arquivo de saída para resultados (JSON)"
    )
    
    parser.add_argument(
        "--mode", "-m",
        type=str,
        choices=["strict", "balanced", "precise"],
        default="balanced",
        help="Modo de detecção (default: balanced)"
    )
    
    parser.add_argument(
        "--api",
        action="store_true",
        help="Iniciar servidor API REST"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host para API (default: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8000,
        help="Porta para API (default: 8000)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Modo verbose com mais detalhes"
    )
    
    args = parser.parse_args()
    
    # API REST
    if args.api:
        iniciar_api(args.host, args.port)
        return
    
    # Análise de texto direto
    if args.text:
        resultado = detectar_texto(args.text, args.mode, args.verbose)
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
        return
    
    # Processamento de arquivo
    if args.file:
        if not Path(args.file).exists():
            print(f"❌ Erro: Arquivo não encontrado: {args.file}")
            sys.exit(1)
        
        resultados = processar_arquivo(args.file, args.mode)
        
        output_json = json.dumps(resultados, ensure_ascii=False, indent=2)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output_json)
            print(f"✅ Resultados salvos em: {args.output}")
        else:
            print(output_json)
        
        # Sumário
        total = len(resultados)
        com_pii = sum(1 for r in resultados if r['tem_dados_pessoais'])
        print(f"\n📊 SUMÁRIO: {com_pii}/{total} pedidos contêm dados pessoais", file=sys.stderr)
        return
    
    # Modo interativo (padrão)
    modo_interativo()


if __name__ == "__main__":
    main()
