"""Estado dos vizinhos, envio de HELLO e detecção de inatividade.

Regras:
    1. A cada 5 s, HELLO:<meu endereço> para TODOS os vizinhos configurados.
    2. Ao receber HELLO, atualizar o horário do último HELLO daquele par.
    3. Vizinho inativo -> ativo: associar endereço virtual ao par, gerar LSP
       próprio novo e enviar a ele cópia de todos os LSPs da LSDB.
    4. Endereço virtual mudou: atualizar associação e gerar LSP novo.
    5. Ativo há mais de 20 s sem HELLO -> inativo: remover associação e gerar LSP novo.
"""

from __future__ import annotations

from estado import Estado, ParReal

INTERVALO_HELLO = 5.0
LIMITE_INATIVIDADE = 20.0


def inicializar(estado: Estado, vizinhos_config) -> None:
    """Preenche estado.vizinhos a partir da configuração (todos inativos)."""
    raise NotImplementedError


def enviar_hellos(estado: Estado, agora: float) -> None:
    """Chamado pela temporizadora; envia HELLO se passaram 5 s."""
    raise NotImplementedError


def receber_hello(estado: Estado, hello, origem_real: ParReal) -> None:
    """Aplica as regras 2 a 4."""
    raise NotImplementedError


def verificar_inatividade(estado: Estado, agora: float) -> None:
    """Aplica a regra 5."""
    raise NotImplementedError


def vizinhos_ativos(estado: Estado) -> dict[str, int]:
    """endereço virtual -> custo, apenas dos ativos (conteúdo do LSP próprio)."""
    raise NotImplementedError


def enviar_para_par(estado: Estado, dados: bytes, par: ParReal) -> None:
    """Envia pelo socket único."""
    raise NotImplementedError


def enviar(estado: Estado, dados: bytes, endereco_virtual: str) -> bool:
    """Envia ao vizinho ativo com esse endereço virtual.
    Retorna False se não houver associação (tratado como ausência de rota)."""
    raise NotImplementedError
