# Fase 2 - Mapa das Fontes

## Escopo
Inspecao estrutural das paginas-fonte para confirmar como extrair dados da pagina principal, das paginas dos atores e das paginas de cerimonia.

## Pagina principal
- URL: `https://en.wikipedia.org/wiki/Academy_Award_for_Best_Actor`
- Secao-alvo: `Winners and nominees`
- Estrutura observada: uma tabela `wikitable` por decada dentro da secao.
- Cabecalhos-base identificados: `Year`, `Actor`, `Role(s)`, `Film`, `Ref.`
- Marcador de vencedor: marcador visual na celula do ator, conforme a legenda da tabela.
- Observacoes criticas:
  - O ano exibido na tabela segue a convencao da Academy e costuma representar o ano do filme, nao o ano da cerimonia.
  - As primeiras cerimonias tem linhas multi-filme, empates e indicacoes com mais de um papel por linha.
  - A normalizacao da tabela vai precisar carregar contexto da linha anterior em alguns casos.

## Paginas de cerimonia
- Exemplo validado: `https://en.wikipedia.org/wiki/96th_Academy_Awards`
- Estrutura observada: a infobox da cerimonia contem o campo `Date`.
- Regra recomendada: extrair o ultimo ano do campo `Date` para preencher `ano_cerimonia`.
- Exemplo validado: `Date March 10, 2024` -> `ano_cerimonia = 2024`

## Paginas de atores
### Caso 1: ator nascido nos EUA
- URL: `https://en.wikipedia.org/wiki/Adrien_Brody`
- Short description: `American actor (born 1973)`
- `Born`: `New York City, U.S.`
- `Citizenship`: ausente
- Implicacao: `Born` e suficiente para classificar como `EUA`; `Citizenship` nao pode ser assumido como campo obrigatorio.

### Caso 2: ator europeu
- URL: `https://en.wikipedia.org/wiki/Cillian_Murphy`
- Short description: `Irish actor (born 1976)`
- `Born`: `Douglas, Cork, Ireland`
- `Citizenship`: ausente
- Implicacao: novamente, `Born` e o campo mais estavel para classificacao.

### Caso 3: ator latino com dupla cidadania
- URL: `https://en.wikipedia.org/wiki/Anthony_Quinn`
- Short description: `American actor (1915-2001)`
- `Born`: `Chihuahua City, Chihuahua, Mexico`
- `Citizenship`: `Mexico`, `United States`
- Implicacao: a descricao curta pode conflitar com o pais de nascimento; para analise, a regra deve seguir `pais_nascimento`.

### Caso 4: Puerto Rico sem citizenship explicita
- URL: `https://en.wikipedia.org/wiki/Jose_Ferrer`
- Short description: `Puerto Rican actor and director (1912-1992)`
- `Born`: `San Juan, Puerto Rico`
- `Citizenship`: ausente
- Implicacao: pela regra definida no projeto, `Puerto Rico` deve ser tratado como `EUA`.

### Caso 5: Puerto Rico com multiplas cidadanias
- URL: `https://en.wikipedia.org/wiki/Benicio_del_Toro`
- Short description: `Puerto Rican actor (born 1967)`
- `Born`: `San German, Puerto Rico`
- `Citizenship`: `Spain`, `United States`
- Implicacao: manter `cidadania_raw`, mas classificar por `pais_nascimento`; o projeto tratara `Puerto Rico` como `EUA`.

## Mapa de extracao recomendado
### Pagina principal
- Selecionar a secao `Winners and nominees`.
- Iterar pelas tabelas `wikitable` subsequentes ate o proximo `h2`.
- Para cada linha, capturar:
  - `ano_filme`
  - `numero_cerimonia`
  - `nome_ator`
  - `filme_indicado`
  - `url_ator`
  - `url_filme`
  - `url_cerimonia`
  - `eh_vencedor`
- Tratar excecoes das primeiras cerimonias explicitamente.

### Pagina do ator
- Fonte primaria para classificacao: campo `Born` da infobox.
- Dados brutos complementares: `Citizenship`, short description e texto cru do local de nascimento.
- Fallback: Wikidata quando `Born` faltar, vier ambigua ou nao permitir inferir `pais_nascimento`.

### Pagina da cerimonia
- Fonte primaria: campo `Date` da infobox.
- Regra: extrair o ano da data exibida.

## Entregaveis desta fase
- Script de inspecao: `scripts/fase2_inspecionar_fontes.py`
- Relatorio estrutural: `docs/fase2_mapa_fontes.md`

## Pendencias que ficam para a Fase 3
- Implementar a normalizacao completa das linhas historicas da pagina principal.
- Transformar o mapa de extracao em scraper executavel para popular a planilha.
- Implementar o fallback em Wikidata dentro do pipeline principal.
