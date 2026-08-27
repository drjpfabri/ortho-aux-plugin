# Registro de riscos

Versão: 1.0 - 2026-08-27

| ID | Risco | Nível | Controle atual | Próxima ação | Estado |
|---|---|---:|---|---|---|
| R-001 | PostgreSQL gratuito expira em 2026-09-26 e não possui backup | crítico | somente casos sintéticos e retenção de 168 h | migrar ou encerrar antes da expiração | aberto |
| R-002 | Uma chave global não identifica nem revoga usuários individualmente | alto | alpha com poucos avaliadores e rotação manual | implementar identidade individual/RBAC antes do beta | aberto |
| R-003 | Detecção heurística de identificadores não garante anonimização | crítico | ambiente aceita somente `synthetic` | manter proibição de dados reais | controlado no alpha |
| R-004 | Safety Gate depende de flags estruturadas fornecidas pelo chamador | alto | contrato obrigatório e 50 testes | revisão clínica e testes ponta a ponta no GPT | aberto |
| R-005 | RAG não está conectado | médio | resposta declara metadata-only | não alegar evidência recuperada; validar RAG separadamente | aceito no alpha |
| R-006 | Action ainda não foi testada no Preview do GPT | alto | schema OpenAPI versionado e sincronizado | importar, autenticar e executar fluxo sintético | aberto |
| R-007 | Não há aprovação jurídica/LGPD institucional | crítico | proibição de dados reais | obter revisão formal antes de qualquer beta clínico | aberto |
| R-008 | Não há monitoramento externo nem alerta automático | médio | health check do Render e verificação manual | definir monitoramento antes do beta | aberto |
| R-009 | Serviço gratuito pode ter cold start | médio | health check e uso controlado | medir latência; escolher plano adequado ao piloto | aberto |
| R-010 | 50 testes de software não equivalem a validação clínica | crítico | casos sintéticos rastreáveis | dois revisores clínicos e adjudicação de divergências | aberto |
| R-011 | Logs da plataforma são externos ao código | alto | aplicação não registra corpos; erros 422 são higienizados | auditoria periódica de logs e contrato do fornecedor | aberto |
| R-012 | Chats descrevem outros MVPs mais amplos que não integram este repositório | alto | repositório canônico declarado | tratar este backend como única fonte implantada | controlado |

## Regra de atualização

Todo incidente, falha de teste, alteração de escopo ou decisão de avançar deve atualizar este arquivo e o registro de decisões no mesmo pull request ou commit.
