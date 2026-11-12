"""Estado compartilhado do roteador (combinado do primeiro dia).

Todas as estruturas ficam atrás de um único threading.RLock (Estado.lock).
Nenhuma thread deve esperar (sleep, Event.wait, input) segurando o lock.

Estruturas (seção "Estado compartilhado" do plano):

    vizinhos         (ip_real, porta) -> Vizinho
    virt_para_real   endereço virtual -> (ip_real, porta) do vizinho ATIVO
    lsdb             endereço virtual de origem -> EntradaLSDB
    tabela           rede "10.G.R" -> Rota
    pings_pendentes  id -> PingPendente
    seq_proprio      número de sequência do último LSP próprio
    prox_id          próximo id para ping
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Optional

ParReal = tuple[str, int]  # (ip_real, porta)


@dataclass
class Vizinho:
    custo: int
    endereco_virtual: Optional[str] = None  # vazio até o primeiro HELLO
    ultimo_hello: Optional[float] = None    # time.monotonic()
    ativo: bool = False


@dataclass
class EntradaLSDB:
    seq: int
    vizinhos: dict[str, int]                # vizinho virtual -> custo
    recebido_em: float                      # time.monotonic()
    texto_original: str                     # reenviado byte a byte na inundação


@dataclass
class Rota:
    proximo_salto: str                      # endereço virtual
    custo: int


@dataclass
class PingPendente:
    enviado_em: float                       # time.monotonic()
    destino: str
    evento: threading.Event = field(default_factory=threading.Event)
    resposta: Optional[object] = None       # pacote ICMP recebido (pacotes.ICMP)
    recebido_em: Optional[float] = None     # time.monotonic() da resposta


@dataclass
class Contadores:
    """Usados pelo comando `stats` (questão 2 do relatório)."""
    lsp_gerados: int = 0
    lsp_aceitos: int = 0
    lsp_reenviados: int = 0
    lsp_copias_descartadas: int = 0


@dataclass
class Estado:
    meu_endereco: str                       # 10.G.R.1
    porta: int
    lock: threading.RLock = field(default_factory=threading.RLock)

    vizinhos: dict[ParReal, Vizinho] = field(default_factory=dict)
    virt_para_real: dict[str, ParReal] = field(default_factory=dict)
    lsdb: dict[str, EntradaLSDB] = field(default_factory=dict)
    tabela: dict[str, Rota] = field(default_factory=dict)
    pings_pendentes: dict[int, PingPendente] = field(default_factory=dict)

    seq_proprio: int = 0                    # último seq usado; o próximo LSP usa +1
    prox_id: int = 1
    contadores: Contadores = field(default_factory=Contadores)

    # Próximos disparos da thread temporizadora (time.monotonic()).
    proximo_hello: float = 0.0
    proxima_renovacao: float = 0.0

    # Opções de experimento (relatório, questões 4 e 5); desligadas por padrão.
    descartar_lsp: int = 0                  # --descartar-lsp N: descarta o N-ésimo LSP novo
    lsps_novos_recebidos: int = 0           # contagem usada por --descartar-lsp

    # Socket UDP único (envia e recebe); preenchido por roteador.py.
    sock: Optional[object] = None
