# Analisador de urnas (TSE)

Pipeline em Python + DuckDB: baixa os dados abertos do TSE por UF, carrega num banco local e responde consultas por candidato, região, UF, comparecimento e horário.

## Instalação
```
pip install -r requirements.txt
```

## Fluxo
```
python cli.py baixar   --ano 2026                 # baixa todas as UFs (+ exterior "ZZ")
python cli.py carregar --ano 2026                 # CSVs -> data/urnas.duckdb
python cli.py candidatos --cargo Presidente --turno 2
python cli.py regioes    --cargo Presidente --turno 2
python cli.py ufs        --cargo Presidente --turno 2 --csv ufs.csv
python cli.py abstencao  --cargo Presidente --turno 2
python cli.py atipicas   --cargo Presidente --turno 2 --limite 95
```
Os nomes de cargo são os que vêm no CSV (ex.: `Presidente`, `Governador`).

## Horário dos votos
Vem dos **logs de urna**, não do boletim. O log diz *quando* cada eleitor concluiu o voto, mas não *em quem* votou (sigilo). Então dá para ver ritmo de votação por hora/região, mas não candidato por hora.
```
python cli.py logs --dir pasta_com_logs_de_SP --uf SP --ano 2026 --turno 1
python cli.py horarios --turno 1 --regiao Sudeste
```

## Pontos para conferir antes de rodar em escala
1. **URLs**: o padrão em `config.py` é o dos dados abertos de 2022. Os BUs de 2026 só entram no Portal de Dados Abertos após o fim da totalização; se o endereço mudou, passe `--url-votacao` / `--url-detalhe` com `{ano}` e `{uf}`.
2. **Log de urna**: `LOG_VOTO_REGEX` e `LOG_NOME_REGEX` em `config.py` foram escritos de memória do formato; valide contra 1 log real.
3. **Colunas**: `carregar.py` assume os nomes de coluna dos CSVs de 2022. Se o TSE alterou o layout, ajuste os SELECTs.
4. **Volume**: o país tem ~470 mil seções; os CSVs por UF são grandes (SP passa de 1 GB descompactado). DuckDB aguenta bem, mas reserve disco.
5. `atipicas` é triagem estatística, não prova de irregularidade: seções pequenas ou homogêneas naturalmente têm percentuais extremos.

`gerar_dados_teste.py` cria dados fictícios para testar tudo sem baixar nada.
