# Consumo de combustível — Colhedoras CRV

Painel de acompanhamento do consumo de diesel das colhedoras com telemetria: litros por hora (L/h), litros por tonelada colhida (L/t), motor ocioso, faixa de RPM e motivos de parada.

**Período atual:** 19/10/2026 a 25/10/2026 (frentes 1, 2 e 3)

Abra o `index.html` ou acesse pelo GitHub Pages.

## Bases usadas
- **Indicador de Consumo de Combustível — Colhedoras (PDF)**: coluna SEMANA, com horas, diesel, L/h, toneladas e L/t por frota e por frente.
- **Monit**: exportação da telemetria (estado, motor ligado, RPM, operação) — motor ocioso, paradas, RPM, motivos e turnos.

## Regras
- Frentes 1, 2, 3 e 6. Colhedoras sem telemetria aparecem só com os dados de consumo.
- L/h = litros abastecidos no período ÷ horas trabalhadas. Meta 32,00 L/h.
- L/t = litros ÷ toneladas, só colhedoras com abastecimento e pesagem.
- Motor ocioso = estado PARADA com motor ligado (monit). Cada parada (sequência contínua de leituras paradas com motor ligado) tem 90 segundos descontados; paradas de até 90 s não contam. Nas colhedoras 850 RPM é a marcha lenta real. Meta 10% das horas de motor ligado.
- Horas = horímetro do abastecimento: maior leitura do período − maior leitura do último dia de abastecimento antes do período.
- Turnos: A 07–15h, B 15–23h, C 23–07h.
- Paradas longas: paradas com motor ligado acima de 10 min e de 30 min, por colhedora.
- Motor ocioso por operador: operador registrado no monit; só operadores com pelo menos 5 h de motor ligado.
- Faixa de RPM: % do tempo de motor ligado por faixa, geral e por frente. Excesso de RPM = acima de 2.000 (top 10 colhedoras).

## Como gerar o relatório de uma nova semana
1. Baixe o PDF do **Indicador Consumo de Combustível — Colhedoras** (a coluna SEMANA define o período) e as exportações do **monit** da mesma semana (CSV com `;`).
2. Rode:
   ```
   python gerar/gerar_relatorio.py --pdf INDICADOR.pdf --monit MONIT1.csv MONIT2.csv --frentes 1,2,3
   ```
3. O `index.html` é refeito com o layout padrão (`gerar/modelo.html`). Publique com commit e push.

Precisa de Python 3 e `pdftotext` (poppler-utils). Para mudar o visual, edite `gerar/modelo.html` (os dados entram no lugar de `__DADOS__`).

## Cores da faixa de RPM
Verde: marcha lenta (até 900). Azul: 901–1.500 (claro) e 1.501–1.800. Amarelo pastel: 1.801–2.000. Vermelho: excesso (acima de 2.000).

