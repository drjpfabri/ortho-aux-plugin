# Registro de decisões

Versão: 1.1 - 2026-08-28

| ID | Decisão | Motivo | Consequência |
|---|---|---|---|
| D-001 | `ortho-aux-plugin` é o backend canônico implantado | foi o repositório e serviço efetivamente validados | outros pacotes descritos em chats não são tratados como produção |
| D-002 | ambiente Render aceita somente `synthetic` | infraestrutura gratuita e governança incompleta | qualquer dado real é proibido |
| D-003 | dado desidentificado fica bloqueado por configuração | desidentificação também exige governança formal | liberação requer DPO/jurídico e variável explícita |
| D-004 | retenção padrão é 168 horas | minimização durante avaliação | consultas expiram e podem ser excluídas antes |
| D-005 | fatos exigem tipo e origem compatíveis | impedir que relato seja promovido a exame ou IA a decisão | clientes antigos precisam atualizar o payload |
| D-006 | toda saída permanece rascunho | o sistema é apoio, não decisão autônoma | resposta inclui `human_review_required=true` |
| D-007 | risco vascular oculto é uma flag explícita, não inferência automática | patch do chat ainda estava em regressão clínica | o Gate preserva o alerta quando informado, inclusive com pulso presente |
| D-008 | RAG permanece fora do alpha | vector store e validação de citações não existem no serviço | endpoint declara metadata-only |
| D-009 | métricas não armazenam texto nem ID de consulta | reduzir risco de privacidade | análise é agregada e não permite auditoria individual completa |
| D-010 | beta real exige identidade individual, backup/PITR e governança | chave global e banco gratuito não bastam | portão do dia 30 bloqueia expansão até conclusão |
| D-011 | todas as flags do Safety Gate são obrigatórias | campo ausente não pode significar normalidade | clientes devem revisar explicitamente cada hard stop |
| D-012 | consultas legadas sem classificação são apagadas no primeiro boot v0.5 | não há atestado de que pertençam ao piloto sintético | somente registros v0.5 classificados permanecem |
| D-013 | a Action foi vinculada ao GPT privado com permissão externa por chamada | manter controle humano explícito também no transporte | `sempre permitir` não foi habilitado durante a validação |
| D-014 | governança passa a ser validada como código | políticas sem verificação podem divergir do deploy | CI compara registro, FastAPI e Render |
| D-015 | autorização do alpha possui revisão com vencimento | aprovação indefinida favorece deriva de escopo | novas consultas param após 2026-09-03 sem renovação deliberada |
| D-016 | uma variável booleana não basta para liberar `deidentified` | aprovação precisa de responsáveis, evidências, identidade e resiliência | startup falha quando qualquer controle obrigatório estiver ausente |
| D-017 | frontend Sites permanece desconectado | contrato de integração e governança de dados ainda não existem | nenhuma chamada de navegador ou tunnel é autorizada |
| D-018 | o projeto não declara enquadramento regulatório concluído | a finalidade pretendida pode alterar a classificação sanitária | uso clínico fica bloqueado até revisão formal de SaMD |
| D-019 | retenção local não é presumida para fornecedores | ChatGPT, Action, Render e futuros serviços têm controles próprios | dados derivados de pacientes exigem revisão contratual e de transferência |
