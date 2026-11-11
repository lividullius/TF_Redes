"""Fase 5 — testes de dijkstra.py com LSDB montada à mão (topologia de teste).

Tabela esperada em R1 (grupo 1):
    10.1.2 -> 10.1.2.1, custo 1
    10.1.3 -> 10.1.2.1, custo 3
    10.1.4 -> 10.1.2.1, custo 6
    10.1.5 -> 10.1.2.1, custo 7
Com R3 fora: rota para 10.1.5 custa 9 (R1, R2, R4, R5).
"""

import unittest

ENLACES = [
    (1, 2, 1), (1, 3, 4), (2, 3, 2), (2, 4, 7),
    (3, 4, 3), (3, 5, 6), (4, 5, 1),
]


def lsdb_topologia_teste(sem=()):
    """Monta origem -> {vizinho: custo} a partir de ENLACES (G = 1)."""
    lsdb = {}
    for a, b, c in ENLACES:
        if a in sem or b in sem:
            continue
        ea, eb = f"10.1.{a}.1", f"10.1.{b}.1"
        lsdb.setdefault(ea, {})[eb] = c
        lsdb.setdefault(eb, {})[ea] = c
    return lsdb


class TestDijkstra(unittest.TestCase):
    @unittest.skip("fase 5 ainda não implementada")
    def test_tabela_r1(self):
        pass

    @unittest.skip("fase 5 ainda não implementada")
    def test_r3_derrubado(self):
        pass


if __name__ == "__main__":
    unittest.main()
