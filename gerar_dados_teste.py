"""Gera CSVs FICTICIOS no formato do TSE e logs falsos, so para testar o pipeline."""
import io
import random
import zipfile
from pathlib import Path

import config

random.seed(1)
ANO = 2026
UFS = {"SP": ("Sudeste", 3), "BA": ("Nordeste", 3), "RS": ("Sul", 2), "AM": ("Norte", 2)}
CANDS = [(13, "CANDIDATO A"), (22, "CANDIDATO B"), (95, "Branco"), (96, "Nulo")]

vdir = config.RAW_DIR / str(ANO) / "votacao"
ddir = config.RAW_DIR / str(ANO) / "detalhe"
ldir = config.DATA_DIR / "logs_teste"
for d in (vdir, ddir, ldir):
    d.mkdir(parents=True, exist_ok=True)

VH = ("ANO_ELEICAO;NR_TURNO;SG_UF;CD_MUNICIPIO;NM_MUNICIPIO;NR_ZONA;NR_SECAO;"
      "CD_CARGO;DS_CARGO;NR_VOTAVEL;NM_VOTAVEL;QT_VOTOS;NR_LOCAL_VOTACAO")
DH = ("ANO_ELEICAO;NR_TURNO;SG_UF;CD_MUNICIPIO;NR_ZONA;NR_SECAO;CD_CARGO;DS_CARGO;"
      "QT_APTOS;QT_COMPARECIMENTO;QT_ABSTENCOES")

for uf, (_, nmun) in UFS.items():
    vl, dl = [VH], [DH]
    for m in range(nmun):
        cod = 10000 + m
        for secao in range(1, 6):
            aptos = random.randint(200, 400)
            comp = int(aptos * random.uniform(0.7, 0.9))
            pesos = [random.random() + (0.8 if uf in ("BA", "AM") else 0.2), random.random() + 0.5, 0.05, 0.05]
            tot = sum(pesos)
            votos = [int(comp * p / tot) for p in pesos]
            for (nr, nm), q in zip(CANDS, votos):
                vl.append(f"{ANO};1;{uf};{cod};MUN{m};1;{secao};1;Presidente;{nr};{nm};{q};1")
            dl.append(f"{ANO};1;{uf};{cod};1;{secao};1;Presidente;{aptos};{comp};{aptos-comp}")
            # log falso no formato real: .jez (zip) com logd.dat, um por secao
            L = ["25/09/2026 11:17:10\tINFO\t01829267\tGAP\tIniciando aplicação - "
                 "ELEIÇÃO OFICIAL PRIMEIRO TURNO - 1º turno\tAAAA"]
            for _ in range(comp):
                h = random.choices(range(8, 17), weights=[3, 5, 4, 3, 2, 3, 4, 3, 1])[0]
                t = h * 3600 + random.randint(0, 3599)
                dur = random.randint(30, 120)
                for seg, msg in ((t, "Eleitor foi habilitado"), (t + dur, "O voto do eleitor foi computado")):
                    L.append(f"04/10/2026 {seg//3600:02d}:{seg%3600//60:02d}:{seg%60:02d}"
                             f"\tINFO\t01829267\tVOTA\t{msg}\tBBBB")
            L.append("21/10/2026 17:30:19\tINFO\t01829267\tGAP\tIniciando aplicação - "
                     "ELEIÇÃO OFICIAL SEGUNDO TURNO - 2º turno\tCCCC")
            for _ in range(comp // 2):  # 2o turno com menos votos, so p/ testar a troca de turno
                seg = random.randint(8 * 3600, 16 * 3600)
                L.append(f"25/10/2026 {seg//3600:02d}:{seg%3600//60:02d}:{seg%60:02d}"
                         "\tINFO\t01829267\tVOTA\tO voto do eleitor foi computado\tDDDD")
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("logd.dat", "\n".join(L).encode("latin-1"))
            nome = f"o03221{uf.lower()}{cod:05d}0001{secao:04d}-log.jez"
            (ldir / nome).write_bytes(buf.getvalue())
    (vdir / f"votacao_secao_{ANO}_{uf}.csv").write_text("\n".join(vl), encoding="latin-1")
    (ddir / f"detalhe_votacao_secao_{ANO}_{uf}.csv").write_text("\n".join(dl), encoding="latin-1")
print("dados de teste gerados em", config.DATA_DIR)
