# Declaração de Uso de IA

**Nome:**
**Data:** 29/10/2026

> Rascunho preenchido com o registro da sessão. Revise cada item e ajuste com a sua avaliação antes da
> entrega: a declaração é sua.

## Ferramenta

Claude Code (modelo Claude Opus 5.5), usado como agente dentro do VS Code, com as skills do Streamlit
(`developing-with-streamlit`, que lê a documentação da versão instalada, 1.66) e de visualização de
dados (`dataviz`, com validador de paleta para contraste e daltonismo).

## Prompts usados

```text
Quero que faça baseado nesse meu EDA essa nova atividade: @"Aula_11_Prática_EDA (1).ipynb" para isso,
analise essas aulas: @"Aula 21 - Streamlit parte 1.pptx" @"Aula 22 - Streamlit parte 2.pptx"
@"Aula 23 - Streamlit parte 3.pptx" para saber como realizar o fluxo da atividade.
```

```text
Desculpa, acabei me confundindo e enviei EDA errado, preciso que reestrutrure TUDO de acordo com esse:
@"Meu_dataset_Prática_EDA (1).ipynb"
```

O primeiro prompt apontava para o notebook de demonstração da aula (Heart Disease). Com o segundo, o
projeto foi refeito do zero sobre a minha EDA (EV Battery Health). Nada do Heart Disease ficou no
repositório além do notebook de referência do professor (`notebooks/arquivo-eda-original.ipynb`).

Os prompts estruturados (Contexto, Entrada, Restrições, Formato) que descrevem cada dashboard estão em
[`layout-skeleton-prompt.md`](layout-skeleton-prompt.md).

## O que a IA produziu

- Leitura dos slides das Aulas 21–23, do notebook de EDA e do repositório-modelo, e montagem do projeto
  na estrutura pedida (`notebooks/`, `data/`, `src/`, `entregas/`, `prompts/`).
- `notebooks/eda-com-downloads.ipynb`: cópia da minha EDA com as células de exportação de `data/raw` e
  `data/clean`, executada de ponta a ponta.
- `notebooks/metricas-dashboard2.ipynb`: teste das métricas e plots prévios em pandas/seaborn.
- `app.py` e os módulos `src/` (carga com cache, estatísticas, métricas e gráficos Altair).
- `.streamlit/config.toml` com a identidade visual.
- Rascunhos dos dois dashboards (`entregas/rascunho-dashboard*.png`), feitos como wireframe digital.
- `entregas/justificativa-metricas.md`, este arquivo e o README.

## O que foi aceito, modificado ou rejeitado e por quê

Decisões tomadas durante a sessão:

- **Modificado — carga do dataset:** o `kagglehub` não conseguiu acessar a API do Kaggle (falha de rede)
  e o download sem versão falhou. No `eda-com-downloads.ipynb`, o handle passou a fixar a versão
  (`.../versions/1`), o que torna a análise reprodutível e usa o arquivo que já estava no cache local.
  O `eda.ipynb` original não foi alterado.
- **Modificado — cores da EDA:** o rosa `#e9d4d0` e o roxo `#2d223a` da EDA reprovaram no validador
  (contraste de 1,4:1 no fundo branco; roxo escuro demais). A convenção rosa = Normal, roxo = Falha foi
  mantida, com os tons `#d4789a` e `#5e3e93`, que passam em contraste (≥ 3:1) e na simulação de daltonismo.
- **Modificado — limite do risco térmico extremo:** recalcular o limite do IQR nos dados já imputados dava
  outro corte (4,4% da frota em vez de 3,5%). O app usa o valor da EDA (53,92), calculado antes da imputação.
- **Modificado — histogramas:** com bins no encoding do Altair, os rótulos do eixo se sobrepunham. Os bins
  passaram para um `transform_bin`, e os números dos gráficos foram configurados no padrão brasileiro
  (1.000,5).
- **Rejeitado — primeira versão do filtro cruzado:** no protótipo, filtrar um gráfico pelo outro fazia a
  barra selecionada sumir e a escala mudar. A versão final mantém todas as categorias e a escala fixa.
- **Rejeitado — KPIs de perda de capacidade e resistência interna:** são redundantes com o SoH
  (correlação de −0,94 e −0,86).
- **Rejeitado — desenhar os 20.000 pontos na dispersão:** o gráfico usa uma amostra fixa de 4.000 pontos,
  mas a área selecionada filtra todos os veículos.

Sua revisão (preencher):

- **Aceito:**
- **Modificado:**
- **Rejeitado:**
