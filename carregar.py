"""Carrega CSVs do TSE (votacao_secao e detalhe_votacao_secao) no DuckDB."""
import duckdb

import config


def conectar() -> duckdb.DuckDBPyConnection:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(config.DB_PATH))


def criar_regiao(con: duckdb.DuckDBPyConnection) -> None:
    """Tabela UF -> regiao (usada pelas views de votos e de horarios)."""
    con.execute("DROP TABLE IF EXISTS regiao")
    con.execute("CREATE TABLE regiao (uf VARCHAR, regiao VARCHAR)")
    con.executemany("INSERT INTO regiao VALUES (?, ?)", list(config.UF_REGIAO.items()))


def carregar_csvs(ano: int) -> None:
    con = conectar()
    base = config.RAW_DIR / str(ano)
    pad_v = str(base / "votacao" / "votacao_secao_*.csv")
    pad_d = str(base / "detalhe" / "detalhe_votacao_secao_*.csv")

    # Arquivos do TSE: ';' como separador, latin1, aspas duplas.
    opts = "delim=';', header=true, encoding='latin-1', quote='\"', all_varchar=true, ignore_errors=true"

    con.execute("DROP TABLE IF EXISTS votos")
    con.execute(f"""
        CREATE TABLE votos AS
        SELECT
            CAST(ANO_ELEICAO AS INT)  AS ano,
            CAST(NR_TURNO AS INT)     AS turno,
            SG_UF                     AS uf,
            CAST(CD_MUNICIPIO AS INT) AS cd_municipio,
            NM_MUNICIPIO              AS municipio,
            CAST(NR_ZONA AS INT)      AS zona,
            CAST(NR_SECAO AS INT)     AS secao,
            CAST(CD_CARGO AS INT)     AS cd_cargo,
            DS_CARGO                  AS cargo,
            CAST(NR_VOTAVEL AS INT)   AS nr_votavel,
            NM_VOTAVEL                AS nm_votavel,
            CAST(QT_VOTOS AS INT)     AS qt_votos,
            NR_LOCAL_VOTACAO          AS local_votacao
        FROM read_csv('{pad_v}', {opts})
    """)

    con.execute("DROP TABLE IF EXISTS detalhe")
    con.execute(f"""
        CREATE TABLE detalhe AS
        SELECT
            CAST(ANO_ELEICAO AS INT)        AS ano,
            CAST(NR_TURNO AS INT)           AS turno,
            SG_UF                           AS uf,
            CAST(CD_MUNICIPIO AS INT)       AS cd_municipio,
            CAST(NR_ZONA AS INT)            AS zona,
            CAST(NR_SECAO AS INT)           AS secao,
            CAST(CD_CARGO AS INT)           AS cd_cargo,
            DS_CARGO                        AS cargo,
            CAST(QT_APTOS AS INT)           AS qt_aptos,
            CAST(QT_COMPARECIMENTO AS INT)  AS qt_comparecimento,
            CAST(QT_ABSTENCOES AS INT)      AS qt_abstencoes
        FROM read_csv('{pad_d}', {opts})
    """)

    criar_regiao(con)

    # View enriquecida
    con.execute("""
        CREATE OR REPLACE VIEW v_votos AS
        SELECT v.*, r.regiao,
               CASE WHEN v.nr_votavel IN (95, 96) THEN 'nao_valido'
                    ELSE 'valido' END AS tipo_voto
        FROM votos v LEFT JOIN regiao r USING (uf)
    """)
    n = con.execute("SELECT count(*) FROM votos").fetchone()[0]
    print(f"{n:,} linhas de votos carregadas")
    con.close()
