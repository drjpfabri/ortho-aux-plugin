# Ortho Aux Plugin v0.6

Backend FastAPI do alpha sintético do Robô de Apoio Ortopédico.

> Perfil atual: avaliação técnica com casos exclusivamente sintéticos. Não enviar dados de pacientes. O serviço não diagnostica, não prescreve e não substitui avaliação ou validação médica.

## Estado funcional

- API HTTPS no Render;
- PostgreSQL em produção e SQLite no desenvolvimento;
- autenticação por `X-Ortho-Api-Key`, obrigatória em produção;
- isolamento e imutabilidade de consultas;
- proveniência obrigatória entre relato, achado, interpretação e sugestão de IA;
- bloqueio heurístico de identificadores diretos e erros de validação higienizados;
- Safety Gate versionado;
- avaliação neurovascular basal explícita e bloqueio pós-intervenção;
- resposta documentada obrigatória diante de alerta prioritário;
- revisão pediátrica específica;
- retenção padrão de 168 horas e exclusão sob demanda;
- métricas agregadas sem texto clínico;
- 50 cenários sintéticos do Gate e testes de API;
- CI no GitHub;
- schema OpenAPI sincronizado para GPT Action;
- política de governança versionada e validada no CI;
- endpoint autenticado de prontidão em `/v1/governance/status`;
- suspensão automática de novas consultas quando a revisão de governança vence;
- busca de evidência ainda limitada a roteamento e metadados.

## Limites do alpha

- O banco gratuito expira em **2026-09-26** e não possui backup/PITR.
- Há uma chave global, sem identidade individual, RBAC ou MFA.
- O bloqueio de identificadores é defesa complementar, não garantia de anonimização.
- O Safety Gate depende de informação estruturada e não substitui revisão clínica.
- O RAG/vector store não está conectado.
- A revisão de governança vigente vence em **2026-09-03**.
- A Action foi importada e testada, mas continua privada e com permissão por chamada.

Esses limites bloqueiam uso com pacientes ou expansão para beta clínico.

## Iniciar localmente

### Python

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
cp .env.example .env
./start.sh
```

### Docker

```bash
docker compose up --build
```

Endereços locais:

- API: `http://127.0.0.1:8000`
- Docs: `http://127.0.0.1:8000/docs`
- OpenAPI: `http://127.0.0.1:8000/openapi.json`
- Health: `http://127.0.0.1:8000/health`

## Testes

```bash
python -m pytest -q
python scripts/validate_governance.py
python scripts/export_openapi.py
```

O validador impede divergência entre política, código e Render. O último comando regenera `gpt-action.openapi.yaml`; a suíte falha se o schema estático divergir do contrato publicado.

## Fluxo mínimo da API

1. Iniciar consulta com classificação e atestado explícitos:

```json
{
  "data_classification": "synthetic",
  "purpose": "technical_test",
  "attested_no_direct_identifiers": true
}
```

2. Capturar somente fatos sintéticos, sempre com `kind` e `source` compatíveis.
3. Executar `/audit` com contexto e estado neurovascular explícitos.
4. Corrigir todos os bloqueadores.
5. Finalizar apenas como `draft_ready`, mantendo revisão humana.
6. Registrar feedback numérico sem texto livre.
7. Excluir a consulta ao terminar quando a retenção não for necessária.

Antes do fluxo, consulte `/v1/governance/status`. `clinical_use_authorized` e `patient_derived_data_authorized` devem permanecer `false` neste estágio. Se `accepting_new_consultations=false`, não tente contornar o bloqueio.

## GPT Action

Produção:

- servidor: `https://ortho-aux-plugin.onrender.com`
- schema por URL: `https://ortho-aux-plugin.onrender.com/openapi.json`
- schema versionado: `gpt-action.openapi.yaml`
- autenticação: API key em cabeçalho customizado `X-Ortho-Api-Key`

Consulte `GPT_INTEGRATION_INSTRUCTIONS.md` antes de importar. A documentação oficial da OpenAI orienta testar a Action no Preview após configurar autenticação e schema.

## Plano de 90 dias

- `docs/MUSASHI_90_DAY_EXECUTION.md`
- `docs/EVALUATION_PROTOCOL.md`
- `docs/RISK_REGISTER.md`
- `docs/RESPONSIBILITY_MATRIX.md`
- `docs/INCIDENT_RUNBOOK.md`
- `docs/DECISION_LOG.md`
- `docs/DATA_GOVERNANCE_POLICY.md`
- `docs/DATA_FLOW_REGISTER.md`
- `docs/PRELIMINARY_RIPD.md`
- `docs/CHANGE_CONTROL.md`
- `governance/control-register.yaml`
