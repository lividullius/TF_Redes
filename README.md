# TF_Redes

Trabalho final de Fundamentos de Redes de Computadores (grupo 1): um roteador de
estado de enlace que roda sobre UDP. Cada roteador descobre os vizinhos com HELLO,
espalha a topologia com LSPs, calcula as rotas com Dijkstra e encaminha mensagens
(DADOS) e pings (ICMP).

Feito em Python 3.9 ou mais novo, só com a biblioteca padrão (não precisa instalar nada).

## Como executar

```sh
python3 roteador.py <arquivo.conf> [--seq-inicial N] [--descartar-lsp N]
```

Cada roteador roda em um terminal próprio. Para encerrar, digite `sair` (ou Ctrl+D).

### Em uma máquina só (5 roteadores)

Os arquivos de [configs/teste5/](configs/teste5/) usam `127.0.0.1` nas portas 6001 a 6005.
Abra 5 terminais e rode um roteador em cada:

```sh
python3 roteador.py configs/teste5/r1.conf
python3 roteador.py configs/teste5/r2.conf
...
python3 roteador.py configs/teste5/r5.conf
```

No macOS, `sh scripts/iniciar_teste5.sh` abre os 5 terminais de uma vez.

### Em dois PCs na mesma rede

Veja o passo a passo em [COMO_RODAR.md](COMO_RODAR.md) (configs em [configs/dois_pcs/](configs/dois_pcs/)).

### Na apresentação (4 PCs)

Use [configs/apresentacao4/](configs/apresentacao4/). Antes, troque `127.0.0.1` pelo IP real
de cada PC e as portas por 6000, e libere a porta UDP 6000 no firewall.

## Comandos

| Comando | O que faz |
|---|---|
| `tabela` | Tabela de roteamento: rede, próximo salto e custo |
| `lsdb` | LSPs conhecidos: origem, sequência, idade e vizinhos |
| `vizinhos` | Vizinhos ativos: endereço virtual, IP real, porta e custo |
| `msg <destino> <texto>` | Envia uma mensagem (sem `:` e sem acentos) |
| `ping <destino> [TTL]` | Envia um ping; mostra quem respondeu e o tempo (RTT) |
| `dijkstra` | Mostra cada iteração do Dijkstra e a tabela final |
| `stats` | Contadores de LSPs gerados, aceitos, reenviados e descartados |
| `ajuda` / `sair` | Lista os comandos / encerra o roteador |

Exemplos, rodando em R1:

```
ping 10.1.5.1        # ping até R5
ping 10.1.5.1 2      # com TTL 2: responde o 2º roteador do caminho
msg 10.1.5.1 ola R5  # mensagem para R5
```

## Arquivo de configuração

Uma diretiva por linha; `#` começa um comentário.

```
# Roteador 1 do grupo 1
endereco 10.1.1.1          # endereço virtual, sempre no formato 10.G.R.1
porta 6001                 # porta UDP (padrão 6000 se faltar)
vizinho 127.0.0.1 6002 1   # vizinho <ip real> <porta> <custo>
vizinho 127.0.0.1 6003 4
```

- O custo é um inteiro positivo, e os dois lados de um enlace devem usar o mesmo custo.
- O IP do vizinho precisa ser numérico (não use `localhost`).
- Se houver erro no arquivo, o roteador mostra a linha com problema e não inicia.

## Formato dos pacotes

Texto ASCII, campos separados por `:`.

```
HELLO:<endereço>
LSP:<origem>:<sequência>:<vizinho>=<custo>;<vizinho>=<custo>
DADOS:<origem>:<destino>:<ttl>:<id>:<mensagem>
ICMP:<origem>:<destino>:<ttl>:<id>:<tipo>
```

Tipos de ICMP: 0 = resposta de eco, 3 = destino inalcançável, 8 = pedido de eco,
11 = tempo excedido.

## Temporizadores

| Evento | Intervalo |
|---|---|
| Envio de HELLO a todos os vizinhos configurados | 5 s |
| Vizinho considerado inativo sem HELLO | 20 s |
| Renovação do LSP próprio | 30 s |
| Remoção de LSP de outro roteador não renovado | 90 s |

## Logs

Cada roteador grava em `logs/roteador-<endereço>.log` e mostra no terminal os eventos
com horário em milissegundos: vizinho ativo/inativo, LSP novo, tabela recalculada,
pacote encaminhado, ICMP gerado, pacotes descartados. Os HELLOs só aparecem no arquivo.

## Opções para o relatório

Ficam desligadas por padrão.

- `--seq-inicial N`: começa os números de sequência em N (questão 4; ex.: `--seq-inicial 0`).
- `--descartar-lsp N`: descarta de propósito o N-ésimo LSP novo recebido (questão 5).

## Testes

```sh
python3 -m unittest discover tests
```

Testam a leitura da configuração, o formato dos pacotes e o Dijkstra na topologia de teste.
Para enviar pacotes malformados ou ICMP arbitrários a um roteador, use
[scripts/enviar_pacote.py](scripts/enviar_pacote.py) (instruções no início do arquivo).

### Topologia de teste (configs/teste5)

| Enlace | Custo |
|---|---|
| R1 – R2 | 1 |
| R1 – R3 | 4 |
| R2 – R3 | 2 |
| R2 – R4 | 7 |
| R3 – R4 | 3 |
| R3 – R5 | 6 |
| R4 – R5 | 1 |

Tabela esperada em R1: todas as rotas saem por R2, com custos 1 (R2), 3 (R3), 6 (R4) e 7 (R5).

## Estrutura

```
roteador.py        início do programa: lê a configuração, abre o socket e inicia as threads
estado.py          dados compartilhados entre as threads (vizinhos, LSDB, tabela, pings)
config.py          leitura e validação do arquivo de configuração
pacotes.py         leitura e montagem dos pacotes HELLO, LSP, DADOS e ICMP
vizinhos.py        HELLO e detecção de vizinho ativo/inativo
lsdb.py            LSPs: geração, inundação, renovação e envelhecimento
dijkstra.py        cálculo da tabela de roteamento
encaminhamento.py  entrega, encaminhamento com TTL e mensagens ICMP
cli.py             comandos digitados pelo usuário
log.py             log no terminal e em arquivo

configs/           arquivos de configuração (teste5, dois_pcs, apresentacao4)
tests/             testes unitários
scripts/           scripts de apoio aos testes
relatorio/         relatório e capturas do Wireshark
logs/              logs gerados ao rodar (não vão para o git)
```
