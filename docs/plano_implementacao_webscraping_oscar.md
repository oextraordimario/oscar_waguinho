# Planejamento de Implementa??o: Oscar de Melhor Ator

## Objetivo
Construir um pipeline em Python para raspar dados da Wikipedia sobre vencedores e indicados ao Oscar de Melhor Ator, consolidar os dados em planilha e gerar visualiza??es que permitam responder, em etapas, quem s?o os atores "estrangeiros" e, depois, quais deles se enquadram como "latinos".

## Questionamento dos Pressupostos
- `grupo_geral_nacionalidade` com valores `EUA` vs `Estrangeiro` n?o responde sozinho ? pergunta sobre atores latinos.
- A coluna `nacionalidade` n?o ? uma base est?vel o suficiente para classifica??o, porque a Wikipedia varia entre adjetivo no resumo, `citizenship`, local de nascimento e m?ltiplas cidadanias.
- Se a regra de "latino" for "nascido em pa?s latino", ent?o a vari?vel realmente usada para classificar n?o ? `nacionalidade`, e sim `pais_nascimento`.

## Modelagem Definida
Vamos tratar a aba `crua` como realmente crua e audit?vel. Isso significa separar dado bruto de dado derivado e manter rastreabilidade suficiente para revisar casos amb?guos sem depender de inspe??o manual posterior.

### Campos brutos definidos
- `nome_ator`
- `nacionalidade`
- `filme_indicado`
- `ano_filme`
- `numero_cerimonia`
- `ano_cerimonia`
- `url_ator`
- `url_filme`
- `url_cerimonia`
- `eh_vencedor`
- `nacionalidade_raw`
- `cidadania_raw`
- `pais_nascimento`
- `local_nascimento_raw`
- `fonte_classificacao`
- `status_extracao`

### Campos derivados definidos
- `grupo_geral_nacionalidade`
- `grupo_especifico_nacionalidade`

## Regras Definidas
### Regra para `grupo_geral_nacionalidade`
- Usar `pais_nascimento` como base can?nica de classifica??o.
- Se `pais_nascimento = EUA`, classificar como `EUA`.
- Caso contr?rio, classificar como `Estrangeiro`.

### Regra para `grupo_especifico_nacionalidade`
- Derivar de `pais_nascimento`.
- Categorias iniciais definidas: `EUA`, `Latino`, `Europeu`, `Asi?tico`, `Africano`, `Oceania`, `Canadense`, `Outro`.
- Exemplos:
  - `EUA` -> `EUA`
  - `Irlanda` -> `Europeu`
  - `M?xico` -> `Latino`
  - `Brasil` -> `Latino`

### Regra para m?ltiplas nacionalidades/cidadanias
- N?o tentar reduzir o dado bruto para um ?nico valor manualmente.
- Armazenar o texto bruto encontrado em `nacionalidade_raw` e/ou `cidadania_raw`.
- Para agrupamento anal?tico, usar `pais_nascimento` como desempate determin?stico.

Justificativa:
- Essa regra ? est?vel.
- Ela ? compat?vel com seu crit?rio atual para "latino".
- Ela evita decis?es arbitr?rias quando a p?gina traz dupla cidadania ou adjetivos mistos.

Limita??o:
- "Nascido fora dos EUA" n?o ? sin?nimo perfeito de "estrangeiro" em todos os contextos culturais e biogr?ficos. Mesmo assim, ? a regra mais operacional e audit?vel para este projeto.

### Regra para `eh_vencedor`
- Exportar como `TRUE/FALSE`.

### Regra para `Latino`
- Considerar como `Latino` qualquer ator nascido em pa?s soberano da Am?rica Latina.
- `Puerto Rico` ser? tratado como `EUA`.

## Fonte Definida
Usar Wikipedia como fonte principal e Wikidata como fallback para campos biogr?ficos estruturados, especialmente `pais_nascimento` e `cidadania`.

Regra de preced?ncia:
1. Extrair da infobox da Wikipedia.
2. Se faltar ou vier amb?guo, consultar Wikidata.
3. Registrar em `fonte_classificacao` qual origem foi usada.

Justificativa:
- Mant?m o scraping aderente ao escopo original.
- Reduz a fragilidade de depender apenas do HTML da Wikipedia.
- Preserva auditabilidade quando a classifica??o vier de uma fonte auxiliar.

## Fases de Implementa??o
## Fase 1: Fechar contrato de dados
Objetivo:
- Congelar o schema final da aba `crua` e a l?gica de classifica??o.

