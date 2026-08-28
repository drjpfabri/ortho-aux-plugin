# Política de governança de dados e segurança clínica

Versão: 1.0 - 2026-08-28

Política técnica: `2026-08-28.1`

Próxima revisão obrigatória: 2026-09-03

## Decisão vigente

O `ortho-aux-plugin` está autorizado somente para avaliação interna com casos integralmente sintéticos. Não há autorização para assistência, diagnóstico, prescrição, triagem autônoma, decisão clínica, integração com prontuário ou tratamento de dados derivados de pacientes.

A API aplica esta decisão em tempo de execução:

- aceita apenas a classificação `synthetic` no Render;
- nunca aceita dados identificáveis como classificação suportada;
- mantém `clinical_use_authorized=false`;
- mantém frontend e RAG sem autorização de integração;
- suspende novas consultas quando a revisão de governança vence;
- exige um conjunto de evidências, responsáveis e controles antes de aceitar `deidentified`.

O bloqueio heurístico de identificadores é defesa complementar. Ele não transforma dados pessoais em dados anônimos nem autoriza seu envio.

## Classificação dos dados

| Classe | Definição operacional | Situação |
|---|---|---|
| `synthetic` | caso inventado, sem origem em pessoa natural e sem combinação reidentificável | permitido no alpha interno |
| `deidentified` | dado derivado de paciente com identificadores removidos | bloqueado; continua sujeito a avaliação de risco e governança |
| identificável | informação relacionada a pessoa identificada ou identificável | não suportado e proibido nesta versão |

Dados de saúde vinculados a pessoa natural são dados pessoais sensíveis. A LGPD também exige medidas de segurança, prevenção e prestação de contas, e define o RIPD como documento que descreve tratamento, riscos e salvaguardas. A referência normativa é a [Lei nº 13.709/2018, texto compilado](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709compilado.htm).

## Finalidades permitidas

- teste técnico sintético;
- validação clínica humana de cenários sintéticos;
- treinamento interno com material sintético;
- medição agregada sem texto clínico.

É proibido reutilizar os registros para atendimento, pesquisa com participantes, treinamento de modelo, publicidade, perfilamento, seleção de risco ou decisão automatizada.

## Minimização e ciclo de vida

1. A consulta nasce com classificação, finalidade e atestado explícitos.
2. Fatos exigem proveniência e não podem conter identificadores diretos detectáveis.
3. O banco retém consultas por no máximo 168 horas, salvo exclusão antecipada.
4. Métricas não recebem texto livre nem identificador de consulta.
5. Logs de aplicação não registram corpos de requisição ou resposta.
6. O endpoint de exclusão remove a consulta e seus fatos.

Retenção da aplicação não equivale à retenção de todos os fornecedores envolvidos. Antes de qualquer dado derivado de paciente, devem ser revisados contratos, subprocessadores, localização, transferências internacionais e controles de retenção de cada serviço. A documentação da OpenAI, por exemplo, descreve controles próprios da API e ressalta que serviços de terceiros têm políticas próprias; isso não deve ser presumido como regra do produto ChatGPT ou de uma Action. Consulte [Data controls in the OpenAI platform](https://developers.openai.com/api/docs/guides/your-data).

## Portões de liberação

O arquivo `governance/control-register.yaml` é a fonte versionada dos controles. O CI impede publicação quando o registro diverge do código ou do `render.yaml`.

Para permitir qualquer dado derivado de paciente, são obrigatórios, no mínimo:

- aprovação formal vigente e referência auditável;
- responsáveis clínico, técnico e de privacidade nomeados;
- revisão clínica independente assinada;
- base legal e papéis de controlador/operador definidos;
- RIPD formal aprovado;
- identidade individual, RBAC, MFA e revogação por usuário;
- branch protegida, checks obrigatórios e revisão compatível com a classe da mudança;
- infraestrutura com backup e recuperação pontual;
- análise contratual de fornecedores e transferência internacional;
- enquadramento regulatório formal;
- política de privacidade e canal do titular, quando aplicáveis.

Uma variável de ambiente isolada não libera o sistema. Todos os controles técnicos exigidos precisam estar presentes e válidos.

## Segurança clínica e regulatória

Toda saída permanece rascunho com revisão médica obrigatória. O Safety Gate não pode ser rebaixado por frontend, GPT, RAG ou outro gerador.

A finalidade pretendida influencia o enquadramento sanitário e a classe de risco. A Anvisa informa que a classificação depende da função pretendida e que software pode estar sujeito às regras de Software como Dispositivo Médico. O projeto não declara enquadramento nem regularização concluídos. Antes de qualquer uso clínico, é obrigatória avaliação regulatória documentada com base na [RDC 657/2022 e orientações de SaMD](https://www.gov.br/anvisa/pt-br/centraisdeconteudo/publicacoes/produtos-para-a-saude/manuais/software-como-dispositivo-medico-perguntas-e-respostas) e nas [regras de classificação aplicáveis](https://www.gov.br/anvisa/pt-br/setorregulado/regularizacao/produtos-para-saude/conceitos-e-definicoes/classificacao-de-equipamentos).

## Revisão e suspensão

A revisão vence em 2026-09-03. Após essa data, a API permanece observável, mas bloqueia novas consultas até atualização deliberada do registro, do `render.yaml` e da decisão correspondente.

Qualquer incidente de privacidade, hard stop crítico perdido, credencial comprometida, divergência de schema, integração não autorizada ou ausência de responsável aciona suspensão imediata e o `INCIDENT_RUNBOOK.md`.

Este documento é um controle de engenharia e não substitui parecer jurídico, regulatório, ético ou institucional.
