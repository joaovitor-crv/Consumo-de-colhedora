"""Gera o index.html do relatório de consumo das colhedoras.

Uso:
  python gerar/gerar_relatorio.py --pdf INDICADOR.pdf --monit MONIT1.csv MONIT2.csv [--frentes 1,2,3]

- Consumo (horas, diesel, L/h, toneladas, L/t): coluna SEMANA do PDF
  "Indicador Consumo de Combustível — Colhedoras". O período do relatório é o da SEMANA.
- Motor ocioso, paradas, RPM, motivos, turnos e operadores: exportação do monit (CSV com ';').
- Requer pdftotext (poppler-utils).

Desenvolvido por João Vitor - CRV
"""
import argparse
import collections
import csv
import json
import os
import re
import subprocess
from datetime import datetime, timedelta

AQUI = os.path.dirname(os.path.abspath(__file__))
CAP = 600          # cada leitura do monit vale no máximo 10 min
DESCONTO = 90      # segundos descontados de cada parada com motor ligado
META_LH, META_LT, META_OC = 32.0, 1.0, 0.10
MIN_H = 5 * 3600   # mínimo de motor ligado para entrar nos rankings (operador e RPM)
ROMANO = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10}
BANDAS = ["1 - 900 (lenta)", "901 - 1.500", "1.501 - 1.800", "1.801 - 2.000", "Acima de 2.000"]


def num(s):
    s = s.strip()
    if s in ("—", "-", ""):
        return None
    return float(s.replace(".", "").replace(",", "."))


def br(v, d):
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ---------------- PDF do indicador ----------------
def ler_pdf(caminho, frentes):
    txt = subprocess.run(["pdftotext", "-layout", caminho, "-"], capture_output=True, text=True, check=True).stdout
    per = re.findall(r"(\d{2}/\d{2}/\d{4}) a (\d{2}/\d{2}/\d{4}) · \d+ dias", txt)
    if not per:
        raise SystemExit("Não achei o período da SEMANA no PDF.")
    ini, fim = per[0]
    atual = re.search(r"Atualizado em (\d{2}/\d{2}/\d{4} \d{2}:\d{2})", txt)
    grupos = collections.OrderedDict()
    totais = {}
    atual_fr = None
    for ln in txt.splitlines():
        s = ln.strip()
        m = re.match(r"^FRENTE ([IVX]+)\b", s)
        if m:
            atual_fr = ROMANO.get(m.group(1))
            continue
        if s.startswith("SEM FRENTE") or s.startswith("Total do bloco") or s.startswith("TOTAL GERAL"):
            atual_fr = None
            continue
        m = re.match(r"^Total FRENTE ([IVX]+)\s+ℓ/h\s+[\d,.]+\s+(.*)$", s)
        if m:
            f = ROMANO.get(m.group(1))
            if f in frentes:
                t = m.group(2).split()
                totais[f] = dict(horas=num(t[0]), litros=num(t[1]), lh=num(t[2]), ton=num(t[3]), lt=num(t[4]))
            continue
        m = re.match(r"^(\d{5})\s+ℓ/h\s+[\d,.]+\s+(.*)$", s)
        if m and atual_fr in frentes:
            t = m.group(2).split()
            grupos.setdefault(atual_fr, []).append(dict(
                frota=int(m.group(1)), horas=num(t[0]), litros=num(t[1]), lh=num(t[2]), ton=num(t[3]), lt=num(t[4])))
    falta = [f for f in frentes if f not in grupos]
    if falta:
        raise SystemExit(f"Frente(s) {falta} não encontrada(s) no PDF.")
    m1 = re.search(r"(\d{5}(?:,\s*\d{5})*):\s*vieram", txt)
    m2 = re.search(r"integrado só até (\d{2}/\d{2}/\d{4})", txt)
    totais["_aviso"] = (f"Atenção (do indicador): {m1.group(1) if m1 else 'algumas frotas'} têm o abastecimento lançado à mão, "
                        f"integrado só até {m2.group(1)}; o diesel da semana depois dessa data pode estar incompleto.") if m2 else None
    return ini, fim, (atual.group(1) if atual else ""), grupos, totais


# ---------------- monit ----------------
def ler_monit(arquivos, frentes, ini, fim):
    d0 = datetime.strptime(ini, "%d/%m/%Y")
    d1 = datetime.strptime(fim, "%d/%m/%Y") + timedelta(days=1)
    nomes = {f"FRENTE {f}" for f in frentes}
    rows = collections.defaultdict(list)
    for arq in arquivos:
        with open(arq, encoding="utf-8", errors="replace") as fh:
            for r in csv.DictReader(fh, delimiter=";"):
                if r["Grupo"].strip() not in nomes:
                    continue
                t = datetime.strptime(r["Data/Hora"], "%d/%m/%Y %H:%M:%S")
                if not (d0 <= t < d1):
                    continue
                try:
                    rpm = float(r["RPM Motor"].replace(",", "."))
                except ValueError:
                    rpm = 0
                rows[r["Equipamento"].strip()].append(dict(
                    t=t, est=r["Estado"].strip(), lig=r["Motor Ligado"] == "Sim" or rpm >= 700, rpm=rpm,
                    op=r["Operacao"].strip().title(), oper=(r["Operador"] or "").strip().title() or "Sem Operador",
                    g=r["Grupo"].strip()))
    return rows, d1


