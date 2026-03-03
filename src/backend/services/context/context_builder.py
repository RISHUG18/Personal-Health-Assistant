"""Context builder — assembles all retrieved data into a validated, structured
object that is sent to the LLM (Gemini).

Design principles
-----------------
* **Single Responsibility**: this module ONLY assembles.  It never fetches
  from the DB, embeds queries, or calls Gemini.
* **Dependency Inversion**: callers pass fully-fetched dicts in; the builder
  is independent of Supabase, FAISS, or any network call.
* **Open/Closed**: adding a new context block (e.g. medication history) means
  adding a new Pydantic model and a new keyword argument — existing callers are
  unaffected.

Size constraints (from ``contracts/context_schema.json``)
---------------------------------------------------------
MAX_CHUNKS            = 5    (schema allows 10; we use 5 to stay well within token limits)
MAX_CHUNK_CHARS       = 500  (per chunk)
MAX_TOTAL_CONTEXT_CHARS = 4000

Usage
-----
::

    from backend.services.context import build_context

    context = build_context(
        query="Why is my iron low?",
        user_id="<uuid>",
        retrieved_chunks=chunks,       # from retrieve_context()
        alerts=alerts,                 # from fetch_active_alerts()
        medical_snapshot=snapshot,     # from fetch_user_lab_snapshot()
    )

    # Serialise to dict for the prompt builder / API response
    payload = context.model_dump()
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Size constraints ──────────────────────────────────────────────────────────

MAX_CHUNKS: int = 5
MAX_CHUNK_CHARS: int = 500
MAX_TOTAL_CONTEXT_CHARS: int = 4000


# ── Pydantic models (one per schema block) ────────────────────────────────────

class Demographics(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None


class UserProfile(BaseModel):
    user_id: str
    name: Optional[str] = None
    demographics: Demographics = Field(default_factory=Demographics)


class RecentVitals(BaseModel):
    heart_rate: Optional[int] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    spo2_percentage: Optional[int] = None


class MedicalSnapshot(BaseModel):
    last_checkup_date: Optional[str] = None
    known_conditions: List[str] = Field(default_factory=list)
    recent_vitals: RecentVitals = Field(default_factory=RecentVitals)


class ActivitySummary(BaseModel):
    steps_today: Optional[int] = None
    calories_burned: Optional[int] = None
    active_minutes: Optional[int] = None


class SleepMetrics(BaseModel):
    total_sleep_hours: Optional[float] = None
    sleep_score: Optional[int] = None
    deep_sleep_minutes: Optional[int] = None


class HeartHealth(BaseModel):
    resting_heart_rate: Optional[int] = None
    hrv_score: Optional[int] = None


class WearableData(BaseModel):
    device_synced_at: Optional[str] = None
    activity_summary: ActivitySummary = Field(default_factory=ActivitySummary)
    sleep_metrics: SleepMetrics = Field(default_factory=SleepMetrics)
    heart_health: HeartHealth = Field(default_factory=HeartHealth)


class AlertItem(BaseModel):
    """Mirrors the ``alerts`` DB table; severity values from schema.sql."""
    id: str
    type: str
    message: str
    severity: str       # 'low' | 'medium' | 'high'  (schema CHECK constraint)
    source_metric: Optional[str] = None


class EnvironmentalContext(BaseModel):
    location_city: Optional[str] = None
    aqi_level: Optional[int] = None
    temperature_celsius: Optional[float] = None
    weather_condition: Optional[str] = None


class RetrievedChunk(BaseModel):
    """A single RAG chunk after trimming and normalisation."""
    chunk_id: str
    text_content: str
    relevance_score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RagKnowledgeBase(BaseModel):
    query_used: str
    retrieved_chunks: List[RetrievedChunk] = Field(default_factory=list)


class ContextMeta(BaseModel):
    version: str = "1.1"
    generated_at: str                       # ISO-8601
    request_id: str                         # UUID, one per builder call
    schema_owner: str = "context-builder"
    size_constraints: Dict[str, int] = Field(
        default_factory=lambda: {
            "max_chunks": MAX_CHUNKS,
            "max_chunk_chars": MAX_CHUNK_CHARS,
            "max_total_context_chars": MAX_TOTAL_CONTEXT_CHARS,
        }
    )


class BuiltContext(BaseModel):
    """The complete, validated context object passed to the prompt layer."""
    meta: ContextMeta
    user_profile: UserProfile
    medical_snapshot: MedicalSnapshot = Field(default_factory=MedicalSnapshot)
    wearable_data: WearableData = Field(default_factory=WearableData)
    active_alerts: List[AlertItem] = Field(default_factory=list)
    environmental_context: EnvironmentalContext = Field(
        default_factory=EnvironmentalContext
    )
    rag_knowledge_base: RagKnowledgeBase
    role: str = "user"      # "user" | "doctor" — selects system prompt


# ── Core assembly function ─────────────────────────────────────────────────────

def build_context(
    query: str,
    user_id: str,
    retrieved_chunks: List[Dict[str, Any]],
    *,
    user_profile: Optional[Dict[str, Any]] = None,
    medical_snapshot: Optional[Dict[str, Any]] = None,
    wearable_data: Optional[Dict[str, Any]] = None,
    alerts: Optional[List[Dict[str, Any]]] = None,
    environment: Optional[Dict[str, Any]] = None,
    role: str = "user",
    request_id: Optional[str] = None,
) -> BuiltContext:
    """Assemble all retrieved data into a validated :class:`BuiltContext`.

    This is a *pure* function: same inputs → same output, no side effects.

    Parameters
    ----------
    query:
        The original user question (preserved verbatim in ``rag_knowledge_base``).
    user_id:
        UUID of the user.  Always required.
    retrieved_chunks:
        List of chunk dicts from :func:`~backend.services.retrieval.retrieve_context`.
        Each dict must contain at minimum ``chunk_id``, ``text_content``, and
        ``relevance_score``.
    user_profile:
        Optional dict with user demographics: ``name``, ``age``, ``gender``,
        ``weight_kg``, ``height_cm``.
    medical_snapshot:
        Optional dict with ``last_checkup_date``, ``known_conditions`` (list),
        and ``recent_vitals`` (nested dict).
    wearable_data:
        Optional dict matching the ``WearableData`` model structure.
    alerts:
        Optional list of alert dicts from :func:`~backend.services.context.data_fetchers.fetch_active_alerts`.
        Each dict should have ``id``, ``severity``, ``reason`` / ``message``.
    environment:
        Optional dict with ``location_city``, ``aqi_level``,
        ``temperature_celsius``, ``weather_condition``.
    role:
        ``"user"`` (default) selects the wellbeing-coach system prompt.
        ``"doctor"`` selects the clinical assistant system prompt.
    request_id:
        Optional UUID to correlate this context build with a traced request.
        Auto-generated if omitted.

    Returns
    -------
    BuiltContext
        Fully validated context object.  Call ``.model_dump()`` to serialise.

    Raises
    ------
    ValueError
        If ``query`` or ``user_id`` are empty.
    pydantic.ValidationError
        If any input dict contains type-incompatible values.
    """
    if not query or not query.strip():
        raise ValueError("query must not be empty.")
    if not user_id or not user_id.strip():
        raise ValueError("user_id must not be empty.")

    # ── 1. Meta ───────────────────────────────────────────────────────────────
    meta = ContextMeta(
        generated_at=datetime.now(timezone.utc).isoformat(),
        request_id=request_id or str(uuid.uuid4()),
    )

    # ── 2. User profile ───────────────────────────────────────────────────────
    up_raw = user_profile or {}
    profile = UserProfile(
        user_id=user_id,
        name=up_raw.get("name"),
        demographics=Demographics(
            age=up_raw.get("age"),
            gender=up_raw.get("gender"),
            weight_kg=up_raw.get("weight_kg"),
            height_cm=up_raw.get("height_cm"),
        ),
    )

    # ── 3. Medical snapshot ───────────────────────────────────────────────────
    ms_raw = medical_snapshot or {}
    vitals_raw = ms_raw.get("recent_vitals") or {}
    snapshot = MedicalSnapshot(
        last_checkup_date=ms_raw.get("last_checkup_date"),
        known_conditions=ms_raw.get("known_conditions") or [],
        recent_vitals=RecentVitals(
            heart_rate=vitals_raw.get("heart_rate"),
            blood_pressure_systolic=vitals_raw.get("blood_pressure_systolic"),
            blood_pressure_diastolic=vitals_raw.get("blood_pressure_diastolic"),
            spo2_percentage=vitals_raw.get("spo2_percentage"),
        ),
    )

    # ── 4. Wearable data ──────────────────────────────────────────────────────
    wd_raw = wearable_data or {}
    act_raw = wd_raw.get("activity_summary") or {}
    slp_raw = wd_raw.get("sleep_metrics") or {}
    hh_raw = wd_raw.get("heart_health") or {}
    wearable = WearableData(
        device_synced_at=wd_raw.get("device_synced_at"),
        activity_summary=ActivitySummary(
            steps_today=act_raw.get("steps_today"),
            calories_burned=act_raw.get("calories_burned"),
            active_minutes=act_raw.get("active_minutes"),
        ),
        sleep_metrics=SleepMetrics(
            total_sleep_hours=slp_raw.get("total_sleep_hours"),
            sleep_score=slp_raw.get("sleep_score"),
            deep_sleep_minutes=slp_raw.get("deep_sleep_minutes"),
        ),
        heart_health=HeartHealth(
            resting_heart_rate=hh_raw.get("resting_heart_rate"),
            hrv_score=hh_raw.get("hrv_score"),
        ),
    )

    # ── 5. Alerts ─────────────────────────────────────────────────────────────
    # Accept both 'message' and 'reason' keys to be compatible with the DB
    # schema (alerts.reason) and the API contract shape (message).
    alert_items = [
        AlertItem(
            id=a.get("id", str(uuid.uuid4())),
            type=a.get("type", "system"),
            message=a.get("reason") or a.get("message") or "",
            severity=(a.get("severity") or "low").lower(),
            source_metric=a.get("source_metric"),
        )
        for a in (alerts or [])
    ]

    # ── 6. Environment ────────────────────────────────────────────────────────
    env_raw = environment or {}
    env = EnvironmentalContext(
        location_city=env_raw.get("location_city"),
        aqi_level=env_raw.get("aqi_level"),
        temperature_celsius=env_raw.get("temperature_celsius"),
        weather_condition=env_raw.get("weather_condition"),
    )

    # ── 7. RAG knowledge base — trim + normalise ──────────────────────────────
    # Hard-cap chunks, then enforce per-chunk and total character budgets.
    trimmed = retrieved_chunks[:MAX_CHUNKS]
    formatted_chunks: List[RetrievedChunk] = []
    total_chars = 0

    for c in trimmed:
        text = (c.get("text_content") or "").strip()
        text = text[:MAX_CHUNK_CHARS]           # per-chunk cap
        if total_chars + len(text) > MAX_TOTAL_CONTEXT_CHARS:
            break                               # total budget exhausted
        total_chars += len(text)
        formatted_chunks.append(
            RetrievedChunk(
                chunk_id=c.get("chunk_id") or str(uuid.uuid4()),
                text_content=text,
                relevance_score=float(c.get("relevance_score") or 0.0),
                metadata=c.get("metadata") or {},
            )
        )

    rag = RagKnowledgeBase(query_used=query, retrieved_chunks=formatted_chunks)

    # ── 8. Assemble ───────────────────────────────────────────────────────────
    return BuiltContext(
        meta=meta,
        user_profile=profile,
        medical_snapshot=snapshot,
        wearable_data=wearable,
        active_alerts=alert_items,
        environmental_context=env,
        rag_knowledge_base=rag,
        role=role,
    )
