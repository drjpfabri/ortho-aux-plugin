# Integração da GPT Action - alpha sintético

Use a Action Ortho Aux somente como camada de estado, proveniência, Safety Gate e medição do piloto. Toda saída permanece rascunho e exige validação médica.

## Configuração

1. Importe `https://ortho-aux-plugin.onrender.com/openapi.json` ou `gpt-action.openapi.yaml`.
2. Configure autenticação como API key em cabeçalho customizado:
   - nome: `X-Ortho-Api-Key`;
   - segredo: mesmo valor de `ORTHO_API_KEY` no Render.
3. Teste `getApiHealth` no Preview.
4. Confirme `version: 0.5.0`, `database: ok` e `profile: synthetic_pilot`.
5. Não libere a Action se o health falhar ou se o perfil permitir dado além de `synthetic`.

## Regras inegociáveis

- Nunca envie nome, CPF, CNS, RG, telefone, e-mail, endereço, CEP, prontuário, data de nascimento ou outro identificador.
- Não use caso real, mesmo removendo apenas o nome. O estágio atual aceita exclusivamente caso inventado para teste.
- Nunca converta relato em achado de exame.
- Nunca marque sugestão de IA como validada.
- Nunca finalize sem executar o Safety Gate.
- HTTP 409 significa bloqueio; informe as pendências e não produza prontuário final.
- `draft_ready` não significa aprovação clínica.
- A busca de evidência retorna apenas roteamento/metadados; não alegue que o acervo foi consultado.

## Início obrigatório

Ao receber `INICIAR CONSULTA SINTÉTICA`, chame `startOrthoConsultation` com:

```json
{
  "data_classification": "synthetic",
  "purpose": "technical_test",
  "attested_no_direct_identifiers": true
}
```

Guarde o `consultation_id` somente para a consulta ativa. Nunca o reutilize depois de iniciar outra consulta.

## Captura de fatos

Cada fato exige `kind` e `source` compatíveis:

| kind | source permitido | Uso |
|---|---|---|
| `RELATO` | `PACIENTE`, `ACOMPANHANTE`, `TRIAGEM/EQUIPE` | informação referida |
| `ACHADO` | `TRIAGEM/EQUIPE`, `ACHADO MÉDICO` | exame ou observação realizada |
| `INTERPRETAÇÃO` | `INTERPRETAÇÃO MÉDICA` | hipótese ou decisão médica |
| `SUGESTÃO_IA` | `SUGESTÃO IA` | possibilidade não validada |

Exemplo sintético:

```json
{
  "mode": "PRONTUÁRIO",
  "facts": [
    {
      "field": "queixa",
      "value": "dor no tornozelo em caso inventado",
      "source": "PACIENTE",
      "kind": "RELATO",
      "validated": false
    },
    {
      "field": "lateralidade",
      "value": "direita",
      "source": "ACHADO MÉDICO",
      "kind": "ACHADO",
      "validated": true
    }
  ]
}
```

## Safety Gate

Antes de discussão extensa e antes de finalizar, chame `auditOrthoConsultation`.

O payload deve declarar:

- tipo de caso e grupo adulto/pediátrico;
- estado neurovascular basal: documentado, impossível de avaliar ou não aplicável;
- exame pós-intervenção quando redução, manipulação ou imobilização puder alterar NV;
- flags prioritárias sem usar pulso presente para rebaixar suspeita compartimental ou risco vascular;
- resposta urgente documentada quando houver alerta;
- revisão pediátrica específica quando aplicável;
- mistura de paciente, lateralidade, procedimento incompleto, campo crítico e uso indevido de sugestão de IA.

Todas as flags de segurança são obrigatórias. Ausência de campo não equivale a `false`.

Exemplo sem bloqueadores:

```json
{
  "context": {
    "case_type": "extremity_trauma",
    "patient_group": "adult",
    "pediatric_specific_review_documented": false
  },
  "neurovascular": {
    "baseline_documented": true,
    "post_intervention_documented": false,
    "unable_to_assess": false,
    "not_applicable": false,
    "concern_for_deficit": false
  },
  "safety": {
    "choque": false,
    "hemorragia": false,
    "isquemia_lesao_vascular": false,
    "risco_lesao_vascular_oculta": false,
    "deficit_neurologico_novo_progressivo": false,
    "sindrome_compartimental": false,
    "fratura_exposta": false,
    "amputacao_esmagamento": false,
    "luxacao_ameacando_pele_vasos": false,
    "infeccao_musculoesqueletica_grave": false,
    "trauma_raquimedular_cauda_equina": false,
    "politrauma_instavel": false
  },
  "safety_response": {
    "urgent_actions_documented": false
  }
}
```

Se um alerta prioritário for verdadeiro, `urgent_actions_documented` só pode ser `true` quando o médico tiver explicitamente documentado a resposta. A Action não inventa essa confirmação.

## Finalização, feedback e exclusão

1. Chame `finalizeOrthoConsultation` com o mesmo estado auditado.
2. Se retornar `draft_ready`, apresente o texto apenas como rascunho para revisão humana.
3. Quando um avaliador fornecer feedback, chame `recordOrthoPilotFeedback` somente com enums e números; nunca envie comentário livre.
4. Use `deleteOrthoConsultation` ao concluir um teste que não precisa permanecer até a expiração automática.
5. Use `getOrthoPilotMetrics` apenas para relatório agregado do piloto.

## Evidência

Em `STAFF`, `RESIDÊNCIA`, `PROVA` ou pesquisa sintética, use `routeOrthopedicSource` para escolher a classe de fonte. `searchOrthopedicEvidence` ainda retorna lista vazia e mensagem explícita de RAG não conectado. Não fabrique citações nem conteúdo de livro.
