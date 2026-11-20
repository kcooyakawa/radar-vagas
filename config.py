# ===== EDITE AQUI =====
# A vaga entra se o TÍTULO ou as TAGS tiverem pelo menos um destes termos.
KEYWORDS = [
    # direção de arte / criação
    "art director", "art direction", "creative director", "diretor de arte", "direção de arte",
    "diretora de arte", "creative lead", "criação", "criativo", "creative",
    # design
    "designer", "design", "graphic", "gráfico", "brand", "branding", "identidade visual",
    "visual identity", "logo", "illustrat", "ilustra", "figma", "ui/ux", "ux/ui", "ui designer",
    "product designer", "web designer", "packaging", "key visual", "banner", "flyer", "poster",
    "presentation", "apresentação", "canva", "photoshop",
    # sites / landing pages
    "landing page", "landing", "website", "web design", "site", "webflow", "framer", "wix",
    # social media
    "social media", "mídias sociais", "redes sociais", "instagram", "content creator",
    "criador de conteúdo", "carrossel", "carousel", "thumbnail",
    # vídeo / motion
    "video", "vídeo", "motion", "animator", "animação", "animation", "after effects", "premiere",
    "editor de vídeo", "video editor", "reels", "tiktok", "youtube", "3d",
    # IA criativa
    "ai art", "ai image", "ai video", "midjourney", "generative", "stable diffusion",
    "runway", "ai content", "prompt",
]

# Se o título tiver qualquer destes, a vaga é descartada (nada de código/engenharia)
EXCLUDE = [
    "developer", "desenvolvedor", "engineer", "engenheiro", "programador", "programmer",
    "backend", "back-end", "frontend", "front-end", "full stack", "fullstack", "devops",
    "python", "java", "php", "node", "react", "angular", ".net", "golang", "ruby",
    "data scientist", "data analyst", "data engineer", "machine learning engineer", "sre",
    "software", "qa ", "tester", "scraping", "api ", "blockchain", "solidity", "sales",
    "account executive", "intern", "estágio", "recruiter", "accountant",
    "ios", "android", "mobile app", "iphone app", "app development", "pcb", "hvac", "electrical",
    "mechanical", "cad ", "interior", "architect", "bathtub", "furniture", "sculpture", "mold",
    "nail", "kurti", "jewelry", "automation", "consultant", "course", "mentorship", "tutor",
    "level artist", "game-ready", "unity", "unreal", "pcb design", "circuit",
]

# Termos que tornam a vaga "TOP" (borda neon)
STRONG = ["art director", "creative director", "diretor de arte", "direção de arte",
          "senior designer", "lead designer", "brand designer", "motion designer",
          "landing page", "web designer", "social media designer", "ai video", "ai art"]

# Buscas nas fontes que aceitam termo (LinkedIn, Remotive, Freelancer)
SEARCH_TERMS = ["art director", "graphic designer", "social media designer",
                "video editor", "landing page design"]

KEEP_DAYS = 21

SOURCES = {
    "remoteok": True,
    "remotive": True,
    "weworkremotely": True,
    "himalayas": True,
    "freelancer": True,
    "linkedin": True,
}
