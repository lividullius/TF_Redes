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
            # Aresta de mão única: "origem chega em vizinho com este custo".
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

    # Passo 2: no começo, só conhecemos a distância até nós mesmos (0).
    distancia: dict[str, float] = {no: INFINITO for no in grafo}
    distancia[eu] = 0
    predecessor: dict[str, Optional[str]] = {no: None for no in grafo}
    primeiro_salto: dict[str, Optional[str]] = {no: None for no in grafo}
    finalizados: set[str] = set()

    # Fila de prioridade: sempre devolve o nó com a menor distância.
    fila: list[tuple[float, str]] = [(0, eu)]
    iteracao = 0

    while fila:
        # Passo 3: pega o nó mais próximo que ainda não foi finalizado.
        dist_u, u = heapq.heappop(fila)
        # O mesmo nó pode estar na fila mais de uma vez; se já foi
        # finalizado, essa entrada é antiga e é ignorada.
        if u in finalizados:
            continue
        finalizados.add(u)
        iteracao += 1

        # Passo 4: para cada vizinho v de u, vê se passar por u é mais barato.
        for v, custo in grafo[u].items():
            if v in finalizados:
                continue
            nova = dist_u + custo
            if nova < distancia[v]:
                distancia[v] = nova
                predecessor[v] = u
                # Primeiro salto = para qual vizinho nosso mandar o pacote.
                # Se u somos nós, v é vizinho direto: o primeiro salto é o próprio v.
                # Senão, o caminho até v passa por u, então usa o mesmo de u.
                primeiro_salto[v] = v if u == eu else primeiro_salto[u]
                heapq.heappush(fila, (nova, v))

        # Usado pelo comando `dijkstra` para mostrar cada iteração.
        if passo_a_passo is not None:
            passo_a_passo({
                "iteracao": iteracao,
                "finalizado": u,
                "finalizados": sorted(finalizados),
                "distancias": dict(distancia),
                "predecessores": dict(predecessor),
            })

    # Passo 5: monta a tabela com uma linha por roteador alcançável.
    # A chave é a rede (ex.: 10.1.5), então qualquer endereço 10.1.5.x
    # usa a rota do roteador 10.1.5.1.
    minha_rede = rede_de(eu)
    tabela: dict[str, tuple[str, int]] = {}
    for no in finalizados:
        rede = rede_de(no)
        if rede == minha_rede:
            continue  # não precisamos de rota para nós mesmos
        tabela[rede] = (primeiro_salto[no], int(distancia[no]))
    return tabela


def rede_de(endereco: str) -> str:
    """Três primeiros octetos: '10.1.3.1' -> '10.1.3'."""
    return ".".join(endereco.split(".")[:3])
