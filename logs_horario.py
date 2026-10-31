"""Le logs de urna no formato entregue pelo TSE e extrai o horario de cada voto.

Formato (conferido em um log real de 2026): o portal entrega um .zip; dentro vem
um .jez (que tambem e um zip) e dentro dele o `logd.dat`: texto latin-1, uma
linha por evento, campos separados por TAB:

    data hora <TAB> nivel <TAB> id da urna <TAB> modulo <TAB> mensagem <TAB> hash

Um mesmo log cobre o ciclo inteiro da urna (preparacao, 1o e 2o turno), entao o
turno e descoberto pelas mensagens do proprio log, e uma urna gera votos de
dois turnos no mesmo arquivo.

SIGILO: o log registra QUANDO cada eleitor votou, nunca EM QUEM. A analise de
horario e de ritmo de votacao por secao/regiao, nao de preferencia por hora.
O log tambem traz identificadores de mesarios e eleitores; este modulo nao
le nem grava nenhum deles: so horarios, turno e a identificacao da secao.
"""
import io
import re
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Iterator

import pandas as pd

import config
from carregar import conectar, criar_regiao

FMT_TS = "%d/%m/%Y %H:%M:%S"
MAX_BYTES = 300 * 1024 * 1024   # limite por arquivo descompactado (arquivos nao confiaveis)
MAX_PROFUNDIDADE = 3            # .zip -> .jez -> logd.dat

RX_NOME = re.compile(config.LOG_NOME_REGEX, re.I)
RX_TURNO = re.compile(config.LOG_TURNO_REGEX)
RX_NUM = re.compile(r"^(Município|Zona Eleitoral|Seção Eleitoral):\s*(\d+)")


def _logs_em(dados: bytes, nome: str, prof: int = 0) -> Iterator[bytes]:
    """Desce zips aninhados (em memoria, sem gravar em disco) ate achar logd.dat."""
    if zipfile.is_zipfile(io.BytesIO(dados)):
        if prof >= MAX_PROFUNDIDADE:
            return
        with zipfile.ZipFile(io.BytesIO(dados)) as z:
            for info in z.infolist():
                if info.is_dir() or info.file_size > MAX_BYTES:
                    continue
                yield from _logs_em(z.read(info), info.filename, prof + 1)
    elif Path(nome).name.lower() == "logd.dat":
        yield dados


def ler_log(dados: bytes) -> dict:
    """Extrai de um logd.dat: votos [(turno, ts, ts_habilitado)] e a secao informada no log."""
    turno = None
    ts_hab = None
    ident: dict[str, int] = {}
    votos = []
    ruins = 0
    for ln in dados.decode("latin-1").splitlines():
        c = ln.split("\t")
        if len(c) < 5:
            continue
        msg = c[4]
        try:
            if msg == config.MSG_VOTO:
                votos.append((turno, datetime.strptime(c[0], FMT_TS), ts_hab))
                ts_hab = None
            elif msg == config.MSG_HABILITADO:
                ts_hab = datetime.strptime(c[0], FMT_TS)
            elif msg.startswith(("Iniciando aplicação", "Turno da UE")):
                m = RX_TURNO.search(msg)
                if m:
                    turno = int(m.group(1))
            elif msg.startswith(("Município:", "Zona Eleitoral:", "Seção Eleitoral:")):
                m = RX_NUM.match(msg)
                if m:
                    ident.setdefault(m.group(1), int(m.group(2)))
        except ValueError:
            ruins += 1
    return {"votos": votos, "ident": ident, "linhas_ruins": ruins}


def _identificar(origem: str, ident_log: dict) -> tuple[dict, list[str]]:
    """Secao a partir do nome do arquivo (preferencial) ou do conteudo do log."""
    avisos = []
    do_log = {"cd_municipio": ident_log.get("Município"),
              "zona": ident_log.get("Zona Eleitoral"),
              "secao": ident_log.get("Seção Eleitoral")}
    m = RX_NOME.search(origem)
    if not m:
        avisos.append("nome sem identificacao da secao; usei o conteudo do log (UF desconhecida)")
        return {"uf": None, **do_log}, avisos
    do_nome = {"uf": m.group(2).upper(), "cd_municipio": int(m.group(3)),
               "zona": int(m.group(4)), "secao": int(m.group(5))}
    for k in ("cd_municipio", "zona", "secao"):
        if do_log[k] is not None and do_log[k] != do_nome[k]:
            avisos.append(f"{k}: nome={do_nome[k]} mas log={do_log[k]}")
    return do_nome, avisos


