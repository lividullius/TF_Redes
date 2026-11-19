# Como rodar em dois PCs (access point)

Guia rápido para ligar o roteador em 2 computadores na mesma rede Wi-Fi
(access point, roteador de casa ou celular como ponto de acesso).

## 1. Pré-requisitos (nos dois PCs)

- Python 3.9 ou mais novo (`python3 --version`; no Windows, `python --version` ou `py --version`).
- Nada para instalar: só a biblioteca padrão.
- O repositório clonado:

```sh
git clone https://github.com/lividullius/TF_Redes.git
cd TF_Redes
```

## 2. Conectar os dois PCs na mesma rede

Os dois precisam estar **no mesmo Wi-Fi**. Evite a rede da universidade (ela costuma
bloquear tráfego entre aparelhos); use o celular como ponto de acesso ou o access point.

## 3. Descobrir o IP real de cada PC

| Sistema | Comando |
|---|---|
| macOS | `ipconfig getifaddr en0` |
| Windows | `ipconfig` (linha "Endereço IPv4" do adaptador Wi-Fi) |
| Linux | `hostname -I` |

Anote os dois IPs (ex.: PC 1 = `192.168.0.11`, PC 2 = `192.168.0.12`).
O IP pode mudar cada vez que o PC conecta (DHCP), então confira de novo a cada teste.

## 4. Editar a configuração

Cada PC usa um arquivo e coloca nele o **IP do outro PC**:

- PC 1 edita [configs/dois_pcs/pc1.conf](configs/dois_pcs/pc1.conf): na linha `vizinho`, o IP do **PC 2**.
- PC 2 edita [configs/dois_pcs/pc2.conf](configs/dois_pcs/pc2.conf): na linha `vizinho`, o IP do **PC 1**.

```
endereco 10.1.1.1             # endereço virtual deste roteador (10.G.R.1)
porta 6000                    # porta UDP local
vizinho 192.168.0.12 6000 1   # <IP real do outro PC> <porta dele> <custo>
```

O custo tem que ser o mesmo nos dois arquivos.

## 5. Liberar a porta UDP 6000 no firewall

- **macOS:** na primeira execução pode aparecer "Deseja que python3 aceite conexões de
  entrada?" → **Permitir**. Se o firewall estiver ativo sem perguntar, veja em
  Ajustes do Sistema → Rede → Firewall → Opções.
- **Windows** (PowerShell como administrador):

  ```
  netsh advfirewall firewall add rule name="TF Redes UDP 6000" dir=in action=allow protocol=UDP localport=6000
  ```

  Ou aceite o aviso do Windows Defender na primeira execução, marcando **redes privadas e públicas**.
- **Linux:** `sudo ufw allow 6000/udp` (se o ufw estiver ativo).

## 6. Rodar

```sh
# PC 1
python3 roteador.py configs/dois_pcs/pc1.conf

# PC 2
python3 roteador.py configs/dois_pcs/pc2.conf
```

(No Windows, troque `python3` por `python` ou `py`.)

Em até 5 s cada lado deve mostrar `VIZINHO ATIVO`.

## 7. Conferir que funcionou

No terminal do PC 1, digite:

```
vizinhos              # deve listar 10.1.2.1 com o IP do PC 2
lsdb                  # LSPs de 10.1.1.1 e 10.1.2.1
tabela                # rota para 10.1.2.0/24
ping 10.1.2.1         # resposta de eco de 10.1.2.1 com o RTT
msg 10.1.2.1 oi       # aparece "MENSAGEM RECEBIDA" no PC 2
```

Para testar a detecção de queda: digite `sair` no PC 2. Uns 15 a 20 s depois o PC 1 mostra
`VIZINHO INATIVO`, e a rota some da `tabela`.

Outros comandos: `dijkstra`, `stats`, `ajuda`, `sair`.
Os logs ficam em `logs/roteador-<endereço>.log`.

## Problemas comuns

| Sintoma | Causa provável |
|---|---|
| Log mostra `ORIGEM DESCONHECIDA 192.168.x.y:6000` | O IP na linha `vizinho` está errado. Use exatamente o IP:porta que aparece nesse log. |
| Nenhum `VIZINHO ATIVO` e nenhum log de origem desconhecida | Os pacotes não estão chegando: firewall bloqueando, PCs em redes diferentes, ou a rede isola os aparelhos (troque para o hotspot do celular). |
| Só um lado fica ativo | O firewall de um dos PCs está bloqueando a entrada. |
| `Não foi possível usar a porta UDP 6000` | Outro roteador já está rodando nesse PC. Feche-o ou mude a `porta` (e avise o outro PC). |
| `Erro na configuração: ...` | A mensagem diz a linha com problema (IP inválido, custo não positivo etc.). |

Para testar sozinho em uma única máquina, use a topologia de 5 roteadores em
`configs/teste5/` (veja o [README](README.md)).
