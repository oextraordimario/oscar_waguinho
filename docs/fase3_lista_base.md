# Fase 3 - Lista Base

## Resultado esperado
- Linhas extraidas: `487`
- Vencedores marcados: `98`
- Decadas encontradas: `1920s, 1930s, 1940s, 1950s, 1960s, 1970s, 1980s, 1990s, 2000s, 2010s, 2020s`

## Colunas exportadas
- `decade`
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

## Observacoes
- `ano_filme_raw` preserva o valor original da tabela, inclusive casos como `1927/28`.
- `ano_filme` guarda o primeiro ano numerico encontrado para facilitar etapas posteriores.
- `numero_cerimonia` e `url_cerimonia` sao extraidos do link da propria tabela principal.
- A normalizacao por `rowspan` permite carregar corretamente linhas de multiplos filmes e empates.

## Amostra
- `1927 / 28 (1st)` | `1` | `Emil Jannings` | `The Last Command` | vencedor=`True`
- `1927 / 28 (1st)` | `1` | `Emil Jannings` | `The Way of All Flesh` | vencedor=`True`
- `1927 / 28 (1st)` | `1` | `Richard Barthelmess` | `The Noose` | vencedor=`False`
- `1927 / 28 (1st)` | `1` | `Richard Barthelmess` | `The Patent Leather Kid` | vencedor=`False`
- `1927 / 28 (1st)` | `1` | `Charlie Chaplin` | `The Circus` | vencedor=`False`
