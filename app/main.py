
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, Header, HTTPException, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from typing import Literal, Optional, List, Dict, Any
from uuid import uuid4
from pathlib import Path
import sqlite3, json, os, time

APP_NAME = "Ortho Aux Plugin"
APP_VERSION = "0.3.0"
DB_PATH = Path(
    os.getenv(
        "ORTHO_AUX_DB",
        str(Path(__file__).resolve().parents[1] / "data" / "ortho_aux.sqlite3"),
    )
)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

Source = Literal[
    "PACIENTE","ACOMPANHANTE","TRIAGEM/EQUIPE",
    "ACHADO MÉDICO","INTERPRETAÇÃO MÉDICA","SUGESTÃO IA"
]

Mode = Literal[
    "STAFF","PLANTÃO","RESIDÊNCIA","PROVA","PRONTUÁRIO","SISREG",
    "IMAGEM","EXAME","CIRURGIA","CASO","PACIENTE","AUDITOR"
]

SAFETY_KEYS = {
    "choque": "choque",
    "hemorragia": "hemorragia",
    "isquemia_lesao_vascular": "isquemia/lesão vascular",
    "deficit_neurologico_novo_progressivo": "déficit neurológico novo/progressivo",
    "sindrome_compartimental": "síndrome compartimental",
    "fratura_exposta": "fratura exposta",
    "amputacao_esmagamento": "amputação/esmagamento",
    "luxacao_ameacando_pele_vasos": "luxação ameaçando pele/vasos",
    "infeccao_musculoesqueletica_grave": "infecção musculoesquelética grave",
    "trauma_raquimedular_cauda_equina": "trauma raquimedular/cauda equina",
    "politrauma_instavel": "politrauma instável",
}

api_key_header = APIKeyHeader(name="X-Ortho-Api-Key", auto_error=False)

def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = db()
    con.execute("""
        CREATE TABLE IF NOT EXISTS sessions(
            id TEXT PRIMARY KEY,
            created_at INTEGER NOT NULL,
            mode TEXT,
            closed INTEGER NOT NULL DEFAULT 0
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS facts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            field TEXT NOT NULL,
            value_json TEXT NOT NULL,
            source TEXT NOT NULL,
            validated INTEGER NOT NULL DEFAULT 0,
            note TEXT,
            created_at INTEGER NOT NULL
        )
    """)
    con.commit()
    con.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=(
        "Auxiliar determinístico de segurança, documentação, auditoria e "
        "roteamento ortopédico. Não substitui validação médica presencial."
    ),
    lifespan=lifespan,
)

def require_api_key(api_key: Optional[str] = Security(api_key_header)) -> None:
    expected = os.getenv("ORTHO_API_KEY")
    if expected and api_key != expected:
        raise HTTPException(status_code=401, detail="Chave de API inválida ou ausente.")

class StartResponse(BaseModel):
    session_id: str
    consultation_id: str
    message: str

class Fact(BaseModel):
    field: str
    value: Any
    source: Source
    validated: bool = False
    note: Optional[str] = None

class CaptureRequest(BaseModel):
    facts: List[Fact] = Field(default_factory=list)
    mode: Optional[Mode] = None

class SafetyFlags(BaseModel):
    choque: bool = False
    hemorragia: bool = False
    isquemia_lesao_vascular: bool = False
    deficit_neurologico_novo_progressivo: bool = False
    sindrome_compartimental: bool = False
    fratura_exposta: bool = False
    amputacao_esmagamento: bool = False
    luxacao_ameacando_pele_vasos: bool = False
    infeccao_musculoesqueletica_grave: bool = False
    trauma_raquimedular_cauda_equina: bool = False
    politrauma_instavel: bool = False

class Intervention(BaseModel):
    performed: bool = False
    kind: Optional[str] = None
    may_change_nv: bool = False
    post_nv_documented: bool = False

class IdentityCheck(BaseModel):
    possible_patient_mix: bool = False
    laterality_conflict: bool = False
    details: Optional[str] = None

class ProcedureCheck(BaseModel):
    procedure_reported: bool = False
    minimum_data_complete: bool = True

class NeurovascularCheck(BaseModel):
    baseline_documented: bool = False
    post_intervention_documented: bool = False
    unable_to_assess: bool = False
    not_applicable: bool = False
    concern_for_deficit: bool = False

class FinalizeRequest(BaseModel):
    identity: IdentityCheck = Field(default_factory=IdentityCheck)
    safety: SafetyFlags = Field(default_factory=SafetyFlags)
    intervention: Intervention = Field(default_factory=Intervention)
    procedure: ProcedureCheck = Field(default_factory=ProcedureCheck)
    neurovascular: NeurovascularCheck = Field(default_factory=NeurovascularCheck)
    critical_field_pending: bool = False
    unvalidated_ai_suggestion_as_decision: bool = False

Domain = Literal[
    "trauma_adulto","trauma_pediatrico","anatomia","semiologia",
    "trauma_brasil","politrauma","terminologia","tumor","medico_legal","angulos"
]

