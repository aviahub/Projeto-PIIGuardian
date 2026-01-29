#!/usr/bin/env python3
"""
Gerador de Dados Sintéticos para Testes
=======================================

Gera dados sintéticos para treino e teste do detector PIIGuardian,
incluindo textos com e sem dados pessoais em formatos variados.

Uso:
    python data/synthetic_generator.py --size 10000 --output dados_treino.json
    python data/synthetic_generator.py --size 1000 --with-labels --output dados_teste.json

Autor: Equipe PIIGuardian
"""

import argparse
import json
import random
import string
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict


# ============================================================================
# DADOS BASE PARA GERAÇÃO
# ============================================================================

# Nomes comuns brasileiros
FIRST_NAMES_MALE = [
    "João", "Pedro", "Lucas", "Gabriel", "Rafael", "Mateus", "Bruno", "Carlos",
    "Daniel", "Felipe", "Gustavo", "Henrique", "Igor", "José", "Leonardo",
    "Marcos", "Nicolas", "Paulo", "Ricardo", "Thiago", "Victor", "William"
]

FIRST_NAMES_FEMALE = [
    "Maria", "Ana", "Juliana", "Fernanda", "Camila", "Amanda", "Bruna", "Carolina",
    "Daniela", "Eduarda", "Fabiana", "Gabriela", "Helena", "Isabela", "Julia",
    "Larissa", "Leticia", "Mariana", "Natalia", "Patricia", "Raquel", "Vanessa"
]

LAST_NAMES = [
    "Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves",
    "Pereira", "Lima", "Gomes", "Costa", "Ribeiro", "Martins", "Carvalho",
    "Almeida", "Lopes", "Soares", "Fernandes", "Vieira", "Barbosa", "Rocha",
    "Dias", "Nascimento", "Andrade", "Moreira", "Nunes", "Marques", "Machado"
]

# DDDs válidos
VALID_DDDS = [
    11, 12, 13, 14, 15, 16, 17, 18, 19,  # SP
    21, 22, 24, 27, 28,                   # RJ/ES
    31, 32, 33, 34, 35, 37, 38,          # MG
    41, 42, 43, 44, 45, 46, 47, 48, 49,  # PR/SC
    51, 53, 54, 55,                       # RS
    61, 62, 63, 64, 65, 66, 67, 68, 69,  # Centro-Oeste/Norte
    71, 73, 74, 75, 77, 79,              # BA/SE
    81, 82, 83, 84, 85, 86, 87, 88, 89,  # Nordeste
    91, 92, 93, 94, 95, 96, 97, 98, 99   # Norte
]

# Domínios de email comuns
EMAIL_DOMAINS = [
    "gmail.com", "hotmail.com", "yahoo.com.br", "outlook.com", "uol.com.br",
    "terra.com.br", "bol.com.br", "ig.com.br", "globo.com", "live.com"
]

# Templates de pedidos de acesso à informação
TEMPLATES_WITH_PII = [
    "Solicito acesso às informações referentes ao processo. Meus dados: CPF {cpf}, telefone {phone}.",
    "Eu, {name}, portador do CPF {cpf}, venho solicitar esclarecimentos sobre o protocolo em questão.",
    "Gostaria de obter cópia dos documentos. Para contato: {email} ou telefone {phone}.",
    "Requeiro informações sobre meu cadastro. Email: {email}, CPF: {cpf}.",
    "Solicito providências urgentes. Dados para contato: Sr(a). {name}, celular {phone}.",
    "Prezados, necessito de informações. Meu CPF é {cpf} e moro no CEP {cep}.",
    "Venho por meio desta solicitar. Contato: {name}, {phone}, {email}.",
    "Peço análise do meu pedido. CPF: {cpf}, Telefone: {phone}, Email: {email}.",
    "Solicito urgência na resposta. Dados: {name}, CPF {cpf}, residente no CEP {cep}.",
    "Para fins de cadastro, informo: Nome: {name}, CPF: {cpf}, Telefone: {phone}.",
]

TEMPLATES_WITHOUT_PII = [
    "Solicito informações sobre o andamento do processo administrativo.",
    "Gostaria de saber quais documentos são necessários para dar entrada no pedido.",
    "Venho por meio desta requerer esclarecimentos sobre a legislação vigente.",
    "Prezados, qual o prazo para análise dos processos protocolados?",
    "Solicito informações sobre os serviços disponíveis para a população.",
    "Gostaria de obter informações sobre o horário de funcionamento do órgão.",
    "Peço orientação sobre como proceder para solicitar o serviço.",
    "Qual é o procedimento para dar entrada em um recurso administrativo?",
    "Solicito informações gerais sobre os programas de governo disponíveis.",
    "Venho requerer cópia de normativas e regulamentos vigentes.",
    "Agradeço a atenção e aguardo retorno.",
    "Desde já agradeço a colaboração.",
    "Atenciosamente, aguardo resposta.",
]


# ============================================================================
# GERADORES DE DADOS
# ============================================================================

