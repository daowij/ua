"""Extrai o horario em que cada voto foi concluido a partir dos logs de urna.

IMPORTANTE: o log registra QUANDO um eleitor concluiu o voto, mas NAO em quem
ele votou (sigilo do voto). Por isso a analise de horario e de ritmo de
votacao por secao/regiao, nunca de preferencia por candidato por hora.
"""
import re
from pathlib import Path

import config
from carregar import conectar


def processar_logs(diretorio: Path, uf: str, ano: int, turno: int) -> int:
    """Le todos os arquivos .dat/.log de um diretorio e grava em voto_horario."""
    rx_voto = re.compile(config.LOG_VOTO_REGEX)
    rx_nome = re.compile(config.LOG_NOME_REGEX)
    linhas = []
    for arq in Path(diretorio).rglob("*"):
        if not arq.is_file():
            continue
        m = rx_nome.search(arq.name)
        if not m:
            continue
        mun, zona, secao = (int(x) for x in m.groups())
        with open(arq, encoding="latin-1", errors="replace") as f:
            for ln in f:
                v = rx_voto.search(ln)
                if v:
                    linhas.append((ano, turno, uf, mun, zona, secao, v.group(1)))
    con = conectar()
    con.execute("""
        CREATE TABLE IF NOT EXISTS voto_horario (
            ano INT, turno INT, uf VARCHAR, cd_municipio INT,
            zona INT, secao INT, ts_txt VARCHAR)
    """)
    con.executemany("INSERT INTO voto_horario VALUES (?,?,?,?,?,?,?)", linhas)
    con.execute("""
        CREATE OR REPLACE VIEW v_voto_horario AS
        SELECT h.*, strptime(ts_txt, '%d/%m/%Y %H:%M:%S') AS ts, r.regiao
        FROM voto_horario h LEFT JOIN regiao r USING (uf)
    """)
    con.close()
    return len(linhas)
