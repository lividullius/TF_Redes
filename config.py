"""Leitura e validação do arquivo de configuração.

Formato (uma diretiva por linha; '#' inicia comentário, inclusive no fim da linha):

    endereco 10.G.R.1
    porta 6000
    vizinho <ip real> <porta> <custo>

Validações (erro => mensagem clara e encerramento):
    - endereco no formato 10.G.R.1;
    - porta entre 1 e 65535 (padrão 6000 se a linha faltar);
    - custo inteiro positivo;
    - nenhum par (ip, porta) repetido.
"""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass, field

PORTA_PADRAO = 6000


class ErroConfiguracao(Exception):
    """Erro de validação, com mensagem pronta para o usuário."""


@dataclass
class VizinhoConfig:
    ip: str
    porta: int
    custo: int


@dataclass
class Configuracao:
    endereco: str
    porta: int = PORTA_PADRAO
    vizinhos: list[VizinhoConfig] = field(default_factory=list)


def carregar(caminho: str) -> Configuracao:
    """Lê e valida o arquivo. Lança ErroConfiguracao em caso de problema."""
    try:
        with open(caminho, encoding="utf-8") as f:
            linhas = f.readlines()
    except OSError as e:
        raise ErroConfiguracao(f"não foi possível abrir {caminho}: {e.strerror}")
    return analisar_linhas(linhas, caminho)


def analisar_linhas(linhas: list[str], nome: str = "configuração") -> Configuracao:
    endereco = None
    porta = None
    vizinhos: list[VizinhoConfig] = []
    vistos: set[tuple[str, int]] = set()

    for numero, linha in enumerate(linhas, start=1):
        linha = linha.split("#", 1)[0].strip()
        if not linha:
            continue
        partes = linha.split()
        diretiva, args = partes[0].lower(), partes[1:]
        onde = f"{nome}, linha {numero}"

        if diretiva == "endereco":
            if len(args) != 1:
                raise ErroConfiguracao(f"{onde}: uso: endereco 10.G.R.1")
            if endereco is not None:
                raise ErroConfiguracao(f"{onde}: endereco repetido")
            if not validar_endereco_roteador(args[0]):
                raise ErroConfiguracao(
                    f"{onde}: endereco {args[0]!r} fora do formato 10.G.R.1")
            endereco = args[0]

        elif diretiva == "porta":
            if len(args) != 1:
                raise ErroConfiguracao(f"{onde}: uso: porta <1-65535>")
            if porta is not None:
                raise ErroConfiguracao(f"{onde}: porta repetida")
            porta = _porta(args[0], onde)

        elif diretiva == "vizinho":
            if len(args) != 3:
                raise ErroConfiguracao(
                    f"{onde}: uso: vizinho <ip real> <porta> <custo>")
            ip = _ip(args[0], onde)
            porta_viz = _porta(args[1], onde)
            custo = _custo(args[2], onde)
            if (ip, porta_viz) in vistos:
                raise ErroConfiguracao(
                    f"{onde}: vizinho {ip}:{porta_viz} repetido")
            vistos.add((ip, porta_viz))
            vizinhos.append(VizinhoConfig(ip, porta_viz, custo))

        else:
            raise ErroConfiguracao(f"{onde}: diretiva desconhecida {partes[0]!r}")

    if endereco is None:
        raise ErroConfiguracao(f"{nome}: falta a linha 'endereco 10.G.R.1'")
    return Configuracao(endereco, porta if porta is not None else PORTA_PADRAO, vizinhos)


def validar_endereco_roteador(endereco: str) -> bool:
    """True se o endereço estiver no formato 10.G.R.1."""
    octetos = endereco.split(".")
    if len(octetos) != 4:
        return False
    if not all(o.isascii() and o.isdigit() and int(o) <= 255 for o in octetos):
        return False
    return octetos[0] == "10" and octetos[3] == "1"


def _porta(texto: str, onde: str) -> int:
    if not (texto.isascii() and texto.isdigit()) or not 1 <= int(texto) <= 65535:
        raise ErroConfiguracao(f"{onde}: porta {texto!r} deve estar entre 1 e 65535")
    return int(texto)


def _custo(texto: str, onde: str) -> int:
    if not (texto.isascii() and texto.isdigit()) or int(texto) < 1:
        raise ErroConfiguracao(f"{onde}: custo {texto!r} deve ser inteiro positivo")
    return int(texto)


def _ip(texto: str, onde: str) -> str:
    try:
        return str(ipaddress.IPv4Address(texto))
    except ValueError:
        raise ErroConfiguracao(f"{onde}: IP real {texto!r} inválido")
