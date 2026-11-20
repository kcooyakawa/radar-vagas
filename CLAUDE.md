# radar-vagas

Monitor de vagas remotas e freelas **criativos** (direção de arte, design, social media, vídeo/motion, landing pages, IA criativa). Coleta vagas de várias fontes, filtra, pontua e gera uma página estática publicada via GitHub Pages.

## Stack
- Python 3.12, **só biblioteca padrão** (sem `requirements.txt`, sem pip). Não adicionar dependências externas.
- Nenhuma IA/LLM no pipeline — filtro e score são regras simples em `config.py`.
- Front-end: um único `template.html` (HTML/CSS/JS inline, sem build).
- Automação: GitHub Actions (`.github/workflows/radar.yml`), roda a cada 3h (`17 */3 * * *`) + botão manual.

## Estrutura
- `config.py` — **o arquivo que mais se edita**: `KEYWORDS` (inclusão por título/tags), `EXCLUDE` (descarta por título), `STRONG` (vaga "TOP"), `SEARCH_TERMS` (buscas por termo), `SEARCH_TERMS_BR`, `SCAM` (anti-golpe), `MIN_FREELA_BUDGET`, `KEEP_DAYS`, `SOURCES` (liga/desliga fontes).
- `radar.py` — fetchers por fonte (`gupy` (BR), `remoteok`, `remotive`, `weworkremotely`, `himalayas`, `freelancer`, `linkedin`), `matches()`, `score()`, `main()`.
- `template.html` — layout da página; os dados entram substituindo o placeholder `/*__DATA__*/null`.
- `data/jobs.json` — histórico de vagas (gerado; mantém `first_seen` para marcar novidades).
- `docs/index.html` — página final (gerada; servida pelo GitHub Pages).

## Comandos
- Rodar localmente: `python radar.py` (faz requisições reais às fontes, imprime status por fonte e total de vagas).
- Ver resultado: abrir `docs/index.html` no navegador.

## Regras
- **Não editar à mão** `docs/index.html` nem `data/jobs.json` — são gerados. Mudanças visuais vão em `template.html`; depois rode `python radar.py` para regenerar.
- Não quebrar o placeholder `/*__DATA__*/null` no template.
- Toda vaga passa pela função `job()` — manter esse formato (`id`, `source`, `kind`, `title`, `company`, `url`, `date`, `desc`, `full`, `tags`, `salary`, `location`, `logo`, `budget`). Campos novos precisam de `setdefault` em `main()` para não quebrar vagas antigas do JSON.
- Nova fonte: criar função geradora em `radar.py` que faz `yield job(...)`, registrar em `FETCHERS` e adicionar a chave em `config.SOURCES`. Erros de uma fonte não podem derrubar as outras (o `try/except` em `main()` cuida disso).
- Respeitar as fontes: manter `time.sleep` entre requisições paginadas e o User-Agent atual.
- Foco é vaga criativa, **não** programação — ao mexer em filtros, não deixar entrar vagas de dev/engenharia.
- Commits automáticos do bot têm a mensagem "Atualiza vagas ..."; commits manuais devem ser descritivos e em português.
- Textos da interface em português (BR).
