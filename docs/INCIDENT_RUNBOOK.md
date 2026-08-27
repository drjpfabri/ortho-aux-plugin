# Runbook de incidente

Versão: 1.0 - 2026-08-27

## Acionamento

Use este runbook diante de acesso não autorizado, chave exposta, dado possivelmente identificável, erro clínico crítico, perda de persistência ou comportamento divergente do Safety Gate.

## Primeiros 30 minutos

1. Suspender novos testes e a Action do GPT.
2. Revogar ou trocar `ORTHO_API_KEY` quando houver dúvida sobre credencial.
3. Registrar horário, versão, endpoint, identificador técnico da requisição e categoria do incidente; não copiar conteúdo clínico para o registro.
4. Excluir a consulta afetada quando isso não destruir evidência necessária e autorizada.
5. Preservar apenas logs técnicos mínimos e métricas agregadas.
6. Notificar responsável técnico, Product Owner clínico e privacidade conforme o RACI.

## Contenção e análise

- verificar logs sem pesquisar ou reproduzir dados assistenciais desnecessariamente;
- identificar versão, commit e regra afetada;
- reproduzir com caso sintético mínimo;
- criar teste de regressão antes da correção;
- avaliar se outras consultas ou credenciais foram afetadas;
- manter o serviço suspenso se houver risco clínico ou de privacidade não delimitado.

## Recuperação

Retomar somente quando:

- causa raiz e alcance estiverem documentados;
- correção e regressão completa estiverem verdes;
- credenciais tiverem sido rotacionadas quando aplicável;
- logs não mostrarem repetição;
- responsáveis técnico, clínico e de privacidade aprovarem a retomada.

## Comunicação

Este repositório não define obrigação legal de notificação. Qualquer notificação a titular, instituição ou autoridade deve ser decidida pelo DPO/jurídico conforme o contexto e a legislação aplicável.
