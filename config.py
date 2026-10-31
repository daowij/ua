"""Configuração central do projeto."""
from pathlib import Path

DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
DB_PATH = DATA_DIR / "urnas.duckdb"

# Padrão de URL dos arquivos de dados abertos do TSE (por UF).
# CONFIRA no portal https://dadosabertos.tse.jus.br se o padrão de 2026 é o mesmo
# de 2022; se mudar, use --url-template no comando `baixar`.
URL_VOTACAO = (
    "https://cdn.tse.jus.br/estatistica/sead/odsele/"
    "votacao_secao/votacao_secao_{ano}_{uf}.zip"
)
URL_DETALHE = (
    "https://cdn.tse.jus.br/estatistica/sead/odsele/"
    "detalhe_votacao_secao/detalhe_votacao_secao_{ano}_{uf}.zip"
)

# UF -> região. "ZZ" = votos no exterior.
UF_REGIAO = {
    "AC": "Norte", "AP": "Norte", "AM": "Norte", "PA": "Norte",
    "RO": "Norte", "RR": "Norte", "TO": "Norte",
    "AL": "Nordeste", "BA": "Nordeste", "CE": "Nordeste", "MA": "Nordeste",
    "PB": "Nordeste", "PE": "Nordeste", "PI": "Nordeste", "RN": "Nordeste",
    "SE": "Nordeste",
    "DF": "Centro-Oeste", "GO": "Centro-Oeste", "MT": "Centro-Oeste",
    "MS": "Centro-Oeste",
    "ES": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",
    "PR": "Sul", "RS": "Sul", "SC": "Sul",
    "ZZ": "Exterior",
}

# --- Log de urna (formato conferido em um log real de 2026) -------------------
# O portal entrega LogDeUrna_o03221sc8113200730167_<n>.zip -> .jez (outro zip)
# -> logd.dat (texto latin-1, campos separados por TAB:
#    data hora, nivel, id da urna, modulo, mensagem, hash).

# Mensagens exatas do log
MSG_VOTO = "O voto do eleitor foi computado"   # uma por eleitor que concluiu o voto
MSG_HABILITADO = "Eleitor foi habilitado"      # mesario liberou a urna para o eleitor

# Identificacao no nome do arquivo: o<eleicao 5><uf 2><municipio 5><zona 4><secao 4>
# ex.: o03221sc8113200730167 -> SC, municipio 81132, zona 0073, secao 0167
LOG_NOME_REGEX = r"o(\d{5})([a-z]{2})(\d{5})(\d{4})(\d{4})"

# Turno em vigor (um mesmo log cobre 1o e 2o turno). Exemplos reais:
#   "Iniciando aplicação - ELEIÇÃO OFICIAL SEGUNDO TURNO - 2º turno"
#   "Turno da UE: 1º turno"
LOG_TURNO_REGEX = r"(?:ELEIÇÃO OFICIAL.*?- |Turno da UE:\s*)(\d)º turno"
