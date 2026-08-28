# RIPD preliminar

Versão: 0.1 - 2026-08-28

## Natureza deste documento

Este é um levantamento técnico preliminar para orientar um futuro Relatório de Impacto à Proteção de Dados Pessoais. Não constitui RIPD formal, parecer jurídico, definição de base legal ou autorização para tratar dados de pacientes.

## Escopo atual

| Item | Situação vigente |
|---|---|
| finalidade | teste técnico, validação e treinamento com casos sintéticos |
| titulares | nenhum titular deve estar presente |
| dados pessoais | não pretendidos e proibidos |
| dados de saúde vinculados a pessoa | proibidos |
| decisões automatizadas | inexistentes; saída é rascunho |
| retenção da API | 168 horas ou exclusão antecipada |
| compartilhamento autorizado | somente trânsito sintético entre GPT Action e API |
| frontend | privado, sintético e desconectado |
| RAG | inativo |

## Fluxo e agentes ainda não definidos

A qualificação jurídica de controlador, operador, suboperador e eventual corresponsabilidade não está definida. Também faltam análise contratual de OpenAI, Render e demais subprocessadores, avaliação de transferência internacional, canal do titular e encarregado formalmente designado.

Essas lacunas não afetam casos realmente sintéticos, mas bloqueiam qualquer dado derivado de paciente.

## Cenários de risco

| Risco | Impacto potencial | Controles atuais | Residual | Decisão |
|---|---|---|---|---|
| usuário envia dado real como sintético | exposição de dado sensível e sigilo profissional | atestado, schema fechado, detector de identificadores, retenção curta | crítico | manter proibição e treinamento |
| reidentificação de caso dito desidentificado | dano ao titular e tratamento sem base definida | classificação `deidentified` bloqueada | crítico | não liberar |
| chave global compartilhada | acesso sem atribuição individual | segredo no servidor e GPT privado | alto | implementar RBAC/MFA antes do beta |
| retenção por fornecedores | permanência além da política local | nenhum dado real permitido | crítico | revisão contratual antes do beta |
| perda do banco | evidência do piloto incompleta | casos sintéticos e retenção curta | alto | migrar para backup/PITR |
| Safety Gate falha | omissão crítica em rascunho | gate determinístico e 50 cenários automatizados | crítico | revisão clínica independente |
| uso como diagnóstico ou prescrição | dano clínico e possível mudança regulatória | mensagens de escopo e revisão humana | crítico | proibir uso clínico |
| integração futura rebaixa alertas | falso senso de segurança | integração não autorizada | crítico | contrato de integração e regressão obrigatória |

## Salvaguardas exigidas antes de ampliar o escopo

- nomear controlador, operadores, encarregado e responsáveis;
- definir finalidade, necessidade e base legal com jurídico/DPO;
- concluir inventário de dados e fornecedores;
- documentar direitos do titular e canais de atendimento;
- aprovar identidade individual, menor privilégio e trilha de auditoria;
- contratar infraestrutura com backup, PITR e monitoramento;
- validar retenção e transferências internacionais;
- concluir revisão clínica independente;
- obter enquadramento regulatório formal;
- aprovar RIPD final e decisão de liberação com prazo de validade.

## Conclusão preliminar

O escopo sintético reduz o tratamento pretendido a dados não pessoais, mas existe risco de uso indevido na entrada. O conjunto atual é aceitável apenas para alpha interno sintético. O risco residual para qualquer dado derivado de paciente permanece incompatível com liberação.

Referência conceitual: a LGPD define RIPD e os princípios de segurança, prevenção e responsabilização em seu [texto compilado oficial](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709compilado.htm).
