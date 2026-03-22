"""LLM enrichment service (OpenAI-compatible API).

Enriches articles with AI-generated Hungarian content:
- mednews_title: humorous/cynical title (max 80 chars)
- summary: 6-10 sentence informative summary with dry humor (respectful if tragic)
- link_text: Hungarian CTA with original title (max 40 chars)
- is_tragic: LLM-determined flag for sensitive content

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

BATCH_SIZE = 10
MAX_RETRIES = 3
RETRY_DELAY = 2.0  # seconds


def _build_enrichment_prompt(articles: list[dict]) -> str:
    """Build the batch enrichment prompt."""
    articles_json = json.dumps(
        [{"id": a["_idx"], "title": a["original_title"]}
         for a in articles],
        ensure_ascii=False,
        indent=2,
    )
    return f"""Te egy magyar egészségügyi IT hírportál szerkesztője vagy. Az olvasóid magyar egészségügyi IT szakemberek — fáradt, cinikus, de okos emberek. Úgy írj, mint egy szarkasztikus kolléga, aki a kávéja mellől kommentálja az aktuális híreket.

LEGFONTOSABB SZABÁLY:
Az összefoglaló INFORMATÍV ÉS SZÓRAKOZTATÓ egyszerre. A szakember az összefoglalóból értse meg, miről szól a hír — DE közben szórakozzon is. A stílus: SZATIRIKUS hírmagazin, nem száraz hírügynökség. Gondolj a Hírcsárdára, az Index régi Vélemény rovatára, vagy a The Borowitz Report-ra. A humor NEM opcionális — a cím ÉS az összefoglaló is legyen szellemes, fanyar, ironikus.

NYELV:
- KIZÁRÓLAG magyarul írj. Egyetlen angol szó, kifejezés vagy mondatrész se legyen a szövegben (kivéve tulajdonneveket, márkaneveket, szakkifejezéseket amiknek nincs magyar megfelelője).
- NE keverd az angolt és a magyart. Ha az eredeti cikk angol, FORDÍTSD LE teljesen.

STÍLUS:
- A humor a TÉMÁBÓL fakadjon, ne erőltesd bele kívülálló utalásokat (pl. ne emlegesd az EESZT-t ha a cikk nem arról szól, ne írj admin123-at ha nem kiberbiztonsági téma).
- NE találj ki magyar párhuzamokat! NE írd azt, hogy "Itthon...", "Nálunk...", "Magyarországon ez..." KIVÉVE ha a cikk tényleg magyar témáról szól. Ha a cikk amerikai vagy európai hírről szól, maradj AZON a témán.
- A humor a CIKK tartalmából fakadjon. Ironizálj a szereplőkön, a helyzeten, az iparág szokásain — NE rakj be kívülálló utalásokat.
- LEGYÉL MERÉSZ a címekben! A cím legyen olyan, ami kiszúrja az ember szemét a hírfolyamban. Provokatív, szellemes, cinikus — de NEM clickbait hazugság. Gondolj ilyen mintára: "X megint Y-t csinált, mindenki meglepődött (nem)".
- NE találj ki tényeket, NE adj hozzá hamis információt a humor kedvéért.

TILOS VICCELNI:
- Súlyos betegségekkel (rák, Alzheimer, stb.) — ezek a betegek számára nem viccesek.
- Halállal, halálesetekkel, tragédiákkal, katasztrófákkal.
- Szenvedéssel, fájdalommal, áldozatokkal.
Ilyen témáknál a cím legyen informatív és komoly, az összefoglaló tárgyilagos és tisztelettudó. A humor KIZÁRÓLAG technológiai, IT, üzleti, bürokratikus témáknál megengedett.

ÉRZÉKENYSÉG (is_tragic):
Döntsd el te, hogy a cikk témája érzékeny-e. Ha a cikk halálról, súlyos betegségről (rák, Alzheimer, ALS, stb.), tragédiáról, járványról szól → is_tragic=true. Ha IT, üzlet, szabályozás, technológia → is_tragic=false. Ha kétséges, inkább legyen true.

PÉLDÁK:

Eredeti: "Az EESZT rendszer új funkcióval bővül 2026-ban"
Cím: "Az EESZT végre megtanult egy új trükköt — és ezúttal nem is fagyott le közben"
is_tragic: false
Összefoglaló: "• Az Elektronikus Egészségügyi Szolgáltatási Tér új modulja lehetővé teszi az orvosok számára a laboreredmények valós idejű megosztását a betegekkel.\n• A fejlesztés három éve volt tervben, ami az egészségügyi IT-ben meglepően gyorsnak számít.\n• A rendszer márciustól éles üzemben működik.\n• Eddig mindössze kétszer kellett újraindítani — ami rekordnak számít.\n• A modul a háziorvosok és szakrendelők közötti kommunikációt is javítja.\n• Az a gyanúnk, hogy a nyomtatási igény ennek ellenére változatlan marad."

