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


def iniciar(endereco: str, diretorio: str = "logs") -> None:
    """Abre o arquivo roteador-<endereço>.log."""
    raise NotImplementedError


def evento(texto: str, terminal: bool = True) -> None:
    """Grava uma linha com horário em ms; thread-safe."""
    raise NotImplementedError


def encerrar() -> None:
    raise NotImplementedError
