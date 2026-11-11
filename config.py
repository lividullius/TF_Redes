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
    raise NotImplementedError


def validar_endereco_roteador(endereco: str) -> bool:
    """True se o endereço estiver no formato 10.G.R.1."""
    raise NotImplementedError
