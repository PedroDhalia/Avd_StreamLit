"""Constantes compartilhadas pelo app: variáveis do estudo, rótulos legíveis e identidade visual."""

# Variáveis quantitativas do estudo (mesma lista VARS_QUANT do notebook de EDA)
VARS_QUANT = ["state_of_health", "cycle_count", "internal_resistance", "capacity_loss_percent", "thermal_runaway_risk"]

ROTULOS = {
    "state_of_health": "Saúde da bateria, SoH (%)",
    "cycle_count": "Ciclos de carga",
    "internal_resistance": "Resistência interna",
    "capacity_loss_percent": "Perda de capacidade (%)",
    "thermal_runaway_risk": "Risco térmico (score)",
}

# Rótulos curtos para eixos e tabelas onde o espaço é pequeno
ROTULOS_CURTOS = {
    "state_of_health": "SoH",
    "cycle_count": "Ciclos",
    "internal_resistance": "Resistência",
    "capacity_loss_percent": "Perda cap.",
    "thermal_runaway_risk": "Risco térmico",
}

# Categorias com ordem fixa: a escala dos gráficos não muda quando um filtro esvazia um grupo
ORDEM_FAIXAS = ["<4 anos", "4-6 anos", "7-8 anos", "9+ anos"]  # mesmas faixas da seção de fairness da EDA
ORDEM_QUIMICA = ["NMC", "LFP", "LMO", "NCA", "LTO"]  # da mais para a menos frequente
CLASSES = ["Normal", "Falha"]
USOS = {"Fleet": "Frota", "Private": "Particular"}

# Identidade visual: mesma convenção da EDA (rosa = Normal, roxo = Falha), com tons ajustados
# para passar nos testes de contraste (>= 3:1 no fundo branco) e de separação para daltonismo
COR_NORMAL = "#d4789a"
COR_FALHA = "#5e3e93"
COR_NEUTRA = "#857f93"  # histogramas sem separar por classe (cinza da EDA, escurecido para 3,8:1)
COR_FORA = "#dcd8e2"  # pontos fora da seleção: pano de fundo, sem papel de identidade
COR_TINTA = "#1f1a2b"  # textos e linhas de referência
CORES_CLASSE = [COR_NORMAL, COR_FALHA]

# Escala divergente da correlação: azul (negativa), cinza neutro (zero), vermelho (positiva),
# a mesma leitura do cmap "coolwarm" usado na EDA
CORES_CORRELACAO = ["#2a78d6", "#f0efec", "#d03b3b"]
