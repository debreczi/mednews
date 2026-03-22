"""xAI Grok enrichment service.

Enriches articles with AI-generated Hungarian content:
- mednews_title: humorous/cynical title (max 80 chars)
- summary: 2-3 sentence humorous summary (respectful if tragic)
- link_text: Hungarian CTA with original title (max 40 chars)

Batch processes articles to minimise API calls.
Retries up to 3 times on failure; falls back to original_title on final failure.
"""
import asyncio
import json
import logging
import re
from typing import Any

from openai import AsyncOpenAI

from ..config import settings

logger = logging.getLogger(__name__)

DEFAULT_MODEL = settings.llm_model

# Pre-enrichment tragic keyword check — avoids wasting tokens on a detection call
TRAGIC_KEYWORDS = [
    "halál", "elhunyt", "meghalt", "tragédia", "elhalálozás",
    "gyász", "katasztrófa", "áldozat", "súlyos sérülés", "halálos",
    "merénylet", "tömegszerencsétlenség", "tömeges halál",
]

BATCH_SIZE = 10
MAX_RETRIES = 3
RETRY_DELAY = 2.0  # seconds


def is_tragic(text: str) -> bool:
    """True if the article title/content contains tragic keywords."""
    lower = text.lower()
    return any(kw in lower for kw in TRAGIC_KEYWORDS)


def _build_enrichment_prompt(articles: list[dict]) -> str:
    """Build the batch enrichment prompt."""
    articles_json = json.dumps(
        [{"id": a["_idx"], "title": a["original_title"], "tragic": a["_tragic"]}
         for a in articles],
        ensure_ascii=False,
        indent=2,
    )
    return f"""Te egy magyar egészségügyi IT hírportál szerkesztője vagy. Az olvasóid magyar egészségügyi IT szakemberek — fáradt, cinikus, de okos emberek.

LEGFONTOSABB SZABÁLY:
Az összefoglaló ELŐSZÖR informatív: a szakember az összefoglalóból értse meg, miről szól a hír, milyen számok/tények vannak benne. Az olvasónak NE kelljen az eredeti cikket megnyitnia. A humor MÁSODLAGOS: fanyar megjegyzés a végén, vagy szellemes megfogalmazás — de SOHA nem az információ rovására.

STÍLUS:
- A humor a TÉMÁBÓL fakadjon, ne erőltesd bele kívülálló utalásokat (pl. ne emlegesd az EESZT-t ha a cikk nem arról szól, ne írj admin123-at ha nem kiberbiztonsági téma).
- Fanyar, száraz humor: inkább egy odavetett megjegyzés a mondat végén, mint erőltetett vicc.
- NE találj ki tényeket, NE adj hozzá hamis információt a humor kedvéért.
- Ha tragic=true: komoly, tisztelettudó, humor nélkül.

PÉLDÁK:

Eredeti: "Az EESZT rendszer új funkcióval bővül 2026-ban"
Cím: "Az EESZT végre megtanult egy új trükköt — és ezúttal nem is fagyott le közben"
Összefoglaló: "Az Elektronikus Egészségügyi Szolgáltatási Tér új modulja lehetővé teszi az orvosok számára a laboreredmények valós idejű megosztását a betegekkel. A fejlesztés három éve volt tervben, ami az egészségügyi IT-ben meglepően gyorsnak számít. A rendszer márciustól éles üzemben működik, és eddig mindössze kétszer kellett újraindítani — ami rekordnak számít."

Eredeti: "Novartis picks up experimental breast cancer therapy for $2B"
Cím: "A Novartis 2 milliárdért vett mellrákos reménységet — drága bevásárlás"
Összefoglaló: "A Novartis 2 milliárd dollárért megvásárolta a Synnovation kísérleti mellrák-terápiáját (SNV4818), amely a korai fázisú vizsgálatokban ígéretes eredményeket mutatott HER2-negatív betegeknél. A deal a Novartis onkológiai portfólióját erősíti, és 2027-re várják a III-as fázisú vizsgálatok indulását. Ennyi pénzért már egy kis magyar kórházat is lehetne digitalizálni — de az kevésbé szexi a befektetőknek."

Eredeti: "A telemedicina használata 40%-kal nőtt Magyarországon"
Cím: "A magyarok rájöttek, hogy a pizsamában is lehet orvoshoz menni"
Összefoglaló: "A KSH legfrissebb adatai szerint a telemedicina igénybevétele 40%-kal emelkedett 2025-höz képest. A háziorvosok egyharmada már rendszeresen használ videókonzultációt, bár az idősebb páciensek körében a \"doktor úr, nem látom a képernyőt\" továbbra is a leggyakoribb panasz. A trend folytatódik, a szoftvercégek pedig dörzsölik a tenyerüket."

Eredeti: "Adatvizualizáció az egészségügyi döntéshozatalban"
Cím: "Dashboardok a kórházban: végre nem Excelben nézik, ki halt meg"
Összefoglaló: "A modern adatvizualizációs eszközök (Power BI, Tableau, Superset) egyre nagyobb teret nyernek a magyar kórházi döntéshozatalban. A kórházvezetők most már valós idejű dashboardokon követhetik az ágykihasználtságot, a várólistákat és a műtéti kapacitásokat. A legnagyobb kihívás nem a technológia, hanem az, hogy rávegyék a főorvosokat: ne nyomtassák ki a dashboardot A4-es papírra."

Kaptál {len(articles)} cikket. Minden cikkhez generálj:
1. "mednews_title": Szellemes, fanyar magyar cím (max 80 karakter). Úgy fogalmazd, ahogy egy magyar kolléga mondaná élőszóban — természetes köznyelv, NEM fordításízű. Ha tragic=true → komoly, tisztelettudó.
2. "summary": 6-10 mondatos, részletes magyar összefoglaló a fenti stílusban. ELŐSZÖR az érdemi információ (számok, tények, nevek, következmények), UTÁNA fanyar megjegyzés. Az olvasónak NE kelljen az eredetit elolvasnia. Ha tragic=true → tárgyilagos, humor nélkül.
3. "link_text": Kontextuális magyar CTA, max 40 karakter. Pl: "Ha tényleg érdekel:", "A hivatalos közlemény itt:", "A részletekért:"

Válaszolj KIZÁRÓLAG valid JSON tömbként, semmi mást ne írj:
[
  {{"id": 0, "mednews_title": "...", "summary": "...", "link_text": "..."}},
  ...
]

Cikkek:
{articles_json}"""


