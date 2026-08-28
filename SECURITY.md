# Política de segurança

## Escopo suportado

A versão `0.6.x` recebe correções de segurança enquanto o alpha sintético estiver ativo. O serviço não está autorizado para dados de pacientes nem para uso clínico.

## Relato responsável

Relate vulnerabilidades de forma privada ao proprietário do repositório. Use o recurso privado de segurança do GitHub quando estiver disponível. Não abra issue pública com segredo, payload, log sensível, captura de tela ou dado de paciente.

Inclua somente:

- versão ou commit;
- endpoint e categoria da falha;
- impacto provável;
- reprodução mínima com dados sintéticos;
- sugestão de contenção, quando houver.

## Resposta imediata

Possível chave exposta, acesso não autorizado, dado pessoal, desvio do Safety Gate ou integração não autorizada exige suspensão da Action e execução de `docs/INCIDENT_RUNBOOK.md`.

Não teste com dados reais e não tente obter acesso a consultas de terceiros.
