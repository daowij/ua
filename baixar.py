"""Download dos arquivos de dados abertos do TSE (um zip por UF)."""
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

import config


def _baixar_um(url: str, destino: Path, forcar: bool) -> tuple[str, str]:
    if destino.exists() and not forcar:
        return url, "ja existia"
    destino.parent.mkdir(parents=True, exist_ok=True)
    tmp = destino.with_suffix(".part")
    try:
        with requests.get(url, stream=True, timeout=120) as r:
            if r.status_code == 404:
                return url, "404 (arquivo nao existe nesse padrao de URL)"
            r.raise_for_status()
            with open(tmp, "wb") as f:
                for chunk in r.iter_content(1 << 20):
                    f.write(chunk)
        tmp.rename(destino)
        with zipfile.ZipFile(destino) as z:
            z.extractall(destino.parent)
        return url, "ok"
    except Exception as e:  # noqa: BLE001
        tmp.unlink(missing_ok=True)
        return url, f"erro: {e}"


def baixar(ano: int, ufs: list[str] | None = None, forcar: bool = False,
           url_votacao: str | None = None, url_detalhe: str | None = None,
           workers: int = 4) -> None:
    ufs = ufs or list(config.UF_REGIAO)
    tv = url_votacao or config.URL_VOTACAO
    td = url_detalhe or config.URL_DETALHE
    tarefas = []
    for uf in ufs:
        tarefas.append((tv.format(ano=ano, uf=uf),
                        config.RAW_DIR / str(ano) / "votacao" / f"{uf}.zip"))
        tarefas.append((td.format(ano=ano, uf=uf),
                        config.RAW_DIR / str(ano) / "detalhe" / f"{uf}.zip"))
    with ThreadPoolExecutor(workers) as ex:
        futs = [ex.submit(_baixar_um, u, d, forcar) for u, d in tarefas]
        for f in as_completed(futs):
            url, status = f.result()
            print(f"[{status}] {url}")
