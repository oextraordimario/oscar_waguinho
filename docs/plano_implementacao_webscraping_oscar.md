# Planejamento de Implementação: Oscar de Melhor Ator

## Objetivo
Construir um pipeline em Python para raspar dados da Wikipedia sobre vencedores e indicados ao Oscar de Melhor Ator, consolidar os dados em planilha e gerar visualizações que permitam responder, em etapas, quem são os atores "estrangeiros" e, depois, quais deles se enquadram como "latinos".

## Questionamento dos Pressupostos
- `grupo_geral_nacionalidade` com valores `EUA` vs `Estrangeiro` não responde sozinho à pergunta sobre atores latinos.
- A coluna `nacionalidade` não é uma base estável o suficiente para classificação, porque a Wikipedia varia entre adjetivo no resumo, `citizenship`, local de nascimento e múltiplas cidadanias.
- Se a regra de "latino" for "nascido em país latino", então a variável realmente usada para classificar não é `nacionalidade`, e sim `pais_nascimento`.

## Modelagem Definida
Vamos tratar a aba `crua` como realmente crua e auditável. Isso significa separar dado bruto de dado derivado e manter rastreabilidade suficiente para revisar casos ambíguos sem depender de inspeção manual posterior.

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
- Usar `pais_nascimento` como base canônica de classificação.
- Se `pais_nascimento = EUA`, classificar como `EUA`.
- Caso contrário, classificar como `Estrangeiro`.

### Regra para `grupo_especifico_nacionalidade`
- Derivar de `pais_nascimento`.
- Categorias iniciais definidas: `EUA`, `Latino`, `Europeu`, `Asiático`, `Africano`, `Oceania`, `Canadense`, `Outro`.
- Exemplos:
  - `EUA` -> `EUA`
  - `Irlanda` -> `Europeu`
  - `México` -> `Latino`
  - `Brasil` -> `Latino`

### Regra para múltiplas nacionalidades/cidadanias
- Não tentar reduzir o dado bruto para um único valor manualmente.
- Armazenar o texto bruto encontrado em `nacionalidade_raw` e/ou `cidadania_raw`.
- Para agrupamento analítico, usar `pais_nascimento` como desempate determinístico.

Justificativa:
- Essa regra é estável.
- Ela é compatível com seu critério atual para "latino".
- Ela evita decisões arbitrárias quando a página traz dupla cidadania ou adjetivos mistos.

Limitação:
- "Nascido fora dos EUA" não é sinônimo perfeito de "estrangeiro" em todos os contextos culturais e biográficos. Mesmo assim, é a regra mais operacional e auditável para este projeto.

### Regra para `eh_vencedor`
- Exportar como `TRUE/FALSE`.

### Regra para `Latino`
- Considerar como `Latino` qualquer ator nascido em país soberano da América Latina.
- `Puerto Rico` será tratado como `EUA`.

## Fonte Definida
Usar Wikipedia como fonte principal e Wikidata como fallback para campos biográficos estruturados, especialmente `pais_nascimento` e `cidadania`.

Regra de precedência:
1. Extrair da infobox da Wikipedia.
2. Se faltar ou vier ambíguo, consultar Wikidata.
3. Registrar em `fonte_classificacao` qual origem foi usada.

Justificativa:
- Mantém o scraping aderente ao escopo original.
- Reduz a fragilidade de depender apenas do HTML da Wikipedia.
- Preserva auditabilidade quando a classificação vier de uma fonte auxiliar.

## Fases de Implementação
## Fase 1: Fechar contrato de dados
Objetivo:
- Congelar o schema final da aba `crua` e a lógica de classificação.

Atividades:
- Revisar a planilha de referência atualizada.
- Confirmar os nomes finais das colunas.
- Confirmar o conjunto inicial de categorias para `grupo_especifico_nacionalidade`.
- Confirmar como marcar `eh_vencedor`.

