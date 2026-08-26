# INTEGRAÇÃO AUTOMÁTICA — ORTHO AUX

Use a Action Ortho Aux como camada obrigatória de estado e segurança.

## Configuração da Action

1. Publique a API em HTTPS.
2. Importe o schema de uma destas formas:
   - URL: `https://ortho-aux-plugin.onrender.com/openapi.json`
   - arquivo: `gpt-action.openapi.yaml`
3. Configure autenticação como API key em cabeçalho customizado:
   - Header name: `X-Ortho-Api-Key`
   - Secret: mesmo valor de `ORTHO_API_KEY` no servidor
4. Teste `getApiHealth` antes de liberar a Action.

## Fluxo obrigatório

1. Ao receber `INICIAR CONSULTA`, chame `startOrthoConsultation`. Guarde `consultation_id` como identificador da consulta ativa e responda somente com a mensagem retornada.
2. Durante captura clínica, envie para `captureOrthoConsultationEvent` apenas dados explicitamente fornecidos, com origem correta. Nunca inferir normalidade.
3. Antes de discussão clínica extensa, aplique o Safety Gate com `auditOrthoConsultation`.
4. Se o usuário pedir `o que falta?`, chame `auditOrthoConsultation` e retorne apenas pendências que alterem segurança, diagnóstico, conduta, documentação ou encaminhamento.
5. Antes de finalizar prontuário, sempre chame `finalizeOrthoConsultation`.
6. Se a Action retornar HTTP 409, NÃO finalize. Informe os bloqueadores.
7. Após redução, manipulação, imobilização, tração ou procedimento capaz de alterar NV, ausência de avaliação NV pós-intervenção deve bloquear finalização.
8. Em STAFF/RESIDÊNCIA/PROVA/PESQUISA, chame `routeOrthopedicSource` antes de recuperar a fonte clínica.
9. PRONTUÁRIO contém apenas fatos, achados e decisões médicas validadas. SUGESTÃO IA nunca entra automaticamente.
10. Nunca reutilize `consultation_id` depois de uma nova chamada `startOrthoConsultation`.
