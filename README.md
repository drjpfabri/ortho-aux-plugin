# Ortho Aux Plugin v0.4

Versão autônoma do auxiliar ortopédico, pronta para execução e publicação.

## Já está implementado

- API FastAPI;
- persistência PostgreSQL em produção e SQLite no desenvolvimento local;
- isolamento de consulta/paciente;
- captura com origem explícita;
- Safety Gate;
- hard-stop de finalização;
- bloqueio por NV pós-intervenção ausente;
- auditoria de mistura de paciente e lateralidade;
- recuperação do estado da consulta;
- roteamento de fonte;
- Docker / Docker Compose;
- inicialização automática para Windows, macOS e Linux;
- arquivos de deploy para Render e Railway;
- testes automatizados.
- endpoints `/v1` compatíveis com integração por GPT Action.
- autenticação opcional por `X-Ortho-Api-Key` quando `ORTHO_API_KEY` estiver configurada.
- verificação de conectividade com o banco em `/health`.
- imutabilidade de consultas já finalizadas.

## Iniciar

### macOS/Linux
`./start.sh`

### Windows
Execute `start.bat`.

O script usa Docker automaticamente quando disponível; caso contrário, cria um ambiente Python e inicia o serviço.

- API: `http://127.0.0.1:8000`
- Docs: `http://127.0.0.1:8000/docs`
- OpenAPI: `http://127.0.0.1:8000/openapi.json`
- Health: `http://127.0.0.1:8000/health`

## Uso como Action de um GPT

O serviço já publica o próprio schema OpenAPI em `/openapi.json`.

Uma Action de GPT exige uma URL HTTPS pública. O pacote inclui `Dockerfile`, `render.yaml` e `railway.json`, portanto não exige alterações de código para hospedagem.

Depois de a plataforma de hospedagem fornecer a URL pública, o schema estará em:

`https://ortho-aux-plugin.onrender.com/openapi.json`

Cole `GPT_INTEGRATION_INSTRUCTIONS.md` nas instruções do GPT que vai chamar a Action.

Operações principais expostas no OpenAPI:

- `getApiHealth`: `GET /health`
- `getApiInfo`: `GET /`
- `startOrthoConsultation`: `POST /v1/consultations`
- `captureOrthoConsultationEvent`: `POST /v1/consultations/{consultation_id}/events`
- `auditOrthoConsultation`: `POST /v1/consultations/{consultation_id}/audit`
- `finalizeOrthoConsultation`: `POST /v1/consultations/{consultation_id}/finalize`
- `routeOrthopedicSource`: `POST /v1/evidence/source-route`
- `searchOrthopedicEvidence`: `POST /v1/evidence/search`

Se `ORTHO_API_KEY` estiver definida no ambiente, envie a mesma chave no cabeçalho:

`X-Ortho-Api-Key: SUA_CHAVE`

Em produção, configure `DATABASE_URL` com a conexão PostgreSQL interna da plataforma. Sem essa variável, o serviço usa `ORTHO_AUX_DB`/SQLite apenas para desenvolvimento local.

O banco gratuito atual é apenas para avaliação: expira em 30 dias e não possui backup. Não use dados identificáveis de pacientes até migrar para infraestrutura com backup/PITR e concluir a revisão de LGPD, segurança, retenção e governança institucional.

## Vinculação ao GPT

A API pública já está disponível no Render. A associação final da Action ao GPT deve importar `https://ortho-aux-plugin.onrender.com/openapi.json` e usar o segredo configurado no Render como API key customizada `X-Ortho-Api-Key`.

## Produção clínica

Para dados clínicos identificáveis, configure a infraestrutura segundo as obrigações legais e institucionais aplicáveis. Evite logs de dados identificáveis, use controle de acesso, criptografia e política de retenção.

O serviço não prescreve, não inventa achados e não substitui decisão/validação médica.
