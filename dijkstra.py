"""Cálculo da tabela de roteamento a partir da LSDB (Dijkstra próprio com heapq).

Não depende de rede nem de threads: pode ser testado desde o primeiro dia com
uma LSDB montada à mão.

    1. Grafo: para cada LSP de origem O, aresta DIRIGIDA O -> vizinho, com o custo.
    2. Distância 0 para `eu`, infinito para os demais.
    3. Retirar da fila o nó de menor distância não finalizado; finalizá-lo.
    4. Relaxar arestas; primeiro salto = o próprio vizinho se o nó retirado é
       `eu`, senão herda o primeiro salto do nó retirado.
    5. Uma linha por roteador alcançável: rede 10.G.R -> (primeiro salto, distância).

Empates: qualquer caminho de custo mínimo é aceito. Na fila, o empate de
distância é desfeito pelo endereço (ordem de string), o que deixa o resultado
determinístico.
"""

from __future__ import annotations

import heapq
from typing import Callable, Optional

# Formato combinado de entrada: origem -> {vizinho: custo}
LSDBSimples = dict[str, dict[str, int]]

INFINITO = float("inf")


def montar_grafo(lsdb: LSDBSimples) -> dict[str, dict[str, int]]:
    """Lista de adjacência dirigida: cada LSP de origem O gera arestas O -> V.

    Nós que só aparecem como vizinho (sem LSP próprio na LSDB) entram no grafo
    sem arestas de saída: são alcançáveis, mas ninguém passa por eles.
    """
    grafo: dict[str, dict[str, int]] = {}
    for origem, vizinhos in lsdb.items():
        grafo.setdefault(origem, {})
        for vizinho, custo in vizinhos.items():
            grafo[origem][vizinho] = custo
            grafo.setdefault(vizinho, {})
    return grafo


def calcular_tabela(
    lsdb: LSDBSimples,
    eu: str,
    passo_a_passo: Optional[Callable[[dict], None]] = None,
) -> dict[str, tuple[str, int]]:
    """Retorna rede ("10.G.R") -> (próximo salto, custo), sem a própria rede.
    Se `passo_a_passo` for dado, é chamado a cada iteração com o nó finalizado,
    distâncias e predecessores (comando `dijkstra`, questão 1 do relatório)."""
    grafo = montar_grafo(lsdb)
    grafo.setdefault(eu, {})

    # Passo 2: distância 0 para mim, infinito para os demais.
    distancia: dict[str, float] = {no: INFINITO for no in grafo}
    distancia[eu] = 0
    predecessor: dict[str, Optional[str]] = {no: None for no in grafo}
    primeiro_salto: dict[str, Optional[str]] = {no: None for no in grafo}
    finalizados: set[str] = set()

    fila: list[tuple[float, str]] = [(0, eu)]
    iteracao = 0

    while fila:
        # Passo 3: nó de menor distância ainda não finalizado.
        dist_u, u = heapq.heappop(fila)
        if u in finalizados:
            continue  # entrada antiga na fila (já achamos caminho melhor)
        finalizados.add(u)
        iteracao += 1

        # Passo 4: relaxar as arestas que saem de u.
        for v, custo in grafo[u].items():
            if v in finalizados:
                continue
            nova = dist_u + custo
            if nova < distancia[v]:
                distancia[v] = nova
                predecessor[v] = u
                primeiro_salto[v] = v if u == eu else primeiro_salto[u]
                heapq.heappush(fila, (nova, v))

        if passo_a_passo is not None:
            passo_a_passo({
                "iteracao": iteracao,
                "finalizado": u,
                "finalizados": sorted(finalizados),
                "distancias": dict(distancia),
                "predecessores": dict(predecessor),
            })

    # Passo 5: uma linha por roteador alcançável, fora a minha rede.
    minha_rede = rede_de(eu)
    tabela: dict[str, tuple[str, int]] = {}
    for no in finalizados:
        rede = rede_de(no)
        if rede == minha_rede:
            continue
        tabela[rede] = (primeiro_salto[no], int(distancia[no]))
    return tabela


def rede_de(endereco: str) -> str:
    """Três primeiros octetos: '10.1.3.1' -> '10.1.3'."""
    return ".".join(endereco.split(".")[:3])
