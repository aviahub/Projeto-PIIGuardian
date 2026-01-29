#!/usr/bin/env python3
"""
Script de Processamento em Lote
===============================

Processa múltiplos arquivos ou registros CSV/JSON para detecção
de dados pessoais em massa.

Uso:
    python scripts/batch_process.py --input pedidos.csv --output classificados.csv --column texto_pedido
    python scripts/batch_process.py --input pedidos.json --output resultados.json

Autor: Equipe PIIGuardian
"""

import argparse
import csv
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Iterator
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Adiciona diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.detector import PIIGuardian
from src.utils import normalize_text, save_json_file


# Lock para thread-safety no contador
progress_lock = threading.Lock()
progress_counter = 0


class BatchProcessor:
    """Processador de lotes para detecção de PII."""
    
    def __init__(
        self,
        mode: str = 'balanced',
        workers: int = 1,
        verbose: bool = False
    ):
        self.mode = mode
        self.workers = workers
        self.verbose = verbose
        self.detector = PIIGuardian(mode=mode)
        
        # Estatísticas
        self.stats = {
            'total_processed': 0,
            'total_with_pii': 0,
            'total_entities': 0,
            'total_time_ms': 0,
            'by_type': {},
            'errors': 0
        }
    
    def process_text(self, text: str, record_id: str = None) -> Dict[str, Any]:
        """
        Processa um único texto.
        
        Args:
            text: Texto a processar
            record_id: ID do registro (opcional)
            
        Returns:
            Resultado do processamento
        """
        try:
            normalized = normalize_text(text) if text else ""
            result = self.detector.detect(normalized)
            
            return {
                'id': record_id,
                'has_pii': result.has_pii,
                'entities': [e.to_dict() for e in result.entities],
                'entity_count': len(result.entities),
                'processing_time_ms': result.metadata['processing_time_ms'],
                'error': None
            }
        except Exception as e:
            return {
                'id': record_id,
                'has_pii': None,
                'entities': [],
                'entity_count': 0,
                'processing_time_ms': 0,
                'error': str(e)
            }
    
    def process_batch(
        self,
        records: List[Dict[str, Any]],
        text_column: str = 'text',
        id_column: str = 'id'
    ) -> List[Dict[str, Any]]:
        """
        Processa um lote de registros.
        
        Args:
            records: Lista de registros
            text_column: Nome da coluna com o texto
            id_column: Nome da coluna com o ID
            
        Returns:
            Lista de resultados
        """
        global progress_counter
        progress_counter = 0
        
        results = []
        start_time = time.time()
        total = len(records)
        
        if self.workers > 1:
            # Processamento paralelo
            with ThreadPoolExecutor(max_workers=self.workers) as executor:
                futures = {}
                for record in records:
                    text = record.get(text_column, '')
                    record_id = record.get(id_column, str(len(futures)))
                    future = executor.submit(self.process_text, text, record_id)
                    futures[future] = record
                
                for future in as_completed(futures):
                    result = future.result()
                    results.append(result)
                    
                    with progress_lock:
                        progress_counter += 1
                        if self.verbose and progress_counter % 100 == 0:
                            print(f"  Processado: {progress_counter}/{total}")
                    
                    self._update_stats(result)
        else:
            # Processamento sequencial
            for i, record in enumerate(records):
                text = record.get(text_column, '')
                record_id = record.get(id_column, str(i))
                
                result = self.process_text(text, record_id)
                results.append(result)
                
                self._update_stats(result)
                
                if self.verbose and (i + 1) % 100 == 0:
                    print(f"  Processado: {i + 1}/{total}")
        
        self.stats['total_time_ms'] = (time.time() - start_time) * 1000
        
        return results
    
    def _update_stats(self, result: Dict[str, Any]):
        """Atualiza estatísticas com resultado."""
        self.stats['total_processed'] += 1
        
        if result.get('error'):
            self.stats['errors'] += 1
        elif result.get('has_pii'):
            self.stats['total_with_pii'] += 1
            self.stats['total_entities'] += result.get('entity_count', 0)
            
            for entity in result.get('entities', []):
                entity_type = entity.get('type', 'UNKNOWN')
                self.stats['by_type'][entity_type] = self.stats['by_type'].get(entity_type, 0) + 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Retorna sumário do processamento."""
        total = self.stats['total_processed']
        with_pii = self.stats['total_with_pii']
        
        return {
            'total_processed': total,
            'total_with_pii': with_pii,
            'total_without_pii': total - with_pii - self.stats['errors'],
            'pii_percentage': round(with_pii / total * 100, 2) if total > 0 else 0,
            'total_entities': self.stats['total_entities'],
            'entities_by_type': self.stats['by_type'],
            'errors': self.stats['errors'],
            'total_time_ms': round(self.stats['total_time_ms'], 2),
            'avg_time_ms': round(self.stats['total_time_ms'] / total, 2) if total > 0 else 0
        }


def load_csv(file_path: str) -> List[Dict[str, Any]]:
    """Carrega dados de arquivo CSV."""
    records = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(dict(row))
    return records


def save_csv(records: List[Dict[str, Any]], file_path: str, fieldnames: List[str] = None):
    """Salva dados em arquivo CSV."""
    if not records:
        return
    
    if fieldnames is None:
        fieldnames = list(records[0].keys())
    
    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            # Converte listas/dicts para JSON string
            row = {}
            for k, v in record.items():
                if k in fieldnames:
                    if isinstance(v, (list, dict)):
                        row[k] = json.dumps(v, ensure_ascii=False)
                    else:
                        row[k] = v
            writer.writerow(row)


def load_json(file_path: str) -> List[Dict[str, Any]]:
    """Carrega dados de arquivo JSON."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return data
    elif 'data' in data:
        return data['data']
    elif 'records' in data:
        return data['records']
    else:
        return [data]