Atividades:
- Revisar a planilha de refer?ncia atualizada.
- Confirmar os nomes finais das colunas.
- Confirmar o conjunto inicial de categorias para `grupo_especifico_nacionalidade`.
- Confirmar como marcar `eh_vencedor`.

Defini??es fechadas:
- `eh_vencedor` ser? exportado como `TRUE/FALSE`.
- `grupo_especifico_nacionalidade` usar? inicialmente: `EUA`, `Latino`, `Europeu`, `Asi?tico`, `Africano`, `Oceania`, `Canadense`, `Outro`.
- A regra de `Latino` ser?: ator nascido em pa?s soberano da Am?rica Latina.
- `Puerto Rico` ser? tratado como `EUA`.

Entreg?vel:
- Documento de schema e regras aprovado.

Verifica??o humana:
- Conferir se cada coluna tem defini??o clara e sem sobreposi??o.

Verifica??o do agente:
- Validar que todas as colunas necess?rias podem ser preenchidas pelo pipeline.

## Fase 2: Prova de estrutura das p?ginas-fonte
Objetivo:
- Confirmar como extrair dados da p?gina principal e das p?ginas individuais.

Atividades:
- Inspecionar a p?gina `Academy Award for Best Actor`.
- Mapear a tabela ou tabelas que cont?m vencedores e indicados.
- Validar se o link da cerim?nia pode ser usado para obter `ano_cerimonia`.
- Testar um pequeno conjunto de p?ginas de atores com perfis diferentes.

Amostra m?nima sugerida:
- ator nascido nos EUA
- ator europeu
- ator latino
- ator com dados biogr?ficos incompletos

Entreg?vel:
- Mapa de seletores e estrat?gia de parsing.

Verifica??o humana:
- Revisar se os exemplos cobrem os principais casos-limite.

Verifica??o do agente:
- Executar scraping pontual e comparar com a p?gina manualmente.

## Fase 3: Extrair lista base da categoria
Objetivo:
- Gerar uma tabela consolidada com todos os vencedores e indicados.

Atividades:
- Raspar a p?gina principal.
- Normalizar linhas por ator/filme/ano.
- Capturar `nome_ator`, `filme_indicado`, `ano_filme`, `numero_cerimonia`, `url_ator`, `url_filme`, `url_cerimonia`, `eh_vencedor`.

Entreg?vel:
- Dataset intermedi?rio com linhas da categoria.

Verifica??o humana:
- Conferir uma amostra manual contra a p?gina.

Verifica??o do agente:
- Checar contagem de linhas por d?cada e presen?a dos links essenciais.

## Fase 4: Enriquecer dados biogr?ficos
Objetivo:
- Preencher os campos biogr?ficos de cada ator.

Atividades:
- Visitar `url_ator`.
- Extrair `local_nascimento_raw`, `pais_nascimento`, `nacionalidade_raw`, `cidadania_raw`.
- Aplicar fallback no Wikidata quando necess?rio.
- Persistir `status_extracao` e `fonte_classificacao`.

Entreg?vel:
- Aba `crua` preenchida com campos brutos e rastreabilidade da origem.

Verifica??o humana:
- Auditar uma amostra com casos simples e amb?guos.

Verifica??o do agente:
- Gerar relat?rio de quantos registros ficaram sem `pais_nascimento`.

## Fase 5: Derivar classifica??es anal?ticas
Objetivo:
- Popular as colunas de agrupamento usadas na an?lise.

Atividades:
- Aplicar a regra `pais_nascimento = EUA => EUA; sen?o Estrangeiro`.
- Mapear o pa?s para `grupo_especifico_nacionalidade`.
- Separar an?lises de `vencedores` e `indicados`.

Entreg?vel:
- Colunas derivadas consistentes na aba `crua`.

Verifica??o humana:
- Validar manualmente alguns atores conhecidos.

Verifica??o do agente:
- Testes automatizados para regras de classifica??o com casos sint?ticos.

## Fase 6: Montar agrega??es
Objetivo:
- Preencher a aba `agregada`.

Atividades:
- Criar agrega??es por `grupo_geral_nacionalidade`.
- Criar agrega??es por `grupo_especifico_nacionalidade`.
- Separar contagens para `vencedores` e `indicados`.

Defini??o fechada:
- A aba `agregada` deve conter contagens separadas de vencedores e indicados.

