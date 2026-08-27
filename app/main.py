import asyncio
import json
import os
import re
import time
import unicodedata
from contextlib import asynccontextmanager, suppress
from hmac import compare_digest
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Security
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    delete,
    func,
    inspect,
    select,
    text,
    update,
)
from sqlalchemy.exc import SQLAlchemyError

APP_NAME = "Ortho Aux Plugin"
APP_VERSION = "0.5.0"
GATE_VERSION = "2026-08-27.1"
DEFAULT_RETENTION_HOURS = 168
MAX_BODY_BYTES = 65_536


def normalize_database_url(url: str) -> str:
    if url.startswith("postgresql+psycopg://"):
        return url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    return url


def database_url() -> str:
    if configured := os.getenv("DATABASE_URL"):
        return normalize_database_url(configured)

    path = Path(
        os.getenv(
            "ORTHO_AUX_DB",
            str(Path(__file__).resolve().parents[1] / "data" / "ortho_aux.sqlite3"),
        )
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{path}"


def runtime_environment() -> str:
    if os.getenv("RENDER", "").lower() == "true":
        return "production"
    return os.getenv("ORTHO_ENV", "development").strip().lower()


def retention_hours() -> int:
    raw = os.getenv("ORTHO_DATA_RETENTION_HOURS", str(DEFAULT_RETENTION_HOURS))
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError("ORTHO_DATA_RETENTION_HOURS deve ser um inteiro positivo.") from exc
    if value < 1:
        raise RuntimeError("ORTHO_DATA_RETENTION_HOURS deve ser maior que zero.")
    return value


def allowed_data_classifications() -> set[str]:
    raw = os.getenv("ORTHO_ALLOWED_DATA_CLASSIFICATIONS", "synthetic")
    values = {item.strip().lower() for item in raw.split(",") if item.strip()}
    supported = {"synthetic", "deidentified"}
    if not values or not values.issubset(supported):
        raise RuntimeError(
            "ORTHO_ALLOWED_DATA_CLASSIFICATIONS aceita apenas synthetic e deidentified."
        )
    return values


DATABASE_URL = database_url()
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
metadata = MetaData()

sessions_table = Table(
    "sessions",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("created_at", BigInteger, nullable=False),
    Column("mode", String(32)),
    Column("closed", Boolean, nullable=False, default=False),
)

facts_table = Table(
    "facts",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "session_id",
        String(36),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column("field", String(200), nullable=False),
    Column("value_json", Text, nullable=False),
    Column("source", String(40), nullable=False),
    Column("kind", String(40)),
    Column("validated", Boolean, nullable=False, default=False),
    Column("note", Text),
    Column("created_at", BigInteger, nullable=False),
)

consultation_metadata_table = Table(
    "consultation_metadata",
    metadata,
    Column(
        "session_id",
        String(36),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("data_classification", String(32), nullable=False),
    Column("purpose", String(40), nullable=False),
    Column("attested_no_direct_identifiers", Boolean, nullable=False),
    Column("created_at", BigInteger, nullable=False),
    Column("expires_at", BigInteger, nullable=False, index=True),
)

pilot_events_table = Table(
    "pilot_events",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("event_type", String(64), nullable=False, index=True),
    Column("status", String(32), nullable=False),
    Column("value", Integer, nullable=False, default=1),
    Column("created_at", BigInteger, nullable=False, index=True),
)


Source = Literal[
    "PACIENTE",
    "ACOMPANHANTE",
    "TRIAGEM/EQUIPE",
    "ACHADO MÉDICO",
    "INTERPRETAÇÃO MÉDICA",
    "SUGESTÃO IA",
]
FactKind = Literal["RELATO", "ACHADO", "INTERPRETAÇÃO", "SUGESTÃO_IA"]
Mode = Literal[
    "STAFF",
    "PLANTÃO",
    "RESIDÊNCIA",
    "PROVA",
    "PRONTUÁRIO",
    "SISREG",
    "IMAGEM",
    "EXAME",
    "CIRURGIA",
    "CASO",
    "PACIENTE",
    "AUDITOR",
]
Domain = Literal[
    "trauma_adulto",
    "trauma_pediatrico",
    "anatomia",
    "semiologia",
    "trauma_brasil",
    "politrauma",
    "terminologia",
    "tumor",
    "medico_legal",
    "angulos",
]
DataClassification = Literal["synthetic", "deidentified"]
PilotPurpose = Literal["technical_test", "clinical_validation", "training"]
CaseType = Literal["extremity_trauma", "axial_trauma", "non_traumatic", "education_only"]
PatientGroup = Literal["adult", "pediatric"]

SAFETY_KEYS = {
    "choque": "choque",
    "hemorragia": "hemorragia",
    "isquemia_lesao_vascular": "isquemia/lesão vascular",
    "risco_lesao_vascular_oculta": "mecanismo ou lesão com risco vascular oculto",
    "deficit_neurologico_novo_progressivo": "déficit neurológico novo/progressivo",
    "sindrome_compartimental": "síndrome compartimental",
    "fratura_exposta": "fratura exposta",
    "amputacao_esmagamento": "amputação/esmagamento",
    "luxacao_ameacando_pele_vasos": "luxação ameaçando pele/vasos",
    "infeccao_musculoesqueletica_grave": "infecção musculoesquelética grave",
    "trauma_raquimedular_cauda_equina": "trauma raquimedular/cauda equina",
    "politrauma_instavel": "politrauma instável",
}

SOURCE_KIND_RULES = {
    "RELATO": {"PACIENTE", "ACOMPANHANTE", "TRIAGEM/EQUIPE"},
    "ACHADO": {"TRIAGEM/EQUIPE", "ACHADO MÉDICO"},
    "INTERPRETAÇÃO": {"INTERPRETAÇÃO MÉDICA"},
    "SUGESTÃO_IA": {"SUGESTÃO IA"},
}

DIRECT_IDENTIFIER_FIELDS = {
    "nome",
    "nome_completo",
    "nome_do_paciente",
    "cpf",
    "rg",
    "cns",
    "cartao_sus",
    "telefone",
    "celular",
    "email",
    "e_mail",
    "endereco",
    "cep",
    "prontuario",
    "numero_prontuario",
    "data_nascimento",
    "patient_name",
    "full_name",
    "national_id",
    "medical_record",
    "phone",
    "address",
    "date_of_birth",
    "dob",
}

DIRECT_IDENTIFIER_PATTERNS = (
    re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"),
    re.compile(r"\b\d{15}\b"),
    re.compile(r"\b\d{5}-\d{3}\b"),
    re.compile(r"(?:\+?55\s*)?\(?\d{2}\)?\s*9?\d{4}[-\s]\d{4}"),
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
)

LABELED_IDENTIFIER_PATTERN = re.compile(
    r"\b(nome(?:\s+completo|\s+do\s+paciente)?|cpf|rg|cns|cartao\s+sus|"
    r"telefone|celular|e[- ]?mail|endereco|cep|prontuario|data\s+de\s+nascimento)\s*[:=]",
    re.IGNORECASE,
)


def normalize_label(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", "_", ascii_value.lower()).strip("_")


def flatten_text(value: Any) -> List[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        parts: List[str] = []
        for key, nested in value.items():
            parts.append(str(key))
            parts.extend(flatten_text(nested))
        return parts
    if isinstance(value, list):
        parts = []
        for nested in value:
            parts.extend(flatten_text(nested))
        return parts
    return []


def contains_direct_identifier_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, nested in value.items():
            if normalize_label(str(key)) in DIRECT_IDENTIFIER_FIELDS:
                return True
            if contains_direct_identifier_key(nested):
                return True
    elif isinstance(value, list):
        return any(contains_direct_identifier_key(item) for item in value)
    return False


def contains_direct_identifier(field: str, value: Any, note: Optional[str]) -> bool:
    if normalize_label(field) in DIRECT_IDENTIFIER_FIELDS:
        return True
    if contains_direct_identifier_key(value):
        return True
    text_value = "\n".join(flatten_text(value) + ([note] if note else []))
    normalized_text = unicodedata.normalize("NFKD", text_value)
    normalized_text = "".join(char for char in normalized_text if not unicodedata.combining(char))
    if LABELED_IDENTIFIER_PATTERN.search(normalized_text):
        return True
    return any(pattern.search(text_value) for pattern in DIRECT_IDENTIFIER_PATTERNS)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class StartConsultationRequest(StrictModel):
    data_classification: DataClassification
    purpose: PilotPurpose
    attested_no_direct_identifiers: bool

    @model_validator(mode="after")
    def require_attestation(self):
        if not self.attested_no_direct_identifiers:
            raise ValueError(
                "A consulta não pode iniciar sem atestar ausência de identificadores diretos."
            )
        return self


class StartResponse(StrictModel):
    session_id: str
    consultation_id: str
    data_classification: DataClassification
    expires_at: int
    message: str


class Fact(StrictModel):
    field: str = Field(..., min_length=1, max_length=200)
    value: Any
    source: Source
    kind: FactKind
    validated: bool = False
    note: Optional[str] = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_provenance_and_privacy(self):
        if self.source not in SOURCE_KIND_RULES[self.kind]:
            raise ValueError("Origem incompatível com o tipo de fato informado.")
        if self.kind == "SUGESTÃO_IA" and self.validated:
            raise ValueError(
                "Sugestão de IA não pode ser armazenada como validada; registre a decisão médica separadamente."
            )
        serialized = json.dumps(self.value, ensure_ascii=False, separators=(",", ":"))
        if len(serialized.encode("utf-8")) > 8_000:
            raise ValueError("Valor do fato excede o limite de 8 KB.")
        if contains_direct_identifier(self.field, self.value, self.note):
            raise ValueError("Possível identificador direto detectado; remova-o antes do envio.")
        return self


class CaptureRequest(StrictModel):
    facts: List[Fact] = Field(default_factory=list, max_length=50)
    mode: Optional[Mode] = None


class SafetyFlags(StrictModel):
    choque: bool
    hemorragia: bool
    isquemia_lesao_vascular: bool
    risco_lesao_vascular_oculta: bool
    deficit_neurologico_novo_progressivo: bool
    sindrome_compartimental: bool
    fratura_exposta: bool
    amputacao_esmagamento: bool
    luxacao_ameacando_pele_vasos: bool
    infeccao_musculoesqueletica_grave: bool
    trauma_raquimedular_cauda_equina: bool
    politrauma_instavel: bool


class ClinicalContext(StrictModel):
    case_type: CaseType
    patient_group: PatientGroup
    pediatric_specific_review_documented: bool = False


class Intervention(StrictModel):
    performed: bool = False
    kind: Optional[str] = Field(default=None, max_length=200)
    may_change_nv: bool = False
    post_nv_documented: bool = False


class IdentityCheck(StrictModel):
    possible_patient_mix: bool = False
    laterality_conflict: bool = False
    details: Optional[str] = Field(default=None, max_length=1000)


class ProcedureCheck(StrictModel):
    procedure_reported: bool = False
    minimum_data_complete: bool = True


class NeurovascularCheck(StrictModel):
    baseline_documented: bool = False
    post_intervention_documented: bool = False
    unable_to_assess: bool = False
    not_applicable: bool = False
    concern_for_deficit: bool = False
    distal_pulse_present: Optional[bool] = None


class SafetyResponse(StrictModel):
    urgent_actions_documented: bool = False


class FinalizeRequest(StrictModel):
    context: ClinicalContext
    neurovascular: NeurovascularCheck
    safety: SafetyFlags
    identity: IdentityCheck = Field(default_factory=IdentityCheck)
    safety_response: SafetyResponse = Field(default_factory=SafetyResponse)
    intervention: Intervention = Field(default_factory=Intervention)
    procedure: ProcedureCheck = Field(default_factory=ProcedureCheck)
    critical_field_pending: bool = False
    unvalidated_ai_suggestion_as_decision: bool = False


class RouteRequest(StrictModel):
    domain: Domain


class EvidenceSearchRequest(StrictModel):
    query: str = Field(..., min_length=3, max_length=500)
    domain: Optional[Domain] = None
    limit: int = Field(default=5, ge=1, le=10)

    @model_validator(mode="after")
    def reject_identifiers(self):
        if contains_direct_identifier("evidence_query", self.query, None):
            raise ValueError("Remova identificadores diretos da consulta de evidência.")
        return self


class PilotFeedbackRequest(StrictModel):
    disposition: Literal["accepted", "edited", "rejected"]
    documentation_seconds: int = Field(ge=1, le=14_400)
    corrections_count: int = Field(default=0, ge=0, le=500)
    false_alerts_count: int = Field(default=0, ge=0, le=100)
    technical_failure: bool = False
    privacy_incident: bool = False


api_key_header = APIKeyHeader(name="X-Ortho-Api-Key", auto_error=False)


def require_api_key(api_key: Optional[str] = Security(api_key_header)) -> None:
    expected = os.getenv("ORTHO_API_KEY")
    if expected and not compare_digest(api_key or "", expected):
        raise HTTPException(status_code=401, detail="Chave de API inválida ou ausente.")
    if not expected and runtime_environment() == "production":
        raise HTTPException(status_code=503, detail="Autenticação de produção indisponível.")


def validate_runtime_configuration() -> None:
    allowed = allowed_data_classifications()
    if "deidentified" in allowed and os.getenv("ORTHO_GOVERNANCE_APPROVED", "").lower() != "true":
        raise RuntimeError(
            "Dados desidentificados exigem ORTHO_GOVERNANCE_APPROVED=true após aprovação formal."
        )
    if runtime_environment() == "production":
        if not os.getenv("ORTHO_API_KEY"):
            raise RuntimeError("ORTHO_API_KEY é obrigatória em produção.")
        if DATABASE_URL.startswith("sqlite"):
            raise RuntimeError("DATABASE_URL PostgreSQL é obrigatória em produção.")
    retention_hours()


def record_pilot_event(connection, event_type: str, status: str = "ok", value: int = 1) -> None:
    connection.execute(
        pilot_events_table.insert().values(
            event_type=event_type,
            status=status,
            value=value,
            created_at=int(time.time()),
        )
    )


def delete_session_rows(connection, session_ids: List[str]) -> None:
    if not session_ids:
        return
    connection.execute(delete(facts_table).where(facts_table.c.session_id.in_(session_ids)))
    connection.execute(
        delete(consultation_metadata_table).where(
            consultation_metadata_table.c.session_id.in_(session_ids)
        )
    )
    connection.execute(delete(sessions_table).where(sessions_table.c.id.in_(session_ids)))


def purge_unclassified_and_expired_sessions() -> Dict[str, int]:
    now = int(time.time())
    with engine.begin() as connection:
        all_sessions = set(connection.execute(select(sessions_table.c.id)).scalars().all())
        classified_sessions = set(
            connection.execute(select(consultation_metadata_table.c.session_id)).scalars().all()
        )
        unclassified = sorted(all_sessions - classified_sessions)
        expired = (
            connection.execute(
                select(consultation_metadata_table.c.session_id).where(
                    consultation_metadata_table.c.expires_at <= now
                )
            )
            .scalars()
            .all()
        )
        delete_session_rows(connection, sorted(set(unclassified + list(expired))))
        if unclassified:
            record_pilot_event(
                connection, "retention_purge", "legacy_unclassified", len(unclassified)
            )
        if expired:
            record_pilot_event(connection, "retention_purge", "expired", len(expired))
    return {"legacy_unclassified": len(unclassified), "expired": len(expired)}


def init_db() -> None:
    metadata.create_all(engine)
    columns = {column["name"] for column in inspect(engine).get_columns("facts")}
    if "kind" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE facts ADD COLUMN kind VARCHAR(40)"))
    purge_unclassified_and_expired_sessions()


async def retention_worker() -> None:
    while True:
        await asyncio.sleep(3600)
        await asyncio.to_thread(purge_unclassified_and_expired_sessions)


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_runtime_configuration()
    init_db()
    cleanup_task = asyncio.create_task(retention_worker())
    try:
        yield
    finally:
        cleanup_task.cancel()
        with suppress(asyncio.CancelledError):
            await cleanup_task


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=(
        "Auxiliar determinístico para piloto sintético de segurança, documentação, "
        "auditoria e roteamento ortopédico. Não substitui avaliação médica presencial."
    ),
    servers=[{"url": "https://ortho-aux-plugin.onrender.com"}],
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def sanitized_validation_error(request: Request, exc: RequestValidationError):
    errors = [
        {
            "location": list(error.get("loc", ())),
            "message": error.get("msg", "Entrada inválida."),
            "type": error.get("type", "validation_error"),
        }
        for error in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": errors})


@app.middleware("http")
async def request_guard(request: Request, call_next):
    request_id = str(uuid4())
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            too_large = int(content_length) > MAX_BODY_BYTES
        except ValueError:
            too_large = True
        if too_large:
            return JSONResponse(
                status_code=413,
                content={"detail": "Corpo da requisição excede 64 KB.", "request_id": request_id},
                headers={"X-Request-ID": request_id},
            )
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


def get_session(session_id: str, connection=None) -> Dict[str, Any]:
    if connection is None:
        with engine.connect() as local_connection:
            row = (
                local_connection.execute(
                    select(sessions_table).where(sessions_table.c.id == session_id)
                )
                .mappings()
                .first()
            )
    else:
        row = (
            connection.execute(
                select(sessions_table).where(sessions_table.c.id == session_id).with_for_update()
            )
            .mappings()
            .first()
        )
    if not row:
        raise HTTPException(status_code=404, detail="Consulta não encontrada.")
    return dict(row)


def run_gate(req: FinalizeRequest):
    alerts: List[str] = []
    blockers: List[str] = []
    priority_alert = False

    for key, label in SAFETY_KEYS.items():
        if getattr(req.safety, key):
            alerts.append(f"ALERTA CLÍNICO PRIORITÁRIO — {label}.")
            priority_alert = True

    if req.identity.possible_patient_mix:
        blockers.append(
            "POSSÍVEL MISTURA DE PACIENTE — confirme se este conteúdo pertence ao paciente atual ou inicie nova consulta."
        )
    if req.identity.laterality_conflict:
        blockers.append("Lateralidade conflitante — corrigir antes de finalizar.")

    baseline_states = sum(
        [
            req.neurovascular.baseline_documented,
            req.neurovascular.unable_to_assess,
            req.neurovascular.not_applicable,
        ]
    )
    if baseline_states == 0:
        blockers.append(
            "Avaliação neurovascular basal sem estado explícito — documentar, justificar impossibilidade ou marcar não aplicável."
        )
    elif baseline_states > 1:
        blockers.append(
            "Estados neurovasculares basais conflitantes — registrar apenas uma situação."
        )

    if req.context.case_type == "extremity_trauma" and req.neurovascular.not_applicable:
        blockers.append(
            "Trauma de extremidade não pode encerrar com avaliação neurovascular marcada como não aplicável."
        )
    if req.neurovascular.unable_to_assess:
        alerts.append(
            "AVALIAÇÃO LIMITADA — exame neurovascular não pôde ser concluído; documentar a limitação e reavaliar conforme o contexto."
        )

    post_nv_documented = (
        req.intervention.post_nv_documented or req.neurovascular.post_intervention_documented
    )
    if req.intervention.performed and req.intervention.may_change_nv and not post_nv_documented:
        blockers.append(
            "PENDÊNCIA ANTES DE FINALIZAR — avaliação neurovascular pós-imobilização/intervenção não documentada."
        )

    if req.neurovascular.concern_for_deficit:
        alerts.append(
            "ALERTA CLÍNICO PRIORITÁRIO — déficit neurovascular exige correlação e conduta documentada."
        )
        priority_alert = True

    if (
        req.context.patient_group == "pediatric"
        and not req.context.pediatric_specific_review_documented
    ):
        blockers.append(
            "Revisão pediátrica específica pendente — considerar idade, fise/crescimento e exame adaptado antes de finalizar."
        )

    if priority_alert and not req.safety_response.urgent_actions_documented:
        blockers.append(
            "Alerta prioritário sem resposta documentada — registrar ações urgentes e escalonamento clínico antes de finalizar."
        )
    if req.procedure.procedure_reported and not req.procedure.minimum_data_complete:
        blockers.append("Procedimento sem dados mínimos — completar antes de finalizar.")
    if req.critical_field_pending:
        blockers.append("Campo crítico pendente — completar antes de finalizar.")
    if req.unvalidated_ai_suggestion_as_decision:
        blockers.append(
            "Sugestão IA não validada foi tratada como decisão — separar/validar antes de finalizar."
        )
    return alerts, blockers


def source_mapping(domain: Domain):
    mapping = {
        "trauma_adulto": {
            "preferred": "Rockwood and Green's Fractures in Adults",
            "use": ["fraturas", "luxações", "classificação", "imagem", "fixação", "complicações"],
        },
        "trauma_pediatrico": {
            "preferred": "Rockwood and Wilkins' Fractures in Children",
            "use": [
                "fise",
                "crescimento",
                "remodelamento",
                "fraturas pediátricas",
                "complicações do crescimento",
            ],
        },
        "anatomia": {
            "preferred": "Netter Atlas de Anatomia Ortopédica",
            "use": ["topografia", "músculos", "tendões", "nervos", "vasos", "acessos"],
        },
        "semiologia": {
            "preferred": "Manual Ilustrado do Exame Ortopédico",
            "use": ["inspeção", "palpação", "ADM", "força", "testes especiais"],
        },
        "trauma_brasil": {
            "preferred": "Manual de Trauma Ortopédico — SBOT",
            "use": ["contexto brasileiro", "revisão operacional"],
        },
        "politrauma": {
            "preferred": "ATLS / materiais de politrauma / INEM",
            "use": ["ABCDE", "estabilização", "prioridades", "transferência"],
        },
        "terminologia": {
            "preferred": "Glossário MS/INTO",
            "use": ["padronização PT/EN", "nomenclatura"],
        },
        "tumor": {
            "preferred": "Jesus-Garcia — Tumores Ósseos",
            "use": ["diagnóstico", "estadiamento conceitual", "princípios de biópsia"],
        },
        "medico_legal": {
            "preferred": "Traumatologia Forense",
            "use": ["descrição de ferimentos", "mecanismo lesivo", "contexto pericial"],
        },
        "angulos": {
            "preferred": "Fonte validada para método/incidência/referência/faixa contextualizada",
            "use": ["mensuração somente com método validado"],
        },
    }
    return mapping[domain]


def create_consultation(req: StartConsultationRequest):
    if req.data_classification not in allowed_data_classifications():
        raise HTTPException(
            status_code=403,
            detail="Classificação de dados não liberada para este estágio do piloto.",
        )
    purge_unclassified_and_expired_sessions()
    session_id = str(uuid4())
    now = int(time.time())
    expires_at = now + retention_hours() * 3600
    with engine.begin() as connection:
        connection.execute(
            sessions_table.insert().values(
                id=session_id,
                created_at=now,
                mode=None,
                closed=False,
            )
        )
        connection.execute(
            consultation_metadata_table.insert().values(
                session_id=session_id,
                data_classification=req.data_classification,
                purpose=req.purpose,
                attested_no_direct_identifiers=req.attested_no_direct_identifiers,
                created_at=now,
                expires_at=expires_at,
            )
        )
        record_pilot_event(connection, "consultation_started", req.data_classification)
    return {
        "session_id": session_id,
        "consultation_id": session_id,
        "data_classification": req.data_classification,
        "expires_at": expires_at,
        "message": (
            "Consulta sintética iniciada. Documentação de piloto ativa."
            if req.data_classification == "synthetic"
            else "Consulta desidentificada iniciada sob governança aprovada."
        ),
    }


def capture_facts(session_id: str, req: CaptureRequest):
    now = int(time.time())
    rows = [
        {
            "session_id": session_id,
            "field": fact.field,
            "value_json": json.dumps(fact.value, ensure_ascii=False),
            "source": fact.source,
            "kind": fact.kind,
            "validated": fact.validated,
            "note": fact.note,
            "created_at": now,
        }
        for fact in req.facts
    ]
    with engine.begin() as connection:
        session = get_session(session_id, connection)
        if session["closed"]:
            raise HTTPException(status_code=409, detail="Consulta já finalizada.")
        if rows:
            connection.execute(facts_table.insert(), rows)
        if req.mode:
            connection.execute(
                update(sessions_table)
                .where(sessions_table.c.id == session_id)
                .values(mode=req.mode)
            )
        record_pilot_event(connection, "capture", "ok", len(rows))
    return {
        "status": "registrado",
        "facts_recorded": len(rows),
        "message": "Fatos sem identificadores diretos registrados.",
    }


def read_session_state(session_id: str):
    session = get_session(session_id)
    with engine.connect() as connection:
        rows = (
            connection.execute(
                select(
                    facts_table.c.field,
                    facts_table.c.value_json,
                    facts_table.c.source,
                    facts_table.c.kind,
                    facts_table.c.validated,
                    facts_table.c.note,
                    facts_table.c.created_at,
                )
                .where(facts_table.c.session_id == session_id)
                .order_by(facts_table.c.id)
            )
            .mappings()
            .all()
        )
        policy = (
            connection.execute(
                select(consultation_metadata_table).where(
                    consultation_metadata_table.c.session_id == session_id
                )
            )
            .mappings()
            .first()
        )
    facts = [
        {
            "field": row["field"],
            "value": json.loads(row["value_json"]),
            "source": row["source"],
            "kind": row["kind"] or "LEGACY_UNCLASSIFIED",
            "validated": bool(row["validated"]),
            "note": row["note"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]
    return {
        "session": session,
        "data_policy": dict(policy) if policy else None,
        "facts": facts,
        "human_review_required": True,
    }


def audit_case(session_id: str, req: FinalizeRequest):
    get_session(session_id)
    alerts, blockers = run_gate(req)
    with engine.begin() as connection:
        record_pilot_event(
            connection,
            "audit",
            "blocked" if blockers else "clear",
            max(1, len(blockers)),
        )
    return {
        "gate_version": GATE_VERSION,
        "alerts": alerts,
        "blockers": blockers,
        "can_finalize": len(blockers) == 0,
        "human_review_required": True,
    }


def finalize_case(session_id: str, req: FinalizeRequest):
    alerts, blockers = run_gate(req)
    if blockers:
        get_session(session_id)
        with engine.begin() as connection:
            record_pilot_event(connection, "finalize", "blocked", len(blockers))
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Finalização bloqueada.",
                "gate_version": GATE_VERSION,
                "blockers": blockers,
                "alerts": alerts,
            },
        )

    with engine.begin() as connection:
        session = get_session(session_id, connection)
        if session["closed"]:
            raise HTTPException(status_code=409, detail="Consulta já finalizada.")
        rows = (
            connection.execute(
                select(
                    facts_table.c.field,
                    facts_table.c.value_json,
                    facts_table.c.source,
                    facts_table.c.kind,
                    facts_table.c.validated,
                    facts_table.c.note,
                    facts_table.c.created_at,
                )
                .where(facts_table.c.session_id == session_id)
                .order_by(facts_table.c.id)
            )
            .mappings()
            .all()
        )
        result = connection.execute(
            update(sessions_table)
            .where(sessions_table.c.id == session_id)
            .where(sessions_table.c.closed.is_(False))
            .values(closed=True)
        )
        if result.rowcount != 1:
            raise HTTPException(status_code=409, detail="Consulta já finalizada.")
        record_pilot_event(connection, "finalize", "ok")

    facts = [
        {
            "field": row["field"],
            "value": json.loads(row["value_json"]),
            "source": row["source"],
            "kind": row["kind"],
            "validated": bool(row["validated"]),
            "note": row["note"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]
    return {
        "status": "draft_ready",
        "gate_version": GATE_VERSION,
        "alerts": alerts,
        "mode": session.get("mode"),
        "facts": facts,
        "human_review_required": True,
        "message": "Gate documental liberado; rascunho ainda exige validação médica.",
    }


def delete_consultation(session_id: str):
    with engine.begin() as connection:
        get_session(session_id, connection)
        delete_session_rows(connection, [session_id])
        record_pilot_event(connection, "consultation_deleted", "ok")
    return {"status": "deleted", "consultation_id": session_id}


def record_pilot_feedback(session_id: str, req: PilotFeedbackRequest):
    get_session(session_id)
    with engine.begin() as connection:
        record_pilot_event(connection, "feedback", req.disposition)
        record_pilot_event(
            connection, "documentation_seconds", req.disposition, req.documentation_seconds
        )
        record_pilot_event(connection, "corrections", req.disposition, req.corrections_count)
        record_pilot_event(connection, "false_alerts", req.disposition, req.false_alerts_count)
        if req.technical_failure:
            record_pilot_event(connection, "technical_failure", "reported")
        if req.privacy_incident:
            record_pilot_event(connection, "privacy_incident", "reported")
    return {
        "status": "recorded",
        "contains_clinical_text": False,
        "incident_action_required": req.privacy_incident,
    }


def read_pilot_metrics():
    with engine.connect() as connection:
        rows = (
            connection.execute(
                select(
                    pilot_events_table.c.event_type,
                    pilot_events_table.c.status,
                    func.count(pilot_events_table.c.id).label("occurrences"),
                    func.sum(pilot_events_table.c.value).label("value_total"),
                )
                .group_by(pilot_events_table.c.event_type, pilot_events_table.c.status)
                .order_by(pilot_events_table.c.event_type, pilot_events_table.c.status)
            )
            .mappings()
            .all()
        )
    return {
        "generated_at": int(time.time()),
        "contains_clinical_text": False,
        "metrics": [dict(row) for row in rows],
    }


@app.get("/", operation_id="getApiInfo", tags=["system"])
def root():
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "status": "ready",
        "profile": "synthetic_pilot",
        "allowed_data_classifications": sorted(allowed_data_classifications()),
        "docs": "/docs",
        "openapi": "/openapi.json",
        "auth": "required in production via X-Ortho-Api-Key",
        "human_review_required": True,
    }


@app.get("/health", operation_id="getApiHealth", tags=["system"])
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Banco de dados indisponível.") from exc
    return {
        "ok": True,
        "service": APP_NAME,
        "version": APP_VERSION,
        "database": "ok",
        "profile": "synthetic_pilot",
    }


@app.post(
    "/session/start",
    response_model=StartResponse,
    operation_id="startOrthoSession",
    tags=["legacy"],
    dependencies=[Depends(require_api_key)],
    include_in_schema=False,
)
def start_legacy_session():
    return create_consultation(
        StartConsultationRequest(
            data_classification="synthetic",
            purpose="technical_test",
            attested_no_direct_identifiers=True,
        )
    )


@app.post(
    "/v1/consultations",
    response_model=StartResponse,
    operation_id="startOrthoConsultation",
    tags=["consultations"],
    dependencies=[Depends(require_api_key)],
)
def start_consultation(req: StartConsultationRequest):
    return create_consultation(req)


@app.post(
    "/capture",
    operation_id="captureOrthoFacts",
    tags=["legacy"],
    dependencies=[Depends(require_api_key)],
    include_in_schema=False,
)
def capture(req: CaptureRequest, x_session_id: str = Header(...)):
    return capture_facts(x_session_id, req)


@app.post(
    "/v1/consultations/{consultation_id}/events",
    operation_id="captureOrthoConsultationEvent",
    tags=["consultations"],
    dependencies=[Depends(require_api_key)],
)
def capture_consultation_event(consultation_id: str, req: CaptureRequest):
    return capture_facts(consultation_id, req)


@app.get(
    "/session/state",
    operation_id="getOrthoSessionState",
    tags=["legacy"],
    dependencies=[Depends(require_api_key)],
    include_in_schema=False,
)
def session_state(x_session_id: str = Header(...)):
    return read_session_state(x_session_id)


@app.get(
    "/v1/consultations/{consultation_id}",
    operation_id="getOrthoConsultationState",
    tags=["consultations"],
    dependencies=[Depends(require_api_key)],
)
def consultation_state(consultation_id: str):
    return read_session_state(consultation_id)


@app.delete(
    "/v1/consultations/{consultation_id}",
    operation_id="deleteOrthoConsultation",
    tags=["consultations"],
    dependencies=[Depends(require_api_key)],
)
def remove_consultation(consultation_id: str):
    return delete_consultation(consultation_id)


@app.post(
    "/audit",
    operation_id="auditOrthoCase",
    tags=["legacy"],
    dependencies=[Depends(require_api_key)],
    include_in_schema=False,
)
def audit(req: FinalizeRequest, x_session_id: str = Header(...)):
    return audit_case(x_session_id, req)


@app.post(
    "/v1/consultations/{consultation_id}/audit",
    operation_id="auditOrthoConsultation",
    tags=["consultations"],
    dependencies=[Depends(require_api_key)],
)
def audit_consultation(consultation_id: str, req: FinalizeRequest):
    return audit_case(consultation_id, req)


@app.post(
    "/finalize",
    operation_id="finalizeOrthoCase",
    tags=["legacy"],
    dependencies=[Depends(require_api_key)],
    include_in_schema=False,
)
def finalize(req: FinalizeRequest, x_session_id: str = Header(...)):
    return finalize_case(x_session_id, req)


@app.post(
    "/v1/consultations/{consultation_id}/finalize",
    operation_id="finalizeOrthoConsultation",
    tags=["consultations"],
    dependencies=[Depends(require_api_key)],
)
def finalize_consultation(consultation_id: str, req: FinalizeRequest):
    return finalize_case(consultation_id, req)


@app.post(
    "/v1/consultations/{consultation_id}/pilot-feedback",
    operation_id="recordOrthoPilotFeedback",
    tags=["pilot"],
    dependencies=[Depends(require_api_key)],
)
def pilot_feedback(consultation_id: str, req: PilotFeedbackRequest):
    return record_pilot_feedback(consultation_id, req)


@app.get(
    "/v1/pilot/metrics",
    operation_id="getOrthoPilotMetrics",
    tags=["pilot"],
    dependencies=[Depends(require_api_key)],
)
def pilot_metrics():
    return read_pilot_metrics()


@app.post(
    "/source-route",
    operation_id="routeOrthoSource",
    tags=["legacy"],
    dependencies=[Depends(require_api_key)],
    include_in_schema=False,
)
def source_route(req: RouteRequest):
    return source_mapping(req.domain)


@app.post(
    "/v1/evidence/source-route",
    operation_id="routeOrthopedicSource",
    tags=["evidence"],
    dependencies=[Depends(require_api_key)],
)
def v1_source_route(req: RouteRequest):
    return source_mapping(req.domain)


@app.post(
    "/v1/evidence/search",
    operation_id="searchOrthopedicEvidence",
    tags=["evidence"],
    dependencies=[Depends(require_api_key)],
)
def evidence_search(req: EvidenceSearchRequest):
    domain = req.domain or "trauma_adulto"
    return {
        "query": req.query,
        "domain": domain,
        "routing": source_mapping(domain),
        "items": [],
        "limit": req.limit,
        "copyright_policy": (
            "Nenhum trecho protegido é exposto por este MVP; retorno limitado a roteamento, metadados e síntese futura."
        ),
        "message": "Busca RAG ainda não conectada. Use o roteamento de fonte como camada segura inicial.",
    }
