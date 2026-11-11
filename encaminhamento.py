"""Entrega local, encaminhamento, TTL e geração de ICMP.

Ao ORIGINAR (msg, ping, respostas de eco, erros): consultar a tabela pela rede
do destino; sem rota, avisar/logar e não enviar nada.

Ao RECEBER com destino na própria rede 10.G.R.0/24 (TTL NÃO é decrementado):
    DADOS      -> exibir origem, destino e mensagem
    ICMP 8     -> responder tipo 0, mesmo id, TTL 16, origem = destino do pedido
    ICMP 0/3/11-> acordar ping pendente pelo id; sem pendente, só log

Ao RECEBER com destino em outra rede, nesta ordem:
    1. decrementar TTL; se 0 -> descartar e gerar ICMP 11 para a origem
    2. consultar tabela; sem rota -> descartar e gerar ICMP 3 para a origem
    3. encaminhar ao próximo salto com o novo TTL e logar

Erros: origem = meu endereço, TTL 16, id do pacote causador.
Nunca gerar erro se o pacote descartado já era ICMP 3 ou 11.
"""

from __future__ import annotations

from estado import Estado


def eh_local(estado: Estado, destino: str) -> bool:
    raise NotImplementedError


def originar(estado: Estado, pacote) -> bool:
    """Consulta a rota e envia. Retorna False se não houver rota/associação."""
    raise NotImplementedError


def receber_dados(estado: Estado, dados) -> None:
    raise NotImplementedError


def receber_icmp(estado: Estado, icmp) -> None:
    raise NotImplementedError


def encaminhar(estado: Estado, pacote) -> None:
    """Passos 1 a 3 do encaminhamento para outra rede."""
    raise NotImplementedError


def gerar_erro_icmp(estado: Estado, causador, tipo: int) -> None:
    """Gera ICMP 3 ou 11 respeitando a regra de não responder erro com erro."""
    raise NotImplementedError
