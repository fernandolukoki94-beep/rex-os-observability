# Failure Testing

O REX deve tratar falhas como estados operacionais explícitos, não como excepções escondidas. A suite backend actual cobre os contratos mais importantes da POC e mantém os cenários futuros visíveis.

| Cenário | Estado | Garantia |
|---|---|---|
| Evento duplicado | Testado | `event_id` idêntico é idempotente; hash diferente devolve `409` sem sobrescrever o original |
| API key ausente ou incorrecta | Testado | `401` quando `REX_API_KEY` está configurada |
| Papel sem permissão de escrita | Testado | `403` quando `REX_RBAC_ENFORCED=1` |
| Fila persistida e recarregada | Testado | Eventos não desaparecem após reabertura |
| Edge Queue SQLite após reinício | Testado | O agente reabre a base local e reconcilia os eventos quando o transporte regressa |
| Transporte rejeita o próximo evento | Testado | O head da fila permanece intacto e os restantes eventos não são descartados |
| Acumulação de 10.000 eventos offline | Testado | SQLite conserva FIFO, profundidade e integridade da base local |
| Sync failed e retry | Testado | O evento permanece retryable com jitter e metadados persistidos |
| JSON corrompido | Testado | O motor falha fechado, inicia vazio e volta a persistir atomicamente |
| Timeout de rede | Frontend boundary | O evento permanece local e retryable |
| Falha parcial de sync | Testado | Sucessos e falhas permanecem com estados independentes após reload |
| Servidor indisponível durante sync | Frontend boundary | Não marcar `SYNCED` sem ACK |
| Dead-letter replay | Testado | Apenas um evento dead-letter é re-encaminhado por decisão supervisionada e auditada |
| Cadeia de hashes | Testado | Cada evento referencia o hash do evento anterior |
| Eventos concorrentes | Próximo teste | JSON não substitui garantias transaccionais de PostgreSQL |
| Payload excessivo ou telemetria inválida | Próximo teste | Requer limites de tamanho e schema validation explícitos |
| Reinício durante sincronização | Testado | O Edge Agent recupera após encerramento; o cenário ACK → crash → retry mantém o evento na fila e a deduplicação do receiver impede um segundo efeito semântico |

A regra de segurança da POC é conservadora: **sem ACK válido, nenhum evento é apresentado como sincronizado**. A suite local prova reinício, rejeição de transporte, integridade SQLite, acumulação de 10.000 amostras e a janela exacta ACK → crash → retry. A garantia é at-least-once com deduplicação semântica; não é uma afirmação de exactly-once distribuído. A validação industrial deverá acrescentar testes multi-processo, retenção, backup/restore, replay protection, autenticação de dispositivos e transporte real autorizado.
