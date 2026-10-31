# Analisador de urnas (TSE)

Pipeline em Python + DuckDB: carrega os dados de votação do TSE num banco local e responde consultas por candidato, região, UF, comparecimento e horário dos votos.

Há duas fontes de dados, independentes:

| Fonte | O que dá | Comando |
|---|---|---|
| CSVs de dados abertos (votação por seção) | votos por candidato, % por região/UF, comparecimento | `baixar`, `carregar` |
| **Log de urna** (`.zip` → `.jez` → `logd.dat`) | **horário** de cada voto, por seção | `logs` |

## Instalação
```
pip install -r requirements.txt
```

## Resultados por candidato e região
```
python cli.py baixar   --ano 2026                 # baixa as UFs (+ exterior "ZZ")
python cli.py carregar --ano 2026                 # CSVs -> data/urnas.duckdb
python cli.py candidatos --cargo Presidente --turno 2
python cli.py regioes    --cargo Presidente --turno 2
python cli.py ufs        --cargo Presidente --turno 2 --csv ufs.csv
python cli.py abstencao  --cargo Presidente --turno 2
python cli.py atipicas   --cargo Presidente --turno 2 --limite 95
```
Os nomes de cargo são os que vêm no CSV (ex.: `Presidente`, `Governador`).

## Horário dos votos (log de urna)

### O formato do arquivo
O portal do TSE entrega o log de cada seção como `LogDeUrna_o03221sc8113200730167_<n>.zip`. Dentro vem um `.jez` (que é só outro zip, extensão do TSE) e, dentro dele, o `logd.dat`: texto latin-1, um evento por linha, campos separados por TAB (`data hora · nível · id da urna · módulo · mensagem · hash`).

O nome carrega a identificação da seção: `o03221` + `sc` (UF) + `81132` (município) + `0073` (zona) + `0167` (seção).

Um mesmo log cobre a vida inteira da urna: preparação, 1º turno **e** 2º turno. O programa descobre o turno pelas mensagens do próprio log.

### Uso
O programa abre o `.zip` do portal diretamente (não precisa descompactar nada) e aceita também `.jez`, `logd.dat` ou uma pasta com vários:
```
python cli.py logs LogDeUrna_o03221sc8113200730167_123.zip
python cli.py logs pasta_com_logs/
python cli.py horarios --turno 1 --regiao Sul     # votos por hora
python cli.py cabine   --turno 1                  # tempo entre habilitar o eleitor e o voto
```
Reprocessar a mesma seção substitui os votos antigos (não duplica).

### O que o log tem e o que não tem
- **Tem:** o horário em que cada eleitor concluiu o voto (`O voto do eleitor foi computado`) e em que foi habilitado pelo mesário.
- **Não tem:** em quem o eleitor votou (sigilo do voto). Dá para analisar ritmo de votação por hora/seção/região, nunca preferência por candidato por horário.
- O log também contém identificadores de mesários e eleitores. O programa não lê nem grava nenhum: só horário, turno e identificação da seção.
- Votos após as 17h não são, por si só, anomalia: quem já está na fila às 17h ainda vota. No log de exemplo (SC), o último voto do 1º turno foi às 17:07.
- Os horários são os do relógio da urna (horário local do estado).

### Conferência
Em teste com dados fictícios, a soma de votos nos logs bate com o comparecimento do CSV por região. Com dados reais, essa comparação por seção é um bom controle de qualidade.

## Pontos para conferir antes de rodar em escala
1. **Download dos logs em massa ainda não está implementado.** O TSE informa que **não há arquivo de índice** e que os arquivos não podem ser listados: cada URL precisa ser montada, a partir do arquivo auxiliar de seção (EA18) e do documento oficial "Instruções para download dos arquivos da divulgação 2026". Há limite de 100 requisições/s por IP, e vários 404 seguidos bloqueiam o IP por 10 minutos. Qualquer downloader precisa de limitador de taxa e de lista de seções válida para não gerar 404.
2. **URLs dos CSVs**: o padrão em `config.py` é o de 2022. Os dados de 2026 só entram nos dados abertos após o fim da totalização; se o endereço mudou, passe `--url-votacao` / `--url-detalhe` com `{ano}` e `{uf}`.
3. **Colunas dos CSVs**: `carregar.py` assume os nomes de coluna de 2022. Se o layout mudou, ajuste os SELECTs.
4. **Volume**: são ~470 mil seções. Cada log tem ~220 KB compactado (~1,2 MB descompactado), ou seja, da ordem de 100 GB só de logs compactados. Os CSVs por UF também são grandes (SP passa de 1 GB).
5. `atipicas` é triagem estatística, não prova de irregularidade: seções pequenas ou homogêneas naturalmente têm percentuais extremos.

`gerar_dados_teste.py` cria CSVs e logs fictícios (no formato real) para testar tudo sem baixar nada.
