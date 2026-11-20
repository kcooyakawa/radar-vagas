"""Radar de Vagas — coleta vagas remotas e freelas e gera docs/index.html.
Só usa a biblioteca padrão do Python. Nenhuma IA envolvida."""
import html, json, os, re, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

import config

UA = "Mozilla/5.0 (RadarVagas; +https://github.com)"
DATA = "data/jobs.json"
NOW = datetime.now(timezone.utc)


def get(url, headers=None):
    h = {"User-Agent": UA, "Accept": "*/*"}
    h.update(headers or {})
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def clean(t, n=280):
    t = re.sub(r"<[^>]+>", " ", html.unescape(t or ""))
    t = re.sub(r"\s+", " ", t).strip()
    return t[:n] + ("…" if len(t) > n else "")


def iso(v):
    try:
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(v, timezone.utc).isoformat()
        if not v:
            return NOW.isoformat()
        try:
            return parsedate_to_datetime(v).astimezone(timezone.utc).isoformat()
        except Exception:
            return datetime.fromisoformat(str(v).replace("Z", "+00:00")).isoformat()
    except Exception:
        return NOW.isoformat()


def job(src, kind, title, company, url, date, desc="", tags=None, salary="", location=""):
    return dict(id=f"{src}:{url}", source=src, kind=kind, title=clean(title, 140),
                company=clean(company, 80), url=url, date=iso(date), desc=clean(desc),
                tags=[str(t) for t in (tags or [])][:6], salary=salary, location=location)


# ---------------- Fontes ----------------
def remoteok():
    data = json.loads(get("https://remoteok.com/api"))
    for j in data[1:]:
        sal = f"US$ {j['salary_min']:,}–{j['salary_max']:,}" if j.get("salary_min") else ""
        yield job("RemoteOK", "Emprego remoto", j.get("position"), j.get("company"),
                  j.get("url"), j.get("epoch"), j.get("description"), j.get("tags"), sal, j.get("location", ""))


def remotive():
    for term in config.SEARCH_TERMS:
        d = json.loads(get("https://remotive.com/api/remote-jobs?search=" + urllib.parse.quote(term)))
        for j in d.get("jobs", []):
            yield job("Remotive", "Emprego remoto", j["title"], j["company_name"], j["url"],
                      j.get("publication_date"), j.get("description"), j.get("tags"),
                      j.get("salary", ""), j.get("candidate_required_location", ""))


def weworkremotely():
    root = ET.fromstring(get("https://weworkremotely.com/remote-jobs.rss"))
    for it in root.iter("item"):
        t = it.findtext("title") or ""
        company, _, title = t.partition(":")
        yield job("WeWorkRemotely", "Emprego remoto", title or t, company, it.findtext("link"),
                  it.findtext("pubDate"), it.findtext("description"), [it.findtext("category") or ""],
                  location=it.findtext("region") or "")


def himalayas():
    d = json.loads(get("https://himalayas.app/jobs/api?limit=100"))
    for j in d.get("jobs", []):
        yield job("Himalayas", "Emprego remoto", j.get("title"), j.get("companyName"),
                  j.get("applicationLink") or j.get("guid"), j.get("pubDate"), j.get("excerpt"),
                  j.get("categories"), location=", ".join(j.get("locationRestrictions") or []))


def arbeitnow():
    d = json.loads(get("https://www.arbeitnow.com/api/job-board-api"))
    for j in d.get("data", []):
        if j.get("remote"):
            yield job("Arbeitnow", "Emprego remoto", j["title"], j["company_name"], j["url"],
                      j.get("created_at"), j.get("description"), j.get("tags"), location=j.get("location", ""))


def freelancer():
    for term in config.SEARCH_TERMS:
        u = ("https://www.freelancer.com/api/projects/0.1/projects/active/?limit=50&full_description=true"
             "&job_details=true&query=" + urllib.parse.quote(term))
        d = json.loads(get(u))
        for p in d.get("result", {}).get("projects", []):
            b, cur = p.get("budget") or {}, (p.get("currency") or {}).get("code", "")
            sal = f"{cur} {b.get('minimum', '')}–{b.get('maximum', '')}" if b else ""
            yield job("Freelancer", "Freela", p["title"], "Cliente Freelancer",
                      f"https://www.freelancer.com/projects/{p['seo_url']}", p.get("time_submitted"),
                      p.get("description") or p.get("preview_description"),
                      [x["name"] for x in p.get("jobs", [])], sal)


