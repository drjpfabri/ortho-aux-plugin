# Runbook de incidente

Versão: 1.1 - 2026-08-28

## Acionamento

Use este runbook diante de acesso não autorizado, chave exposta, dado possivelmente identificável, erro clínico crítico, perda de persistência ou comportamento divergente do Safety Gate.

## Primeiros 30 minutos

1. Suspender novos testes e a Action do GPT.
2. Revogar ou trocar `ORTHO_API_KEY` quando houver dúvida sobre credencial.
3. Registrar horário, versão, endpoint, identificador técnico da requisição e categoria do incidente; não copiar conteúdo clínico para o registro.
4. Excluir a consulta afetada quando isso não destruir evidência necessária e autorizada.
5. Preservar apenas logs técnicos mínimos e métricas agregadas.
6. Notificar responsável técnico, Product Owner clínico e privacidade conforme o RACI.

Não registrar segredo, corpo clínico ou dado pessoal em issue, commit, chat, captura de tela ou canal sem controle próprio para incidente.

## Classificação inicial

| Severidade | Exemplo | Resposta |
|---|---|---|
| S0 | falso alarme sem dado ou impacto | registrar e revisar na rotina |
| S1 | falha técnica restrita ao caso sintético | corrigir antes do próximo teste |
| S2 | chave possivelmente exposta, perda de persistência ou gate divergente | suspender Action e rotacionar credencial |
| S3 | possível dado pessoal/sensível ou risco clínico real | suspender tudo, acionar controlador/DPO/jurídico imediatamente |

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

Quando houver possível dado pessoal, o operador deve informar o controlador sem demora injustificada. Cabe ao controlador, com DPO/jurídico, avaliar risco ou dano relevante e decidir as comunicações aplicáveis.

A orientação vigente da ANPD informa prazo de três dias úteis para comunicação à ANPD e aos titulares quando os critérios regulamentares forem atendidos, além da possibilidade de complemento posterior. O registro de incidentes com dados pessoais deve ser preservado por pelo menos cinco anos, separado do banco clínico e sem exposição indevida. Consulte o procedimento oficial da [ANPD para Comunicação de Incidente de Segurança](https://www.gov.br/anpd/pt-br/canais_atendimento/agente-de-tratamento/comunicado-de-incidente-de-seguranca-cis).

Este runbook não decide sozinho a obrigação legal. DPO, controlador e jurídico devem aplicar a norma ao contexto concreto e registrar horário do conhecimento, decisão, justificativa e comunicações realizadas.
