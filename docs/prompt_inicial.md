**APAGAR DEPOIS:** input - etapas - output | output -> input -> etapas

## ENTREGÁVEIS FINAIS
- Tabela contendo aba de planilha com dados raspados crus e aba de tabela agregada. Referência: `refs\entregavel_tabela.xlsx`
- Gráfico de pizza comparando as nacionalidades dos vencedores. Referência: `refs\grafico_nacionalidade.png`

##  VISÃO GERAL DO PROCESSO
### FONTES DE DADOS
- Página contendo dados de todos os vencedores e indicados a Melhor Ator: `https://en.wikipedia.org/wiki/Academy_Award_for_Best_Actor`
- Páginas de cada ator, contendo dados de nacionalidade, entre outros. Ex: `https://en.wikipedia.org/wiki/Adrien_Brody`

### PASSO A PASSO DE EXTRAÇÃO
- Entrar na página que contém todos os vencedores. Salvar na aba `crua` os dados principais contidos na página: ano da cerimônia, nome do vencedor, link da página do vencedor na Wikipedia
- Acessar o link de cada vencedor pra raspar os dados de nacionalidade e atualizar na aba `crua`
- Montar a tabela agregada na aba `agregada`
- Gerar o gráfico de visualização

## TAREFA IMEDIATA
A primeira tarefa é montar um planejamento completo da implementação do projeto. O planejamento deve ser dividido em fases verificáveis, tanto pelo humano no loop quanto pelo agente de IA.