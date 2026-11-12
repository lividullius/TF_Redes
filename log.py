"""Log com horário em milissegundos, no terminal e em roteador-<endereço>.log.

Formato combinado (uma linha por evento):
    HH:MM:SS.mmm EVENTO detalhes

Exemplos:
    19:02:11.482 VIZINHO ATIVO 10.1.2.1 (192.168.0.12:6000)
    19:02:11.483 LSP GERADO seq=1794348131 vizinhos=10.1.2.1=1
    19:02:11.490 LSP NOVO origem=10.1.3.1 seq=1794348102 via=10.1.2.1
    19:02:11.491 TABELA RECALCULADA 4 rotas
    19:02:15.027 ENCAMINHADO DADOS 10.1.1.1->10.1.5.1 prox=10.1.3.1 ttl=14
    19:02:19.310 ICMP GERADO tipo=11 para=10.1.1.1 id=42

Eventos exigidos: vizinho ativo/inativo, LSP novo, recálculo da tabela,
pacote encaminhado, ICMP gerado.
Adicionais: LSP cópia, LSP envelhecido, malformado, origem desconhecida.
HELLO enviado/recebido: apenas no arquivo (terminal=False).
"""

from __future__ import annotations

import os
import threading
import time
from typing import Optional, TextIO

_lock = threading.Lock()
_arquivo: Optional[TextIO] = None


def iniciar(endereco: str, diretorio: str = "logs") -> None:
    """Abre o arquivo roteador-<endereço>.log (acrescenta ao final)."""
    global _arquivo
    os.makedirs(diretorio, exist_ok=True)
    caminho = os.path.join(diretorio, f"roteador-{endereco}.log")
    _arquivo = open(caminho, "a", encoding="utf-8", buffering=1)


def horario() -> str:
    """Horário local com milissegundos: HH:MM:SS.mmm."""
    agora = time.time()
    ms = int((agora % 1) * 1000)
    return time.strftime("%H:%M:%S", time.localtime(agora)) + f".{ms:03d}"


def evento(texto: str, terminal: bool = True) -> None:
    """Grava uma linha com horário em ms; thread-safe."""
    linha = f"{horario()} {texto}"
    with _lock:
        if _arquivo is not None:
            _arquivo.write(linha + "\n")
        if terminal:
            print(linha, flush=True)


def encerrar() -> None:
    global _arquivo
    with _lock:
        if _arquivo is not None:
            _arquivo.close()
            _arquivo = None
