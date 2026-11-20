"""Radar de Vagas — vagas criativas remotas e freelas. Gera docs/index.html.
Só usa a biblioteca padrão do Python. Nenhuma IA envolvida."""
import html, json, os, re, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

import config

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
DATA = "data/jobs.json"
NOW = datetime.now(timezone.utc)


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def clean(t, n=280):
    t = re.sub(r"<[^>]+>", " ", html.unescape(t or ""))
    t = re.sub(r"\s+", " ", t).strip()
    return t[:n] + ("…" if len(t) > n else "")


def full_text(t, n=6000):
    t = html.unescape(t or "")
    t = re.sub(r"(?i)<br\s*/?>|</p>|</li>|</h\d>|</div>", "\n", t)
    t = re.sub(r"(?i)<li[^>]*>", "• ", t)
    t = re.sub(r"<[^>]+>", "", t)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n\s*\n+", "\n\n", t).strip()
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
            d = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
            return (d if d.tzinfo else d.replace(tzinfo=timezone.utc)).isoformat()
    except Exception:
        return NOW.isoformat()


def job(src, kind, title, company, url, date, desc="", tags=None, salary="", location="", logo="", budget=0):
    return dict(id=f"{src}:{url}", source=src, kind=kind, title=clean(title, 140),
                company=clean(company, 80), url=url, date=iso(date), desc=clean(desc), full=full_text(desc),
                tags=[str(t) for t in (tags or []) if t][:6], salary=salary, location=clean(location, 90),
                logo=logo or "", budget=budget or 0)


# ---------------- Fontes ----------------
def remoteok():
    for j in json.loads(get("https://remoteok.com/api"))[1:]:
        sal = f"US$ {j['salary_min']:,}–{j['salary_max']:,}/ano" if j.get("salary_min") else ""
        yield job("RemoteOK", "Emprego remoto", j.get("position"), j.get("company"), j.get("url"),
                  j.get("epoch"), j.get("description"), j.get("tags"), sal, j.get("location", ""),
                  j.get("company_logo") or j.get("logo"), j.get("salary_max") or 0)


def remotive():
    urls = ["https://remotive.com/api/remote-jobs?category=design"] + [
        "https://remotive.com/api/remote-jobs?search=" + urllib.parse.quote(t) for t in config.SEARCH_TERMS]
    for u in urls:
        for j in json.loads(get(u)).get("jobs", []):
            yield job("Remotive", "Emprego remoto", j["title"], j["company_name"], j["url"],
                      j.get("publication_date"), j.get("description"), j.get("tags") + [j.get("category", "")],
                      j.get("salary", ""), j.get("candidate_required_location", ""), j.get("company_logo"))


def weworkremotely():
    for feed in ("remote-design-jobs", "remote-sales-and-marketing-jobs"):
        root = ET.fromstring(get(f"https://weworkremotely.com/categories/{feed}.rss"))
        for it in root.iter("item"):
            t = it.findtext("title") or ""
            company, _, title = t.partition(":")
            media = it.find("{http://search.yahoo.com/mrss/}content")
            yield job("WeWorkRemotely", "Emprego remoto", title or t, company, it.findtext("link"),
                      it.findtext("pubDate"), it.findtext("description"), [it.findtext("category") or ""],
                      location=it.findtext("region") or "", logo=media.get("url") if media is not None else "")


def himalayas():
    for off in (0, 100):
        d = json.loads(get(f"https://himalayas.app/jobs/api?limit=100&offset={off}"))
        for j in d.get("jobs", []):
            yield job("Himalayas", "Emprego remoto", j.get("title"), j.get("companyName"),
                      j.get("applicationLink") or j.get("guid"), j.get("pubDate"), j.get("description") or j.get("excerpt"),
                      (j.get("categories") or []) + (j.get("parentCategories") or []), "",
                      ", ".join(j.get("locationRestrictions") or []) or "Mundo todo", j.get("companyLogo"),
                      j.get("maxSalary") or 0)


def freelancer():
    for term in config.SEARCH_TERMS:
        u = ("https://www.freelancer.com/api/projects/0.1/projects/active/?limit=50&full_description=true"
             "&job_details=true&query=" + urllib.parse.quote(term))
        for p in json.loads(get(u)).get("result", {}).get("projects", []):
            b, cur = p.get("budget") or {}, (p.get("currency") or {}).get("code", "")
            rate = (p.get("currency") or {}).get("exchange_rate") or 1
            sal = f"{cur} {(b.get('minimum') or 0):g}–{(b.get('maximum') or 0):g}" if b else ""
            yield job("Freelancer", "Freela", p["title"], "Cliente Freelancer",
                      f"https://www.freelancer.com/projects/{p['seo_url']}", p.get("time_submitted"),
                      p.get("description") or p.get("preview_description"),
                      [x["name"] for x in p.get("jobs", [])], sal, budget=(b.get("maximum") or 0) * rate)
        time.sleep(1)