def banda(r):
    return BANDAS[0] if r <= 900 else BANDAS[1] if r <= 1500 else BANDAS[2] if r <= 1800 else BANDAS[3] if r <= 2000 else BANDAS[4]


def turno(t):
    return "A" if 7 <= t.hour < 15 else "B" if 15 <= t.hour < 23 else "C"


def calcular(rows, fim_dt):
    F = {}
    lig_d = collections.defaultdict(float); oc_d = collections.defaultdict(float)
    rpm_b = collections.defaultdict(float); mot = collections.defaultdict(float); tur = collections.defaultdict(float)
    op_l = collections.defaultdict(float); op_o = collections.defaultdict(float); op_f = collections.defaultdict(set)
    fr_rpm = collections.defaultdict(lambda: collections.defaultdict(float))
    eq_rpm = collections.defaultdict(lambda: collections.defaultdict(float))
    longas = {}
    tot = dict(paradas=0, paradas_90=0, oc_bruto=0.0)
    for eq, L in rows.items():
        L.sort(key=lambda x: x["t"])
        for i, x in enumerate(L):
            nt = L[i + 1]["t"] if i + 1 < len(L) else min(x["t"] + timedelta(seconds=60), fim_dt)
            x["d"] = max(0.0, min((nt - x["t"]).total_seconds(), CAP))
        lig = oc = 0.0; par = p10 = p30 = 0; h10 = 0.0
        for x in L:  # tempo de motor ligado (todas as leituras)
            if x["lig"]:
                lig += x["d"]; dia = x["t"].strftime("%d/%m"); lig_d[dia] += x["d"]
                rpm_b[banda(x["rpm"])] += x["d"]; fr_rpm[x["g"]][banda(x["rpm"])] += x["d"]
                eq_rpm[eq][banda(x["rpm"])] += x["d"]
                op_l[x["oper"]] += x["d"]; op_f[x["oper"]].add(eq)
        i = 0
        while i < len(L):  # paradas com motor ligado
            if L[i]["est"] == "PARADA" and L[i]["lig"]:
                j = i; dur = 0.0
                while j < len(L) and L[j]["est"] == "PARADA" and L[j]["lig"]:
                    dur += L[j]["d"]; j += 1
                par += 1; tot["paradas"] += 1; tot["oc_bruto"] += dur
                if dur > 600: p10 += 1; h10 += dur
                if dur > 1800: p30 += 1
                if dur > DESCONTO:
                    tot["paradas_90"] += 1; k = (dur - DESCONTO) / dur
                    for s in L[i:j]:
                        v = s["d"] * k; oc += v
                        oc_d[s["t"].strftime("%d/%m")] += v; mot[s["op"]] += v; tur[turno(s["t"])] += v; op_o[s["oper"]] += v
                i = j
            else:
                i += 1
        F[eq] = dict(lig=lig, oc=oc, paradas=par, pct=oc / lig if lig else None)
        longas[eq] = dict(frota=eq, p10=p10, p30=p30, h10=h10 / 3600)
    dias = sorted(lig_d, key=lambda s: (s[3:], s[:2]))
    mt = sorted(mot.items(), key=lambda x: -x[1]); outros = sum(v for _, v in mt[7:])
    tl = sum(rpm_b.values()) or 1
    ops = [dict(l=o, v=op_o[o] / op_l[o], lig=op_l[o] / 3600, oc=op_o[o] / 3600,
                fr=", ".join(sorted(op_f[o])) if len(op_f[o]) <= 3 else f"{len(op_f[o])} colhedoras")
           for o in op_l if op_l[o] >= MIN_H]
    ops.sort(key=lambda x: -x["v"])
    rtop = [dict(l=e, v=v[BANDAS[4]] / sum(v.values())) for e, v in eq_rpm.items() if sum(v.values()) >= MIN_H]
    rtop.sort(key=lambda x: -x["v"])
    lg = sorted((v for v in longas.values() if v["p10"]), key=lambda x: (-x["p10"], -x["h10"]))
    return dict(
        F=F,
        oc_frota=sorted([dict(l=e, v=x["pct"]) for e, x in F.items() if x["pct"] is not None], key=lambda r: -r["v"]),
        oc_top=[dict(l=e, v=x["oc"] / 3600) for e, x in sorted(F.items(), key=lambda x: -x[1]["oc"])[:10]],
        oc_dia=[dict(l=d, v=oc_d[d] / lig_d[d]) for d in dias if lig_d[d]],
        rpm=[dict(l=b, v=rpm_b[b] / tl) for b in BANDAS],
        rpm_frente=[dict(l=g.title(), **{f"b{i}": fr_rpm[g][b] / (sum(fr_rpm[g].values()) or 1) for i, b in enumerate(BANDAS)})
                    for g in sorted(fr_rpm, key=lambda s: int(s.split()[-1]))],
        rpm_top=rtop[:10],
        motivo=[dict(l=l, v=v / 3600) for l, v in mt[:7]] + ([dict(l="Outros", v=outros / 3600)] if outros else []),
        oc_turno=[dict(l=t, v=tur[t] / 3600) for t in "ABC"],
        oc_op=ops[:10],
        longas=lg[:8],
        tot=dict(lig=sum(x["lig"] for x in F.values()) / 3600, oc=sum(x["oc"] for x in F.values()) / 3600,
                 oc_bruto=tot["oc_bruto"] / 3600, paradas=tot["paradas"], paradas_90=tot["paradas_90"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--monit", required=True, nargs="+")
    ap.add_argument("--frentes", default="1,2,3,5,6")
    ap.add_argument("--saida", default=os.path.join(AQUI, "..", "index.html"))
    a = ap.parse_args()
    frentes = [int(x) for x in a.frentes.split(",")]

    ini, fim, atualizado, grupos, totais = ler_pdf(a.pdf, frentes)
    rows, fim_dt = ler_monit(a.monit, frentes, ini, fim)
    M = calcular(rows, fim_dt)

    tab, fr, sem, sem_monit = [], [], [], []
    for f in frentes:
        linhas = []
        for x in grupos[f]:
            m = M["F"].get(str(x["frota"]))
            if not m:
                sem.append(str(x["frota"]))
                sem_monit.append(dict(frota=x["frota"], frente=f, litros=x["litros"], horas=x["horas"], lh=x["lh"]))
            linhas.append(dict(x, pct=m["pct"] if m else None, paradas=m["paradas"] if m else None))
        T = totais.get(f) or dict(
            horas=sum(x["horas"] or 0 for x in grupos[f]), litros=sum(x["litros"] or 0 for x in grupos[f]),
            ton=sum(x["ton"] or 0 for x in grupos[f]))
        T.setdefault("lh", T["litros"] / T["horas"] if T["horas"] else None)
        T.setdefault("lt", T["litros"] / T["ton"] if T["ton"] else None)
        tab.append(dict(grupo=f"FRENTE {f}", linhas=linhas, tot=T))
        fr.append(dict(l=f"Frente {f}", **T))
    TL = sum(x["litros"] for x in fr); TH = sum(x["horas"] for x in fr); TT = sum(x["ton"] for x in fr)
    t = M["tot"]
    nf = ", ".join(map(str, frentes[:-1])) + (" e " if len(frentes) > 1 else "") + str(frentes[-1])
    D = dict(
        periodo=f"{ini} - {fim}",
        K=dict(litros=TL, frotas=sum(len(g["linhas"]) for g in tab), ton=TT, lt=TL / TT if TT else 0, meta=META_LT,
               horas=TH, lh=TL / TH if TH else 0, meta_lh=META_LH, horas_oc=t["oc"], horas_oc_bruto=t["oc_bruto"],
               paradas=t["paradas"], paradas_90=t["paradas_90"], pct_oc=t["oc"] / t["lig"] if t["lig"] else 0),
        tabela=tab, frentes=fr, meta_oc=META_OC, sem_monit=sem_monit,
        **{k: M[k] for k in ["oc_frota", "oc_top", "oc_dia", "rpm", "rpm_frente", "rpm_top", "motivo", "oc_turno", "oc_op", "longas"]},
        notas=[
            f"Litros, horas, toneladas, L/h e L/t: coluna SEMANA ({ini[:5]} a {fim}) do Indicador de Consumo de Combustível — Colhedoras"
            + (f", atualizado em {atualizado}" if atualizado else "") + f". Frentes {nf}.",
            f"Motor ocioso, paradas, RPM, motivos, turnos e operadores: monit de {ini[:5]} a {fim}."
            + (f" Sem telemetria nesse período: {', '.join(sem)} ({'aparece' if len(sem) == 1 else 'aparecem'} na tabela só com os dados de consumo)." if sem else ""),
            *([totais["_aviso"]] if totais.get("_aviso") else []),
            f"Motor ocioso descontando 90 s de cada parada: {br(t['paradas'], 0)} paradas com motor ligado; "
            f"{br(t['paradas'] - t['paradas_90'], 0)} duraram até 90 s e não contam. Sem o desconto seriam {br(t['oc_bruto'], 1)} h; "
            f"com o desconto, {br(t['oc'], 1)} h.",
        ])
    html = open(os.path.join(AQUI, "modelo.html"), encoding="utf-8").read()
    html = html.replace("__DADOS__", json.dumps(D, ensure_ascii=False)).replace("__FRENTES__", f"Frentes {nf}")
    open(a.saida, "w", encoding="utf-8").write(html)
    print(f"Relatório gerado: {ini} a {fim} · frentes {nf} · {D['K']['frotas']} colhedoras · "
          f"{br(TL, 0)} L · {br(TT, 0)} t · {br(D['K']['lh'], 2)} L/h · ocioso {br(t['oc'], 1)} h ({br(D['K']['pct_oc'] * 100, 1)}%)")
    if sem:
        print("Sem monit:", ", ".join(sem))


if __name__ == "__main__":
    main()
