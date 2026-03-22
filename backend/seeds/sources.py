"""Seed the sources table with 50+ Hungarian medical and international sources."""
from sqlalchemy.orm import Session
from backend.models.source import Source


SOURCES = [
    # ── Hungarian Medical Portals ──────────────────────────────────────────
    {"name": "Házipatika", "url": "https://www.hazipatika.com", "type": "portal", "spider_name": "rss_spider", "region": "HU"},
    {"name": "WEBBeteg", "url": "https://www.webbeteg.hu", "type": "portal", "spider_name": "rss_spider", "region": "HU"},
    {"name": "EgészségKalauz", "url": "https://www.egeszsegkalauz.hu", "type": "portal", "spider_name": "rss_spider", "region": "HU"},
    {"name": "OrvosVálasz", "url": "https://www.orvosvalasz.hu", "type": "portal", "spider_name": "rss_spider", "region": "HU"},
    {"name": "Medical Online", "url": "https://medicalonline.hu", "type": "portal", "spider_name": "rss_spider", "region": "HU"},
    {"name": "Medicus Anonymus", "url": "https://medicusanonymus.hu", "type": "portal", "spider_name": "rss_spider", "region": "HU"},
    {"name": "Gyógyszer.hu", "url": "https://www.gyogyszer.hu", "type": "portal", "spider_name": "rss_spider", "region": "HU"},
    {"name": "MediFókusz", "url": "https://medifokusz.hu", "type": "portal", "spider_name": "rss_spider", "region": "HU"},
    {"name": "Egészség ABC", "url": "https://egeszsegabc.hu", "type": "portal", "spider_name": "rss_spider", "region": "HU"},
    {"name": "Kórház.hu", "url": "https://korhaz.hu", "type": "portal", "spider_name": "rss_spider", "region": "HU"},
    {"name": "Patika Magazin", "url": "https://patikamagazin.hu", "type": "portal", "spider_name": "rss_spider", "region": "HU"},
    {"name": "Pszichiáter.hu", "url": "https://www.pszichiater.hu", "type": "portal", "spider_name": "rss_spider", "region": "HU"},
    {"name": "Diabétesz Online", "url": "https://diabetes.hu", "type": "portal", "spider_name": "rss_spider", "region": "HU"},
    {"name": "RákGyógyítás.hu", "url": "https://rakgyogitas.hu", "type": "portal", "spider_name": "rss_spider", "region": "HU"},
    {"name": "Szív.hu", "url": "https://sziv.hu", "type": "portal", "spider_name": "rss_spider", "region": "HU"},

    # ── Hungarian Medical IT / Health Tech ────────────────────────────────
    {"name": "eHealth Hungary", "url": "https://ehealth.hu", "type": "portal", "spider_name": "rss_spider", "region": "HU"},
    {"name": "HIMSS Europe Hungary", "url": "https://www.himss.org/europe", "type": "international", "spider_name": "rss_spider", "region": "EU"},
    {"name": "Digitális Egészség", "url": "https://digitalisegeszség.hu", "type": "portal", "spider_name": "rss_spider", "region": "HU"},
    {"name": "HealthTech Hungary", "url": "https://healthtech.hu", "type": "portal", "spider_name": "rss_spider", "region": "HU"},
    {"name": "Informatikai és Hírközlési Minisztérium – Egészségügy", "url": "https://iit.gov.hu", "type": "portal", "spider_name": "rss_spider", "region": "HU"},

    # ── Hungarian Health RSS Feeds ─────────────────────────────────────────
    {"name": "Házipatika RSS", "url": "https://www.hazipatika.com/rss.xml", "type": "rss", "spider_name": "rss_spider", "region": "HU"},
    {"name": "WEBBeteg RSS", "url": "https://www.webbeteg.hu/rss/webbeteg.xml", "type": "rss", "spider_name": "rss_spider", "region": "HU"},
    {"name": "Medical Online RSS", "url": "https://medicalonline.hu/feed", "type": "rss", "spider_name": "rss_spider", "region": "HU"},
    {"name": "Medicus Anonymus RSS", "url": "https://medicusanonymus.hu/feed", "type": "rss", "spider_name": "rss_spider", "region": "HU"},
    {"name": "Portfolio Egészségügy RSS", "url": "https://www.portfolio.hu/rss/egeszsegugy.xml", "type": "rss", "spider_name": "rss_spider", "region": "HU"},
    {"name": "G7 Egészségügy RSS", "url": "https://g7.hu/feed/?cat=egeszseg", "type": "rss", "spider_name": "rss_spider", "region": "HU"},
    {"name": "24.hu Egészség RSS", "url": "https://24.hu/fn/egeszseg/feed/", "type": "rss", "spider_name": "rss_spider", "region": "HU"},
    {"name": "Telex Egészség RSS", "url": "https://telex.hu/rss/egeszseg", "type": "rss", "spider_name": "rss_spider", "region": "HU"},
    {"name": "Index Egészség RSS", "url": "https://index.hu/24ora/rss/?rovat=egeszseg", "type": "rss", "spider_name": "rss_spider", "region": "HU"},
    {"name": "HVG Egészség RSS", "url": "https://hvg.hu/rss/egeszseg", "type": "rss", "spider_name": "rss_spider", "region": "HU"},
    {"name": "Napi.hu Egészségügy RSS", "url": "https://www.napi.hu/rss/egeszsegugy", "type": "rss", "spider_name": "rss_spider", "region": "HU"},
    {"name": "Magyar Orvos RSS", "url": "https://www.magyarorvos.hu/rss.xml", "type": "rss", "spider_name": "rss_spider", "region": "HU"},
    {"name": "Farmakológia.hu RSS", "url": "https://farmakologia.hu/feed", "type": "rss", "spider_name": "rss_spider", "region": "HU"},
    {"name": "Semmelweis Hírek RSS", "url": "https://semmelweis.hu/hirek/feed", "type": "rss", "spider_name": "rss_spider", "region": "HU"},
    {"name": "ANTSZ Közlemények RSS", "url": "https://www.antsz.hu/felso_menu/sajtoszoba/rss.xml", "type": "rss", "spider_name": "rss_spider", "region": "HU"},

    # ── Hungarian Government / Official ───────────────────────────────────
    {"name": "NEAK (Nemzeti Egészségbiztosítási Alapkezelő)", "url": "https://neak.gov.hu", "type": "portal", "spider_name": "rss_spider", "region": "HU"},
    {"name": "OGYÉI (Gyógyszerészeti Hivatal)", "url": "https://ogyei.gov.hu", "type": "portal", "spider_name": "rss_spider", "region": "HU"},
    {"name": "NNK (Nemzeti Népegészségügyi Központ)", "url": "https://www.nnk.gov.hu", "type": "portal", "spider_name": "rss_spider", "region": "HU"},
    {"name": "Egészségügyi Minisztérium", "url": "https://gov.hu/egeszsegugy", "type": "portal", "spider_name": "rss_spider", "region": "HU"},

    # ── EU / European Organizations ─────────────────────────────────────────
    {"name": "EMA (European Medicines Agency) News RSS", "url": "https://www.ema.europa.eu/en/news/rss.xml", "type": "international", "spider_name": "rss_spider", "region": "EU"},
    {"name": "WHO Europe RSS", "url": "https://www.euro.who.int/en/media-centre/news/rss.xml", "type": "international", "spider_name": "rss_spider", "region": "EU"},
    {"name": "ECDC News RSS", "url": "https://www.ecdc.europa.eu/en/news-events/rss.xml", "type": "international", "spider_name": "rss_spider", "region": "EU"},
    {"name": "Politico EU Health RSS", "url": "https://www.politico.eu/section/health-care/feed/", "type": "international", "spider_name": "rss_spider", "region": "EU"},

    # ── US / International ──────────────────────────────────────────────────
    {"name": "IQVIA Insights RSS", "url": "https://www.iqvia.com/insights/the-iqvia-institute/rss", "type": "international", "spider_name": "rss_spider", "region": "US"},
    {"name": "Health Data Management RSS", "url": "https://www.healthdatamanagement.com/feed", "type": "international", "spider_name": "rss_spider", "region": "US"},
    {"name": "Healthcare IT News RSS", "url": "https://www.healthcareitnews.com/rss.xml", "type": "international", "spider_name": "rss_spider", "region": "US"},
    {"name": "HIMSS News RSS", "url": "https://www.himss.org/news/rss.xml", "type": "international", "spider_name": "rss_spider", "region": "US"},
    {"name": "Modern Healthcare IT RSS", "url": "https://www.modernhealthcare.com/section/technology/rss", "type": "international", "spider_name": "rss_spider", "region": "US"},
    {"name": "MedCity News RSS", "url": "https://medcitynews.com/feed/", "type": "international", "spider_name": "rss_spider", "region": "US"},
    {"name": "Rock Health Blog RSS", "url": "https://rockhealth.com/feed/", "type": "international", "spider_name": "rss_spider", "region": "US"},
    {"name": "Fierce Healthcare IT RSS", "url": "https://www.fiercehealthcare.com/rss/xml", "type": "international", "spider_name": "rss_spider", "region": "US"},
    {"name": "Digital Health Today RSS", "url": "https://digitalhealth.today/feed/", "type": "international", "spider_name": "rss_spider", "region": "US"},
    {"name": "STAT News RSS", "url": "https://www.statnews.com/feed/", "type": "international", "spider_name": "rss_spider", "region": "US"},

    # ── Social / LinkedIn Public Pages ────────────────────────────────────
    {"name": "Semmelweis Egyetem LinkedIn", "url": "https://www.linkedin.com/school/semmelweis-university/", "type": "social", "spider_name": "social_spider", "region": "HU"},
    {"name": "NEAK LinkedIn", "url": "https://www.linkedin.com/company/neak-hu/", "type": "social", "spider_name": "social_spider", "region": "HU"},
    {"name": "HealthTech Hungary LinkedIn", "url": "https://www.linkedin.com/company/healthtech-hungary/", "type": "social", "spider_name": "social_spider", "region": "HU"},
]


def seed_sources(db: Session) -> int:
    """Insert sources that don't already exist. Returns count of new sources added."""
    added = 0
    existing_urls = {url for (url,) in db.query(Source.url).all()}
    for src in SOURCES:
        if src["url"] not in existing_urls:
            db.add(Source(**src))
            added += 1
    db.commit()
    return added


if __name__ == "__main__":
    from backend.database import SessionLocal, init_db
    init_db()
    with SessionLocal() as db:
        n = seed_sources(db)
        print(f"Seeded {n} new sources ({len(SOURCES)} total defined)")
