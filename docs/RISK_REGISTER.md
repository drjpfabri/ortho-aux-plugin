# Registro de riscos

Versão: 1.1 - 2026-08-28

Próxima revisão: 2026-09-03

| ID | Risco | Nível | Controle atual | Responsável | Próxima ação / prazo | Estado |
|---|---|---:|---|---|---|---|
| R-001 | PostgreSQL gratuito expira em 2026-09-26 e não possui backup | crítico | somente casos sintéticos e retenção de 168 h | responsável técnico a nomear | migrar, promover ou encerrar até 2026-09-20 | aberto |
| R-002 | Uma chave global não identifica nem revoga usuários individualmente | alto | GPT privado, poucos avaliadores e rotação manual | responsável técnico a nomear | implementar identidade/RBAC/MFA antes de usuário externo | aberto |
| R-003 | Detecção heurística não garante anonimização | crítico | produção aceita somente `synthetic` | Product Owner clínico | manter proibição de qualquer caso real | controlado no alpha |
| R-004 | Safety Gate depende de flags estruturadas fornecidas pelo chamador | alto | contrato fechado, 50 cenários e revisão obrigatória | Product Owner clínico | concluir revisão clínica independente até o portão do dia 30 | aberto |
| R-005 | RAG não está conectado | médio | resposta declara metadata-only | Product Owner clínico | não alegar evidência recuperada | aceito no alpha |
| R-006 | Action pode regredir após mudança de schema ou autenticação | alto | schema sincronizado e teste no Preview obrigatório | responsável técnico a nomear | repetir ponta a ponta em toda mudança contratual | controlado |
| R-007 | Não há aprovação jurídica/LGPD institucional | crítico | proibição de dado derivado de paciente | DPO/jurídico a nomear | definir papéis, base legal e RIPD antes de beta | aberto |
| R-008 | Não há monitoramento externo nem alerta automático | médio | health check do Render e verificação manual | responsável técnico a nomear | configurar alerta antes de usuário externo | aberto |
| R-009 | Serviço gratuito pode ter cold start | médio | uso controlado e health check | responsável técnico a nomear | medir latência no alpha | aberto |
| R-010 | Testes de software não equivalem a validação clínica | crítico | casos sintéticos rastreáveis | revisores clínicos a nomear | dois revisores e adjudicação documentada | aberto |
| R-011 | Logs da plataforma ficam fora do controle do código | alto | aplicação não registra corpos e higieniza erros | privacidade/técnico a nomear | revisar contrato, retenção e logs antes do beta | aberto |
| R-012 | Chats descrevem MVPs que não integram o backend canônico | alto | repositório e serviço canônicos declarados | Product Owner clínico | manter inventário e fronteira explícitos | controlado |
| R-013 | Consulta externa direta ao PostgreSQL não foi validada por limitação TLS | médio | conexão privada da API e fluxo HTTP saudáveis | responsável técnico a nomear | definir observabilidade suportada antes do beta | aberto |
| R-014 | Uma aprovação booleana isolada poderia liberar escopo sensível | crítico | portão v0.6 exige referências, responsáveis, validade, RBAC e PITR | responsável técnico a nomear | testar o portão em toda mudança | controlado |
| R-015 | Tratamento, retenção e transferência em ChatGPT/Action não foram avaliados contratualmente | crítico | somente conteúdo sintético | DPO/jurídico a nomear | revisar produto, contrato, subprocessadores e localização | aberto |
| R-016 | Enquadramento regulatório de SaMD não foi definido | crítico | finalidade atual não autoriza uso clínico | regulatório/qualidade a nomear | formalizar uso pretendido e classificação antes do beta clínico | aberto |
| R-017 | Aprovação pode ficar obsoleta com deriva de configuração | alto | versão de política, CI e vencimento automático em 2026-09-03 | Product Owner + técnico | renovar ou suspender na data | controlado |
| R-018 | Integração futura do frontend pode omitir ou rebaixar bloqueadores | crítico | frontend separado, sem tunnel e sem CORS | clínico + técnico | contrato fechado e testes E2E antes de integrar | controlado no alpha |
| R-019 | CODEOWNERS e CI não garantem revisão sem proteção efetiva da branch | alto | template, Dependabot e deploy configurado para aguardar checks | responsável técnico a nomear | confirmar branch protegida e checks obrigatórios antes de usuário externo | aberto |

## Regra de aceitação

- Risco crítico aberto bloqueia dados derivados de paciente e uso clínico.
- `A DEFINIR` ou `a nomear` não conta como responsável designado.
- Aceitação de risco precisa de responsável, justificativa, prazo e escopo; não pode ser presumida pelo silêncio.
- Alteração de estado deve atualizar `governance/control-register.yaml` e `docs/DECISION_LOG.md` no mesmo conjunto versionado.

Todo incidente, falha de teste, mudança de finalidade, fornecedor, classificação de dados ou decisão de avançar exige nova revisão deste registro.
