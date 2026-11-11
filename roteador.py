"""Ponto de entrada do roteador de estado de enlace sobre UDP.

Uso:
    python3 roteador.py <arquivo.conf> [--seq-inicial N] [--descartar-lsp N]

Responsabilidades (fase 1 — esqueleto):
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

from estado import Estado


def analisar_argumentos(argv: list[str]):
    """Lê o caminho da configuração e as opções de experimento
    --seq-inicial e --descartar-lsp (desligadas por padrão)."""
    raise NotImplementedError


def criar_socket(porta: int):
    """Cria o socket UDP único, ligado a ("0.0.0.0", porta)."""
    raise NotImplementedError


def thread_receptora(estado: Estado) -> None:
    """Laço de recvfrom. Para cada datagrama:
    1. descarta se (ip, porta) não estiver em estado.vizinhos;
    2. decodifica ASCII estrito e analisa com pacotes.analisar;
    3. despacha por tipo (vizinhos / lsdb / encaminhamento).
    Captura OSError (ConnectionResetError no Windows) e qualquer exceção
    do tratamento de um pacote, registrando no log, sem encerrar a thread."""
    raise NotImplementedError


def despachar(estado: Estado, pacote, origem_real) -> None:
    """Encaminha o pacote já analisado para o módulo responsável pelo tipo."""
    raise NotImplementedError


def thread_temporizadora(estado: Estado) -> None:
    """Acorda a cada 1 s (time.monotonic) e chama:
    vizinhos.enviar_hellos, vizinhos.verificar_inatividade,
    lsdb.renovar_se_preciso, lsdb.envelhecer."""
    raise NotImplementedError


def main(argv: list[str]) -> int:
    raise NotImplementedError


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]))
