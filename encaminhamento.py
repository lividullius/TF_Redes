"""Entrega local, encaminhamento, TTL e geração de ICMP.

Ao ORIGINAR (msg, ping, respostas de eco, erros): consultar a tabela pela rede
do destino; sem rota, avisar/logar e não enviar nada. Destino na própria rede
é entregue localmente, sem passar pela rede.

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

import dataclasses
import time
from typing import Union

import log
import pacotes
import vizinhos
from dijkstra import rede_de
from estado import Estado
from pacotes import ICMP, Dados

PacoteRoteavel = Union[Dados, ICMP]


def eh_local(estado: Estado, destino: str) -> bool:
    """True se o destino está na nossa rede (ex.: 10.1.1.x para o R1)."""
    return rede_de(destino) == rede_de(estado.meu_endereco)


def originar(estado: Estado, pacote: PacoteRoteavel) -> bool:
    """Consulta a rota e envia. Retorna False se não houver rota/associação."""
    # Usado quando ESTE roteador cria o pacote (msg, ping, respostas e erros).
    with estado.lock:
        # Destino na nossa própria rede: entrega aqui mesmo.
        if eh_local(estado, pacote.destino):
            entregar_local(estado, pacote)
            return True
        # Procura a rota pela rede do destino (ex.: 10.1.5).
        rota = estado.tabela.get(rede_de(pacote.destino))
        if rota is None:
            return False  # sem rota: nada é enviado
        # Envia ao próximo salto. Retorna False se esse vizinho estiver inativo.
        return vizinhos.enviar(estado, pacotes.montar(pacote), rota.proximo_salto)


def receber(estado: Estado, pacote: PacoteRoteavel) -> None:
    """Ponto de entrada da thread receptora para DADOS e ICMP."""
    with estado.lock:
        if eh_local(estado, pacote.destino):
            entregar_local(estado, pacote)   # é para nós
        else:
            encaminhar(estado, pacote)       # é para outro roteador: repassa


def receber_dados(estado: Estado, dados: Dados) -> None:
    receber(estado, dados)


def receber_icmp(estado: Estado, icmp: ICMP) -> None:
    receber(estado, icmp)


def entregar_local(estado: Estado, pacote: PacoteRoteavel) -> None:
    """Trata um pacote que chegou ao destino final (a nossa rede)."""
    # Mensagem de texto: só mostra na tela.
    if isinstance(pacote, Dados):
        log.evento(f"MENSAGEM RECEBIDA de={pacote.origem} para={pacote.destino}: "
                   f"{pacote.mensagem}")
        return

    log.evento(f"ICMP RECEBIDO tipo={pacote.tipo} de={pacote.origem} id={pacote.id}",
               terminal=False)

    # Pedido de eco (alguém fez ping para nós): responde com tipo 0.
    if pacote.tipo == pacotes.ICMP_ECO_PEDIDO:
        resposta = ICMP(
            # A resposta sai com o endereço que foi pingado (ex.: 10.1.5.77),
            # e não com o endereço do roteador.
            origem=pacote.destino,
            destino=pacote.origem,
            ttl=pacotes.TTL_PADRAO,
            id=pacote.id,  # mesmo id do pedido
            tipo=pacotes.ICMP_ECO_RESPOSTA,
        )
        log.evento(f"ICMP GERADO tipo=0 para={resposta.destino} id={resposta.id}")
        if not originar(estado, resposta):
            log.evento(f"SEM ROTA para {resposta.destino}: resposta de eco não enviada")
        return

    # Tipos 0, 3 e 11: é a resposta de um ping que nós fizemos.
    # O id diz de qual ping é a resposta.
    pendente = estado.pings_pendentes.get(pacote.id)
    if pendente is None or pendente.resposta is not None:
        log.evento(f"ICMP tipo={pacote.tipo} de={pacote.origem} id={pacote.id} "
                   f"sem ping pendente")
        return
    pendente.resposta = pacote
    pendente.recebido_em = time.monotonic()
    # Avisa o comando ping (que está esperando) que a resposta chegou.
    pendente.evento.set()


def encaminhar(estado: Estado, pacote: PacoteRoteavel) -> None:
    """Passos 1 a 3 do encaminhamento para outra rede."""
    with estado.lock:
        desc = pacotes.descrever(pacote)

        # Passo 1: diminui o TTL. Se chegar a 0, o pacote "morre" aqui
        # e avisamos quem enviou com ICMP tipo 11 (tempo excedido).
        # (O TTL é testado antes da rota, como pede o plano.)
        novo_ttl = pacote.ttl - 1
        if novo_ttl <= 0:
            log.evento(f"DESCARTADO {desc} id={pacote.id}: TTL esgotado")
            gerar_erro_icmp(estado, pacote, pacotes.ICMP_TEMPO_EXCEDIDO)
            return

        # Passo 2: procura a rota. Sem rota (ou com o próximo salto inativo),
        # descarta e avisa quem enviou com ICMP tipo 3 (destino inalcançável).
        rota = estado.tabela.get(rede_de(pacote.destino))
        novo = dataclasses.replace(pacote, ttl=novo_ttl)  # mesmo pacote, TTL novo
        if rota is None or not vizinhos.enviar(estado, pacotes.montar(novo),
                                               rota.proximo_salto):
            log.evento(f"DESCARTADO {desc} id={pacote.id}: sem rota")
            gerar_erro_icmp(estado, pacote, pacotes.ICMP_INALCANCAVEL)
            return

        # Passo 3: deu certo, o pacote foi enviado ao próximo salto.
        log.evento(f"ENCAMINHADO {desc} prox={rota.proximo_salto} ttl={novo_ttl}")


def gerar_erro_icmp(estado: Estado, causador: PacoteRoteavel, tipo: int) -> None:
    """Gera ICMP 3 ou 11 respeitando a regra de não responder erro com erro."""
    # Se o pacote descartado já era uma mensagem de erro, não gera outra.
    # Senão, dois roteadores poderiam ficar trocando erros sem parar.
    if isinstance(causador, ICMP) and causador.tipo in pacotes.TIPOS_ERRO_ICMP:
        log.evento(f"ICMP NAO GERADO: pacote descartado já era erro "
                   f"(tipo={causador.tipo} id={causador.id})")
        return
    # O erro sai com o NOSSO endereço (é assim que o ping descobre o caminho)
    # e com o mesmo id do pacote que causou o erro.
    erro = ICMP(
        origem=estado.meu_endereco,
        destino=causador.origem,
        ttl=pacotes.TTL_PADRAO,
        id=causador.id,
        tipo=tipo,
    )
    log.evento(f"ICMP GERADO tipo={tipo} para={erro.destino} id={erro.id}")
    if not originar(estado, erro):
        log.evento(f"SEM ROTA para {erro.destino}: ICMP tipo={tipo} não enviado")