Entreg?vel:
- Aba `agregada` pronta para consumo.

Verifica??o humana:
- Conferir se os totais batem com a aba `crua`.

Verifica??o do agente:
- Recalcular agregados a partir do dataframe e comparar com a planilha exportada.

## Fase 7: Gerar visualiza??o
Objetivo:
- Produzir o gr?fico de pizza de refer?ncia e deixar espa?o para gr?ficos futuros.

Atividades:
- Gerar pizza para `EUA` vs `Estrangeiro`.
- Avaliar se pizza continua adequada quando houver mais categorias espec?ficas.
- Exportar imagem no padr?o de `refs/grafico_nacionalidade.png`.

Defini??o fechada:
- O gr?fico principal considerar? apenas vencedores, para manter ader?ncia ao objetivo principal do projeto.

Entreg?vel:
- Arquivo PNG final.

Verifica??o humana:
- Conferir legibilidade, r?tulos e consist?ncia com a tabela agregada.

Verifica??o do agente:
- Validar se os percentuais do gr?fico batem com os agregados.

## Fase 8: Robustez e repetibilidade
Objetivo:
- Garantir que o pipeline possa ser reexecutado sem ajustes manuais.

Atividades:
- Parametrizar URLs e caminhos de sa?da.
- Tratar falhas de request e campos ausentes.
- Salvar logs de scraping.
- Documentar como rodar o projeto do zero.

Conven??o de sa?da definida:
- N?o sobrescrever arquivos de refer?ncia em `refs/`.
- Gerar novos arquivos por fase.
- Conven??o de nomes: `fase1_<nome>`, `fase2_<nome>`, `fase3_<nome>` e assim por diante.
- Exemplo: `fase3_entregavel_tabela.xlsx`, `fase7_grafico_nacionalidade.png`.

Entreg?vel:
- Pipeline repet?vel e documentado.

Verifica??o humana:
- Rodar a partir de um ambiente limpo seguindo a documenta??o.

Verifica??o do agente:
- Execu??o de ponta a ponta sem interven??o manual.

## Decis?es T?cnicas Recomendadas
- Linguagem: Python
- Parsing HTML: `requests` + `beautifulsoup4`
- Tabelas: `pandas`
- Planilha Excel: `openpyxl`
- Gr?ficos: `matplotlib`
- Configura??o de categorias por pa?s: arquivo de mapeamento simples em JSON ou CSV

## Riscos Principais
- Mudan?a na estrutura HTML da Wikipedia.
- P?ginas de atores sem infobox padronizada.
- Casos-limite de pa?s de nascimento e identidade cultural.
- Ambiguidade entre "nacionalidade", "cidadania" e "local de nascimento".

## Estrat?gias de Mitiga??o
- Registrar o dado bruto junto da classifica??o derivada.
- Usar fallback controlado no Wikidata.
- Manter lista expl?cita de pa?ses mapeados para `Latino`.
- Incluir relat?rio de exce??es para revis?o manual.

## Crit?rios de Aceite do Projeto
- A aba `crua` cont?m todos os vencedores e indicados de Melhor Ator.
- Cada linha possui links rastre?veis e campos biogr?ficos audit?veis.
- A aba `agregada` reproduz corretamente os totais da aba `crua`.
- O gr?fico `EUA` vs `Estrangeiro` bate com a agrega??o.
- O pipeline consegue ser executado novamente sem edi??o manual de c?digo.

## Resumo das Decis?es Fechadas
- Fonte principal: Wikipedia.
- Fallback: Wikidata.
- Aba `crua`: audit?vel, com campos brutos e derivados.
- `eh_vencedor`: `TRUE/FALSE`.
- `grupo_especifico_nacionalidade`: `EUA`, `Latino`, `Europeu`, `Asi?tico`, `Africano`, `Oceania`, `Canadense`, `Outro`.
- Regra de `Latino`: nascido em pa?s soberano da Am?rica Latina.
- `Puerto Rico`: tratar como `EUA`.
- Arquivos de sa?da: sempre novos, com prefixo da fase.
- Gr?fico principal: somente vencedores.

## Pr?ximo Passo Recomendado
Implementar primeiro uma prova de conceito curta com 5 a 10 atores para validar:
- extra??o da p?gina principal
- extra??o de `pais_nascimento`
- regra de classifica??o
- exporta??o para a aba `crua`

Se essa prova de conceito fechar, o restante do pipeline fica muito menos arriscado.
