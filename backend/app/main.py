from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from .db import Base, engine, SessionLocal
from .media import safe_media_path
from .models import AiKnowledgeItem, BlogPost, CalendarEvent, Pest, User
from .seed_20_pests import PEST_KNOWLEDGE_ITEMS, TWENTY_PESTS
from .pdf_knowledge import PDF_KNOWLEDGE_ITEMS
from .dataset_sources import OPEN_DATASET_SOURCES
from .researcher_pest_guide import RESEARCHER_GUIDE_ITEMS, RESEARCHER_TRANSLATIONS
from .security import hash_password
from .routers import admin, auth, blogs, chat, detections, events, insecticides, notifications, pests, training

app = FastAPI(title="CitriSurksha API", version="0.1.0", default_response_class=ORJSONResponse)

app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(detections.router)
app.include_router(pests.router)
app.include_router(blogs.router)
app.include_router(events.router)
app.include_router(insecticides.router)
app.include_router(chat.router)
app.include_router(notifications.router)
app.include_router(training.router)
app.include_router(admin.router)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"success": False, "error": exc.detail, "path": str(request.url.path)})

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"success": False, "error": "Internal server error", "detail": str(exc), "path": str(request.url.path)})

SEED_PESTS = [
    {
        "id": "citrus-psyllid",
        "common_name": "Asian Citrus Psyllid",
        "scientific_name": "Diaphorina citri",
        "category": "insect",
        "lifecycle": {"egg": "Yellow/orange eggs on tender shoots", "nymph": "Flat yellow/orange nymphs produce waxy tubules", "adult": "Small mottled brown insect, feeds at 45 degree angle"},
        "symptoms": "Curling young leaves, sooty mould from honeydew, vector of citrus greening/HLB.",
        "prevention": "Use disease-free nursery plants, inspect flush growth weekly, remove infected shoots, manage ants, use yellow sticky traps.",
        "cure": "There is no cure for HLB-infected trees; control psyllids early and remove severely infected trees after expert confirmation.",
        "organic_control": "Neem oil/azadirachtin on new flush, horticultural oil, conserve ladybird beetles and lacewings.",
        "chemical_control": "Use locally registered systemic/contact insecticides in rotation; follow label dose, PHI and PPE requirements.",
    },
    {
        "id": "citrus-leaf-miner",
        "common_name": "Citrus Leaf Miner",
        "scientific_name": "Phyllocnistis citrella",
        "category": "insect",
        "lifecycle": {"egg": "Laid on young leaves", "larva": "Mines serpentine tunnels", "pupa": "At curled leaf margin", "adult": "Tiny silvery moth"},
        "symptoms": "Silvery serpentine mines, curled distorted young leaves, reduced seedling growth.",
        "prevention": "Avoid excessive nitrogen flush, prune only when needed, monitor nursery plants.",
        "cure": "Protect new flush during high infestation and remove heavily damaged nursery shoots.",
        "organic_control": "Neem oil, parasitoid conservation, pheromone traps where available.",
        "chemical_control": "Use registered insect growth regulators/spinosad/abamectin options as per local advisory.",
    },
    {
        "id": "citrus-aphid",
        "common_name": "Citrus Aphid",
        "scientific_name": "Toxoptera citricida / Aphis spp.",
        "category": "insect",
        "lifecycle": {"nymph": "Soft-bodied colonies on tender shoots", "adult": "Winged/wingless black or green aphids"},
        "symptoms": "Curled leaves, sticky honeydew, sooty mould, weak young shoots; can transmit tristeza virus.",
        "prevention": "Monitor new flush, control ants, avoid excess nitrogen.",
        "cure": "Wash off small colonies; treat early during flush if colonies increase.",
        "organic_control": "Soap spray, neem oil, release/conserve ladybirds, hoverflies and lacewings.",
        "chemical_control": "Use selective registered aphicides only when economic threshold is crossed.",
    },
    {
        "id": "citrus-whitefly",
        "common_name": "Citrus Whitefly",
        "scientific_name": "Dialeurodes citri",
        "category": "insect",
        "lifecycle": {"egg": "On underside of leaves", "nymph": "Scale-like immature stages", "adult": "Small white flying insect"},
        "symptoms": "Yellowing, sticky honeydew, black sooty mould, reduced tree vigour.",
        "prevention": "Maintain orchard sanitation, prune for airflow, avoid broad-spectrum insecticide overuse.",
        "cure": "Target nymphs on leaf underside; repeat monitoring after spray.",
        "organic_control": "Horticultural oil, neem, parasitoids and predators.",
        "chemical_control": "Use registered whitefly products with resistance rotation.",
    },
]

# Merge the full 20-pest citrus list supplied by the product team.
for _p in TWENTY_PESTS:
    if not any(existing["id"] == _p["id"] for existing in SEED_PESTS):
        SEED_PESTS.append(_p)

