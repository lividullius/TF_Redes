"""Interface de comandos (thread principal).

    tabela                 rede, próximo salto e custo, ordenados por rede
    lsdb                   origem, sequência, vizinhos e custos, idade em s
    vizinhos               endereço virtual, IP real e porta de cada ativo
    msg <destino> <texto>  DADOS com TTL 16 e id 0; recusa ':' e não-ASCII
    ping <destino> [TTL]   ICMP 8; tipo da resposta, quem respondeu e RTT,
                           ou timeout após 2 s (Event.wait FORA do lock)
    dijkstra   (extra)     iterações do algoritmo passo a passo
    stats      (extra)     LSPs gerados, aceitos, reenviados, cópias descartadas

Comando inválido -> uma linha de uso, sem derrubar o programa.
"""

from __future__ import annotations

from estado import Estado

TIMEOUT_PING = 2.0


def laco(estado: Estado) -> None:
    """Lê comandos com input() até EOF/Ctrl+C."""
    raise NotImplementedError


def cmd_tabela(estado: Estado, args: list[str]) -> None:
    raise NotImplementedError


def cmd_lsdb(estado: Estado, args: list[str]) -> None:
    raise NotImplementedError


def cmd_vizinhos(estado: Estado, args: list[str]) -> None:
    raise NotImplementedError


def cmd_msg(estado: Estado, args: list[str]) -> None:
    raise NotImplementedError


def cmd_ping(estado: Estado, args: list[str]) -> None:
    raise NotImplementedError


def cmd_dijkstra(estado: Estado, args: list[str]) -> None:
    raise NotImplementedError


def cmd_stats(estado: Estado, args: list[str]) -> None:
    raise NotImplementedError


COMANDOS = {
    "tabela": cmd_tabela,
    "lsdb": cmd_lsdb,
    "vizinhos": cmd_vizinhos,
    "msg": cmd_msg,
    "ping": cmd_ping,
    "dijkstra": cmd_dijkstra,
    "stats": cmd_stats,
}
