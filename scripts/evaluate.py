#!/usr/bin/env python3
"""
Script de Avaliação do PIIGuardian
==================================

Avalia a performance do detector usando conjunto de dados de teste,
calculando métricas como recall, precisão, F1-score e falsos negativos.

Uso:
    python scripts/evaluate.py --data data/test_data.json --output results.json
    python scripts/evaluate.py --data data/test_data.json --metrics all --verbose

Autor: Equipe PIIGuardian
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime

# Adiciona diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.detector import PIIGuardian
from src.utils import load_json_file, save_json_file, normalize_text


@dataclass
class EvaluationMetrics:
    """Métricas de avaliação."""
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    true_negatives: int = 0
    
    # Métricas calculadas
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    accuracy: float = 0.0
    
    # Detalhes por tipo
    by_type: Dict[str, Dict[str, int]] = field(default_factory=dict)
    
    # Tempos
    total_time_ms: float = 0.0
    avg_time_ms: float = 0.0
    
    def calculate(self):
        """Calcula métricas derivadas."""
        tp, fp, fn, tn = self.true_positives, self.false_positives, self.false_negatives, self.true_negatives
        
        self.precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        self.recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        self.f1_score = 2 * self.precision * self.recall / (self.precision + self.recall) if (self.precision + self.recall) > 0 else 0.0
        self.accuracy = (tp + tn) / (tp + fp + fn + tn) if (tp + fp + fn + tn) > 0 else 0.0
    
    def to_dict(self) -> Dict:
        """Converte para dicionário."""
        return {
            'true_positives': self.true_positives,
            'false_positives': self.false_positives,
            'false_negatives': self.false_negatives,
            'true_negatives': self.true_negatives,
            'precision': round(self.precision, 4),
            'recall': round(self.recall, 4),
            'f1_score': round(self.f1_score, 4),
            'accuracy': round(self.accuracy, 4),
            'by_type': self.by_type,
            'total_time_ms': round(self.total_time_ms, 2),
            'avg_time_ms': round(self.avg_time_ms, 2),
        }


@dataclass
class TestCase:
    """Caso de teste para avaliação."""
    id: str
    text: str
    expected_entities: List[Dict[str, Any]]
    expected_has_pii: bool
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TestCase':
        return cls(
            id=data.get('id', 'unknown'),
            text=data.get('text', ''),
            expected_entities=data.get('expected_entities', data.get('entities', [])),
            expected_has_pii=data.get('expected_has_pii', data.get('has_pii', len(data.get('expected_entities', data.get('entities', []))) > 0))
        )


class Evaluator:
    """Avaliador de performance do detector."""
    
    def __init__(self, detector: PIIGuardian, verbose: bool = False):
        self.detector = detector
        self.verbose = verbose
        self.metrics = EvaluationMetrics()
        self.errors: List[Dict] = []
        self.results: List[Dict] = []
    
    def evaluate(self, test_cases: List[TestCase]) -> EvaluationMetrics:
        """
        Avalia o detector com casos de teste.
        
        Args:
            test_cases: Lista de casos de teste
            
        Returns:
            Métricas de avaliação
        """
        start_time = time.time()
        
        for i, test_case in enumerate(test_cases):
            if self.verbose and (i + 1) % 100 == 0:
                print(f"  Processando {i + 1}/{len(test_cases)}...")
            
            self._evaluate_single(test_case)
        
        # Calcula tempo total
        self.metrics.total_time_ms = (time.time() - start_time) * 1000
        self.metrics.avg_time_ms = self.metrics.total_time_ms / len(test_cases) if test_cases else 0
        
        # Calcula métricas derivadas
        self.metrics.calculate()
        
        return self.metrics
    
    def _evaluate_single(self, test_case: TestCase):
        """Avalia um único caso de teste."""
        # Executa detecção
        result = self.detector.detect(normalize_text(test_case.text))
        
        # Extrai entidades detectadas
        detected = {self._normalize_entity(e.to_dict()) for e in result.entities}
        expected = {self._normalize_entity(e) for e in test_case.expected_entities}
        
        # Calcula TP, FP, FN
        tp = len(detected & expected)
        fp = len(detected - expected)
        fn = len(expected - detected)
        
        # Atualiza métricas globais
        self.metrics.true_positives += tp
        self.metrics.false_positives += fp
        self.metrics.false_negatives += fn
        
        # Se não tinha PII esperado e não detectou, é TN
        if not test_case.expected_has_pii and not result.has_pii:
            self.metrics.true_negatives += 1
        
        # Atualiza métricas por tipo
        for entity in test_case.expected_entities:
            entity_type = entity.get('type', 'UNKNOWN')
            if entity_type not in self.metrics.by_type:
                self.metrics.by_type[entity_type] = {'tp': 0, 'fp': 0, 'fn': 0}
            
            # Verifica se foi detectado
            normalized = self._normalize_entity(entity)
            if normalized in detected:
                self.metrics.by_type[entity_type]['tp'] += 1
            else:
                self.metrics.by_type[entity_type]['fn'] += 1
        
        for entity in result.entities:
            entity_type = entity.type.replace('_CONTEXTUAL', '')
            if entity_type not in self.metrics.by_type:
                self.metrics.by_type[entity_type] = {'tp': 0, 'fp': 0, 'fn': 0}
            
            normalized = self._normalize_entity(entity.to_dict())
            if normalized not in expected:
                self.metrics.by_type[entity_type]['fp'] += 1
        
        # Registra erros (falsos negativos)
        if fn > 0:
            self.errors.append({
                'id': test_case.id,
                'text': test_case.text[:100],
                'expected': list(expected - detected),
                'detected': list(detected),
                'false_negatives': fn
            })
        
        # Registra resultado
        self.results.append({
            'id': test_case.id,
            'has_pii_expected': test_case.expected_has_pii,
            'has_pii_detected': result.has_pii,
            'tp': tp,
            'fp': fp,
            'fn': fn,
            'correct': fn == 0 and fp == 0
        })
    
    def _normalize_entity(self, entity: Dict) -> Tuple:
        """Normaliza entidade para comparação."""
        entity_type = entity.get('type', 'UNKNOWN').replace('_CONTEXTUAL', '')
        value = entity.get('value', '').strip()
        
        # Remove formatação para comparação
        import re
        value_normalized = re.sub(r'[\s\.\-\/\(\)]', '', value.lower())
        
        return (entity_type, value_normalized)
    
    def get_report(self) -> str:
        """Gera relatório de avaliação."""
        m = self.metrics
        
        lines = [
            "=" * 70,
            "RELATÓRIO DE AVALIAÇÃO - PIIGuardian",
            "=" * 70,
            "",
            "## Métricas Gerais",
            "",
            f"  Precisão (Precision): {m.precision:.4f} ({m.precision*100:.2f}%)",
            f"  Recall (Sensibilidade): {m.recall:.4f} ({m.recall*100:.2f}%)",
            f"  F1-Score: {m.f1_score:.4f} ({m.f1_score*100:.2f}%)",
            f"  Acurácia: {m.accuracy:.4f} ({m.accuracy*100:.2f}%)",
            "",
            "## Matriz de Confusão",
            "",
            f"  True Positives (TP): {m.true_positives}",
            f"  False Positives (FP): {m.false_positives}",
            f"  False Negatives (FN): {m.false_negatives} ⚠️ CRITÉRIO DE DESEMPATE",
            f"  True Negatives (TN): {m.true_negatives}",
            "",
            "## Performance",
            "",
            f"  Tempo total: {m.total_time_ms:.2f}ms",
            f"  Tempo médio por texto: {m.avg_time_ms:.2f}ms",
            "",
        ]
        
        if m.by_type:
            lines.append("## Métricas por Tipo de PII")
            lines.append("")
            for pii_type, counts in sorted(m.by_type.items()):
                tp = counts['tp']
                fp = counts['fp']
                fn = counts['fn']
                recall = tp / (tp + fn) if (tp + fn) > 0 else 0
                precision = tp / (tp + fp) if (tp + fp) > 0 else 0
                lines.append(f"  {pii_type}:")
                lines.append(f"    - Recall: {recall:.4f}, Precision: {precision:.4f}")
                lines.append(f"    - TP: {tp}, FP: {fp}, FN: {fn}")
            lines.append("")
        
        if self.errors:
            lines.append("## Falsos Negativos (Primeiros 10)")
            lines.append("")
            for error in self.errors[:10]:
                lines.append(f"  ID: {error['id']}")
                lines.append(f"  Texto: {error['text']}...")
                lines.append(f"  Esperado mas não detectado: {error['expected']}")
                lines.append("")
        
        lines.append("=" * 70)
        
        return "\n".join(lines)


def load_test_data(file_path: str) -> List[TestCase]:
    """Carrega dados de teste de arquivo JSON."""
    data = load_json_file(file_path)
    
    # Suporta diferentes formatos
    if isinstance(data, list):
        return [TestCase.from_dict(d) for d in data]
    elif 'test_cases' in data:
        return [TestCase.from_dict(d) for d in data['test_cases']]
    elif 'data' in data:
        return [TestCase.from_dict(d) for d in data['data']]
    else:
        raise ValueError("Formato de dados de teste não reconhecido")


def main():
    parser = argparse.ArgumentParser(
        description='Avalia performance do PIIGuardian'
    )
    parser.add_argument(
        '--data', '-d',
        required=True,
        help='Arquivo JSON com dados de teste'
    )
    parser.add_argument(
        '--output', '-o',
        help='Arquivo para salvar resultados (JSON)'
    )
    parser.add_argument(
        '--mode', '-m',
        choices=['strict', 'balanced', 'precise'],
        default='balanced',
        help='Modo de detecção'
    )
    parser.add_argument(
        '--metrics',
        choices=['basic', 'all'],
        default='all',
        help='Nível de métricas a calcular'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Saída detalhada'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("PIIGuardian - Avaliação de Performance")
    print("=" * 70)
    print()
    
    # Carrega dados de teste
    print(f"📂 Carregando dados de: {args.data}")
    try:
        test_cases = load_test_data(args.data)
        print(f"   ✓ {len(test_cases)} casos de teste carregados")
    except Exception as e:
        print(f"   ✗ Erro ao carregar dados: {e}")
        sys.exit(1)
    
    # Inicializa detector
    print(f"\n🔧 Inicializando detector (modo: {args.mode})...")
    detector = PIIGuardian(mode=args.mode)
    print("   ✓ Detector inicializado")
    
    # Executa avaliação
    print(f"\n🔍 Executando avaliação...")
    evaluator = Evaluator(detector, verbose=args.verbose)
    metrics = evaluator.evaluate(test_cases)
    
    # Exibe relatório
    print()
    print(evaluator.get_report())
    
    # Salva resultados
    if args.output:
        output_data = {
            'timestamp': datetime.now().isoformat(),
            'mode': args.mode,
            'total_tests': len(test_cases),
            'metrics': metrics.to_dict(),
            'errors': evaluator.errors[:100],  # Limita erros salvos
        }
        save_json_file(output_data, args.output)
        print(f"\n💾 Resultados salvos em: {args.output}")
    
    # Retorna código de saída baseado em FN
    if metrics.false_negatives > 0:
        print(f"\n⚠️  ATENÇÃO: {metrics.false_negatives} falsos negativos detectados!")
        sys.exit(1)
    else:
        print("\n✅ Avaliação concluída com sucesso - Zero falsos negativos!")
        sys.exit(0)


if __name__ == "__main__":
    main()
