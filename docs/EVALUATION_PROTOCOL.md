# Protocolo de avaliação do alpha

Versão: 1.0 - 2026-08-27

## Objetivo

Demonstrar, com casos exclusivamente sintéticos, que o sistema preserva proveniência, bloqueia omissões documentais críticas, não promove sugestão de IA a decisão e produz métricas sem texto clínico.

## Suíte mínima

A suíte automatizada contém exatamente 50 cenários clínico-documentais em `tests/test_safety_scenarios.py`, além de testes de API, privacidade, autenticação, retenção lógica, exclusão, métricas e schema.

Os sete aprendizados do MRO são cobertos assim:

| Patch observado nos chats | Controle permanente |
|---|---|
| relato não equivale a exame | combinação obrigatória `kind` + `source` |
| “NV preservado” não basta | estado basal explícito no Gate |
| NV pré/pós intervenção | bloqueador pós-intervenção |
| fratura exposta requer resposta urgente | flag prioritária + resposta documentada |
| pulso não exclui compartimental | teste com pulso presente mantém alerta |
| risco arterial oculto | flag própria, inclusive com pulso presente |
| pediatria exige fluxo específico | revisão pediátrica obrigatória |

## Revisão clínica humana

1. Dois ortopedistas revisam independentemente os 50 cenários.
2. Cada cenário recebe `APROVADO`, `CORRIGIR` ou `INCONCLUSIVO`.
3. Divergências são adjudicadas pelo Product Owner clínico e registradas.
4. Alteração clínica exige novo teste e regressão completa.
5. Nenhum teste automatizado é apresentado como validação clínica por si só.

## Métricas do piloto

O endpoint `/v1/pilot/metrics` agrega somente eventos enumerados e números:

- consultas iniciadas, finalizadas, bloqueadas e excluídas;
- disposição da saída: aceita, editada ou rejeitada;
- tempo de documentação;
- quantidade de correções e falsos alertas;
- falha técnica e incidente de privacidade.

Não são aceitos comentários livres, diagnóstico, texto de prontuário ou identificadores nas métricas.

## Critérios do portão

Obrigatórios:

- zero falso negativo nos hard stops críticos aprovados;
- zero finalização quando houver bloqueador;
- zero sugestão de IA pré-validada;
- zero identificador dos padrões de teste refletido na resposta de erro;
- 100% dos casos clínicos revisados e assinados antes de usuários externos;
- qualquer incidente de privacidade resulta em suspensão e runbook executado.

Indicadores de utilidade, como tempo, edição e aceitação, devem ser observados; não devem ser usados como substituto de segurança nem como desfecho clínico.