class RouteRequest(BaseModel):
    domain: Domain

class EvidenceSearchRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)
    domain: Optional[Domain] = None
    limit: int = Field(default=5, ge=1, le=10)

def get_session(session_id: str) -> Dict[str, Any]:
    con = db()
    row = con.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
    con.close()
    if not row:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")
    return dict(row)

def run_gate(req: FinalizeRequest):
    alerts, blockers = [], []
    for key, label in SAFETY_KEYS.items():
        if getattr(req.safety, key):
            alerts.append(f"ALERTA CLÍNICO PRIORITÁRIO — {label}.")
    if req.identity.possible_patient_mix:
        blockers.append("POSSÍVEL MISTURA DE PACIENTE — confirme se este conteúdo pertence ao paciente atual ou inicie nova consulta.")
    if req.identity.laterality_conflict:
        blockers.append("Lateralidade conflitante — corrigir antes de finalizar.")
    if req.intervention.performed and req.intervention.may_change_nv and not req.intervention.post_nv_documented:
        blockers.append("PENDÊNCIA ANTES DE FINALIZAR — Avaliação neurovascular pós-imobilização/intervenção não documentada.")
    if req.neurovascular.concern_for_deficit:
        alerts.append("ALERTA CLÍNICO PRIORITÁRIO — déficit neurovascular exige correlação e conduta documentada.")
    if req.procedure.procedure_reported and not req.procedure.minimum_data_complete:
        blockers.append("Procedimento sem dados mínimos — completar antes de finalizar.")
    if req.critical_field_pending:
        blockers.append("Campo crítico pendente — completar antes de finalizar.")
    if req.unvalidated_ai_suggestion_as_decision:
        blockers.append("Sugestão IA não validada foi tratada como decisão — separar/validar antes de finalizar.")
    return alerts, blockers

def source_mapping(domain: Domain):
    mapping = {
        "trauma_adulto": {"preferred": "Rockwood and Green's Fractures in Adults", "use": ["fraturas","luxações","classificação","imagem","fixação","complicações"]},
        "trauma_pediatrico": {"preferred": "Rockwood and Wilkins' Fractures in Children", "use": ["fise","crescimento","remodelamento","fraturas pediátricas","complicações do crescimento"]},
        "anatomia": {"preferred": "Netter Atlas de Anatomia Ortopédica", "use": ["topografia","músculos","tendões","nervos","vasos","acessos"]},
        "semiologia": {"preferred": "Manual Ilustrado do Exame Ortopédico", "use": ["inspeção","palpação","ADM","força","testes especiais"]},
        "trauma_brasil": {"preferred": "Manual de Trauma Ortopédico — SBOT", "use": ["contexto brasileiro","revisão operacional"]},
        "politrauma": {"preferred": "ATLS / materiais de politrauma / INEM", "use": ["ABCDE","estabilização","prioridades","transferência"]},
        "terminologia": {"preferred": "Glossário MS/INTO", "use": ["padronização PT/EN","nomenclatura"]},
        "tumor": {"preferred": "Jesus-Garcia — Tumores Ósseos", "use": ["diagnóstico","estadiamento conceitual","princípios de biópsia"]},
        "medico_legal": {"preferred": "Traumatologia Forense", "use": ["descrição de ferimentos","mecanismo lesivo","contexto pericial"]},
        "angulos": {"preferred": "Fonte validada para método/incidência/referência/faixa contextualizada", "use": ["mensuração somente com método validado"]},
    }
    return mapping[domain]

def capture_facts(session_id: str, req: CaptureRequest):
    get_session(session_id)
    con = db()
    for fact in req.facts:
        con.execute(
            "INSERT INTO facts(session_id,field,value_json,source,validated,note,created_at) VALUES(?,?,?,?,?,?,?)",
            (session_id, fact.field, json.dumps(fact.value, ensure_ascii=False), fact.source, 1 if fact.validated else 0, fact.note, int(time.time()))
        )
    if req.mode:
        con.execute("UPDATE sessions SET mode=? WHERE id=?", (req.mode, session_id))
    con.commit()
    con.close()
    return {"status": "registrado", "message": "Registrado."}

def read_session_state(session_id: str):
    s = get_session(session_id)
    con = db()
    rows = con.execute("SELECT field,value_json,source,validated,note,created_at FROM facts WHERE session_id=? ORDER BY id", (session_id,)).fetchall()
    con.close()
    facts = [{
        "field": r["field"], "value": json.loads(r["value_json"]), "source": r["source"],
        "validated": bool(r["validated"]), "note": r["note"], "created_at": r["created_at"]
    } for r in rows]
    return {"session": s, "facts": facts}

def audit_case(session_id: str, req: FinalizeRequest):
    get_session(session_id)
    alerts, blockers = run_gate(req)
    return {"alerts": alerts, "blockers": blockers, "can_finalize": len(blockers) == 0}

