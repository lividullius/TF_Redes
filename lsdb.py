"""LSDB, geração do LSP próprio, inundação, sincronização e envelhecimento.

Geração:
    primeira sequência = int(time.time()) (ou --seq-inicial); depois +1.
    LSP lista apenas vizinhos ativos. Gravado na própria LSDB, enviado a todos
    os vizinhos ativos, tabela recalculada.
    Gatilhos: vizinho ativo, vizinho inativo, renovação a cada 30 s.

Recebimento do vizinho V, nesta ordem:
    1. origem == eu                         -> descartar
    2. LSDB tem seq >= da mesma origem      -> descartar, log como cópia
    3. caso contrário                       -> substituir, anotar horário,
                                               reenviar TEXTO ORIGINAL a todos os
                                               ativos exceto V, recalcular tabela

Envelhecimento: a cada 1 s, remover LSPs de OUTROS recebidos há mais de 90 s.
O LSP próprio nunca envelhece; cópia descartada não renova o horário.
"""

from __future__ import annotations

from estado import Estado, ParReal

INTERVALO_RENOVACAO = 30.0
IDADE_MAXIMA = 90.0


def gerar_lsp_proprio(estado: Estado, motivo: str) -> None:
    raise NotImplementedError


def receber_lsp(estado: Estado, lsp, origem_real: ParReal) -> None:
    """Aplica as três regras de recebimento (e --descartar-lsp, se ligado)."""
    raise NotImplementedError


def inundar(estado: Estado, texto_original: str, exceto: ParReal | None) -> None:
    raise NotImplementedError


def sincronizar_vizinho(estado: Estado, par: ParReal) -> None:
    """Envia ao vizinho recém-ativo uma cópia de todos os LSPs da LSDB."""
    raise NotImplementedError


def renovar_se_preciso(estado: Estado, agora: float) -> None:
    raise NotImplementedError


def envelhecer(estado: Estado, agora: float) -> None:
    raise NotImplementedError


def recalcular_tabela(estado: Estado, motivo: str) -> None:
    """Chama dijkstra.calcular_tabela e grava em estado.tabela, com log."""
    raise NotImplementedError
