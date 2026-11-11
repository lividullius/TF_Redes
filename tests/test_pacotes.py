"""Fase 2 — testes de pacotes.py.

Cobrir: exemplos do enunciado (HELLO, LSP, DADOS, ICMP) e uma lista de
pacotes malformados (tipo desconhecido, campos a menos/a mais, TTL 'abc',
bytes fora do ASCII, endereço inválido, custo não positivo, ':' na mensagem,
tipo ICMP fora de {0, 3, 8, 11}). Aceitar '\\n' no final.

Executar: python3 -m unittest discover tests
"""

import unittest


class TestAnalisar(unittest.TestCase):
    @unittest.skip("fase 2 ainda não implementada")
    def test_exemplos_do_enunciado(self):
        pass

    @unittest.skip("fase 2 ainda não implementada")
    def test_malformados(self):
        pass


class TestMontar(unittest.TestCase):
    @unittest.skip("fase 2 ainda não implementada")
    def test_ida_e_volta(self):
        """analisar(montar_x(...)) devolve os mesmos campos."""
        pass


if __name__ == "__main__":
    unittest.main()
