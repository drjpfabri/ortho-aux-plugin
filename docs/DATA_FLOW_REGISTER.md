# Registro de fluxo de dados e fornecedores

Versão: 1.0 - 2026-08-28

## Arquitetura autorizada

```text
Avaliador interno
      |
      | caso integralmente sintético
      v
GPT privado / GPT Action
      |
      | HTTPS + X-Ortho-Api-Key
      v
ortho-aux-plugin no Render
      |
      | conexão privada
      v
PostgreSQL no Render
```

O frontend `ortho-safety-mvp` está fora desse fluxo. Não existe autorização para conexão, tunnel, chamada de navegador ou envio de dados entre frontend e API. A ausência de CORS no backend reforça a separação atual, mas não substitui governança futura.

## Inventário

| Componente | Função | Entrada permitida | Persistência conhecida | Estado de governança |
|---|---|---|---|---|
| ChatGPT / GPT privado | interface e orquestração da Action | somente conteúdo sintético | termos e controles do produto precisam de revisão específica | uso sintético privado |
| GPT Action | chamada HTTPS ao backend | payload fechado e sintético | schema configurado no GPT | autenticada, permissão por chamada |
| Render Web Service | API FastAPI | payload sintético | logs técnicos da plataforma | ativo; sem corpo clínico na aplicação |
| Render PostgreSQL | consultas e fatos sintéticos | dados estruturados | até 168 h na aplicação; plano sem backup/PITR | temporário, expira em 2026-09-26 |
| GitHub | código, CI e documentos | nenhum dado clínico | histórico de versão | repositório privado |
| Sites frontend | demonstração privada | somente entradas sintéticas locais | conforme projeto separado | desconectado |

## Dados por etapa

| Etapa | Conteúdo | Identificador permitido | Controle |
|---|---|---|---|
| início | classificação, finalidade e atestado | nenhum | schema fechado |
| captura | fatos sintéticos com origem e tipo | nenhum | detector complementar e limite de tamanho |
| auditoria | flags estruturadas de segurança | nenhum | Gate determinístico |
| finalização | rascunho e fatos sintéticos | ID técnico aleatório da consulta | revisão humana obrigatória |
| métricas | enumerações e números agregados | nenhum ID de consulta | sem texto livre |
| logs | rota, status e metadados técnicos mínimos | request ID técnico | sem corpos na aplicação |

## Retenção e eliminação

- consultas: 168 horas por padrão;
- exclusão antecipada: endpoint autenticado `DELETE`;
- métricas: agregadas, sem texto ou ID de consulta;
- registros de incidente com dado pessoal: fora do banco clínico e sob custódia definida pelo controlador;
- logs e retenção de fornecedores: pendentes de análise contratual antes de qualquer dado derivado de paciente.

## Perguntas obrigatórias antes de integração ou beta

1. Quem é controlador e quem são os operadores em cada fluxo?
2. Quais países processam ou armazenam dados e qual mecanismo sustenta a transferência?
3. Qual retenção efetiva existe em ChatGPT, Action, Render e backups?
4. Há contrato, confidencialidade, suboperadores e resposta a incidente compatíveis?
5. O usuário tem identidade individual, menor privilégio e revogação?
6. O frontend preserva integralmente os bloqueadores e a proveniência?
7. A finalidade pretendida altera o enquadramento regulatório?

Sem respostas aprovadas e registradas, o fluxo permanece sintético e desconectado.
