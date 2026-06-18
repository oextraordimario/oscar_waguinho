# Fase 3 - Implementacao da Lista Base

## Escopo
Implementar o scraper da pagina principal `Academy Award for Best Actor` para gerar a lista-base de vencedores e indicados com links e metadados de cerimonia.

## Abordagem
- Buscar a pagina principal com `requests`.
- Localizar a secao `Winners and nominees`.
- Percorrer cada `wikitable` por decada.
- Expandir `rowspan` e `colspan` para reconstruir linhas completas.
- Extrair, por linha normalizada:
  - `ano_filme_raw`
  - `ano_filme`
  - `numero_cerimonia`
  - `nome_ator`
  - `filme_indicado`
  - `role_raw`
  - `url_ator`
  - `url_filme`
  - `url_cerimonia`
  - `eh_vencedor`
  - `ceremony_label_raw`

## Arquivos desta fase
- Script: `scripts/fase3_extrair_lista_base.py`
- Saida CSV prevista: `output/fase3_lista_base.csv`
- Saida JSON prevista: `output/fase3_lista_base.json`
- Resumo previsto: `docs/fase3_lista_base.md`

## Decisoes tecnicas
- Preservar `ano_filme_raw` porque as primeiras cerimonias usam formatos como `1927/28`.
- Derivar `ano_filme` como o primeiro ano numerico da celula para facilitar agregacoes posteriores.
- Derivar `numero_cerimonia` a partir do link/texto da propria celula do ano.
- Marcar `eh_vencedor` pelos indicadores visuais na celula do ator.

## Limitacoes conhecidas
- A execucao completa do scraper depende de acesso de rede no ambiente local.
- A pagina historica pode ter pequenas variacoes de markup; a estrategia de expansao de `rowspan` foi escolhida para reduzir esse risco.
- O parse das primeiras cerimonias ainda deve ser validado com uma execucao real, porque sao as linhas mais irregulares da tabela.

## Proximo passo
A partir desta base, a Fase 4 pode enriquecer cada ator visitando `url_ator` e cada cerimonia visitando `url_cerimonia`.