def finalize_case(session_id: str, req: FinalizeRequest):
    s = get_session(session_id)
    alerts, blockers = run_gate(req)
    if blockers:
        raise HTTPException(status_code=409, detail={"message": "Finalização bloqueada.", "blockers": blockers, "alerts": alerts})
    con = db()
    rows = con.execute("SELECT field,value_json,source,validated,note,created_at FROM facts WHERE session_id=? ORDER BY id", (session_id,)).fetchall()
    con.execute("UPDATE sessions SET closed=1 WHERE id=?", (session_id,))
    con.commit()
    con.close()
    facts = [{
        "field": r["field"], "value": json.loads(r["value_json"]), "source": r["source"],
        "validated": bool(r["validated"]), "note": r["note"], "created_at": r["created_at"]
    } for r in rows]
    return {"status": "ok", "alerts": alerts, "mode": s.get("mode"), "facts": facts, "message": "Gate documental liberado para finalização pelo médico."}

@app.get("/", operation_id="getApiInfo", tags=["system"])
def root():
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "status": "ready",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "auth": "optional via X-Ortho-Api-Key when ORTHO_API_KEY is configured",
    }

@app.get("/health", operation_id="getApiHealth", tags=["system"])
def health():
    return {"ok": True, "service": APP_NAME, "version": APP_VERSION}

@app.post("/session/start", response_model=StartResponse, operation_id="startOrthoSession", tags=["legacy"], dependencies=[Depends(require_api_key)])
@app.post("/v1/consultations", response_model=StartResponse, operation_id="startOrthoConsultation", tags=["consultations"], dependencies=[Depends(require_api_key)])
def start_session():
    session_id = str(uuid4())
    con = db()
    con.execute("INSERT INTO sessions(id, created_at, mode, closed) VALUES(?,?,?,0)", (session_id, int(time.time()), None))
    con.commit()
    con.close()
    return {"session_id": session_id, "consultation_id": session_id, "message": "Consulta iniciada. Documentação clínica ativa."}

@app.post("/capture", operation_id="captureOrthoFacts", tags=["legacy"], dependencies=[Depends(require_api_key)])
def capture(req: CaptureRequest, x_session_id: str = Header(...)):
    return capture_facts(x_session_id, req)

@app.post("/v1/consultations/{consultation_id}/events", operation_id="captureOrthoConsultationEvent", tags=["consultations"], dependencies=[Depends(require_api_key)])
def capture_consultation_event(consultation_id: str, req: CaptureRequest):
    return capture_facts(consultation_id, req)

@app.get("/session/state", operation_id="getOrthoSessionState", tags=["legacy"], dependencies=[Depends(require_api_key)])
def session_state(x_session_id: str = Header(...)):
    return read_session_state(x_session_id)

@app.get("/v1/consultations/{consultation_id}", operation_id="getOrthoConsultationState", tags=["consultations"], dependencies=[Depends(require_api_key)])
def consultation_state(consultation_id: str):
    return read_session_state(consultation_id)

@app.post("/audit", operation_id="auditOrthoCase", tags=["legacy"], dependencies=[Depends(require_api_key)])
def audit(req: FinalizeRequest, x_session_id: str = Header(...)):
    return audit_case(x_session_id, req)

@app.post("/v1/consultations/{consultation_id}/audit", operation_id="auditOrthoConsultation", tags=["consultations"], dependencies=[Depends(require_api_key)])
def audit_consultation(consultation_id: str, req: FinalizeRequest):
    return audit_case(consultation_id, req)

@app.post("/finalize", operation_id="finalizeOrthoCase", tags=["legacy"], dependencies=[Depends(require_api_key)])
def finalize(req: FinalizeRequest, x_session_id: str = Header(...)):
    return finalize_case(x_session_id, req)

@app.post("/v1/consultations/{consultation_id}/finalize", operation_id="finalizeOrthoConsultation", tags=["consultations"], dependencies=[Depends(require_api_key)])
def finalize_consultation(consultation_id: str, req: FinalizeRequest):
    return finalize_case(consultation_id, req)

@app.post("/source-route", operation_id="routeOrthoSource", tags=["legacy"], dependencies=[Depends(require_api_key)])
def source_route(req: RouteRequest):
    return source_mapping(req.domain)

@app.post("/v1/evidence/source-route", operation_id="routeOrthopedicSource", tags=["evidence"], dependencies=[Depends(require_api_key)])
def v1_source_route(req: RouteRequest):
    return source_mapping(req.domain)

@app.post("/v1/evidence/search", operation_id="searchOrthopedicEvidence", tags=["evidence"], dependencies=[Depends(require_api_key)])
def evidence_search(req: EvidenceSearchRequest):
    domain = req.domain or "trauma_adulto"
    return {
        "query": req.query,
        "domain": domain,
        "routing": source_mapping(domain),
        "items": [],
        "limit": req.limit,
        "copyright_policy": "Nenhum trecho protegido é exposto por este MVP; retorno limitado a roteamento, metadados e síntese futura.",
        "message": "Busca RAG ainda não conectada. Use o roteamento de fonte como camada segura inicial.",
    }
