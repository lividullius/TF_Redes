"""Fase 5 — testes de dijkstra.py com LSDB montada à mão (topologia de teste).

Tabela esperada em R1 (grupo 1):
    10.1.2 -> 10.1.2.1, custo 1
    10.1.3 -> 10.1.2.1, custo 3
    10.1.4 -> 10.1.2.1, custo 6
    10.1.5 -> 10.1.2.1, custo 7
Com R3 fora: rota para 10.1.5 custa 9 (R1, R2, R4, R5).

Executar: python3 -m unittest discover tests
"""

import unittest

from dijkstra import calcular_tabela, montar_grafo, rede_de

ENLACES = [
    (1, 2, 1), (1, 3, 4), (2, 3, 2), (2, 4, 7),
    (3, 4, 3), (3, 5, 6), (4, 5, 1),
]


def r(n):
    return f"10.1.{n}.1"


def lsdb_topologia_teste(sem=()):
    """Monta origem -> {vizinho: custo} a partir de ENLACES (G = 1)."""
    lsdb = {}
    for a, b, c in ENLACES:
        if a in sem or b in sem:
            continue
        ea, eb = r(a), r(b)
        lsdb.setdefault(ea, {})[eb] = c
        lsdb.setdefault(eb, {})[ea] = c
    return lsdb


class TestDijkstra(unittest.TestCase):
    def test_tabela_r1(self):
        tabela = calcular_tabela(lsdb_topologia_teste(), r(1))
        self.assertEqual(tabela, {
            "10.1.2": (r(2), 1),
            "10.1.3": (r(2), 3),
            "10.1.4": (r(2), 6),
            "10.1.5": (r(2), 7),
        })

    def test_tabela_r5(self):
        tabela = calcular_tabela(lsdb_topologia_teste(), r(5))
        self.assertEqual(tabela, {
            "10.1.4": (r(4), 1),
            "10.1.3": (r(4), 4),
            "10.1.2": (r(4), 6),
            "10.1.1": (r(4), 7),
        })

    def test_r3_derrubado(self):
        tabela = calcular_tabela(lsdb_topologia_teste(sem={3}), r(1))
        self.assertNotIn("10.1.3", tabela)
        self.assertEqual(tabela["10.1.5"], (r(2), 9))
        self.assertEqual(tabela["10.1.4"], (r(2), 8))

    def test_lsp_antigo_do_roteador_caido_nao_cria_rota(self):
        # R3 caiu: os vizinhos já o retiraram dos seus LSPs, mas o LSP de R3
        # continua na LSDB (até 90 s). Arestas dirigidas => R3 inalcançável.
        lsdb = lsdb_topologia_teste(sem={3})
        lsdb[r(3)] = {r(1): 4, r(2): 2, r(4): 3, r(5): 6}
        tabela = calcular_tabela(lsdb, r(1))
        self.assertNotIn("10.1.3", tabela)
        self.assertEqual(tabela["10.1.5"], (r(2), 9))

    def test_lsdb_so_com_meu_lsp_sem_vizinhos(self):
        self.assertEqual(calcular_tabela({r(1): {}}, r(1)), {})
        self.assertEqual(calcular_tabela({}, r(1)), {})

    def test_vizinho_sem_lsp_e_alcancavel(self):
        # R2 ainda não enviou LSP, mas aparece no meu.
        tabela = calcular_tabela({r(1): {r(2): 5}}, r(1))
        self.assertEqual(tabela, {"10.1.2": (r(2), 5)})

    def test_nao_inclui_a_propria_rede(self):
        tabela = calcular_tabela(lsdb_topologia_teste(), r(3))
        self.assertNotIn("10.1.3", tabela)

    def test_passo_a_passo_uma_iteracao_por_no(self):
        iteracoes = []
        calcular_tabela(lsdb_topologia_teste(), r(1), iteracoes.append)
        ordem = [it["finalizado"] for it in iteracoes]
        self.assertEqual(ordem, [r(1), r(2), r(3), r(4), r(5)])
        ultima = iteracoes[-1]
        self.assertEqual(ultima["distancias"][r(5)], 7)
        self.assertEqual(ultima["predecessores"][r(5)], r(4))

    def test_montar_grafo_dirigido(self):
        grafo = montar_grafo({r(1): {r(2): 3}})
        self.assertEqual(grafo, {r(1): {r(2): 3}, r(2): {}})

    def test_rede_de(self):
        self.assertEqual(rede_de("10.1.3.1"), "10.1.3")
        self.assertEqual(rede_de("10.1.5.77"), "10.1.5")


if __name__ == "__main__":
    unittest.main()
