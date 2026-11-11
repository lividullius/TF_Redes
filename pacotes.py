"""Análise e montagem dos 4 tipos de pacote. Único módulo que conhece o formato.

Rigor ao enviar (formato exato, ASCII, sem quebra de linha), tolerância ao
receber (ex.: aceitar '\\n' no final).

Filtros aplicados a todo pacote recebido:
    decodificação ASCII estrita e número exato de campos após split(":").

    Tipo   Campos  Verificações
    HELLO  2       endereço virtual válido
    LSP    4       origem válida, sequência inteira, itens vizinho=custo com
                   custo inteiro positivo; lista vazia aceita
    DADOS  6       origem e destino válidos, TTL e id inteiros;
                   mais de 6 campos => ':' na mensagem => malformado
    ICMP   6       origem e destino válidos, TTL e id inteiros, tipo em {0,3,8,11}

TODO: conferir no enunciado a ordem exata dos campos de DADOS e ICMP.
"""

from __future__ import annotations

from dataclasses import dataclass

TTL_PADRAO = 16

ICMP_ECO_RESPOSTA = 0
ICMP_INALCANCAVEL = 3
ICMP_ECO_PEDIDO = 8
ICMP_TEMPO_EXCEDIDO = 11
TIPOS_ICMP = {ICMP_ECO_RESPOSTA, ICMP_INALCANCAVEL, ICMP_ECO_PEDIDO, ICMP_TEMPO_EXCEDIDO}


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


# ---------- recepção ----------

def analisar(dados: bytes):
    """Decodifica e valida um datagrama. Retorna Hello | LSP | Dados | ICMP.
    Lança PacoteMalformado em qualquer falha."""
    raise NotImplementedError


def endereco_valido(endereco: str) -> bool:
    """4 octetos inteiros entre 0 e 255."""
    raise NotImplementedError


# ---------- envio ----------

def montar_hello(endereco: str) -> bytes:
    raise NotImplementedError


def montar_lsp(origem: str, seq: int, vizinhos: dict[str, int]) -> bytes:
    raise NotImplementedError


def montar_dados(origem: str, destino: str, ttl: int, id_: int, mensagem: str) -> bytes:
    raise NotImplementedError


def montar_icmp(origem: str, destino: str, ttl: int, id_: int, tipo: int) -> bytes:
    raise NotImplementedError


def mensagem_valida(texto: str) -> bool:
    """Recusa ':' e caracteres fora do ASCII (comando msg)."""
    raise NotImplementedError