def generate_cpf(valid: bool = True) -> Tuple[str, str]:
    """
    Gera um CPF (válido ou inválido).
    
    Returns:
        Tupla (cpf_formatado, cpf_raw)
    """
    if valid:
        # Gera 9 dígitos aleatórios
        digits = [random.randint(0, 9) for _ in range(9)]
        
        # Calcula primeiro dígito verificador
        sum1 = sum(d * w for d, w in zip(digits, range(10, 1, -1)))
        d1 = (sum1 * 10 % 11) % 10
        digits.append(d1)
        
        # Calcula segundo dígito verificador
        sum2 = sum(d * w for d, w in zip(digits, range(11, 1, -1)))
        d2 = (sum2 * 10 % 11) % 10
        digits.append(d2)
    else:
        # CPF inválido
        digits = [random.randint(0, 9) for _ in range(11)]
    
    cpf_raw = ''.join(str(d) for d in digits)
    cpf_formatted = f"{cpf_raw[:3]}.{cpf_raw[3:6]}.{cpf_raw[6:9]}-{cpf_raw[9:]}"
    
    return cpf_formatted, cpf_raw


def generate_phone(mobile: bool = True, formatted: bool = True) -> str:
    """Gera um número de telefone brasileiro."""
    ddd = random.choice(VALID_DDDS)
    
    if mobile:
        # Celular: 9XXXX-XXXX
        number = f"9{random.randint(1000, 9999)}{random.randint(1000, 9999)}"
    else:
        # Fixo: [2-5]XXX-XXXX
        first = random.randint(2, 5)
        number = f"{first}{random.randint(100, 999)}{random.randint(1000, 9999)}"
    
    if formatted:
        if mobile:
            return f"({ddd}) {number[:5]}-{number[5:]}"
        else:
            return f"({ddd}) {number[:4]}-{number[4:]}"
    else:
        return f"{ddd}{number}"


def generate_email(name: str = None) -> str:
    """Gera um endereço de email."""
    if name:
        local = name.lower().replace(' ', '.').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('ã', 'a').replace('õ', 'o').replace('ç', 'c')
    else:
        local = ''.join(random.choices(string.ascii_lowercase, k=random.randint(5, 10)))
    
    # Adiciona números aleatórios às vezes
    if random.random() < 0.3:
        local += str(random.randint(1, 999))
    
    domain = random.choice(EMAIL_DOMAINS)
    return f"{local}@{domain}"


def generate_cep(formatted: bool = True) -> str:
    """Gera um CEP brasileiro."""
    # Primeiro dígito indica a região
    first = random.randint(0, 9)
    rest = random.randint(1000000, 9999999)
    cep = f"{first}{rest:07d}"[:8]
    
    if formatted:
        return f"{cep[:5]}-{cep[5:]}"
    return cep


def generate_name() -> str:
    """Gera um nome brasileiro completo."""
    if random.random() < 0.5:
        first = random.choice(FIRST_NAMES_MALE)
    else:
        first = random.choice(FIRST_NAMES_FEMALE)
    
    # 1 a 3 sobrenomes
    num_last = random.randint(1, 3)
    last_names = random.sample(LAST_NAMES, num_last)
    
    return f"{first} {' '.join(last_names)}"


def generate_cnpj(valid: bool = True) -> Tuple[str, str]:
    """Gera um CNPJ."""
    if valid:
        base = [random.randint(0, 9) for _ in range(8)] + [0, 0, 0, 1]
        
        # Primeiro dígito
        weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        sum1 = sum(d * w for d, w in zip(base, weights1))
        d1 = 0 if sum1 % 11 < 2 else 11 - sum1 % 11
        base.append(d1)
        
        # Segundo dígito
        weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        sum2 = sum(d * w for d, w in zip(base, weights2))
        d2 = 0 if sum2 % 11 < 2 else 11 - sum2 % 11
        base.append(d2)
    else:
        base = [random.randint(0, 9) for _ in range(14)]
    
    cnpj_raw = ''.join(str(d) for d in base)
    cnpj_formatted = f"{cnpj_raw[:2]}.{cnpj_raw[2:5]}.{cnpj_raw[5:8]}/{cnpj_raw[8:12]}-{cnpj_raw[12:]}"
    
    return cnpj_formatted, cnpj_raw


def generate_date(min_year: int = 1950, max_year: int = 2005) -> str:
    """Gera uma data de nascimento."""
    year = random.randint(min_year, max_year)
    month = random.randint(1, 12)
    day = random.randint(1, 28)  # Simplificado para evitar problemas
    
    formats = [
        f"{day:02d}/{month:02d}/{year}",
        f"{day:02d}-{month:02d}-{year}",
        f"{year}-{month:02d}-{day:02d}",
    ]
    return random.choice(formats)


# ============================================================================
# GERADOR DE REGISTROS
# ============================================================================

