# Controle de mudanças e liberação

Versão: 1.0 - 2026-08-28

## Princípio

Nenhuma alteração de código, schema, prompt, Action, infraestrutura, fornecedor, finalidade ou classificação de dados é apenas técnica. Mudanças materiais exigem evidência, avaliação de risco e decisão de liberação registrada.

## Classes de mudança

| Classe | Exemplos | Aprovação mínima |
|---|---|---|
| C1 documental | correção sem alterar regra ou escopo | responsável técnico |
| C2 técnica | dependência, infraestrutura ou endpoint sem efeito clínico pretendido | técnico + CI + atualização de risco |
| C3 clínica | Safety Gate, flags, texto de alerta, proveniência ou finalização | técnico + Product Owner clínico + revisor independente |
| C4 dados/regulatória | nova classe de dados, fornecedor, integração, RAG ou finalidade clínica | técnico + clínico + privacidade/DPO + jurídico/regulatório |
| C5 emergência | incidente ativo ou vulnerabilidade crítica | suspensão imediata; aprovação de retomada conforme runbook |

## Evidência obrigatória

Toda mudança C2-C4 deve incluir no mesmo conjunto versionado:

- motivo e escopo;
- testes novos ou justificativa explícita;
- suíte completa e lint aprovados;
- atualização de risco e decisão quando aplicável;
- schema OpenAPI regenerado quando houver contrato alterado;
- teste sintético ponta a ponta no GPT após mudança da Action;
- confirmação de que nenhum segredo ou dado clínico entrou no commit ou log;
- plano de reversão não destrutivo.

Mudança C3 não pode reduzir alerta, bloqueador ou revisão humana sem duas revisões clínicas e caso de regressão específico. Geradores, RAG e frontend nunca podem rebaixar o resultado do motor determinístico.

## Portão automatizado

O CI executa compilação, lint, registro de governança, testes da API, 50 cenários de segurança e sincronização do OpenAPI. `scripts/validate_governance.py` falha quando:

- a política diverge entre código, registro e Render;
- o ambiente deixa de ser `synthetic` sem uma mudança formal;
- um portão bloqueado aparece como autorizado;
- controles ou evidências obrigatórios desaparecem.

O Blueprint usa `autoDeployTrigger: checksPass`; a configuração efetiva do serviço foi confirmada no Render em 2026-08-28 como **After CI Checks Pass**. Essa verificação deve ser repetida após cada mudança de infraestrutura.

`CODEOWNERS`, o template de pull request e Dependabot estão versionados. Enquanto proteção da branch e checks obrigatórios não estiverem confirmados no GitHub, o controle permanece parcial e bloqueia qualquer liberação de dados derivados de paciente.

## Validade

A autorização técnica tem prazo. `ORTHO_GOVERNANCE_REVIEW_DUE` é verificada pela API; ao vencer, novas consultas são suspensas. Renovação exige revisão do registro de controles, riscos, incidentes, dependências, logs e infraestrutura.

## Mudança emergencial

1. Suspender Action e novas consultas.
2. Rotacionar credenciais quando houver possibilidade de exposição.
3. Reproduzir somente com caso sintético.
4. Criar teste de regressão.
5. Corrigir e executar todos os portões.
6. Registrar causa, impacto e decisão de retomada.

Não usar `git reset --hard`, reescrita de histórico ou exclusão de evidência para tratar incidentes.
