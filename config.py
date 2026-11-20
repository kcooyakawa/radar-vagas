# ===== EDITE AQUI =====
# Palavras-chave: a vaga entra se o título/tags/descrição contiver QUALQUER uma.
KEYWORDS = ["python", "django", "fastapi", "data", "automação", "automation", "scraping"]

# Palavras que excluem a vaga (ex.: senioridade que você não quer)
EXCLUDE = ["intern", "estágio"]

# Busca usada nas fontes que aceitam termo (LinkedIn, Remotive, Freelancer)
SEARCH_TERMS = ["python"]

# Quantos dias manter vagas antigas no painel
KEEP_DAYS = 21

# Liga/desliga fontes
SOURCES = {
    "remoteok": True,
    "remotive": True,
    "weworkremotely": True,
    "himalayas": True,
    "arbeitnow": True,
    "freelancer": True,
    "linkedin": True,        # página pública, sem login; pode falhar às vezes
    "github_br": True,       # vagas BR: backend-br, frontendbr, react-brasil
}

GITHUB_BR_REPOS = ["backend-br/vagas", "frontendbr/vagas", "react-brasil/vagas"]
