# Plano Musashi 90 dias - execução verificável

Versão: 1.2
Dia 0: 2026-08-27
Revisões: 2026-09-03, 2026-09-26, 2026-10-26 e 2026-11-25

## Decisão executiva

O produto inicial é somente **documentação ortopédica estruturada com Safety Gate e auditoria de omissões**, sempre como rascunho sujeito à validação médica.

Durante os 90 dias:

- não lançar como SaaS público;
- não usar dados identificáveis de pacientes;
- não afirmar que existe RAG enquanto a busca retornar apenas metadados;
- não adicionar função clínica sem substituir outra ou responder a falha observada;
- interromper o piloto diante de incidente de privacidade, hard stop perdido ou responsabilidade indefinida.

## Estado em 2026-08-28

| Entrega | Estado | Evidência |
|---|---|---|
| API privada HTTPS | concluída | Render e `/health` |
| PostgreSQL durável | concluído para avaliação | Render PostgreSQL gratuito |
| Autenticação servidor-servidor | concluída | `X-Ortho-Api-Key` |
| Safety Gate | concluído em engenharia | suíte sintética automatizada |
| 50 casos sintéticos | concluído em automação | `tests/test_safety_scenarios.py` |
| Fluxo HTTP v0.6 em produção | concluído | health, governança e evidência ponta a ponta preservada em `TEST_REPORT.txt` |
| Logs sem corpo clínico | concluído na revisão atual | registros do Render contêm somente rota e status |
| Bloqueio de identificadores | concluído como defesa complementar | testes de privacidade e erros higienizados |
| Retenção e exclusão | concluídas para o alpha | expiração em 168 horas e endpoint `DELETE` |
| Métricas sem texto clínico | concluídas | feedback e agregação do piloto |
| GPT Action v0.6 importada no GPT | concluída | health e governança autenticada testados no Preview; nenhum registro criado nesta mudança |
| Governança como código | concluída para o alpha | registro de 13 controles, CI e `/v1/governance/status` |
| Deploy condicionado ao CI | concluído no Render | configuração efetiva `autoDeployTrigger=checksPass` |
| Vencimento da autorização técnica | concluído | novas consultas bloqueiam após 2026-09-03 sem renovação |
| Fluxo de dados e RIPD preliminar | concluídos como diagnóstico | não equivalem a aprovação jurídica nem autorizam dado real |
| Frontend privado sintético | concluído em projeto separado | permanece deliberadamente desconectado da API |
| Revisão clínica humana dos 50 casos | pendente | não substituída pelos testes de software |
| RBAC/MFA por usuário | pendente | bloqueia beta com múltiplos usuários reais |
| Revisão jurídica/LGPD institucional | pendente | bloqueia qualquer dado real |
| RAG/vector store | fora do alpha | endpoint continua metadata-only |

## Portão do dia 7 - 2026-09-03

Critérios obrigatórios:

- CI verde na branch principal;
- `/health`, `/docs` e `/openapi.json` válidos;
- autenticação `401/200` comprovada;
- uma Action ponta a ponta testada no Preview do GPT;
- zero corpo clínico ou identificador nos logs de aplicação;
- 50 cenários sintéticos aprovados;
- riscos, decisões e responsáveis versionados;
- ambiente limitado a `synthetic`.
- `/v1/governance/status` confirma revisão vigente e uso clínico não autorizado.

Decisão permitida: `AVANÇAR PARA ALPHA INTERNO` ou `CORRIGIR`. Não há autorização para paciente real.

## Dias 8-30 - alpha controlado

- revisar clinicamente os 50 cenários sintéticos;
- manter no máximo 5 avaliadores internos até a revisão clínica completa;
- registrar apenas disposição (`accepted`, `edited`, `rejected`), tempo, correções, falsos alertas e falha técnica;
- realizar revisão semanal de falsos negativos, falsos positivos e incidentes;
- testar revogação de chave, exclusão e runbook de incidente;
- renovar ou suspender formalmente a autorização técnica em 2026-09-03;
- substituir ou promover o banco antes de 2026-09-26; o banco gratuito expira nessa data.

Portão do dia 30:

- zero hard stop crítico perdido na suíte aprovada;
- zero finalização com bloqueador pendente;
- zero incidente de privacidade não resolvido;
- revisão clínica assinada dos casos;
- responsável técnico, responsável clínico, privacidade e jurídico nomeados;
- decisão documentada sobre infraestrutura com backup e PITR.

## Dias 31-60 - beta fechado

Somente após aprovação do portão do dia 30:

- até 10-15 usuários treinados;
- autenticação individual, RBAC, revogação por usuário e trilha de auditoria;
- ambiente com backup/PITR e contrato institucional;
- termos de uso, confidencialidade, propriedade intelectual e governança aprovados;
- onboarding padronizado;
- piloto remunerado pequeno, sem prometer escala.

Qualquer uso de dado desidentificado exige aprovação formal e configuração deliberada de `ORTHO_GOVERNANCE_APPROVED=true`. Dado identificável permanece proibido nesta versão.

Na v0.6, essa variável isolada é insuficiente: a API também exige referências de aprovação, responsáveis, revisão clínica, base legal, RIPD, análise de fornecedor e regulatória, identidade individual, RBAC e infraestrutura com PITR.

## Dias 61-90 - produto repetível

- consolidar onboarding, suporte e custo de implantação;
- emitir relatório agregado sem conteúdo assistencial;
- retirar funções sem adoção observada;
- definir licença de equipe, piloto institucional ou assinatura fechada;
- decidir `ESCALAR`, `CORRIGIR` ou `INTERROMPER` em 2026-11-25.

## Gatilhos de parada

Suspender imediatamente quando ocorrer qualquer um destes eventos:

- possível dado identificável persistido ou exposto;
- hard stop crítico não sinalizado;
- saída tratada como decisão clínica autônoma;
- acesso não autorizado ou chave comprometida;
- perda de dados que invalide a avaliação;
- responsável clínico ou técnico indisponível;
- expiração do banco sem migração concluída.

Retomada exige causa registrada, correção testada, rotação de credenciais quando aplicável e aprovação dos responsáveis definidos no RACI.
