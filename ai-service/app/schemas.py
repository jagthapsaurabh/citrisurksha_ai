from pydantic import BaseModel, ConfigDict

class TrainingRequest(BaseModel):
    dataset_version: str
    base_model: str = "mobilenet_v3_small"
    epochs: int = 3
    batch_size: int = 8
    min_accuracy_gate: float = 0.75
    classes: list[dict] = []
    training_records: list[dict] = []
    knowledge_records: list[dict] = []

class Prediction(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    is_citrus_pest: bool = True
    pest_id: str | None = None
    pest_name: str
    confidence: float
    severity_level: str = "unknown"
    stage: str | None = None
    model_version: str
    top_k: list[dict] = []
    explanation: str
    recommendation: str | None = None
    # Additive multi-stage pipeline fields (upgrade step 2). Old clients ignore these.
    decision: str | None = None
    candidates: list[dict] = []
    evidence: dict = {}
    quality: dict = {}
    detector: dict = {}
    review_priority: float | None = None
    timings: dict = {}

class KnowledgeIn(BaseModel):
    source_type: str = "developer"
    title: str
    content: str
    url: str | None = None
    pest_id: str | None = None
    metadata: dict = {}
