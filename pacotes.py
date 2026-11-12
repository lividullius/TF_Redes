"""Análise e montagem dos 4 tipos de pacote. Único módulo que conhece o formato.

Rigor ao enviar (formato exato, ASCII, sem quebra de linha), tolerância ao
receber (aceita '\\n' ou '\\r\\n' no final e ';' sobrando na lista do LSP).

Formatos:
    HELLO:<endereço>
    LSP:<origem>:<seq>:<viz>=<custo>;<viz>=<custo>     (lista pode ser vazia)
    DADOS:<origem>:<destino>:<ttl>:<id>:<mensagem>
    ICMP:<origem>:<destino>:<ttl>:<id>:<tipo>

ATENÇÃO: a ORDEM dos campos de DADOS e ICMP foi assumida a partir do plano
(que só informa a quantidade). Conferir no enunciado; se mudar, basta ajustar
_analisar_dados, _analisar_icmp, montar_dados e montar_icmp.

    Tipo   Campos  Verificações
    HELLO  2       endereço virtual válido
    LSP    4       origem válida, sequência inteira, itens vizinho=custo com
                   custo inteiro positivo; lista vazia aceita
    DADOS  6       origem e destino válidos, TTL e id inteiros;
                   mais de 6 campos => ':' na mensagem => malformado
    ICMP   6       origem e destino válidos, TTL e id inteiros, tipo em {0,3,8,11}
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Union

TTL_PADRAO = 16

ICMP_ECO_RESPOSTA = 0
ICMP_INALCANCAVEL = 3
ICMP_ECO_PEDIDO = 8
ICMP_TEMPO_EXCEDIDO = 11
TIPOS_ICMP = {ICMP_ECO_RESPOSTA, ICMP_INALCANCAVEL, ICMP_ECO_PEDIDO, ICMP_TEMPO_EXCEDIDO}
TIPOS_ERRO_ICMP = {ICMP_INALCANCAVEL, ICMP_TEMPO_EXCEDIDO}


class PacoteMalformado(Exception):
    """Pacote que não passa na validação; a mensagem vai para o log."""


@dataclass
class Hello:
    endereco: str


@dataclass
class LSP:
    origem: str
    seq: int
    vizinhos: dict[str, int]
    texto_original: str  # reenviado sem alteração na inundação


@dataclass
class Dados:
    origem: str
    destino: str
    ttl: int
    id: int
    mensagem: str


@dataclass
class ICMP:
    origem: str
    destino: str
    ttl: int
    id: int
    tipo: int


Pacote = Union[Hello, LSP, Dados, ICMP]


# ---------- recepção ----------

def analisar(dados: bytes) -> Pacote:
    """Decodifica e valida um datagrama. Retorna Hello | LSP | Dados | ICMP.
    Lança PacoteMalformado em qualquer falha."""
    try:
        texto = dados.decode("ascii")
    except UnicodeDecodeError:
        raise PacoteMalformado("bytes fora do ASCII")

    texto = texto.rstrip("\r\n")
    campos = texto.split(":")
    tipo = campos[0]

    if tipo == "HELLO":
        return _analisar_hello(campos)
    if tipo == "LSP":
        return _analisar_lsp(campos, texto)
    if tipo == "DADOS":
        return _analisar_dados(campos)
    if tipo == "ICMP":
        return _analisar_icmp(campos)
    raise PacoteMalformado(f"tipo desconhecido {tipo[:20]!r}")


def _analisar_hello(campos: list[str]) -> Hello:
    _exigir_campos(campos, 2)
    return Hello(_endereco(campos[1], "endereço"))


def _analisar_lsp(campos: list[str], texto: str) -> LSP:
    _exigir_campos(campos, 4)
    origem = _endereco(campos[1], "origem")
    seq = _inteiro(campos[2], "sequência")
    vizinhos: dict[str, int] = {}
    for item in campos[3].split(";"):
        if item == "":
            continue  # lista vazia ou ';' sobrando
        partes = item.split("=")
        if len(partes) != 2:
            raise PacoteMalformado(f"item de LSP inválido {item[:30]!r}")
        vizinho = _endereco(partes[0], "vizinho do LSP")
        vizinhos[vizinho] = _inteiro(partes[1], "custo", minimo=1)
    return LSP(origem, seq, vizinhos, texto)


def _analisar_dados(campos: list[str]) -> Dados:
    _exigir_campos(campos, 6)
    return Dados(
        origem=_endereco(campos[1], "origem"),
        destino=_endereco(campos[2], "destino"),
        ttl=_inteiro(campos[3], "TTL"),
        id=_inteiro(campos[4], "id"),
        mensagem=campos[5],
    )


def _analisar_icmp(campos: list[str]) -> ICMP:
    _exigir_campos(campos, 6)
    tipo = _inteiro(campos[5], "tipo ICMP")
    if tipo not in TIPOS_ICMP:
        raise PacoteMalformado(f"tipo ICMP {tipo} fora de {{0, 3, 8, 11}}")
    return ICMP(
        origem=_endereco(campos[1], "origem"),
        destino=_endereco(campos[2], "destino"),
        ttl=_inteiro(campos[3], "TTL"),
        id=_inteiro(campos[4], "id"),
        tipo=tipo,
    )


def _exigir_campos(campos: list[str], n: int) -> None:
    if len(campos) != n:
        raise PacoteMalformado(
            f"{campos[0]} com {len(campos)} campos (esperado {n})")


def _endereco(texto: str, nome: str) -> str:
    if not endereco_valido(texto):
        raise PacoteMalformado(f"{nome} inválido {texto[:30]!r}")
    return texto


def _inteiro(texto: str, nome: str, minimo: int = 0) -> int:
    if not (texto.isascii() and texto.isdigit()) or int(texto) < minimo:
        raise PacoteMalformado(f"{nome} inválido {texto[:30]!r}")
    return int(texto)


def endereco_valido(endereco: str) -> bool:
    """4 octetos inteiros entre 0 e 255."""
    octetos = endereco.split(".")
    return len(octetos) == 4 and all(
        o.isascii() and o.isdigit() and int(o) <= 255 for o in octetos)


# ---------- envio ----------

def montar_hello(endereco: str) -> bytes:
    return f"HELLO:{endereco}".encode("ascii")


def montar_lsp(origem: str, seq: int, vizinhos: dict[str, int]) -> bytes:
    lista = ";".join(f"{v}={c}" for v, c in sorted(vizinhos.items()))
    return f"LSP:{origem}:{seq}:{lista}".encode("ascii")


def montar_dados(origem: str, destino: str, ttl: int, id_: int, mensagem: str) -> bytes:
    return f"DADOS:{origem}:{destino}:{ttl}:{id_}:{mensagem}".encode("ascii")


def montar_icmp(origem: str, destino: str, ttl: int, id_: int, tipo: int) -> bytes:
    return f"ICMP:{origem}:{destino}:{ttl}:{id_}:{tipo}".encode("ascii")


def montar(pacote: Pacote) -> bytes:
    """Monta qualquer um dos 4 tipos a partir do objeto."""
    if isinstance(pacote, Hello):
        return montar_hello(pacote.endereco)
    if isinstance(pacote, LSP):
        return montar_lsp(pacote.origem, pacote.seq, pacote.vizinhos)
    if isinstance(pacote, Dados):
        return montar_dados(pacote.origem, pacote.destino, pacote.ttl,
                            pacote.id, pacote.mensagem)
    if isinstance(pacote, ICMP):
        return montar_icmp(pacote.origem, pacote.destino, pacote.ttl,
                           pacote.id, pacote.tipo)
    raise TypeError(f"não é um pacote: {pacote!r}")


def mensagem_valida(texto: str) -> bool:
    """Recusa ':', quebras de linha e caracteres fora do ASCII (comando msg)."""
    return texto.isascii() and ":" not in texto and "\n" not in texto and "\r" not in texto


def descrever(pacote: Pacote) -> str:
    """Resumo de uma linha para o log."""
    if isinstance(pacote, Dados):
        return f"DADOS {pacote.origem}->{pacote.destino}"
    if isinstance(pacote, ICMP):
        return f"ICMP tipo={pacote.tipo} {pacote.origem}->{pacote.destino}"
    return type(pacote).__name__.upper()
