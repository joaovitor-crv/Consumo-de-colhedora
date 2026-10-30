# Relatório de consumo das colhedoras (CRV)

Ao gerar ou atualizar o relatório, use sempre o gerador. Não redesenhe a página à mão.

```
python3 gerar/gerar_relatorio.py --pdf <INDICADOR.pdf> --monit <MONIT1.csv> [<MONIT2.csv> ...] --frentes 1,2,3,5,6
```

## Entradas
- PDF "INDICADOR CONSUMO DE COMBUSTÍVEL — COLHEDORAS". A coluna SEMANA define o período e traz horas, diesel, L/h, toneladas e L/t por frota e por frente.
- CSVs do monit (separados por `;`) da mesma semana.
- Frentes padrão: 1, 2, 3, 5 e 6 (frentes 5 e 6 incluídas a pedido do usuário em 28/10/2026).

## Padrão aprovado pelo usuário (28/10/2026)
- **Layout** em `gerar/modelo.html`:
  - Tabela por colhedora com total por frente, e abaixo dela motivo e turno do motor ocioso.
  - % ocioso por colhedora com meta de 10%, horas ociosas (top 10), paradas longas (>10 e >30 min) e ocioso diário.
  - L/h e L/t por frente.
  - Faixa de RPM geral e por frente, top 10 colhedoras e top 10 operadores em excesso de RPM (>2.000) e ocioso por operador.
  - Rankings de % ocioso, horas ociosas e excesso de RPM por colhedora são clicáveis: abrem os operadores daquela colhedora (motor ligado, ocioso, % ocioso, tempo e % acima de 2.000 RPM).
  - Nos rankings por operador, ao lado do nome: frente e colhedora com mais horas (+N = outras colhedoras). Operador com +N é clicável (azul sublinhado): abre as colhedoras que operou, com frente, horas de motor ligado e % do tempo (30/10/2026).
  - Motor ocioso por motivo: 7 maiores motivos + "Outros". "Outros" é clicável e abre cada motivo com horas, % de Outros e % do total ocioso (30/10/2026).
  - Abaixo do ocioso por operador: quadro "Com abastecimento, sem dados no Solinftec" (frotas do PDF sem monit).
- **Cores de RPM**:
  - Verde: marcha lenta (até 900).
  - Azul claro: 901–1.500.
  - Azul escuro: 1.501–1.800.
  - Amarelo pastel: 1.801–1.900.
  - Laranja: 1.901–2.000.
  - Vermelho: 2.001+ (excesso).
- **Faixas de RPM** (30/10/2026): 1–900, 901–1.500, 1.501–1.800, 1.801–1.900, 1.901–2.000 e 2.001+, no gráfico geral e por frente.
- **Metas**: 32,00 L/h e 10% de motor ocioso.
- **Motor ocioso**:
  - É a sequência de leituras em PARADA com motor ligado (Sim ou RPM ≥ 700).
  - Cada leitura vale até a próxima, com limite de 10 min.
  - Descontam-se 90 s de cada parada.
- **Rankings de operador e de RPM**: só entram com pelo menos 5 h de motor ligado.
- **Assinatura no rodapé**: "Desenvolvido por João Vitor - CRV".

## Mudanças
- Mudanças de visual vão em `gerar/modelo.html`; os dados entram em `__DADOS__`.
- Mudanças de cálculo vão em `gerar/gerar_relatorio.py`.
- Depois de mudar qualquer um dos dois, regenere o `index.html`, confira a página no navegador e faça commit e push.