def _gravar(con, linhas: list, chaves: list) -> None:
    """Grava um lote; reprocessar a mesma secao substitui os votos antigos."""
    k = pd.DataFrame(chaves, columns=["uf", "cd_municipio", "zona", "secao"])
    con.register("chaves_df", k)
    con.execute("""DELETE FROM voto_horario USING chaves_df k
                   WHERE voto_horario.uf = k.uf AND voto_horario.cd_municipio = k.cd_municipio
                     AND voto_horario.zona = k.zona AND voto_horario.secao = k.secao""")
    con.unregister("chaves_df")
    if linhas:
        df = pd.DataFrame(linhas, columns=["ano", "turno", "uf", "cd_municipio", "zona",
                                           "secao", "ts", "ts_habilitado"])
        con.register("lote_df", df)
        con.execute("INSERT INTO voto_horario SELECT * FROM lote_df")
        con.unregister("lote_df")


def processar_logs(caminho: Path, lote: int = 200) -> dict:
    """Processa um arquivo (.zip/.jez/logd.dat) ou uma pasta inteira deles."""
    caminho = Path(caminho)
    if caminho.is_file():
        arquivos = [caminho]
    else:
        arquivos = sorted(p for p in caminho.rglob("*")
                          if p.is_file() and p.suffix.lower() in (".zip", ".jez", ".dat"))
    con = conectar()
    criar_regiao(con)
    con.execute("""
        CREATE TABLE IF NOT EXISTS voto_horario (
            ano INT, turno INT, uf VARCHAR, cd_municipio INT, zona INT, secao INT,
            ts TIMESTAMP, ts_habilitado TIMESTAMP)
    """)
    con.execute("""
        CREATE OR REPLACE VIEW v_voto_horario AS
        SELECT h.*, date_diff('second', h.ts_habilitado, h.ts) AS seg_cabine, r.regiao
        FROM voto_horario h LEFT JOIN regiao r USING (uf)
    """)

    resumo = {"arquivos": 0, "logs": 0, "votos": {}, "avisos": []}
    linhas, chaves = [], []
    for arq in arquivos:
        resumo["arquivos"] += 1
        try:
            logs = list(_logs_em(arq.read_bytes(), arq.name))
        except (zipfile.BadZipFile, OSError) as e:
            resumo["avisos"].append(f"{arq.name}: ilegivel ({e})")
            continue
        if not logs:
            resumo["avisos"].append(f"{arq.name}: nenhum logd.dat dentro")
            continue
        for dados in logs:
            r = ler_log(dados)
            ident, avisos = _identificar(str(arq), r["ident"])
            avisos += [f"{r['linhas_ruins']} linhas com data invalida"] if r["linhas_ruins"] else []
            if any(v is None for k, v in ident.items() if k != "uf"):
                resumo["avisos"].append(f"{arq.name}: secao nao identificada, ignorado")
                continue
            if any(t is None for t, _, _ in r["votos"]):
                avisos.append("votos sem turno identificado (turno NULL)")
            resumo["avisos"] += [f"{arq.name}: {a}" for a in avisos]
            resumo["logs"] += 1
            for turno, ts, th in r["votos"]:
                linhas.append((ts.year, turno, ident["uf"], ident["cd_municipio"],
                               ident["zona"], ident["secao"], ts, th))
                resumo["votos"][turno] = resumo["votos"].get(turno, 0) + 1
            chaves.append((ident["uf"], ident["cd_municipio"], ident["zona"], ident["secao"]))
            if len(chaves) >= lote:
                _gravar(con, linhas, chaves)
                linhas, chaves = [], []
    if chaves:
        _gravar(con, linhas, chaves)
    con.close()
    return resumo
