# Template: rascunho de layout → esqueleto do app

Template de 4 blocos (Contexto, Entrada, Restrições, Formato de saída) preenchido para os dois dashboards.

---

## Dashboard 1 (Aula 21)

### Contexto

Sou aluno da disciplina Análise e Visualização de Dados (CESAR School, 2026.2). Estou construindo um app
Streamlit a partir da minha EDA da Aula 11, feita com o dataset EV Battery Health Prediction (Kaggle,
20.000 veículos elétricos, alvo `battery_failure`). O dado tratado está em `data/clean/dataset.csv` e é
carregado por `src/data_loader.py` (`load_data()`). O Dashboard 1 mostra **correlação e distribuição das
variáveis quantitativas**.

Estrutura do repositório: `app.py` na raiz, `src/` com módulos auxiliares, `data/clean/` com o CSV,
`notebooks/` com a EDA, `entregas/` com os rascunhos, `.streamlit/config.toml` com o tema.

### Entrada

- Rascunho anexado: `entregas/rascunho-dashboard1.png`.
- Colunas quantitativas: `state_of_health`, `cycle_count`, `internal_resistance`, `capacity_loss_percent`,
  `thermal_runaway_risk`. Classe: `status_bateria` (Normal / Falha). Filtro global: `fleet_or_private`
  (Fleet / Private).
- Perguntas que o dashboard responde: quais variáveis se correlacionam e com que força? Remover valores
  extremos muda essa correlação? Como cada variável se distribui, e a distribuição muda entre Normal e
  Falha?
- Layout: sidebar com filtro de tipo de uso, seletor de variáveis (multiselect), método de correlação,
  toggles "remover outliers (IQR)" e "separar por status" e um slider de intervalo por variável. Área
  principal em duas colunas: à esquerda o heatmap de correlação (triângulo inferior), à direita os
  histogramas em grade de 2 colunas.

### Restrições

- Streamlit + Altair (`st.altair_chart`); nada de HTML/CSS customizado.
- Dados só via `src/data_loader.py`, com `@st.cache_data`, caminho relativo e só as colunas usadas
  (o CSV tem 73 colunas e 20.000 linhas).
- Gerar só o **esqueleto estrutural**: widgets funcionando e placeholders (`st.empty()` / `# TODO`) onde
  vão os gráficos, sem lógica de cálculo ainda.
- O dashboard deve ficar numa aba (`st.tabs`), já prevendo a aba do Dashboard 2.
- Textos da interface em português.

### Formato de saída

Um único `app.py` completo, pronto para `streamlit run app.py`, com comentários curtos separando sidebar,
filtros e área principal.

---

## Dashboard 2 (Aula 22)

### Contexto

Mesmo projeto. O Dashboard 2 entra na segunda aba do app e mostra **KPIs para a gestão de manutenção de
uma frota** decidir quais veículos inspecionar primeiro. As métricas já foram testadas em
`notebooks/metricas-dashboard2.ipynb` e justificadas em `entregas/justificativa-metricas.md`.

### Entrada

- Rascunho anexado: `entregas/rascunho-dashboard2.png`.
- KPIs (`st.metric`, com delta em relação à base completa): veículos no recorte (contagem), taxa de falha
  (média de `battery_failure`), SoH mediano (`state_of_health`) e risco térmico extremo (% de
  `thermal_runaway_risk` > 53,92, o limite do IQR da EDA).
- Visuais: taxa de falha por `faixa_idade_veiculo` (barras verticais), taxa de falha por
  `battery_chemistry` (barras horizontais) e dispersão `state_of_health` × `thermal_runaway_risk` colorida
  por status.
- Widgets: filtro de tipo de uso da sidebar, clique nas barras, área arrastada na dispersão e botão
  "Limpar seleções".

### Restrições

- Altair com seleção cruzada: `alt.selection_point` nas barras e `alt.selection_interval` na dispersão,
  com `on_select="rerun"` para levar a seleção ao Python e recalcular os KPIs (ver `ALTAIR-CROSSFILTER.md`).
- Cada gráfico mantém todas as categorias e a escala fixa quando outro gráfico filtra os dados.
- A dispersão desenha uma amostra de pontos (20.000 deixariam o app pesado), mas a seleção filtra todos
  os veículos.
- Cálculos dos KPIs num módulo separado (`src/metricas.py`), iguais aos do notebook.
- Recorte vazio não pode quebrar o app (mostrar "—" no card).

### Formato de saída

Código da aba do Dashboard 2 para o `app.py` existente e as funções de `src/metricas.py` e
`src/graficos.py`, com uma explicação curta de como a seleção circula entre os gráficos.
