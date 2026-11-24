# TF_Redes

Trabalho final de Fundamentos de Redes de Computadores (grupo 1): um roteador de
estado de enlace que roda sobre UDP. Cada roteador descobre os vizinhos com HELLO,
espalha a topologia com LSPs, calcula as rotas com Dijkstra e encaminha mensagens
(DADOS) e pings (ICMP).

Feito em Python 3.9 ou mais novo, só com a biblioteca padrão (não precisa instalar nada).

## Como executar

### Pré-requisitos

- Python 3.9 ou mais novo (`python3 --version`; no Windows, `python --version` ou `py --version`).
- Nada para instalar: só a biblioteca padrão.
- O repositório clonado:

```sh
git clone https://github.com/lividullius/TF_Redes.git
cd TF_Redes
```

### Uso

```sh
python3 roteador.py <arquivo.conf> [--seq-inicial N] [--descartar-lsp N]
```

Cada roteador roda em um terminal próprio. Para encerrar, digite `sair` (ou Ctrl+D).
No Windows, troque `python3` por `python` ou `py`.

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

Usa os arquivos de [configs/dois_pcs/](configs/dois_pcs/).

**1. Conectar os dois PCs na mesma rede.** Os dois precisam estar **no mesmo Wi-Fi**
(access point, roteador de casa ou celular como ponto de acesso). Evite a rede da
universidade: ela costuma bloquear tráfego entre aparelhos.

**2. Descobrir o IP real de cada PC.**

| Sistema | Comando |
|---|---|
| macOS | `ipconfig getifaddr en0` |
| Windows | `ipconfig` (linha "Endereço IPv4" do adaptador Wi-Fi) |
| Linux | `hostname -I` |

Anote os dois IPs (ex.: PC 1 = `192.168.0.11`, PC 2 = `192.168.0.12`).
O IP pode mudar cada vez que o PC conecta (DHCP), então confira de novo a cada teste.

**3. Editar a configuração.** Cada PC coloca no seu arquivo o **IP do outro PC**:

- PC 1 edita [configs/dois_pcs/pc1.conf](configs/dois_pcs/pc1.conf): na linha `vizinho`, o IP do **PC 2**.
- PC 2 edita [configs/dois_pcs/pc2.conf](configs/dois_pcs/pc2.conf): na linha `vizinho`, o IP do **PC 1**.

```
endereco 10.1.1.1             # endereço virtual deste roteador (10.G.R.1)
porta 6000                    # porta UDP local
vizinho 192.168.0.12 6000 1   # <IP real do outro PC> <porta dele> <custo>
```

O custo tem que ser o mesmo nos dois arquivos.

**4. Liberar a porta UDP 6000 no firewall.**

- **macOS:** na primeira execução pode aparecer "Deseja que python3 aceite conexões de
  entrada?". Clique em **Permitir**. Se o firewall estiver ativo e não perguntar, veja em
  Ajustes do Sistema → Rede → Firewall → Opções.
- **Windows** (PowerShell como administrador):

  ```
  netsh advfirewall firewall add rule name="TF Redes UDP 6000" dir=in action=allow protocol=UDP localport=6000
  ```

  Ou aceite o aviso do Windows Defender na primeira execução, marcando **redes privadas e públicas**.
- **Linux:** `sudo ufw allow 6000/udp` (se o ufw estiver ativo).

**5. Rodar.**

```sh
# PC 1
python3 roteador.py configs/dois_pcs/pc1.conf

# PC 2
python3 roteador.py configs/dois_pcs/pc2.conf
```

Em até 5 s cada lado deve mostrar `VIZINHO ATIVO`.

**6. Conferir que funcionou.** No terminal do PC 1, digite:

```
vizinhos              # deve listar 10.1.2.1 com o IP do PC 2
lsdb                  # LSPs de 10.1.1.1 e 10.1.2.1
tabela                # rota para 10.1.2.0/24
ping 10.1.2.1         # resposta de eco de 10.1.2.1 com o RTT
msg 10.1.2.1 oi       # aparece "MENSAGEM RECEBIDA" no PC 2
```

Para testar a detecção de queda, digite `sair` no PC 2. Uns 15 a 20 s depois o PC 1 mostra
`VIZINHO INATIVO`, e a rota some da `tabela`.

### Na apresentação (4 PCs)

Use [configs/apresentacao4/](configs/apresentacao4/) (R1 a R4, um por PC). Os passos são os
mesmos de [dois PCs](#em-dois-pcs-na-mesma-rede): mesma rede, troque `127.0.0.1` pelo IP real
de cada PC vizinho, troque as portas (`porta` e as dos `vizinho`) por 6000 e libere a porta
UDP 6000 no firewall.

| Enlace | Custo |
|---|---|
| R1 – R2 | 1 |
| R2 – R3 | 2 |
| R3 – R4 | 3 |
| R4 – R1 | 7 |

Sem mudar nada, os 4 arquivos também rodam em uma máquina só (portas 6001 a 6004).

### Problemas comuns

| Sintoma | Causa provável |
|---|---|
| Log mostra `ORIGEM DESCONHECIDA 192.168.x.y:6000` | O IP na linha `vizinho` está errado. Use exatamente o IP:porta que aparece nesse log. |
| Nenhum `VIZINHO ATIVO` e nenhum log de origem desconhecida | Os pacotes não estão chegando: firewall bloqueando, PCs em redes diferentes, ou a rede isola os aparelhos (troque para o hotspot do celular). |
| Só um lado fica ativo | O firewall de um dos PCs está bloqueando a entrada. |
| `Não foi possível usar a porta UDP 6000` | Outro roteador já está rodando nesse PC. Feche-o ou mude a `porta` (e avise quem tem você como vizinho). |
| `Erro na configuração: ...` | A mensagem diz a linha com problema (IP inválido, custo não positivo etc.). |

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

| Diretiva | Obrigatória | Regras |
|---|---|---|
| `endereco 10.G.R.1` | sim, uma vez | Primeiro octeto 10 e último 1 |
| `porta <n>` | não (padrão 6000) | Entre 1 e 65535, no máximo uma vez |
| `vizinho <ip> <porta> <custo>` | não, uma linha por vizinho | Sem repetir o mesmo IP e porta |

- O custo é um inteiro positivo, e os dois lados de um enlace devem usar o mesmo custo.
- O IP do vizinho precisa ser numérico (não use `localhost`).
- Diretiva desconhecida ou com argumentos a mais ou a menos é erro.
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