def linkedin():
    for term in config.SEARCH_TERMS:
        for start in (0, 25):
            u = ("https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?f_WT=2&f_TPR=r604800"
                 f"&keywords={urllib.parse.quote(term)}&start={start}")
            page = get(u)
            for card in page.split("<li")[1:]:
                link = re.search(r'href="(https://[^"]*linkedin\.com/jobs/view/[^"?]+)', card)
                title = re.search(r'base-search-card__title[^>]*>(.*?)<', card, re.S)
                comp = re.search(r'base-search-card__subtitle[^>]*>(.*?)</h4>', card, re.S)
                loc = re.search(r'job-search-card__location[^>]*>(.*?)<', card, re.S)
                dt = re.search(r'datetime="([^"]+)"', card)
                if link and title:
                    yield job("LinkedIn", "Emprego remoto", title.group(1), comp.group(1) if comp else "",
                              link.group(1), dt.group(1) if dt else None, "", [term],
                              location=clean(loc.group(1)) if loc else "")
            time.sleep(2)


def github_br():
    tok = os.getenv("GITHUB_TOKEN")
    h = {"Accept": "application/vnd.github+json", **({"Authorization": f"Bearer {tok}"} if tok else {})}
    for repo in config.GITHUB_BR_REPOS:
        for i in json.loads(get(f"https://api.github.com/repos/{repo}/issues?state=open&per_page=50", h)):
            if "pull_request" in i:
                continue
            labels = [l["name"] for l in i.get("labels", [])]
            yield job("Vagas BR (GitHub)", "Emprego BR", i["title"], repo.split("/")[0], i["html_url"],
                      i.get("created_at"), i.get("body"), labels,
                      location="Remoto" if any("remoto" in l.lower() for l in labels) else "")


FETCHERS = dict(remoteok=remoteok, remotive=remotive, weworkremotely=weworkremotely, himalayas=himalayas,
                arbeitnow=arbeitnow, freelancer=freelancer, linkedin=linkedin, github_br=github_br)


# ---------------- Pipeline ----------------
def matches(j):
    text = " ".join([j["title"], j["desc"], " ".join(j["tags"])]).lower()
    return any(k.lower() in text for k in config.KEYWORDS) and not any(e.lower() in text for e in config.EXCLUDE)


def main():
    old = {}
    if os.path.exists(DATA):
        old = {j["id"]: j for j in json.load(open(DATA, encoding="utf-8"))}
    status, fresh = {}, {}
    for name, fn in FETCHERS.items():
        if not config.SOURCES.get(name):
            continue
        try:
            n = 0
            for j in fn():
                if j["url"] and matches(j):
                    fresh[j["id"]] = j
                    n += 1
            status[name] = f"ok ({n})"
        except Exception as e:
            status[name] = f"erro: {e.__class__.__name__}"
        print(name, status[name])

    merged = {}
    for jid, j in {**old, **fresh}.items():
        j["first_seen"] = old.get(jid, {}).get("first_seen") or NOW.isoformat()
        j["is_new"] = jid not in old
        if datetime.fromisoformat(j["first_seen"]) > NOW - timedelta(days=config.KEEP_DAYS):
            merged[jid] = j
    jobs = sorted(merged.values(), key=lambda j: j["date"], reverse=True)

    os.makedirs("data", exist_ok=True)
    json.dump(jobs, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    tpl = open("template.html", encoding="utf-8").read()
    payload = json.dumps({"jobs": jobs, "status": status, "updated": NOW.isoformat()}, ensure_ascii=False)
    out = tpl.replace("/*__DATA__*/null", payload.replace("</", "<\\/"))
    os.makedirs("docs", exist_ok=True)
    open("docs/index.html", "w", encoding="utf-8").write(out)
    print(f"{len(jobs)} vagas no painel ({sum(j['is_new'] for j in jobs)} novas)")


if __name__ == "__main__":
    main()