def main():
    parser = argparse.ArgumentParser(
        description='Processa lote de textos para detecção de PII'
    )
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Arquivo de entrada (CSV ou JSON)'
    )
    parser.add_argument(
        '--output', '-o',
        required=True,
        help='Arquivo de saída'
    )
    parser.add_argument(
        '--column', '-c',
        default='text',
        help='Nome da coluna com o texto (padrão: text)'
    )
    parser.add_argument(
        '--id-column',
        default='id',
        help='Nome da coluna com o ID (padrão: id)'
    )
    parser.add_argument(
        '--mode', '-m',
        choices=['strict', 'balanced', 'precise'],
        default='balanced',
        help='Modo de detecção'
    )
    parser.add_argument(
        '--workers', '-w',
        type=int,
        default=1,
        help='Número de workers para processamento paralelo'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Saída detalhada'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("PIIGuardian - Processamento em Lote")
    print("=" * 70)
    print()
    
    # Determina formato do arquivo de entrada
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ Arquivo não encontrado: {args.input}")
        sys.exit(1)
    
    # Carrega dados
    print(f"📂 Carregando dados de: {args.input}")
    if input_path.suffix.lower() == '.csv':
        records = load_csv(args.input)
    else:
        records = load_json(args.input)
    print(f"   ✓ {len(records)} registros carregados")
    
    # Verifica coluna de texto
    if records and args.column not in records[0]:
        available_columns = list(records[0].keys())
        print(f"❌ Coluna '{args.column}' não encontrada.")
        print(f"   Colunas disponíveis: {available_columns}")
        sys.exit(1)
    
    # Inicializa processador
    print(f"\n🔧 Inicializando processador (modo: {args.mode}, workers: {args.workers})...")
    processor = BatchProcessor(
        mode=args.mode,
        workers=args.workers,
        verbose=args.verbose
    )
    print("   ✓ Processador inicializado")
    
    # Processa lote
    print(f"\n🔍 Processando {len(records)} registros...")
    start_time = time.time()
    
    results = processor.process_batch(
        records,
        text_column=args.column,
        id_column=args.id_column
    )
    
    elapsed = time.time() - start_time
    print(f"   ✓ Processamento concluído em {elapsed:.2f}s")
    
    # Salva resultados
    print(f"\n💾 Salvando resultados em: {args.output}")
    output_path = Path(args.output)
    
    if output_path.suffix.lower() == '.csv':
        # Para CSV, mescla dados originais com resultados
        merged = []
        for record, result in zip(records, results):
            merged_record = dict(record)
            merged_record['pii_detected'] = result['has_pii']
            merged_record['pii_count'] = result['entity_count']
            merged_record['pii_entities'] = result['entities']
            merged.append(merged_record)
        
        fieldnames = list(records[0].keys()) + ['pii_detected', 'pii_count', 'pii_entities']
        save_csv(merged, args.output, fieldnames)
    else:
        # Para JSON, salva estrutura completa
        output_data = {
            'timestamp': datetime.now().isoformat(),
            'input_file': args.input,
            'mode': args.mode,
            'summary': processor.get_summary(),
            'results': results
        }
        save_json_file(output_data, args.output)
    
    print("   ✓ Resultados salvos")
    
    # Exibe sumário
    summary = processor.get_summary()
    print()
    print("=" * 70)
    print("SUMÁRIO DO PROCESSAMENTO")
    print("=" * 70)
    print(f"  Total processado: {summary['total_processed']}")
    print(f"  Com PII detectado: {summary['total_with_pii']} ({summary['pii_percentage']}%)")
    print(f"  Sem PII: {summary['total_without_pii']}")
    print(f"  Erros: {summary['errors']}")
    print(f"  Total de entidades: {summary['total_entities']}")
    print(f"  Tempo total: {summary['total_time_ms']:.2f}ms")
    print(f"  Tempo médio: {summary['avg_time_ms']:.2f}ms por registro")
    
    if summary['entities_by_type']:
        print()
        print("  Entidades por tipo:")
        for entity_type, count in sorted(summary['entities_by_type'].items()):
            print(f"    - {entity_type}: {count}")
    
    print("=" * 70)
    print()
    print("✅ Processamento concluído com sucesso!")


if __name__ == "__main__":
    main()
