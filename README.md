# Consumo de combustível — Colhedoras CRV

Painel de acompanhamento do consumo de diesel das colhedoras com telemetria: litros por hora (L/h), litros por tonelada colhida (L/t), motor ocioso, faixa de RPM e motivos de parada.

**Período atual:** 26/10/2026 a 01/11/2026 (frentes 1, 2, 3, 5 e 6)

Abra o `index.html` ou acesse pelo GitHub Pages. Para baixar, use o botão **Baixar PDF** no topo e escolha "Salvar como PDF" (o painel inteiro sai numa folha A3).

## Bases usadas
- **Indicador de Consumo de Combustível — Colhedoras (PDF)**: a coluna da semana do relatório (a última, quando o PDF traz várias semanas lado a lado), com horas, diesel, L/h, toneladas e L/t por frota e por frente.
- **Monit**: exportação da telemetria (estado, motor ligado, RPM, operação) — motor ocioso, paradas, RPM, motivos e turnos.

## Regras
- Frentes 1, 2, 3, 5 e 6. Colhedoras sem telemetria aparecem só com os dados de consumo.
- L/h = litros abastecidos no período ÷ horas trabalhadas. Meta 34,00 L/h (até 02/11/2026 era 32,00).
- L/t = litros ÷ toneladas, só colhedoras com abastecimento e pesagem.
- Motor ocioso = estado PARADA com motor ligado (monit). Cada parada (sequência contínua de leituras paradas com motor ligado) tem 90 segundos descontados; paradas de até 90 s não contam. Nas colhedoras 850 RPM é a marcha lenta real. Meta 10% das horas de motor ligado.
- Horas = horímetro do abastecimento: maior leitura do período − maior leitura do último dia de abastecimento antes do período.
- Turnos: A 07–15h, B 15–23h, C 23–07h.
- Paradas longas: paradas com motor ligado acima de 10 min e de 30 min, por colhedora.
- Motor ocioso por operador: operador registrado no monit; só operadores com pelo menos 5 h de motor ligado.
- Faixa de RPM: % do tempo de motor ligado por faixa, geral e por frente. Faixas: 1-900, 901-1.500, 1.501-1.800, 1.801-1.900, 1.901-2.000 e 2.001+. Excesso de RPM = 2.001+ (top 10 colhedoras).
- Cliques: colhedora nos rankings abre os operadores; operador com +N abre as outras colhedoras; "Outros" em motivos abre os motivos que estão dentro dele.

## Como gerar o relatório de uma nova semana
1. Baixe o PDF do **Indicador Consumo de Combustível — Colhedoras** (a última coluna de semana define o período; `--coluna N` escolhe outra, 1 = primeira) e as exportações do **monit** da mesma semana (CSV com `;`).
2. Rode:
   ```
   python gerar/gerar_relatorio.py --pdf INDICADOR.pdf --monit MONIT1.csv MONIT2.csv --monit-anterior MONIT_SEMANA_ANTERIOR.csv --frentes 1,2,3,5,6
   ```
   Quando o PDF traz a semana anterior ao lado, o relatório compara com ela: nos cartões do topo (valor anterior e variação), na coluna "vs" da tabela (diferença de L/h por colhedora e por frente) e nos gráficos de L/h e L/t por frente (barra cinza = semana anterior). Com `--monit-anterior`, compara também o motor ocioso e o tempo acima de 2.000 RPM (geral e por frente). Sem semana anterior no PDF, a página sai como antes.
3. O `index.html` é refeito com o layout padrão (`gerar/modelo.html`). Publique com commit e push.

Precisa de Python 3 e `pdftotext` (poppler-utils). Para mudar o visual, edite `gerar/modelo.html` (os dados entram no lugar de `__DADOS__`).

## Cores da faixa de RPM
Verde: marcha lenta (até 900). Azul: 901–1.500 (claro) e 1.501–1.800. Amarelo pastel: 1.801–1.900. Laranja: 1.901–2.000. Vermelho: excesso (2.001+).

