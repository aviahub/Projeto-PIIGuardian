================================================================================
                    EXEMPLOS DE TESTE - PIIGuardian
================================================================================

Este diretório contém exemplos de entrada e saída para demonstrar o 
funcionamento do PIIGuardian.

ARQUIVOS:
---------

1. AMOSTRA_ENTRADA.json
   - 10 pedidos de acesso à informação simulados
   - Formato compatível com e-SIC
   - Mistura de pedidos COM e SEM dados pessoais

2. AMOSTRA_SAIDA.json
   - Resultado do processamento pelo PIIGuardian
   - Classificação de cada pedido (PÚBLICO / NÃO PÚBLICO)
   - Entidades detectadas com tipo, valor e confiança
   - Métricas de tempo de processamento

COMO REPRODUZIR:
----------------

1. Navegue até a pasta do projeto PIIGuardian
2. Execute o comando:

   python main.py --file Exemplos_de_Teste/AMOSTRA_ENTRADA.json --output resultado.json

3. Compare o arquivo resultado.json com AMOSTRA_SAIDA.json

RESULTADOS ESPERADOS:
---------------------

- Total de pedidos: 10
- Pedidos COM dados pessoais: 5 (classificados como NÃO PÚBLICO)
- Pedidos SEM dados pessoais: 5 (classificados como PÚBLICO)
- Total de entidades detectadas: 15

TIPOS DE ENTIDADES DETECTADAS:
------------------------------

- NOME: 3 ocorrências
- CPF: 2 ocorrências
- CNPJ: 1 ocorrência
- TELEFONE: 2 ocorrências
- EMAIL: 2 ocorrências
- CEP: 1 ocorrência
- RG: 1 ocorrência
- ENDERECO: 1 ocorrência
- DATA_NASCIMENTO: 1 ocorrência

================================================================================
Desenvolvido por Aviahub - 1º Hackathon em Controle Social da CGDF
================================================================================