@dataclass
class SyntheticRecord:
    """Registro sintético para teste."""
    id: str
    text: str
    has_pii: bool
    entities: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SyntheticDataGenerator:
    """Gerador de dados sintéticos para teste."""
    
    def __init__(self, seed: int = None):
        if seed:
            random.seed(seed)
        self.counter = 0
    
    def generate_record_with_pii(self) -> SyntheticRecord:
        """Gera um registro COM dados pessoais."""
        self.counter += 1
        
        # Gera dados
        name = generate_name()
        cpf, cpf_raw = generate_cpf(valid=True)
        phone = generate_phone(mobile=random.random() < 0.7)
        email = generate_email(name)
        cep = generate_cep()
        
        # Escolhe template
        template = random.choice(TEMPLATES_WITH_PII)
        text = template.format(
            name=name,
            cpf=cpf,
            phone=phone,
            email=email,
            cep=cep
        )
        
        # Monta entidades esperadas
        entities = []
        
        if '{cpf}' in template:
            start = text.find(cpf)
            if start >= 0:
                entities.append({
                    'type': 'CPF',
                    'value': cpf,
                    'start': start,
                    'end': start + len(cpf)
                })
        
        if '{phone}' in template:
            start = text.find(phone)
            if start >= 0:
                entities.append({
                    'type': 'TELEFONE',
                    'value': phone,
                    'start': start,
                    'end': start + len(phone)
                })
        
        if '{email}' in template:
            start = text.find(email)
            if start >= 0:
                entities.append({
                    'type': 'EMAIL',
                    'value': email,
                    'start': start,
                    'end': start + len(email)
                })
        
        if '{cep}' in template:
            start = text.find(cep)
            if start >= 0:
                entities.append({
                    'type': 'CEP',
                    'value': cep,
                    'start': start,
                    'end': start + len(cep)
                })
        
        if '{name}' in template:
            start = text.find(name)
            if start >= 0:
                entities.append({
                    'type': 'NOME_PESSOA',
                    'value': name,
                    'start': start,
                    'end': start + len(name)
                })
        
        return SyntheticRecord(
            id=f"pii_{self.counter:06d}",
            text=text,
            has_pii=True,
            entities=entities
        )
    
    def generate_record_without_pii(self) -> SyntheticRecord:
        """Gera um registro SEM dados pessoais."""
        self.counter += 1
        
        text = random.choice(TEMPLATES_WITHOUT_PII)
        
        return SyntheticRecord(
            id=f"clean_{self.counter:06d}",
            text=text,
            has_pii=False,
            entities=[]
        )
    
    def generate_dataset(
        self,
        size: int,
        pii_ratio: float = 0.7
    ) -> List[SyntheticRecord]:
        """
        Gera dataset sintético.
        
        Args:
            size: Número total de registros
            pii_ratio: Proporção de registros com PII (0.0 a 1.0)
            
        Returns:
            Lista de registros sintéticos
        """
        records = []
        num_with_pii = int(size * pii_ratio)
        
        # Gera registros com PII
        for _ in range(num_with_pii):
            records.append(self.generate_record_with_pii())
        
        # Gera registros sem PII
        for _ in range(size - num_with_pii):
            records.append(self.generate_record_without_pii())
        
        # Embaralha
        random.shuffle(records)
        
        return records


def main():
    parser = argparse.ArgumentParser(
        description='Gera dados sintéticos para teste do PIIGuardian'
    )
    parser.add_argument(
        '--size', '-s',
        type=int,
        default=1000,
        help='Número de registros a gerar'
    )
    parser.add_argument(
        '--output', '-o',
        required=True,
        help='Arquivo de saída (JSON)'
    )
    parser.add_argument(
        '--pii-ratio', '-r',
        type=float,
        default=0.7,
        help='Proporção de registros com PII (0.0 a 1.0)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        help='Seed para reprodutibilidade'
    )
    parser.add_argument(
        '--with-labels',
        action='store_true',
        help='Inclui labels para avaliação'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("PIIGuardian - Gerador de Dados Sintéticos")
    print("=" * 60)
    print()
    
    # Gera dados
    print(f"🔄 Gerando {args.size} registros (PII ratio: {args.pii_ratio})...")
    generator = SyntheticDataGenerator(seed=args.seed)
    records = generator.generate_dataset(args.size, args.pii_ratio)
    print(f"   ✓ {len(records)} registros gerados")
    
    # Estatísticas
    with_pii = sum(1 for r in records if r.has_pii)
    total_entities = sum(len(r.entities) for r in records)
    
    print(f"\n📊 Estatísticas:")
    print(f"   - Com PII: {with_pii} ({with_pii/len(records)*100:.1f}%)")
    print(f"   - Sem PII: {len(records) - with_pii} ({(len(records)-with_pii)/len(records)*100:.1f}%)")
    print(f"   - Total de entidades: {total_entities}")
    
    # Salva
    print(f"\n💾 Salvando em: {args.output}")
    
    output_data = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'size': len(records),
            'pii_ratio': args.pii_ratio,
            'seed': args.seed,
            'with_labels': args.with_labels
        },
        'statistics': {
            'total_records': len(records),
            'records_with_pii': with_pii,
            'records_without_pii': len(records) - with_pii,
            'total_entities': total_entities
        },
        'data': [r.to_dict() for r in records]
    }
    
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print("   ✓ Arquivo salvo com sucesso")
    print()
    print("=" * 60)
    print("✅ Geração concluída!")


if __name__ == "__main__":
    main()
