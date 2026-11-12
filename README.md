# TF_Redes
Repositório para desenvolvimento do trabalho final de Fundamentos de Redes de Computadores:
roteador de estado de enlace sobre UDP, em Python 3 (apenas biblioteca padrão).

## Execução

```sh
python3 roteador.py configs/teste5/r1.conf [--seq-inicial N] [--descartar-lsp N]
sh scripts/iniciar_teste5.sh          # abre os 5 roteadores (macOS)
python3 -m unittest discover tests    # testes unitários
```

Comandos: `tabela`, `lsdb`, `vizinhos`, `msg <destino> <texto>`, `ping <destino> [TTL]`,
`dijkstra`, `stats`, `ajuda`, `sair`.

Opções de experimento (relatório): `--seq-inicial N` fixa o primeiro número de
sequência (questão 4); `--descartar-lsp N` descarta de propósito o N-ésimo LSP
novo recebido (questão 5).

Logs: `logs/roteador-<endereço>.log` (HELLOs só aparecem no arquivo).

## Estrutura

```
roteador.py        ponto de entrada: configuração, socket único, threads
estado.py          estruturas de estado compartilhado + RLock (combinado do 1º dia)
config.py          leitura e validação do arquivo de configuração
pacotes.py         análise e montagem de HELLO, LSP, DADOS, ICMP
vizinhos.py        vizinhos, HELLO (5 s), inatividade (20 s)
lsdb.py            LSDB, LSP próprio, inundação, renovação (30 s), envelhecimento (90 s)
dijkstra.py        tabela de roteamento a partir da LSDB (heapq)
encaminhamento.py  entrega local, TTL, encaminhamento, ICMP
cli.py             comandos tabela, lsdb, vizinhos, msg, ping, dijkstra, stats
log.py             log com horário em ms (terminal + roteador-<endereço>.log)

configs/teste5/        5 roteadores em 127.0.0.1:6001-6005 (topologia de teste)
configs/apresentacao4/ 4 roteadores da apresentação (trocar IPs reais)
tests/                 testes unitários (python3 -m unittest discover tests)
scripts/               envio de pacotes arbitrários e inicialização da topologia
relatorio/             relatório e capturas .pcapng
logs/                  arquivos de log gerados (ignorados pelo git)
```

## Arquivo de configuração

```
# comentário
endereco 10.G.R.1
porta 6000
vizinho <ip real> <porta> <custo>
```

Os dois lados de um enlace devem usar o mesmo custo.

## Fases

1. Esqueleto · 2. Pacotes · 3. Vizinhança · 4. LSPs e inundação · 5. Dijkstra e tabela ·
6. Encaminhamento de DADOS · 7. ICMP e ping · 8. Robustez, testes e relatório
