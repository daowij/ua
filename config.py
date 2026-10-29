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

# Linha do log da urna que marca um voto concluído (uma por eleitor).
# VALIDE contra um log real: a mensagem exata pode variar entre versões.
LOG_VOTO_REGEX = r"^(\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}).*O voto do eleitor foi computado"

# Nome do arquivo de log: o00407-<município 5><zona 4><seção 4>
LOG_NOME_REGEX = r"-(\d{5})(\d{4})(\d{4})"