PEST_TRANSLATIONS = {
    "citrus-psyllid": {
        "mr": {"common_name": "आशियाई सिट्रस सायला", "symptoms": "कोवळ्या पानांचे वाकणे, मधासारखा चिकट स्त्राव, काळी बुरशी आणि सिट्रस ग्रीनिंगचा धोका.", "prevention": "रोगमुक्त रोपे वापरा, कोवळ्या फुटीची नियमित तपासणी करा, पिवळे चिकट सापळे वापरा.", "cure": "HLB बाधित झाडावर थेट उपचार नाही; सायला नियंत्रण आणि तज्ञ सल्ल्याने बाधित झाड काढणे आवश्यक.", "organic_control": "नीम तेल, बागायती तेल, लेडीबर्ड व लेसविंगसारखे नैसर्गिक शत्रू जपणे.", "chemical_control": "स्थानिक शिफारशीनुसार नोंदणीकृत कीटकनाशक फेरपालट करून वापरा.", "safety_note": "कीटकनाशक वापरण्यापूर्वी स्थानिक कृषी विभागाचा सल्ला घ्या."},
        "hi": {"common_name": "एशियन सिट्रस साइलिड", "symptoms": "नई पत्तियों का मुड़ना, चिपचिपा रस, काली फफूंद और सिट्रस ग्रीनिंग का खतरा।", "prevention": "रोगमुक्त पौधे लगाएं, नई बढ़वार की नियमित जांच करें, पीले चिपचिपे ट्रैप लगाएं।", "cure": "HLB संक्रमित पेड़ का सीधा इलाज नहीं; साइलिड नियंत्रण और विशेषज्ञ सलाह जरूरी है।", "organic_control": "नीम तेल, हॉर्टिकल्चर ऑयल, लेडीबर्ड और लेसविंग जैसे मित्र कीट बचाएं।", "chemical_control": "स्थानीय सलाह के अनुसार पंजीकृत कीटनाशक रोटेशन में उपयोग करें।", "safety_note": "कीटनाशक उपयोग से पहले स्थानीय कृषि विभाग की सलाह लें।"}
    },
    "citrus-leaf-miner": {
        "mr": {"common_name": "सिट्रस लीफ मायनर", "symptoms": "पानांवर चांदीसारखे वळणदार बोगदे, पानांचे वाकणे आणि रोपांची वाढ कमी होणे.", "prevention": "अति नत्र खत टाळा, अनावश्यक छाटणी टाळा, रोपवाटिकेतील रोपे तपासा.", "cure": "जास्त प्रादुर्भाव असलेल्या कोवळ्या फुटीचे संरक्षण करा व नुकसान झालेल्या फुटी काढा.", "organic_control": "नीम तेल, परजीवी कीटकांचे संरक्षण आणि फेरोमोन सापळे.", "chemical_control": "स्थानिक सल्ल्यानुसार स्पिनोसॅड/अबामेक्टिन किंवा नोंदणीकृत पर्याय वापरा."},
        "hi": {"common_name": "सिट्रस लीफ माइनर", "symptoms": "पत्तियों पर चांदी जैसे घुमावदार सुरंग, पत्ते मुड़ना और पौधे की वृद्धि कम होना।", "prevention": "अधिक नाइट्रोजन से बचें, अनावश्यक छंटाई न करें, नर्सरी पौधों की जांच करें।", "cure": "अधिक प्रकोप में नई बढ़वार की सुरक्षा करें और क्षतिग्रस्त भाग हटाएं।", "organic_control": "नीम तेल, परजीवी कीट संरक्षण और फेरोमोन ट्रैप।", "chemical_control": "स्थानीय सलाह अनुसार स्पिनोसैड/अबामेक्टिन या पंजीकृत विकल्प इस्तेमाल करें।"}
    },
    "citrus-aphid": {
        "mr": {"common_name": "सिट्रस मावा", "symptoms": "पाने वाकणे, चिकट स्त्राव, काळी बुरशी आणि कोवळ्या फुटी कमकुवत होणे.", "prevention": "नवीन फुटी तपासा, मुंग्या नियंत्रणात ठेवा, अति नत्र खत टाळा.", "cure": "लहान वसाहती पाण्याने धुवा; वाढत असल्यास लवकर नियंत्रण करा.", "organic_control": "साबण फवारणी, नीम तेल, लेडीबर्ड/लेसविंग संरक्षण.", "chemical_control": "आर्थिक पातळी ओलांडल्यास निवडक नोंदणीकृत मावानाशक वापरा."},
        "hi": {"common_name": "सिट्रस एफिड", "symptoms": "पत्ते मुड़ना, चिपचिपा रस, काली फफूंद और नई टहनियां कमजोर होना।", "prevention": "नई बढ़वार देखें, चींटियों को नियंत्रित करें, अधिक नाइट्रोजन से बचें।", "cure": "छोटी कॉलोनी पानी से धोएं; बढ़ने पर जल्दी नियंत्रण करें।", "organic_control": "साबुन स्प्रे, नीम तेल, लेडीबर्ड/लेसविंग संरक्षण।", "chemical_control": "आर्थिक सीमा पार होने पर चयनित पंजीकृत एफिडनाशी इस्तेमाल करें।"}
    },
    "citrus-whitefly": {
        "mr": {"common_name": "सिट्रस पांढरी माशी", "symptoms": "पानांचे पिवळेपण, चिकट स्त्राव, काळी बुरशी आणि झाडाची वाढ कमी होणे.", "prevention": "बाग स्वच्छ ठेवा, हवा खेळती राहील अशी छाटणी करा, व्यापक कीटकनाशकांचा अति वापर टाळा.", "cure": "पानांच्या खालच्या बाजूवरील पिल्लांवर लक्ष्य करा; फवारणीनंतर पुन्हा तपासणी करा.", "organic_control": "बागायती तेल, नीम आणि नैसर्गिक परजीवी/भक्षक कीटक.", "chemical_control": "प्रतिरोध व्यवस्थापनासह नोंदणीकृत पांढरी माशी नियंत्रण उत्पादने वापरा."},
        "hi": {"common_name": "सिट्रस व्हाइटफ्लाई", "symptoms": "पत्तों का पीला होना, चिपचिपा रस, काली फफूंद और पेड़ की शक्ति कम होना।", "prevention": "बाग साफ रखें, हवा के लिए छंटाई करें, व्यापक कीटनाशक का अधिक उपयोग न करें।", "cure": "पत्तियों की निचली सतह के निम्फ पर नियंत्रण करें; छिड़काव के बाद फिर जांचें।", "organic_control": "हॉर्टिकल्चर ऑयल, नीम और प्राकृतिक परजीवी/भक्षक।", "chemical_control": "प्रतिरोध प्रबंधन के साथ पंजीकृत व्हाइटफ्लाई उत्पाद उपयोग करें।"}
    }
}

