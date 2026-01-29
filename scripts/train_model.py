#!/usr/bin/env python3
"""
Script de Treinamento de Modelo (Opcional)
==========================================

Script para fine-tuning do modelo BERT para detecção de entidades
nomeadas específicas do domínio.

NOTA: Este script é OPCIONAL. O PIIGuardian funciona perfeitamente
com os modelos pré-treinados. Use apenas se quiser melhorar
a detecção para casos específicos.

Uso:
    python scripts/train_model.py --data data/training_data.json --epochs 3 --output models/

Autor: Equipe PIIGuardian
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Adiciona diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Verifica disponibilidade de dependências
try:
    import torch
    from torch.utils.data import Dataset, DataLoader
    from transformers import (
        AutoTokenizer,
        AutoModelForTokenClassification,
        TrainingArguments,
        Trainer,
        DataCollatorForTokenClassification
    )
    from sklearn.model_selection import train_test_split
    import numpy as np
    TRAINING_AVAILABLE = True
except ImportError as e:
    TRAINING_AVAILABLE = False
    MISSING_IMPORT = str(e)


# ============================================================================
# CONFIGURAÇÕES
# ============================================================================

# Mapeamento de labels para IDs
LABEL2ID = {
    "O": 0,
    "B-PER": 1,
    "I-PER": 2,
    "B-CPF": 3,
    "I-CPF": 4,
    "B-PHONE": 5,
    "I-PHONE": 6,
    "B-EMAIL": 7,
    "I-EMAIL": 8,
    "B-CEP": 9,
    "I-CEP": 10,
    "B-CNPJ": 11,
    "I-CNPJ": 12,
    "B-DATE": 13,
    "I-DATE": 14,
}

ID2LABEL = {v: k for k, v in LABEL2ID.items()}


# ============================================================================
# DATASET
# ============================================================================

class PIIDataset(Dataset):
    """Dataset para treinamento de NER com dados pessoais."""
    
    def __init__(
        self,
        data: List[Dict],
        tokenizer,
        max_length: int = 128
    ):
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        item = self.data[idx]
        text = item['text']
        entities = item.get('entities', [])
        
        # Tokeniza
        encoding = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_length,
            padding='max_length',
            return_offsets_mapping=True,
            return_tensors='pt'
        )
        
        # Cria labels
        labels = self._create_labels(
            text,
            entities,
            encoding['offset_mapping'][0].tolist()
        )
        
        return {
            'input_ids': encoding['input_ids'].squeeze(),
            'attention_mask': encoding['attention_mask'].squeeze(),
            'labels': torch.tensor(labels)
        }
    
    def _create_labels(
        self,
        text: str,
        entities: List[Dict],
        offset_mapping: List[Tuple[int, int]]
    ) -> List[int]:
        """Cria labels para cada token baseado nas entidades."""
        labels = [LABEL2ID["O"]] * len(offset_mapping)
        
        for entity in entities:
            entity_start = entity.get('start', 0)
            entity_end = entity.get('end', 0)
            entity_type = entity.get('type', 'PER')
            
            # Mapeia tipo para label
            if 'CPF' in entity_type:
                b_label = LABEL2ID.get("B-CPF", 0)
                i_label = LABEL2ID.get("I-CPF", 0)
            elif 'PHONE' in entity_type or 'TELEFONE' in entity_type:
                b_label = LABEL2ID.get("B-PHONE", 0)
                i_label = LABEL2ID.get("I-PHONE", 0)
            elif 'EMAIL' in entity_type:
                b_label = LABEL2ID.get("B-EMAIL", 0)
                i_label = LABEL2ID.get("I-EMAIL", 0)
            elif 'CEP' in entity_type:
                b_label = LABEL2ID.get("B-CEP", 0)
                i_label = LABEL2ID.get("I-CEP", 0)
            elif 'CNPJ' in entity_type:
                b_label = LABEL2ID.get("B-CNPJ", 0)
                i_label = LABEL2ID.get("I-CNPJ", 0)
            elif 'DATA' in entity_type or 'DATE' in entity_type:
                b_label = LABEL2ID.get("B-DATE", 0)
                i_label = LABEL2ID.get("I-DATE", 0)
            else:
                b_label = LABEL2ID.get("B-PER", 0)
                i_label = LABEL2ID.get("I-PER", 0)
            
            # Atribui labels aos tokens
            is_first = True
            for idx, (start, end) in enumerate(offset_mapping):
                if start == end:  # Token especial
                    continue
                
                if start >= entity_start and end <= entity_end:
                    if is_first:
                        labels[idx] = b_label
                        is_first = False
                    else:
                        labels[idx] = i_label
        
        return labels


# ============================================================================
# MÉTRICAS
# ============================================================================

def compute_metrics(eval_pred):
    """Calcula métricas de avaliação."""
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=2)
    
    # Remove padding (-100)
    true_predictions = [
        [ID2LABEL[p] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]
    true_labels = [
        [ID2LABEL[l] for l in label if l != -100]
        for label in labels
    ]
    
    # Calcula métricas simples
    correct = 0
    total = 0
    for preds, labs in zip(true_predictions, true_labels):
        for p, l in zip(preds, labs):
            total += 1
            if p == l:
                correct += 1
    
    accuracy = correct / total if total > 0 else 0
    
    return {
        'accuracy': accuracy,
    }


# ============================================================================
# TREINAMENTO
# ============================================================================

def load_training_data(file_path: str) -> List[Dict]:
    """Carrega dados de treinamento."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, dict):
        if 'data' in data:
            return data['data']
        elif 'train' in data:
            return data['train']
    
    return data


