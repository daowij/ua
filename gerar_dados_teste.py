"""Gera CSVs FICTICIOS no formato do TSE e logs falsos, so para testar o pipeline."""
import random
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
            # log falso, um arquivo por secao, com horarios entre 8h e 17h
            with open(ldir / f"o00407-{cod:05d}0001{secao:04d}.dat", "w", encoding="latin-1") as f:
                for _ in range(comp):
                    h = random.choices(range(8, 17), weights=[3, 5, 4, 3, 2, 3, 4, 3, 1])[0]
                    f.write(f"04/10/2026 {h:02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d}"
                            "\tINFO\tLOGD\tVoto\tO voto do eleitor foi computado\n")
    (vdir / f"votacao_secao_{ANO}_{uf}.csv").write_text("\n".join(vl), encoding="latin-1")
    (ddir / f"detalhe_votacao_secao_{ANO}_{uf}.csv").write_text("\n".join(dl), encoding="latin-1")
print("dados de teste gerados em", config.DATA_DIR)
