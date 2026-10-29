# Justificativa das métricas — Dashboard 2

**Dataset:** EV Battery Health Prediction (Kaggle), 20.000 veículos elétricos após o tratamento da EDA
(Aula 11: ausentes imputados pela mediana/moda, outliers mantidos).
**Público-alvo geral:** gestão de manutenção de uma frota de veículos elétricos (ou equipe de garantia de
baterias), que precisa decidir quais veículos mandar primeiro para inspeção preventiva ou troca de bateria.

As métricas saíram dos testes da EDA (Mann-Whitney, Qui-quadrado e correlação de Spearman) e foram
conferidas em [`notebooks/metricas-dashboard2.ipynb`](../notebooks/metricas-dashboard2.ipynb) antes de
entrarem no app. Todas são recalculadas quando o usuário muda o filtro de tipo de uso ou seleciona algo
nos gráficos, e cada card mostra a diferença para a base completa.

## Métrica 1: Veículos no recorte
- **Variável:** contagem de linhas (veículos) que atendem aos filtros e às seleções.
- **O que mede:** o tamanho do grupo analisado, em número absoluto e em % da base (20.000).
- **Por que foi escolhida:** a falha é rara (6,9%, razão de desbalanceamento de 13:1 na EDA). Num grupo
  pequeno, um punhado de falhas muda muito a taxa. Mostrar o tamanho do grupo ao lado das outras métricas
  evita conclusões tiradas de poucos veículos.
- **Público-alvo:** quem lê os outros KPIs (gestão de manutenção).
- **Qual decisão pode ser apoiada por essa métrica?** dimensionar a ação: quantas inspeções um critério
  de priorização vai gerar (por exemplo, "inspecionar todos os veículos com 9 anos ou mais" significa
  4.770 veículos, 24% da frota).
- **O que comunica ao público-alvo:** "estamos falando de X veículos, Y% da frota", o peso do grupo
  antes de olhar as taxas.

## Métrica 2: Taxa de falha
- **Variável:** `battery_failure` (0 = sem falha, 1 = falha; rótulo `status_bateria` criado na EDA).
- **O que mede:** a proporção de veículos do recorte com falha de bateria. O delta mostra a diferença em
  pontos percentuais (p.p.) para a taxa da base (6,9%).
- **Por que foi escolhida:** é o desfecho do dataset e a medida mais direta de risco de um grupo. Na EDA,
  a faixa de idade do veículo teve a associação mais forte com a falha (Qui² p ≈ 10⁻²⁰⁵): a taxa vai de 1,3%
  (<4 anos) a 15,8% (9+ anos).
- **Público-alvo:** gestão de manutenção e de garantia.
- **Qual decisão pode ser apoiada por essa métrica?** quais grupos entram primeiro na fila de inspeção.
  Por exemplo, veículos com SoH até 70% e risco térmico acima de 50 têm 84,6% de falha, mais de 12 vezes a
  média da base.
- **O que comunica ao público-alvo:** "de cada 100 veículos deste grupo, N têm a bateria em falha", e se
  o grupo está acima ou abaixo da média da frota.

## Métrica 3: SoH mediano
- **Variável:** `state_of_health` (saúde da bateria, em % da capacidade original).
- **O que mede:** a mediana da saúde das baterias do recorte, com o delta em p.p. em relação à base
  (82,9%).
- **Por que foi escolhida:** é a variável de degradação que o público já conhece ("a bateria está com 80%")
  e uma das que mais separa as classes (mediana de 71,7% nas falhas contra 83,0% nas normais). Usamos a
  **mediana** porque o Shapiro-Wilk rejeitou a normalidade na EDA e a variável tem assimetria negativa.
  Perda de capacidade e resistência interna ficaram **fora** dos KPIs por redundância: correlação de −0,94
  e −0,86 com o SoH (EDA, matriz de Spearman). As três medem a mesma degradação.
- **Público-alvo:** gestão de manutenção e equipe técnica.
- **Qual decisão pode ser apoiada por essa métrica?** planejar a troca de baterias por grupo: um grupo com
  SoH mediano bem abaixo da base (como os veículos com 9+ anos, 73,5%) pede orçamento de reposição.
- **O que comunica ao público-alvo:** "a bateria típica deste grupo ainda tem X% da capacidade original".

## Métrica 4: Risco térmico extremo
- **Variável:** `thermal_runaway_risk` (score de risco de thermal runaway, a fuga térmica que pode levar a
  incêndio).
- **O que mede:** a proporção de veículos do recorte com risco acima de **53,92**, o limite superior do
  IQR calculado na EDA (Seção 4). São os outliers que a EDA decidiu manter. O delta mostra a diferença em
  p.p. para a base (3,5%).
- **Por que foi escolhida:** o risco térmico é o sinal que mais separa as classes (mediana de 40,6 nas
  falhas contra 14,2 nas normais) e é **independente** do SoH (Spearman −0,05). Ele captura um risco que o
  SoH não mostra. A EDA levantou a hipótese de que os outliers seriam justamente as falhas, e o notebook de
  métricas confirmou: os 700 veículos acima do limite têm 47,4% de falha, contra 5,5% no restante.
  Uma proporção acima do limite é mais fácil de comunicar que a mediana de um score sem unidade.
- **Público-alvo:** gestão de manutenção e segurança da frota.
- **Qual decisão pode ser apoiada por essa métrica?** acionar inspeção de segurança imediata nos veículos
  acima do limite, independentemente da saúde da bateria.
- **O que comunica ao público-alvo:** "X% dos veículos deste grupo estão numa faixa de risco térmico fora
  do padrão da frota".

## Variáveis consideradas e descartadas
- **Perda de capacidade e resistência interna:** redundantes com o SoH (ver Métrica 3). Continuam no
  Dashboard 1.
- **Ciclos de carga:** correlação moderada com o SoH (−0,47) e diferença menor entre as classes (mediana
  1.498 contra 1.295 ciclos). Ficou só no Dashboard 1.
- **Química, tipo de uso, tipo de veículo, terreno, tração e fabricante:** nenhuma associação com falha
  (Qui² p > 0,4; na EDA, o Kruskal-Wallis também não achou diferença de risco térmico entre terrenos).
  A química entra num gráfico para mostrar esse resultado ao público.

## Visuais e widgets do Dashboard 2
| Visual | Variáveis | Interação | Por que |
|---|---|---|---|
| Taxa de falha por idade do veículo (barras) | `faixa_idade_veiculo` | clique numa barra filtra KPIs e os outros gráficos | discretização da idade (Aula 22), com as mesmas faixas da seção de fairness da EDA; a taxa cresce 12 vezes entre a primeira e a última faixa |
| Taxa de falha por química da bateria (barras horizontais) | `battery_chemistry` | clique numa barra filtra KPIs e os outros gráficos | mostra que a química **não** explica a falha (Qui² da EDA), o que evita priorizar inspeções pelo critério errado |
| Saúde da bateria × risco térmico (dispersão por status) | `state_of_health`, `thermal_runaway_risk` | arrastar uma área filtra KPIs e barras | os dois sinais independentes juntos mostram a "zona de falha" (SoH baixo e risco alto) |

Widgets definidos antes do rascunho: filtro de **tipo de uso** (Frota/Particular, `st.pills` na sidebar,
vale para os dois painéis), **seleção por clique** nas barras, **seleção por área** na dispersão (Altair +
`on_select`) e o botão **Limpar seleções**.
