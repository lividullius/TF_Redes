"""Fase 2 — testes de pacotes.py.

Executar: python3 -m unittest discover tests
"""

import unittest

from pacotes import (ICMP, LSP, Dados, Hello, PacoteMalformado, analisar,
                     endereco_valido, mensagem_valida, montar, montar_lsp)


class TestAnalisar(unittest.TestCase):
    def test_hello(self):
        self.assertEqual(analisar(b"HELLO:10.1.2.1"), Hello("10.1.2.1"))

    def test_lsp(self):
        p = analisar(b"LSP:10.1.3.1:1794348102:10.1.1.1=4;10.1.2.1=2")
        self.assertIsInstance(p, LSP)
        self.assertEqual(p.origem, "10.1.3.1")
        self.assertEqual(p.seq, 1794348102)
        self.assertEqual(p.vizinhos, {"10.1.1.1": 4, "10.1.2.1": 2})
        self.assertEqual(p.texto_original, "LSP:10.1.3.1:1794348102:10.1.1.1=4;10.1.2.1=2")

    def test_lsp_lista_vazia(self):
        p = analisar(b"LSP:10.1.3.1:7:")
        self.assertEqual(p.vizinhos, {})

    def test_lsp_ponto_e_virgula_sobrando(self):
        p = analisar(b"LSP:10.1.3.1:7:10.1.1.1=4;")
        self.assertEqual(p.vizinhos, {"10.1.1.1": 4})

    def test_dados(self):
        p = analisar(b"DADOS:10.1.1.1:10.1.5.1:16:0:ola mundo")
        self.assertEqual(p, Dados("10.1.1.1", "10.1.5.1", 16, 0, "ola mundo"))

    def test_icmp(self):
        p = analisar(b"ICMP:10.1.1.1:10.1.5.1:3:42:8")
        self.assertEqual(p, ICMP("10.1.1.1", "10.1.5.1", 3, 42, 8))

    def test_destino_qualquer_da_rede(self):
        p = analisar(b"ICMP:10.1.1.1:10.1.5.77:16:1:8")
        self.assertEqual(p.destino, "10.1.5.77")

    def test_quebra_de_linha_no_final(self):
        self.assertEqual(analisar(b"HELLO:10.1.2.1\n"), Hello("10.1.2.1"))
        self.assertEqual(analisar(b"HELLO:10.1.2.1\r\n"), Hello("10.1.2.1"))

    def test_malformados(self):
        casos = [
            b"",
            b"OLA:10.1.1.1",                         # tipo desconhecido
            b"hello:10.1.1.1",                       # tipo em minúsculas
            b"HELLO",                                # campos a menos
            b"HELLO:10.1.1.1:extra",                 # campos a mais
            b"HELLO:10.1.1",                         # endereço com 3 octetos
            b"HELLO:10.1.1.256",                     # octeto > 255
            b"HELLO:10.1.1.x",
            b"HELLO:10.1.2.\xc3\xa9",                # fora do ASCII
            b"\xff\xfe",
            b"LSP:10.1.3.1:abc:",                    # sequência não inteira
            b"LSP:10.1.3.1:7:10.1.1.1=0",            # custo não positivo
            b"LSP:10.1.3.1:7:10.1.1.1=-1",
            b"LSP:10.1.3.1:7:10.1.1.1",              # item sem custo
            b"LSP:10.1.3.1:7",                       # campos a menos
            b"DADOS:10.1.1.1:10.1.5.1:abc:0:oi",     # TTL abc
            b"DADOS:10.1.1.1:10.1.5.1:16:x:oi",      # id inválido
            b"DADOS:10.1.1.1:10.1.5.1:16:0:a:b",     # ':' na mensagem
            b"DADOS:10.1.1.1:10.1.5.1:16:0",         # campos a menos
            b"ICMP:10.1.1.1:10.1.5.1:16:1:5",        # tipo fora de {0,3,8,11}
            b"ICMP:10.1.1.1:10.1.5.1:16:1",
            b"ICMP:10.1.1.1:999.1.5.1:16:1:8",
        ]
        for dados in casos:
            with self.subTest(dados=dados):
                with self.assertRaises(PacoteMalformado):
                    analisar(dados)


class TestMontar(unittest.TestCase):
    def test_ida_e_volta(self):
        pacotes = [
            Hello("10.1.2.1"),
            Dados("10.1.1.1", "10.1.5.1", 16, 0, "ola"),
            ICMP("10.1.1.1", "10.1.5.1", 16, 7, 8),
        ]
        for p in pacotes:
            with self.subTest(p=p):
                self.assertEqual(analisar(montar(p)), p)

    def test_lsp_formato_exato(self):
        self.assertEqual(montar_lsp("10.1.1.1", 5, {"10.1.3.1": 4, "10.1.2.1": 1}),
                         b"LSP:10.1.1.1:5:10.1.2.1=1;10.1.3.1=4")
        self.assertEqual(montar_lsp("10.1.1.1", 5, {}), b"LSP:10.1.1.1:5:")

    def test_sem_quebra_de_linha(self):
        self.assertFalse(montar(Hello("10.1.2.1")).endswith(b"\n"))


class TestValidacoes(unittest.TestCase):
    def test_endereco_valido(self):
        self.assertTrue(endereco_valido("10.1.5.77"))
        self.assertTrue(endereco_valido("0.0.0.0"))
        self.assertFalse(endereco_valido("10.1.5"))
        self.assertFalse(endereco_valido("10.1.5.-1"))
        self.assertFalse(endereco_valido("10.1.5.1 "))

    def test_mensagem_valida(self):
        self.assertTrue(mensagem_valida("ola mundo"))
        self.assertFalse(mensagem_valida("a:b"))
        self.assertFalse(mensagem_valida("olá"))


if __name__ == "__main__":
    unittest.main()
