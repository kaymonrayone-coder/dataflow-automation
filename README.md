# dataflow-automation

Automação de limpeza, validação e consolidação de arquivos CSV e Excel em Python.
Projeto open source com CLI e API Python, pensado para rotinas reproduzíveis de dados tabulares.

## Funcionalidades

- Importa CSV UTF-8 e XLSX (primeira aba ou aba selecionada).
- Preserva campos como texto, incluindo códigos com zeros à esquerda armazenados como texto.
- Normaliza cabeçalhos (acentos, espaços e pontuação), remove espaços nas extremidades e linhas vazias.
- Valida campos obrigatórios e números finitos; separa registros inválidos com os motivos.
- Consolida por união de colunas; verifica colunas configuradas em cada arquivo.
- Remove duplicatas globais ou por chave, mantendo a primeira ocorrência válida na ordem dos arquivos.
- Exporta CSV ou XLSX, com origem do registro e relatório JSON de contagens.
- Impede sobrescrever entradas e exige opção explícita para substituir saídas existentes.
- Neutraliza textos que possam ser interpretados como fórmulas ao exportar planilhas.

## Instalação

Requer Python 3.10 ou superior. No diretório do projeto:

```bash
python -m venv .venv
# Linux / macOS
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e .
```

As dependências também estão em `requirements.txt`; a instalação acima registra o comando `dataflow`.
Não há serviço externo, credenciais, telemetria ou acesso à rede durante o processamento.

## Demonstração

Os arquivos em `examples/input/` são inteiramente fictícios.

```bash
dataflow examples/input/orders_a.csv examples/input/orders_b.csv -o outputs/orders.xlsx --required order_id product quantity --numeric quantity --dedupe-on order_id
```

Resultado esperado: 7 registros lidos, 2 inválidos, 1 duplicata removida e 4 registros consolidados.
São gerados:

| Arquivo | Conteúdo |
| --- | --- |
| `outputs/orders.xlsx` | Registros válidos, sem duplicatas e com `df_source` |
| `outputs/orders.rejected.csv` | Registros rejeitados, origem e `df_errors` |
| `outputs/orders.report.json` | Contagens globais e por arquivo, colunas de deduplicação |

Para repetir, acrescente `--overwrite`. As contagens satisfazem:
`rows_read = blank_rows_removed + invalid_rows + duplicates_removed + rows_written`.
Linhas físicas vazias ignoradas pelo leitor CSV não entram em `rows_read`.

### CSV com ponto e vírgula e seleção de aba

```bash
dataflow dados.csv -o outputs/dados.csv --delimiter ';'
dataflow dados.xlsx -o outputs/dados.csv --sheet Vendas --required codigo
```

Regras usam nomes de colunas **após** normalização: `Código Produto` vira `codigo_produto`.
Campos vazios são ausentes; textos como `NA` e `NULL` permanecem literais.
Validação numérica aceita ponto decimal; não converte nem reformata os valores.
Campos numéricos vazios só são rejeitados se também estiverem em `--required`.
O processo retorna código 0 quando conclui, inclusive com linhas rejeitadas, e 1 em erro operacional/configuração.
Use o relatório para decidir se linhas rejeitadas devem interromper sua rotina.

### API Python

```python
from dataflow_automation import run_pipeline

report = run_pipeline(
    ["examples/input/orders_a.csv", "examples/input/orders_b.csv"],
    "outputs/orders.csv",
    required=["order_id", "product", "quantity"],
    numeric=["quantity"],
    dedupe_on=["order_id"],
)
print(report)
```

## Arquitetura

Pacote em `src/dataflow_automation/`:

| Módulo | Responsabilidade |
| --- | --- |
| `io.py` | Leitura, exportação e exceção de domínio |
| `cleaning.py` | Normalização de cabeçalhos e valores |
| `validation.py` | Regras e classificação de registros |
| `pipeline.py` | Consolidação, deduplicação e relatório |
| `cli.py` | Argumentos e mensagens de erro |

As funções são independentes da CLI. Não há banco de dados nem infraestrutura necessária.

## Desenvolvimento e testes

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
python -m build
```

Os testes cobrem consolidação CSV/XLSX, zeros à esquerda, rejeições, colisões de cabeçalho,
colunas obrigatórias por arquivo, duplicatas, união de esquemas, segurança da exportação,
proteção de entradas/saídas, formatos inválidos e CLI. GitHub Actions está configurado para
Python 3.10, 3.12 e 3.13; a execução local não substitui a confirmação da matriz remota.

## Limitações

- Processamento em memória; arquivos grandes exigem RAM proporcional ao volume.
- Não suporta XLS antigo, macros, estilos, imagens, células mescladas ou múltiplas abas em uma execução.
- Fórmulas de entrada não são calculadas; XLSX depende dos valores armazenados pelo aplicativo de origem.
- Não recupera zeros representados apenas por formatação visual de células numéricas.
- Não interpreta datas nem números com vírgula decimal; prepare esses campos explicitamente.
- Cabeçalhos vazios ou que colidam após normalização interrompem o fluxo; `df_` é reservado.
- Exportação acrescenta apóstrofo a valores iniciados por caracteres de fórmula, inclusive números negativos em texto.
- Escrita dos três artefatos não é uma transação: falhas de disco podem deixar uma saída parcial.
- `df_source` usa somente o nome do arquivo, não o caminho completo; nomes iguais podem ter a mesma origem exibida.

## Roadmap

- Configuração declarativa de regras e conversões por coluna.
- Validação de datas e formatos numéricos regionais.
- Escrita transacional e estratégia de streaming para grandes volumes.
- Política configurável de falha em registros rejeitados.

## Contribuição e licença

Leia [CONTRIBUTING.md](CONTRIBUTING.md). Licença [MIT](LICENSE).
Não envie dados pessoais, arquivos corporativos, credenciais ou amostras confidenciais em issues ou pull requests.