def train_model(
    train_data: List[Dict],
    val_data: List[Dict],
    output_dir: str,
    model_name: str = "neuralmind/bert-base-portuguese-cased",
    epochs: int = 3,
    batch_size: int = 16,
    learning_rate: float = 2e-5
):
    """
    Treina o modelo de NER.
    
    Args:
        train_data: Dados de treinamento
        val_data: Dados de validação
        output_dir: Diretório de saída
        model_name: Nome do modelo base
        epochs: Número de épocas
        batch_size: Tamanho do batch
        learning_rate: Taxa de aprendizado
    """
    print(f"\n🔧 Carregando modelo base: {model_name}")
    
    # Carrega tokenizer e modelo
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForTokenClassification.from_pretrained(
        model_name,
        num_labels=len(LABEL2ID),
        id2label=ID2LABEL,
        label2id=LABEL2ID
    )
    
    print(f"   ✓ Modelo carregado ({model.num_parameters():,} parâmetros)")
    
    # Cria datasets
    print("\n📊 Preparando datasets...")
    train_dataset = PIIDataset(train_data, tokenizer)
    val_dataset = PIIDataset(val_data, tokenizer)
    print(f"   ✓ Treino: {len(train_dataset)} exemplos")
    print(f"   ✓ Validação: {len(val_dataset)} exemplos")
    
    # Configura treinamento
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        learning_rate=learning_rate,
        weight_decay=0.01,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        logging_dir=f"{output_dir}/logs",
        logging_steps=100,
        report_to="none",  # Desabilita wandb/tensorboard
    )
    
    # Data collator
    data_collator = DataCollatorForTokenClassification(tokenizer)
    
    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )
    
    # Treina
    print(f"\n🚀 Iniciando treinamento ({epochs} épocas)...")
    trainer.train()
    
    # Salva modelo final
    print(f"\n💾 Salvando modelo em: {output_dir}")
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)
    
    # Salva configurações
    config = {
        'model_name': model_name,
        'epochs': epochs,
        'batch_size': batch_size,
        'learning_rate': learning_rate,
        'train_size': len(train_data),
        'val_size': len(val_data),
        'labels': LABEL2ID,
        'trained_at': datetime.now().isoformat()
    }
    
    with open(f"{output_dir}/training_config.json", 'w') as f:
        json.dump(config, f, indent=2)
    
    print("   ✓ Modelo salvo com sucesso")
    
    return trainer


def main():
    parser = argparse.ArgumentParser(
        description='Treina modelo de NER para detecção de PII'
    )
    parser.add_argument(
        '--data', '-d',
        required=True,
        help='Arquivo JSON com dados de treinamento'
    )
    parser.add_argument(
        '--output', '-o',
        default='models/piiguardian-ner',
        help='Diretório de saída para o modelo'
    )
    parser.add_argument(
        '--model', '-m',
        default='neuralmind/bert-base-portuguese-cased',
        help='Modelo base para fine-tuning'
    )
    parser.add_argument(
        '--epochs', '-e',
        type=int,
        default=3,
        help='Número de épocas de treinamento'
    )
    parser.add_argument(
        '--batch-size', '-b',
        type=int,
        default=16,
        help='Tamanho do batch'
    )
    parser.add_argument(
        '--learning-rate', '-lr',
        type=float,
        default=2e-5,
        help='Taxa de aprendizado'
    )
    parser.add_argument(
        '--val-split',
        type=float,
        default=0.1,
        help='Proporção para validação'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("PIIGuardian - Treinamento de Modelo NER")
    print("=" * 70)
    
    # Verifica dependências
    if not TRAINING_AVAILABLE:
        print(f"\n❌ Dependências de treinamento não disponíveis!")
        print(f"   Erro: {MISSING_IMPORT}")
        print("\n   Instale com: pip install torch transformers scikit-learn")
        sys.exit(1)
    
    # Verifica GPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"\n🖥️  Device: {device}")
    if device == "cuda":
        print(f"   GPU: {torch.cuda.get_device_name(0)}")
    
    # Carrega dados
    print(f"\n📂 Carregando dados de: {args.data}")
    data = load_training_data(args.data)
    print(f"   ✓ {len(data)} exemplos carregados")
    
    # Split treino/validação
    train_data, val_data = train_test_split(
        data,
        test_size=args.val_split,
        random_state=42
    )
    
    # Cria diretório de saída
    Path(args.output).mkdir(parents=True, exist_ok=True)
    
    # Treina
    trainer = train_model(
        train_data=train_data,
        val_data=val_data,
        output_dir=args.output,
        model_name=args.model,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate
    )
    
    # Avaliação final
    print("\n📊 Avaliação final:")
    metrics = trainer.evaluate()
    for key, value in metrics.items():
        print(f"   {key}: {value:.4f}")
    
    print()
    print("=" * 70)
    print("✅ Treinamento concluído com sucesso!")
    print(f"   Modelo salvo em: {args.output}")
    print("=" * 70)


if __name__ == "__main__":
    main()
