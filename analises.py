"""Consultas de analise sobre o banco DuckDB."""
import pandas as pd

from carregar import conectar


def _q(sql: str, params: list | None = None) -> pd.DataFrame:
    con = conectar()
    try:
        return con.execute(sql, params or []).df()
    finally:
        con.close()


def percentual_candidatos(cargo: str, turno: int, uf: str | None = None) -> pd.DataFrame:
    """% de cada candidato/opcao sobre votos totais e sobre votos validos."""
    filtro_uf = "AND uf = ?" if uf else ""
    params = [cargo, turno] + ([uf] if uf else [])
    return _q(f"""
        WITH t AS (
            SELECT nr_votavel, nm_votavel, tipo_voto, sum(qt_votos) AS votos
            FROM v_votos
            WHERE cargo = ? AND turno = ? {filtro_uf}
            GROUP BY ALL
        )
        SELECT nr_votavel, nm_votavel, tipo_voto, votos,
               round(100.0 * votos / sum(votos) OVER (), 2) AS pct_total,
               CASE WHEN tipo_voto = 'valido'
                    THEN round(100.0 * votos /
                         sum(votos) FILTER (WHERE tipo_voto='valido') OVER (), 2) END
                    AS pct_validos
        FROM t ORDER BY votos DESC
    """, params)


def tempo_cabine(turno: int) -> pd.DataFrame:
    """Tempo entre o mesario habilitar o eleitor e o voto ser computado, por regiao."""
    return _q("""
        SELECT regiao, count(*) AS votos,
               round(avg(seg_cabine), 1) AS media_seg,
               round(median(seg_cabine), 1) AS mediana_seg
        FROM v_voto_horario
        WHERE turno = ? AND seg_cabine IS NOT NULL
        GROUP BY regiao ORDER BY regiao
    """, [turno])


def por_regiao(cargo: str, turno: int) -> pd.DataFrame:
    """% de votos validos de cada candidato dentro de cada regiao."""
    return _q("""
        WITH t AS (
            SELECT regiao, nm_votavel, sum(qt_votos) AS votos
            FROM v_votos
            WHERE cargo = ? AND turno = ? AND tipo_voto = 'valido'
            GROUP BY ALL
        )
        SELECT regiao, nm_votavel, votos,
               round(100.0 * votos / sum(votos) OVER (PARTITION BY regiao), 2) AS pct
        FROM t ORDER BY regiao, votos DESC
    """, [cargo, turno])


def por_uf(cargo: str, turno: int) -> pd.DataFrame:
    return _q("""
        WITH t AS (
            SELECT uf, regiao, nm_votavel, sum(qt_votos) AS votos
            FROM v_votos
            WHERE cargo = ? AND turno = ? AND tipo_voto = 'valido'
            GROUP BY ALL
        )
        SELECT uf, regiao, nm_votavel, votos,
               round(100.0 * votos / sum(votos) OVER (PARTITION BY uf), 2) AS pct
        FROM t ORDER BY uf, votos DESC
    """, [cargo, turno])


def comparecimento(turno: int, cargo: str) -> pd.DataFrame:
    """Comparecimento e abstencao por regiao."""
    return _q("""
        SELECT r.regiao,
               sum(d.qt_aptos) AS aptos,
               sum(d.qt_comparecimento) AS comparecimento,
               sum(d.qt_abstencoes) AS abstencoes,
               round(100.0 * sum(d.qt_abstencoes) / nullif(sum(d.qt_aptos),0), 2)
                   AS pct_abstencao
        FROM detalhe d LEFT JOIN regiao r USING (uf)
        WHERE d.turno = ? AND d.cargo = ?
        GROUP BY r.regiao ORDER BY r.regiao
    """, [turno, cargo])


def votos_por_hora(turno: int, regiao: str | None = None) -> pd.DataFrame:
    """Quantidade de votos concluidos por hora (a partir dos logs)."""
    filtro = "AND regiao = ?" if regiao else ""
    params = [turno] + ([regiao] if regiao else [])
    return _q(f"""
        SELECT regiao, date_trunc('hour', ts) AS hora, count(*) AS votos
        FROM v_voto_horario
        WHERE turno = ? {filtro}
        GROUP BY ALL ORDER BY regiao, hora
    """, params)


def secoes_atipicas(cargo: str, turno: int, limite_pct: float = 95.0,
                    min_aptos: int = 50) -> pd.DataFrame:
    """Secoes em que um unico candidato passa de limite_pct dos validos.
    Serve para triagem estatistica, NAO e prova de irregularidade: secoes
    pequenas, ou de populacoes homogeneas, produzem esses valores naturalmente."""
    return _q("""
        WITH s AS (
            SELECT uf, cd_municipio, municipio, zona, secao, nm_votavel,
                   sum(qt_votos) AS votos
            FROM v_votos
            WHERE cargo = ? AND turno = ? AND tipo_voto = 'valido'
            GROUP BY ALL
        ), p AS (
            SELECT *, 100.0 * votos / sum(votos) OVER
                   (PARTITION BY uf, cd_municipio, zona, secao) AS pct,
                   sum(votos) OVER (PARTITION BY uf, cd_municipio, zona, secao) AS validos
            FROM s
        )
        SELECT * FROM p WHERE pct >= ? AND validos >= ? ORDER BY pct DESC
    """, [cargo, turno, limite_pct, min_aptos])