Eredeti: "Novartis picks up experimental breast cancer therapy for $2B"
Cím: "A Novartis 2 milliárdot fizetett egy mellrák elleni gyógymódért — jó befektetés?"
is_tragic: true
Összefoglaló: "• A Novartis 2 milliárd dollárért megvásárolta a Synnovation kísérleti mellrák-terápiáját (SNV4818).\n• A kezelés a korai fázisú vizsgálatokban ígéretes eredményeket mutatott HER2-negatív betegeknél.\n• Az üzlet a Novartis onkológiai portfólióját erősíti.\n• A III-as fázisú vizsgálatokat 2027-re tervezik.\n• A tranzakció az onkológiai felvásárlások legfrissebb nagy tétele.\n• A fejlesztés kimenetele a további klinikai adatoktól függ."

Eredeti: "A telemedicina használata 40%-kal nőtt Magyarországon"
Cím: "A magyarok rájöttek, hogy a pizsamában is lehet orvoshoz menni"
is_tragic: false
Összefoglaló: "• A KSH legfrissebb adatai szerint a telemedicina igénybevétele 40%-kal emelkedett 2025-höz képest.\n• A háziorvosok egyharmada már rendszeresen használ videókonzultációt.\n• Az idősebb páciensek körében a \"doktor úr, nem látom a képernyőt\" továbbra is a leggyakoribb panasz.\n• A trend nem lassul, a szoftvercégek pedig dörzsölik a tenyerüket.\n• A legnagyobb kihívás nem a technológia, hanem a digitális írástudás.\n• A pizsama mint hivatalos orvosi várótermi viselet egyre elfogadottabb."

Eredeti: "Adatvizualizáció az egészségügyi döntéshozatalban"
Cím: "Dashboardok a kórházban: végre nem Excelben nézik, ki halt meg"
is_tragic: false
Összefoglaló: "• A modern adatvizualizációs eszközök (Power BI, Tableau, Superset) egyre nagyobb teret nyernek a magyar kórházi döntéshozatalban.\n• A kórházvezetők most már valós idejű dashboardokon követhetik az ágykihasználtságot, a várólistákat és a műtéti kapacitásokat.\n• A döntéshozatal végre adatvezérelt lesz — legalábbis elméletben.\n• A legnagyobb kihívás nem a technológia, hanem az, hogy rávegyék a főorvosokat: ne nyomtassák ki a dashboardot A4-es papírra.\n• Az implementáció országszerte eltérő ütemben halad.\n• Ahol dashboard van, ott jön a következő kérdés: ki fogja értelmezni?"

Kaptál {len(articles)} cikket. Minden cikkhez generálj:
1. "mednews_title": SZATIRIKUS, provokatív magyar cím. A cím legyen vicces, ironikus, szúrós — olyan, ami mosolyt csal. Úgy fogalmazd, ahogy egy cinikus kolléga mondaná a kávéja mellől. NEM semleges hírügynökségi cím! Ha érzékeny téma → komoly, de informatív cím. A cím legyen annyi hosszú, amennyit a tartalom megkíván — NE vágd le.
2. "summary": MINIMUM 6 felsorolási pont (bullet point), magyar összefoglaló. FORMÁTUM: minden pont "• " karakterrel kezdődjön, és új sorba kerüljön (\\n). Az információ legyen pontos (számok, tények, nevek), DE a stílus legyen szatirikus, ironikus, szellemes — mint egy szarkasztikus kolléga mesélné el a hírt. Szőjj bele fanyar megjegyzéseket, ironikus fordulatokat a tények közé. Ha érzékeny téma → tárgyilagos, humor nélkül. FONTOS: 6 pontnál rövidebb összefoglaló ELFOGADHATATLAN.
3. "link_text": Kontextuális magyar CTA, max 40 karakter. Pl: "Ha tényleg érdekel:", "A hivatalos közlemény itt:", "A részletekért:"
4. "is_tragic": true ha a téma érzékeny (betegség, halál, tragédia, járvány, szenvedés), false ha nem.

Válaszolj KIZÁRÓLAG valid JSON tömbként, semmi mást ne írj:
[
  {{"id": 0, "mednews_title": "...", "summary": "...", "link_text": "...", "is_tragic": false}},
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
                article["mednews_title"] = r.get("mednews_title") or article["original_title"]
                article["summary"] = r.get("summary") or ""
                article["link_text"] = (r.get("link_text") or "Az eredeti cikk itt olvasható:")[:40]
                article["is_tragic"] = r.get("is_tragic", False)
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
        article["is_tragic"] = False
        article["enrichment_status"] = "failed"
    return batch


async def enrich_articles(articles: list[dict]) -> list[dict]:
    """Enrich articles in batches. Modifies dicts in-place and returns them."""
    if not articles:
        return articles

    # Tag each article with index
    for i, a in enumerate(articles):
        a["_idx"] = i

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

    logger.info(f"[Enrichment] Enriched {len(results)} articles")
    return results