Definições fechadas:
- `eh_vencedor` será exportado como `TRUE/FALSE`.
- `grupo_especifico_nacionalidade` usará inicialmente: `EUA`, `Latino`, `Europeu`, `Asiático`, `Africano`, `Oceania`, `Canadense`, `Outro`.
- A regra de `Latino` será: ator nascido em país soberano da América Latina.
- `Puerto Rico` será tratado como `EUA`.

Entregável:
- Documento de schema e regras aprovado.

Verificação humana:
- Conferir se cada coluna tem definição clara e sem sobreposição.

Verificação do agente:
- Validar que todas as colunas necessárias podem ser preenchidas pelo pipeline.

## Fase 2: Prova de estrutura das páginas-fonte
Objetivo:
- Confirmar como extrair dados da página principal e das páginas individuais.

Atividades:
- Inspecionar a página `Academy Award for Best Actor`.
- Mapear a tabela ou tabelas que contêm vencedores e indicados.
- Validar se o link da cerimônia pode ser usado para obter `ano_cerimonia`.
- Testar um pequeno conjunto de páginas de atores com perfis diferentes.

Amostra mínima sugerida:
- ator nascido nos EUA
- ator europeu
- ator latino
- ator com dados biográficos incompletos

Entregável:
- Mapa de seletores e estratégia de parsing.

Verificação humana:
- Revisar se os exemplos cobrem os principais casos-limite.

Verificação do agente:
- Executar scraping pontual e comparar com a página manualmente.

## Fase 3: Extrair lista base da categoria
Objetivo:
- Gerar uma tabela consolidada com todos os vencedores e indicados.

Atividades:
- Raspar a página principal.
- Normalizar linhas por ator/filme/ano.
- Capturar `nome_ator`, `filme_indicado`, `ano_filme`, `numero_cerimonia`, `url_ator`, `url_filme`, `url_cerimonia`, `eh_vencedor`.

Entregável:
- Dataset intermediário com linhas da categoria.

Verificação humana:
- Conferir uma amostra manual contra a página.

Verificação do agente:
- Checar contagem de linhas por década e presença dos links essenciais.

## Fase 4: Enriquecer dados biográficos
Objetivo:
- Preencher os campos biográficos de cada ator.

Atividades:
- Visitar `url_ator`.
- Extrair `local_nascimento_raw`, `pais_nascimento`, `nacionalidade_raw`, `cidadania_raw`.
- Aplicar fallback no Wikidata quando necessário.
- Persistir `status_extracao` e `fonte_classificacao`.

Entregável:
- Aba `crua` preenchida com campos brutos e rastreabilidade da origem.

Verificação humana:
- Auditar uma amostra com casos simples e ambíguos.

Verificação do agente:
- Gerar relatório de quantos registros ficaram sem `pais_nascimento`.

## Fase 5: Derivar classificações analíticas
Objetivo:
- Popular as colunas de agrupamento usadas na análise.

Atividades:
- Aplicar a regra `pais_nascimento = EUA => EUA; senão Estrangeiro`.
- Mapear o país para `grupo_especifico_nacionalidade`.
- Separar análises de `vencedores` e `indicados`.

Entregável:
- Colunas derivadas consistentes na aba `crua`.

Verificação humana:
- Validar manualmente alguns atores conhecidos.

Verificação do agente:
- Testes automatizados para regras de classificação com casos sintéticos.

## Fase 6: Montar agregações
Objetivo:
- Preencher a aba `agregada`.

Atividades:
- Criar agregações por `grupo_geral_nacionalidade`.
- Criar agregações por `grupo_especifico_nacionalidade`.
- Separar contagens para `vencedores` e `indicados`.

Definição fechada:
- A aba `agregada` deve conter contagens separadas de vencedores e indicados.

Entregável:
- Aba `agregada` pronta para consumo.

Verificação humana:
- Conferir se os totais batem com a aba `crua`.