CALENDAR = [
    (1, "Winter orchard sanitation", "Remove fallen fruit, prune dead twigs, check scale insects and sooty mould."),
    (2, "Pre-flush monitoring", "Install sticky traps and inspect tender shoots for psyllid/aphid activity."),
    (3, "Spring flush protection", "High-risk month for psyllid, aphid and leaf miner. Scout every 7 days."),
    (4, "Fruit set care", "Manage mites, thrips and irrigation stress. Avoid unnecessary sprays during pollinator activity."),
    (5, "Summer pest surveillance", "Watch whitefly, scale and leaf miner on new growth."),
    (6, "Monsoon disease+pest hygiene", "Improve drainage and remove weeds; monitor fruit fly and fungal issues."),
    (7, "Canopy airflow", "Light pruning and sanitation reduce pest shelter and disease humidity."),
    (8, "Fruit fly monitoring", "Use traps and collect dropped fruit; protect maturing fruit."),
    (9, "Post-monsoon flush", "Scout for psyllid and leaf miner on fresh flush."),
    (10, "Harvest preparation", "Follow pre-harvest intervals; avoid late unsafe pesticide applications."),
    (11, "Harvest and records", "Record pest incidence and treatments for next season planning."),
    (12, "Soil/tree health", "Balanced nutrition and irrigation planning for resilient citrus plants."),
]

def ensure_lightweight_migrations():
    """Small dev migration helper for this scaffold. Use Alembic in production."""
    columns = {
        "users": [
            ("is_active", "BOOLEAN DEFAULT TRUE"),
            ("email", "VARCHAR(180)"), ("village", "VARCHAR(120)"), ("state", "VARCHAR(120)"),
            ("address", "VARCHAR(300)"), ("acres_land", "FLOAT"), ("plants", "TEXT"),
            ("citrus_varieties", "TEXT"), ("irrigation_type", "VARCHAR(120)"),
            ("farming_experience_years", "INTEGER"), ("profile_completed", "BOOLEAN DEFAULT FALSE"),
            ("fcm_token", "TEXT"), ("fcm_platform", "VARCHAR(30)"), ("fcm_token_updated_at", "TIMESTAMP"),
        ],
        "detections": [
            ("admin_note", "TEXT"), ("corrected_by_admin", "BOOLEAN DEFAULT FALSE"),
            ("reviewed_by", "VARCHAR"), ("reviewed_at", "TIMESTAMP"),
        ],
        "chat_messages": [
            ("attachment_url", "VARCHAR(500)"), ("attachment_name", "VARCHAR(255)"), ("attachment_type", "VARCHAR(80)"),
        ],
        "blog_posts": [
            ("image_url", "VARCHAR(500)"), ("doc_url", "VARCHAR(500)"), ("content_type", "VARCHAR(20) DEFAULT 'html'"), ("author_name", "VARCHAR(180)"), ("views_count", "INTEGER DEFAULT 0"),
        ],
        "pests": [
            ("is_active", "BOOLEAN DEFAULT TRUE"),
            ("translations", "JSON DEFAULT '{}'"),
        ],
    }
    with engine.begin() as conn:
        dialect = engine.dialect.name
        for table, defs in columns.items():
            for name, typ in defs:
                try:
                    if dialect == "postgresql":
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {name} {typ}"))
                    elif dialect == "sqlite":
                        existing = [row[1] for row in conn.execute(text(f"PRAGMA table_info({table})"))]
                        if name not in existing:
                            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {typ}"))
                except Exception:
                    pass


