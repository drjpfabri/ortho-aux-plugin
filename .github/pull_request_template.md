## Escopo

- [ ] A mudança tem finalidade e limites descritos.
- [ ] Nenhum dado clínico, identificador ou segredo foi incluído.
- [ ] O ambiente permanece `synthetic` ou há aprovação C4 formal anexada.

## Segurança

- [ ] Safety Gate, revisão humana e proveniência não foram rebaixados.
- [ ] Mudança clínica inclui revisor independente e teste de regressão.
- [ ] Mudança de schema inclui OpenAPI regenerado e teste da GPT Action no Preview.
- [ ] Mudança de fornecedor, dados, RAG ou integração atualiza fluxo, RIPD, riscos e decisão.

## Verificação

- [ ] `ruff check app tests scripts`
- [ ] `python scripts/validate_governance.py`
- [ ] `python -m pytest -q`
- [ ] `python scripts/export_openapi.py` sem diff inesperado
- [ ] Plano de reversão descrito e não destrutivo

## Aprovação

- [ ] Classe da mudança: C1 / C2 / C3 / C4 / C5
- [ ] Aprovações exigidas por `docs/CHANGE_CONTROL.md` registradas
