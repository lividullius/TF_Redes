"""Testes de config.py.

Executar: python3 -m unittest discover tests
"""

import os
import unittest

from config import ErroConfiguracao, analisar_linhas, carregar

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def cfg(texto):
    return analisar_linhas(texto.strip().splitlines())


class TestConfig(unittest.TestCase):
    def test_valida(self):
        c = cfg("""
            # comentário
            endereco 10.1.1.1
            porta 6001
            vizinho 127.0.0.1 6002 1   # R2
            vizinho 127.0.0.1 6003 4
        """)
        self.assertEqual(c.endereco, "10.1.1.1")
        self.assertEqual(c.porta, 6001)
        self.assertEqual([(v.ip, v.porta, v.custo) for v in c.vizinhos],
                         [("127.0.0.1", 6002, 1), ("127.0.0.1", 6003, 4)])

    def test_porta_padrao(self):
        self.assertEqual(cfg("endereco 10.1.1.1").porta, 6000)

    def test_erros(self):
        casos = [
            "porta 6000",                                      # sem endereco
            "endereco 10.1.1.2",                               # não termina em .1
            "endereco 11.1.1.1",                               # não começa com 10
            "endereco 10.1.1.1\nporta 0",
            "endereco 10.1.1.1\nporta 70000",
            "endereco 10.1.1.1\nvizinho 127.0.0.1 6002 0",     # custo 0
            "endereco 10.1.1.1\nvizinho 127.0.0.1 6002 x",
            "endereco 10.1.1.1\nvizinho 127.0.0.1 6002",       # falta custo
            "endereco 10.1.1.1\nvizinho 1.2.3 6002 1",         # IP inválido
            "endereco 10.1.1.1\nvizinho 127.0.0.1 6002 1\nvizinho 127.0.0.1 6002 3",
            "endereco 10.1.1.1\nroteador x",                   # diretiva desconhecida
        ]
        for texto in casos:
            with self.subTest(texto=texto):
                with self.assertRaises(ErroConfiguracao):
                    cfg(texto)

    def test_arquivo_inexistente(self):
        with self.assertRaises(ErroConfiguracao):
            carregar("nao-existe.conf")

    def test_arquivos_de_exemplo(self):
        for pasta in ("teste5", "apresentacao4"):
            dir_ = os.path.join(RAIZ, "configs", pasta)
            for nome in sorted(os.listdir(dir_)):
                with self.subTest(arquivo=f"{pasta}/{nome}"):
                    carregar(os.path.join(dir_, nome))


if __name__ == "__main__":
    unittest.main()