def seed_data(db: Session):
    for item in SEED_PESTS:
        research = RESEARCHER_TRANSLATIONS.get(item["id"], {})
        item.setdefault("translations", research or PEST_TRANSLATIONS.get(item["id"], {}))
        if research.get("en"):
            en = research["en"]
            item["symptoms"] = en.get("symptoms", item.get("symptoms", ""))
            item["prevention"] = en.get("prevention", item.get("prevention", ""))
            item["cure"] = en.get("cure", item.get("cure", ""))
            item["organic_control"] = en.get("biological_management", item.get("organic_control", ""))
            item["chemical_control"] = en.get("chemical_control", item.get("chemical_control", ""))
        pest = db.get(Pest, item["id"])
        if not pest:
            db.add(Pest(**item))
        else:
            # Keep existing admin edits but backfill missing translations/details from seed.
            if not getattr(pest, "translations", None):
                pest.translations = item.get("translations") or PEST_TRANSLATIONS.get(item["id"], {})
            for field in ["category", "symptoms", "prevention", "cure", "organic_control", "chemical_control", "safety_note"]:
                if not getattr(pest, field, None) and item.get(field):
                    setattr(pest, field, item[field])
    if not db.query(User).filter(User.phone == "9999999999").first():
        db.add(User(name="Admin", phone="9999999999", password_hash=hash_password("admin123"), role="admin"))
    if db.query(CalendarEvent).count() == 0:
        for month, title, desc in CALENDAR:
            db.add(CalendarEvent(month=month, title=title, description=desc, region="India"))
    if db.query(BlogPost).count() == 0:
        db.add(BlogPost(title="How to take a clear pest photo", summary="Improve AI accuracy with these steps.", body="Take photos in daylight, focus on the pest or damaged leaf, avoid blur, and capture both close-up and full plant context."))
    for item in PEST_KNOWLEDGE_ITEMS + PDF_KNOWLEDGE_ITEMS + RESEARCHER_GUIDE_ITEMS:
        if not db.query(AiKnowledgeItem).filter(AiKnowledgeItem.title == item["title"], AiKnowledgeItem.source_type == item.get("source_type", "seed")).first():
            db.add(AiKnowledgeItem(title=item["title"], content=item["content"], source_type=item.get("source_type", "seed"), url=item.get("url"), pest_id=item["pest_id"], metadata_json=item.get("metadata", {})))
    for src in OPEN_DATASET_SOURCES:
        title = f"Open dataset source: {src['name']}"
        if not db.query(AiKnowledgeItem).filter(AiKnowledgeItem.title == title, AiKnowledgeItem.source_type == "dataset").first():
            db.add(AiKnowledgeItem(title=title, content=f"Dataset URL: {src['url']}\nSuitable for: {src['suitable_for']}\nUse only after license review and local download/curation.", source_type="dataset", url=src["url"], pest_id=None, metadata_json=src))
    db.commit()

def ensure_translation_columns():
    """Idempotent additive migration for existing SQLite/Postgres databases."""
    from sqlalchemy import inspect as sa_inspect, text
    insp = sa_inspect(engine)
    specs = {
        "blog_posts": "ALTER TABLE blog_posts ADD COLUMN translations JSON",
        "calendar_events": "ALTER TABLE calendar_events ADD COLUMN translations JSON",
        "platform_events": "ALTER TABLE platform_events ADD COLUMN translations JSON",
    }
    with engine.begin() as conn:
        for table, ddl in specs.items():
            if table in insp.get_table_names():
                cols = [c["name"] for c in insp.get_columns(table)]
                if "translations" not in cols:
                    try:
                        conn.execute(text(ddl))
                    except Exception:
                        pass


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    ensure_translation_columns()
    ensure_lightweight_migrations()
    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()

@app.get("/media/{file_path:path}")
def media(file_path: str):
    return FileResponse(safe_media_path(file_path))

@app.get("/health")
def health():
    return {"status": "healthy", "service": "citrisurksha-api"}
