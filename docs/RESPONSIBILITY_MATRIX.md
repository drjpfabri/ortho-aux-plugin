# Matriz de responsabilidades

Versão: 1.0 - 2026-08-27

`R` executa, `A` responde pela decisão, `C` é consultado e `I` é informado.

| Atividade | Product Owner clínico | Responsável técnico | Revisor clínico independente | Privacidade/DPO | Jurídico institucional |
|---|---|---|---|---|---|
| Escopo e prioridade | A/R | C | C | I | I |
| Código, CI e deploy | C | A/R | I | C | I |
| Aprovação dos casos sintéticos | A | C | R | I | I |
| Critérios de segurança clínica | A/R | C | R | C | I |
| Incidente técnico | I | A/R | C | C | I |
| Incidente de privacidade | I | R | I | A/R | C |
| Contrato e propriedade intelectual | C | I | I | C | A/R |
| Decisão de avançar portão | A | R | C | C | C |
| Suspensão do piloto | A/R | R | R | R | C |

## Pessoas nomeadas

| Papel | Pessoa | Situação |
|---|---|---|
| Product Owner clínico | Dr. João Pedro Fabri | definido nos chats do plano |
| Responsável técnico | A DEFINIR | bloqueia alpha com avaliadores externos |
| Revisor clínico independente 1 | A DEFINIR | bloqueia aprovação clínica dos 50 casos |
| Revisor clínico independente 2 | A DEFINIR | bloqueia aprovação clínica dos 50 casos |
| Privacidade/DPO | A DEFINIR | bloqueia dados desidentificados ou reais |
| Jurídico institucional | A DEFINIR | bloqueia contrato de beta |

Uma ferramenta de IA não ocupa papel legal, clínico ou institucional no RACI.
