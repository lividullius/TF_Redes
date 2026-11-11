"""Cálculo da tabela de roteamento a partir da LSDB (Dijkstra próprio com heapq).

Não depende de rede nem de threads: pode ser testado desde o primeiro dia com
uma LSDB montada à mão.

    1. Grafo: para cada LSP de origem O, aresta DIRIGIDA O -> vizinho, com o custo.
    2. Distância 0 para `eu`, infinito para os demais.
    3. Retirar da fila o nó de menor distância não finalizado; finalizá-lo.
    4. Relaxar arestas; primeiro salto = o próprio vizinho se o nó retirado é
       `eu`, senão herda o primeiro salto do nó retirado.
    5. Uma linha por roteador alcançável: rede 10.G.R -> (primeiro salto, distância).

Empates: qualquer caminho de custo mínimo é aceito.
"""

from __future__ import annotations

from typing import Callable, Optional

# Formato combinado de entrada: origem -> {vizinho: custo}
LSDBSimples = dict[str, dict[str, int]]


def montar_grafo(lsdb: LSDBSimples) -> dict[str, dict[str, int]]:
    raise NotImplementedError


def calcular_tabela(
    lsdb: LSDBSimples,
    eu: str,
    passo_a_passo: Optional[Callable[[dict], None]] = None,
) -> dict[str, tuple[str, int]]:
    """Retorna rede ("10.G.R") -> (próximo salto, custo), sem a própria rede.
    Se `passo_a_passo` for dado, é chamado a cada iteração com o nó finalizado,
    distâncias e predecessores (comando `dijkstra`, questão 1 do relatório)."""
    raise NotImplementedError


def rede_de(endereco: str) -> str:
    """Três primeiros octetos: '10.1.3.1' -> '10.1.3'."""
    raise NotImplementedError