def _build_scoring_prompt(articles: list[dict]) -> str:
    """Build batch scoring prompt — scores relevance 1-10 for Hungarian medical IT pros."""
    articles_json = json.dumps(
        [{"id": a["_idx"], "title": a["original_title"]}
         for a in articles],
        ensure_ascii=False,
        indent=2,
    )
    return f"""Értékeld az alábbi cikkek relevanciáját 1-10 skálán magyar egészségügyi IT szakemberek számára.
10 = rendkívül releváns (egészségügyi IT, digitalizáció, orvosi szoftver, AI az egészségügyben, EESZT, NEAK)
5  = közepesen releváns (általános egészségügy, gyógyszer, kórház)
1  = nem releváns (politika, sport, szórakoztatás)

Válaszolj KIZÁRÓLAG valid JSON tömbként:
[{{"id": 0, "score": 7.5}}, ...]

Cikkek:
{articles_json}"""


async def _call_llm(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """Call the configured LLM API (OpenAI-compatible)."""
    client = AsyncOpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url or None,
    )
    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_completion_tokens=4096,
    )
    return response.choices[0].message.content


def _extract_json(text: str) -> Any:
    """Extract JSON array from LLM response (handles markdown code fences)."""
    # Strip markdown code fences if present
    text = re.sub(r"```(?:json)?\s*", "", text).strip()
    # Find the JSON array
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    return json.loads(text)


async def _enrich_batch(batch: list[dict]) -> list[dict]:
    """Enrich one batch of articles, with retry logic."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            raw = await _call_llm(_build_enrichment_prompt(batch))
            results = _extract_json(raw)
            # Map results back by id
            by_id = {r["id"]: r for r in results}
            for article in batch:
                r = by_id.get(article["_idx"], {})
                article["mednews_title"] = (r.get("mednews_title") or article["original_title"])[:80]
                article["summary"] = r.get("summary") or ""
                article["link_text"] = (r.get("link_text") or "Az eredeti cikk itt olvasható:")[:40]
                article["enrichment_status"] = "complete"
            return batch
        except Exception as e:
            logger.warning(f"[Enrichment] Attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY * attempt)

    # Final fallback — use original title
    logger.error("[Enrichment] All retries exhausted — falling back to original titles")
    for article in batch:
        article["mednews_title"] = article["original_title"]
        article["summary"] = ""
        article["link_text"] = "Az eredeti cikk itt olvasható:"
        article["enrichment_status"] = "failed"
    return batch


async def enrich_articles(articles: list[dict]) -> list[dict]:
    """Enrich articles in batches. Modifies dicts in-place and returns them."""
    if not articles:
        return articles

    # Tag each article with index and tragic flag
    for i, a in enumerate(articles):
        a["_idx"] = i
        a["_tragic"] = is_tragic(a.get("original_title", "") + " " + a.get("summary", ""))
        a["is_tragic"] = a["_tragic"]

    # Process in batches
    batches = [articles[i:i + BATCH_SIZE] for i in range(0, len(articles), BATCH_SIZE)]
    results = []
    for batch in batches:
        enriched = await _enrich_batch(batch)
        results.extend(enriched)
        if len(batches) > 1:
            await asyncio.sleep(0.5)  # gentle rate limiting between batches

    # Clean up internal keys
    for a in results:
        a.pop("_idx", None)
        a.pop("_tragic", None)

    logger.info(f"[Enrichment] Enriched {len(results)} articles")
    return results