Verificação do agente:
- Recalcular agregados a partir do dataframe e comparar com a planilha exportada.

## Fase 7: Gerar visualização
Objetivo:
- Produzir o gráfico de pizza de referência e deixar espaço para gráficos futuros.

Atividades:
- Gerar pizza para `EUA` vs `Estrangeiro`.
- Avaliar se pizza continua adequada quando houver mais categorias específicas.
- Exportar imagem no padrão de `refs/grafico_nacionalidade.png`.

Definição fechada:
- O gráfico principal considerará apenas vencedores, para manter aderência ao objetivo principal do projeto.

Entregável:
- Arquivo PNG final.

Verificação humana:
- Conferir legibilidade, rótulos e consistência com a tabela agregada.

Verificação do agente:
- Validar se os percentuais do gráfico batem com os agregados.

## Fase 8: Robustez e repetibilidade
Objetivo:
- Garantir que o pipeline possa ser reexecutado sem ajustes manuais.

Atividades:
- Parametrizar URLs e caminhos de saída.
- Tratar falhas de request e campos ausentes.
- Salvar logs de scraping.
- Documentar como rodar o projeto do zero.

Convenção de saída definida:
- Não sobrescrever arquivos de referência em `refs/`.
- Gerar novos arquivos por fase.
- Convenção de nomes: `fase1_<nome>`, `fase2_<nome>`, `fase3_<nome>` e assim por diante.
- Exemplo: `fase3_entregavel_tabela.xlsx`, `fase7_grafico_nacionalidade.png`.

Entregável:
- Pipeline repetível e documentado.

Verificação humana:
- Rodar a partir de um ambiente limpo seguindo a documentação.

Verificação do agente:
- Execução de ponta a ponta sem intervenção manual.

## Decisões Técnicas Recomendadas
- Linguagem: Python
- Parsing HTML: `requests` + `beautifulsoup4`
- Tabelas: `pandas`
- Planilha Excel: `openpyxl`
- Gráficos: `matplotlib`
- Configuração de categorias por país: arquivo de mapeamento simples em JSON ou CSV

## Riscos Principais
- Mudança na estrutura HTML da Wikipedia.
- Páginas de atores sem infobox padronizada.
- Casos-limite de país de nascimento e identidade cultural.
- Ambiguidade entre "nacionalidade", "cidadania" e "local de nascimento".

## Estratégias de Mitigação
- Registrar o dado bruto junto da classificação derivada.
- Usar fallback controlado no Wikidata.
- Manter lista explícita de países mapeados para `Latino`.
- Incluir relatório de exceções para revisão manual.

## Critérios de Aceite do Projeto
- A aba `crua` contém todos os vencedores e indicados de Melhor Ator.
- Cada linha possui links rastreáveis e campos biográficos auditáveis.
- A aba `agregada` reproduz corretamente os totais da aba `crua`.
- O gráfico `EUA` vs `Estrangeiro` bate com a agregação.
- O pipeline consegue ser executado novamente sem edição manual de código.

## Resumo das Decisões Fechadas
- Fonte principal: Wikipedia.
- Fallback: Wikidata.
- Aba `crua`: auditável, com campos brutos e derivados.
- `eh_vencedor`: `TRUE/FALSE`.
- `grupo_especifico_nacionalidade`: `EUA`, `Latino`, `Europeu`, `Asiático`, `Africano`, `Oceania`, `Canadense`, `Outro`.
- Regra de `Latino`: nascido em país soberano da América Latina.
- `Puerto Rico`: tratar como `EUA`.
- Arquivos de saída: sempre novos, com prefixo da fase.
- Gráfico principal: somente vencedores.

## Próximo Passo Recomendado
Implementar primeiro uma prova de conceito curta com 5 a 10 atores para validar:
- extração da página principal
- extração de `pais_nascimento`
- regra de classificação
- exportação para a aba `crua`

Se essa prova de conceito fechar, o restante do pipeline fica muito menos arriscado.
