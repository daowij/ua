"""Uso:
  python cli.py baixar  --ano 2026 [--ufs SP RJ] [--url-votacao URL] [--url-detalhe URL]
  python cli.py carregar --ano 2026
  python cli.py logs LogDeUrna_o03221sc8113200730167_123.zip     # ou uma pasta com varios
  python cli.py cabine --turno 1                                 # tempo entre habilitar e votar
  python cli.py candidatos --cargo Presidente --turno 1 [--uf SP]
  python cli.py regioes --cargo Presidente --turno 1
  python cli.py horarios --turno 1 [--regiao Sudeste]
  python cli.py abstencao --cargo Presidente --turno 1
  python cli.py atipicas --cargo Presidente --turno 1 [--limite 95]
Adicione --csv arquivo.csv em qualquer consulta para exportar.
"""
import argparse
from pathlib import Path

import analises
import baixar as bx
import carregar
import logs_horario


def main() -> None:
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="cmd", required=True)

    a = sp.add_parser("baixar")
    a.add_argument("--ano", type=int, required=True)
    a.add_argument("--ufs", nargs="*")
    a.add_argument("--url-votacao")
    a.add_argument("--url-detalhe")
    a.add_argument("--forcar", action="store_true")

    a = sp.add_parser("carregar")
    a.add_argument("--ano", type=int, required=True)

    a = sp.add_parser("logs")
    a.add_argument("caminho", help="arquivo .zip/.jez/logd.dat ou pasta com varios")

    for nome in ("candidatos", "regioes", "ufs", "abstencao", "atipicas"):
        a = sp.add_parser(nome)
        a.add_argument("--cargo", required=True)
        a.add_argument("--turno", type=int, required=True)
        a.add_argument("--uf")
        a.add_argument("--limite", type=float, default=95.0)
        a.add_argument("--csv")

    a = sp.add_parser("horarios")
    a.add_argument("--turno", type=int, required=True)
    a.add_argument("--regiao")
    a.add_argument("--csv")

    a = sp.add_parser("cabine")
    a.add_argument("--turno", type=int, required=True)
    a.add_argument("--csv")

    args = p.parse_args()

    if args.cmd == "baixar":
        bx.baixar(args.ano, args.ufs, args.forcar, args.url_votacao, args.url_detalhe)
        return
    if args.cmd == "carregar":
        carregar.carregar_csvs(args.ano)
        return
    if args.cmd == "logs":
        r = logs_horario.processar_logs(Path(args.caminho))
        por_turno = ", ".join(f"turno {t}: {n:,}" for t, n in sorted(
            r["votos"].items(), key=lambda x: (x[0] is None, x[0])))
        print(f"{r['logs']} logs lidos de {r['arquivos']} arquivos; votos gravados -> {por_turno or 'nenhum'}")
        for av in r["avisos"][:20]:
            print("  aviso:", av)
        if len(r["avisos"]) > 20:
            print(f"  ... e mais {len(r['avisos']) - 20} avisos")
        return

    df = {
        "candidatos": lambda: analises.percentual_candidatos(args.cargo, args.turno, args.uf),
        "regioes": lambda: analises.por_regiao(args.cargo, args.turno),
        "ufs": lambda: analises.por_uf(args.cargo, args.turno),
        "abstencao": lambda: analises.comparecimento(args.turno, args.cargo),
        "atipicas": lambda: analises.secoes_atipicas(args.cargo, args.turno, args.limite),
        "horarios": lambda: analises.votos_por_hora(args.turno, args.regiao),
        "cabine": lambda: analises.tempo_cabine(args.turno),
    }[args.cmd]()
    print(df.to_string(index=False, max_rows=60))
    if args.csv:
        df.to_csv(args.csv, index=False)
        print(f"-> salvo em {args.csv}")


if __name__ == "__main__":
    main()
