"""Ponto de entrada do roteador de estado de enlace sobre UDP.

Uso:
    python3 roteador.py <arquivo.conf> [--seq-inicial N] [--descartar-lsp N]

Responsabilidades:
    - ler a configuração (config.py);
    - criar UM socket UDP com bind(("0.0.0.0", porta)), usado para enviar e receber;
    - iniciar o log (log.py);
    - iniciar as threads receptora e temporizadora;
    - entregar a thread principal ao laço de comandos (cli.py).

Threads:
    receptora     laço de recvfrom; decodifica, valida origem e despacha por tipo
    temporizadora acorda a cada 1 s: HELLO (5 s), inatividade (20 s),
                  renovação do LSP (30 s), envelhecimento (90 s)
    principal     lê comandos com input()
"""

from __future__ import annotations

import argparse
import socket
import sys
import threading
import time

import cli
import config
import encaminhamento
import log
import lsdb
import pacotes
import vizinhos
from estado import Estado, ParReal

TAMANHO_MAX_DATAGRAMA = 65535


def analisar_argumentos(argv: list[str]) -> argparse.Namespace:
    """Lê o caminho da configuração e as opções de experimento
    --seq-inicial e --descartar-lsp (desligadas por padrão)."""
    p = argparse.ArgumentParser(description="Roteador de estado de enlace sobre UDP")
    p.add_argument("config", help="arquivo de configuração")
    p.add_argument("--seq-inicial", type=int, default=None,
                   help="primeiro número de sequência (padrão: int(time.time()))")
    p.add_argument("--descartar-lsp", type=int, default=0, metavar="N",
                   help="descarta de propósito o N-ésimo LSP novo recebido")
    return p.parse_args(argv)


def criar_socket(porta: int) -> socket.socket:
    """Cria o socket UDP único, ligado a ("0.0.0.0", porta)."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Windows: sem isto, recvfrom lança ConnectionResetError quando um
    # vizinho está desligado (ICMP port unreachable do envio anterior).
    if hasattr(socket, "SIO_UDP_CONNRESET"):
        sock.ioctl(socket.SIO_UDP_CONNRESET, False)
    sock.bind(("0.0.0.0", porta))
    return sock


def thread_receptora(estado: Estado) -> None:
    """Laço de recvfrom. Nenhuma exceção encerra a thread em silêncio."""
    while True:
        try:
            dados, origem = estado.sock.recvfrom(TAMANHO_MAX_DATAGRAMA)
        except ConnectionResetError:
            continue  # Windows, vizinho desligado
        except OSError as e:
            if estado.sock.fileno() == -1:
                return  # socket fechado no encerramento
            log.evento(f"ERRO DE RECEPCAO: {e}")
            continue
        try:
            tratar_datagrama(estado, dados, (origem[0], origem[1]))
        except Exception as e:
            log.evento(f"ERRO AO TRATAR PACOTE de {origem[0]}:{origem[1]}: "
                       f"{type(e).__name__}: {e}")


def tratar_datagrama(estado: Estado, dados: bytes, origem_real: ParReal) -> None:
    """Filtros: origem conhecida, ASCII estrito, número de campos (pacotes.analisar)."""
    par_txt = f"{origem_real[0]}:{origem_real[1]}"
    if origem_real not in estado.vizinhos:
        log.evento(f"ORIGEM DESCONHECIDA {par_txt}: pacote descartado")
        return
    try:
        pacote = pacotes.analisar(dados)
    except pacotes.PacoteMalformado as e:
        log.evento(f"MALFORMADO de {par_txt}: {e}")
        return
    despachar(estado, pacote, origem_real)


def despachar(estado: Estado, pacote: pacotes.Pacote, origem_real: ParReal) -> None:
    """Encaminha o pacote já analisado para o módulo responsável pelo tipo."""
    if isinstance(pacote, pacotes.Hello):
        vizinhos.receber_hello(estado, pacote, origem_real)
    elif isinstance(pacote, pacotes.LSP):
        lsdb.receber_lsp(estado, pacote, origem_real)
    elif isinstance(pacote, pacotes.Dados):
        encaminhamento.receber_dados(estado, pacote)
    elif isinstance(pacote, pacotes.ICMP):
        encaminhamento.receber_icmp(estado, pacote)


def thread_temporizadora(estado: Estado) -> None:
    """Acorda a cada 1 s e verifica os quatro temporizadores."""
    while True:
        agora = time.monotonic()
        try:
            vizinhos.enviar_hellos(estado, agora)
            vizinhos.verificar_inatividade(estado, agora)
            lsdb.renovar_se_preciso(estado, agora)
            lsdb.envelhecer(estado, agora)
        except Exception as e:
            log.evento(f"ERRO NA TEMPORIZADORA: {type(e).__name__}: {e}")
        time.sleep(1.0)


def main(argv: list[str]) -> int:
    args = analisar_argumentos(argv)
    try:
        cfg = config.carregar(args.config)
    except config.ErroConfiguracao as e:
        print(f"Erro na configuração: {e}", file=sys.stderr)
        return 1

    try:
        sock = criar_socket(cfg.porta)
    except OSError as e:
        print(f"Não foi possível usar a porta UDP {cfg.porta}: {e}", file=sys.stderr)
        return 1

    log.iniciar(cfg.endereco)
    estado = Estado(meu_endereco=cfg.endereco, porta=cfg.porta, sock=sock,
                    descartar_lsp=args.descartar_lsp)
    vizinhos.inicializar(estado, cfg.vizinhos)

    seq_inicial = args.seq_inicial if args.seq_inicial is not None else int(time.time())
    estado.seq_proprio = seq_inicial - 1  # o primeiro LSP gerado usa seq_inicial

    log.evento(f"ROTEADOR INICIADO {cfg.endereco} porta={cfg.porta} "
               f"vizinhos configurados={len(cfg.vizinhos)}")
    lsdb.gerar_lsp_proprio(estado, "início")

    threading.Thread(target=thread_receptora, args=(estado,),
                     name="receptora", daemon=True).start()
    threading.Thread(target=thread_temporizadora, args=(estado,),
                     name="temporizadora", daemon=True).start()

    try:
        cli.laco(estado)
    finally:
        log.evento("ROTEADOR ENCERRADO")
        sock.close()
        log.encerrar()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
