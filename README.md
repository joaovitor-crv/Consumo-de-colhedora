# Consumo de combustível — Colhedoras CRV

Painel de acompanhamento do consumo de diesel das colhedoras com telemetria: litros por hora (L/h), litros por tonelada colhida (L/t), motor ocioso, faixa de RPM e motivos de parada.

**Período atual:** 12/10/2026 a 22/10/2026

Abra o `index.html` ou acesse pelo GitHub Pages.

## Bases usadas
- **Abastecimento**: relatório "Saída de Combustível por Código do Posto" (625xx, com horímetro) e relatório analítico (225xx).
- **Balança**: pesagem "Colhedora - Cana", peso líquido em kg da coluna M, somado por colhedora (coluna C).
- **Monit**: exportação da telemetria (estado, motor ligado, RPM, operação).

## Regras
- Só entram colhedoras com telemetria (monit).
- L/h = litros abastecidos no período ÷ horas trabalhadas. Meta 32,00 L/h.
- L/t = litros ÷ toneladas, só colhedoras com abastecimento e pesagem.
- Motor ocioso = estado PARADA com motor ligado (monit). Cada parada (sequência contínua de leituras paradas com motor ligado) tem 90 segundos descontados; paradas de até 90 s não contam. Nas colhedoras 850 RPM é a marcha lenta real. Meta 10% das horas de motor ligado.
- Horas = horímetro do abastecimento: maior leitura do período − maior leitura do último dia de abastecimento antes do período.
- Turnos: A 07–15h, B 15–23h, C 23–07h.