def linkedin():
    for term in config.SEARCH_TERMS:
        for start in (0, 25):
            u = ("https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?f_WT=2&f_TPR=r604800"
                 f"&keywords={urllib.parse.quote(term)}&start={start}")
            for card in get(u).split("<li")[1:]:
                link = re.search(r'href="(https://[^"]*linkedin\.com/jobs/view/[^"?]+)', card)
                title = re.search(r'base-search-card__title[^>]*>(.*?)<', card, re.S)
                comp = re.search(r'base-search-card__subtitle[^>]*>(.*?)</h4>', card, re.S)
                loc = re.search(r'job-search-card__location[^>]*>(.*?)<', card, re.S)
                dt = re.search(r'datetime="([^"]+)"', card)
                logo = re.search(r'data-delayed-url="([^"]+)"', card)
                if link and title:
                    yield job("LinkedIn", "Emprego remoto", title.group(1), comp.group(1) if comp else "",
                              link.group(1), dt.group(1) if dt else None, "", [term],
                              location=loc.group(1) if loc else "",
                              logo=html.unescape(logo.group(1)) if logo else "")
            time.sleep(2)


def gupy():
    """Brasil: portal público da Gupy (vagas publicadas por empresas reais)."""
    for term in config.SEARCH_TERMS_BR:
        u = ("https://portal.api.gupy.io/api/v1/jobs?limit=100&jobName=" + urllib.parse.quote(term))
        for j in json.loads(get(u)).get("data", []):
            wp = (j.get("workplaceType") or "").lower()
            if wp not in ("remote", "hybrid") and not j.get("isRemoteWork"):
                continue
            loc = "Remoto (Brasil)" if wp == "remote" or j.get("isRemoteWork") else \
                f"Híbrido — {j.get('city') or ''}/{j.get('state') or ''}"
            yield job("Gupy", "Emprego BR", j.get("name"), j.get("careerPageName"), j.get("jobUrl"),
                      j.get("publishedDate"), j.get("description") or "", [term, j.get("type") or ""],
                      location=loc, logo=j.get("careerPageLogo") or "")
        time.sleep(1)


FETCHERS = dict(gupy=gupy, remoteok=remoteok, remotive=remotive, weworkremotely=weworkremotely,
                himalayas=himalayas, freelancer=freelancer, linkedin=linkedin)


# ---------------- Filtro e pontuação ----------------
def has(text, words):
    return any(re.search(r"(?<![a-z])" + re.escape(w.lower()), text) for w in words)


def matches(j):
    title = j["title"].lower()
    text = title + " " + " ".join(j["tags"]).lower()
    if not has(text, config.KEYWORDS) or has(title, config.EXCLUDE):
        return False
    return not is_scam(j)


def is_scam(j):
    """Minimiza golpes: termos suspeitos, freela com orçamento irrisório, sem link/empresa."""
    body = (j["title"] + " " + j.get("full", "") + " " + j.get("desc", "")).lower()
    if has(body, config.SCAM):
        return True
    if j["kind"] == "Freela" and 0 < j.get("budget", 0) < config.MIN_FREELA_BUDGET:
        return True
    return not j["url"].startswith("https://")


def score(j):
    title = j["title"].lower()
    s = 0
    if has(title, config.STRONG): s += 3
    if re.search(r"senior|sênior|sr\.?|lead|head|principal", title): s += 1
    if j["salary"]: s += 1
    if j["budget"] >= 1000: s += 2
    elif j["budget"] >= 500: s += 1
    loc = j["location"].lower()
    if any(w in loc for w in ("brazil", "brasil", "latam", "latin", "anywhere", "worldwide", "mundo", "americas")): s += 1
    if datetime.fromisoformat(j["date"]) > NOW - timedelta(hours=24): s += 1
    if j["logo"]: s += 0.5
    if j["source"] == "Gupy": s += 1  # empresa verificada no Brasil
    return s


def main():
    old = {}
    if os.path.exists(DATA):
        old = {j["id"]: j for j in json.load(open(DATA, encoding="utf-8")) if matches(j)}
    status, fresh = {}, {}
    for name, fn in FETCHERS.items():
        if not config.SOURCES.get(name):
            continue
        try:
            n = 0
            for j in fn():
                if j["url"] and matches(j) and j["id"] not in fresh:
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
        j.setdefault("logo", ""); j.setdefault("budget", 0)
        j["score"] = score(j)
        if datetime.fromisoformat(j["first_seen"]) > NOW - timedelta(days=config.KEEP_DAYS):
            merged[jid] = j
    jobs = sorted(merged.values(), key=lambda j: j["date"], reverse=True)
    ranked = sorted(j["score"] for j in jobs)
    cut = max(5, ranked[int(len(ranked) * 0.9)] if ranked else 4)
    for j in jobs:
        j["top"] = j["score"] >= cut

    os.makedirs("data", exist_ok=True)
    json.dump(jobs, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    tpl = open("template.html", encoding="utf-8").read()
    payload = json.dumps({"jobs": jobs, "status": status, "updated": NOW.isoformat()}, ensure_ascii=False)
    out = tpl.replace("/*__DATA__*/null", payload.replace("</", "<\\/"))
    os.makedirs("docs", exist_ok=True)
    open("docs/index.html", "w", encoding="utf-8").write(out)
    print(f"{len(jobs)} vagas ({sum(j['is_new'] for j in jobs)} novas, {sum(j['top'] for j in jobs)} top)")


if __name__ == "__main__":
    main()
