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

import time

import log
import lsdb
import pacotes
from estado import Estado, ParReal, Vizinho

INTERVALO_HELLO = 5.0
LIMITE_INATIVIDADE = 20.0


def inicializar(estado: Estado, vizinhos_config) -> None:
    """Preenche estado.vizinhos a partir da configuração (todos inativos)."""
    with estado.lock:
        for v in vizinhos_config:
            estado.vizinhos[(v.ip, v.porta)] = Vizinho(custo=v.custo)


def enviar_hellos(estado: Estado, agora: float) -> None:
    """Chamado pela temporizadora; envia HELLO se passaram 5 s."""
    with estado.lock:
        if agora < estado.proximo_hello:
            return
        estado.proximo_hello = agora + INTERVALO_HELLO
        dados = pacotes.montar_hello(estado.meu_endereco)
        for par in estado.vizinhos:  # todos os configurados, ativos ou não
            enviar_para_par(estado, dados, par)
            log.evento(f"HELLO ENVIADO para {par[0]}:{par[1]}", terminal=False)


def receber_hello(estado: Estado, hello: pacotes.Hello, origem_real: ParReal) -> None:
    """Aplica as regras 2 a 4."""
    with estado.lock:
        viz = estado.vizinhos[origem_real]
        par_txt = f"{origem_real[0]}:{origem_real[1]}"
        log.evento(f"HELLO RECEBIDO de {hello.endereco} ({par_txt})", terminal=False)

        if hello.endereco == estado.meu_endereco:
            log.evento(f"HELLO IGNORADO: {par_txt} anuncia o meu próprio endereço")
            return

        viz.ultimo_hello = time.monotonic()

        if not viz.ativo:
            viz.ativo = True
            viz.endereco_virtual = hello.endereco
            estado.virt_para_real[hello.endereco] = origem_real
            log.evento(f"VIZINHO ATIVO {hello.endereco} ({par_txt})")
            lsdb.gerar_lsp_proprio(estado, "vizinho ativo")
            lsdb.sincronizar_vizinho(estado, origem_real)

        elif viz.endereco_virtual != hello.endereco:
            antigo = viz.endereco_virtual
            if estado.virt_para_real.get(antigo) == origem_real:
                del estado.virt_para_real[antigo]
            viz.endereco_virtual = hello.endereco
            estado.virt_para_real[hello.endereco] = origem_real
            log.evento(f"VIZINHO MUDOU DE ENDERECO {antigo} -> {hello.endereco} ({par_txt})")
            lsdb.gerar_lsp_proprio(estado, "endereço de vizinho mudou")


def verificar_inatividade(estado: Estado, agora: float) -> None:
    """Aplica a regra 5."""
    with estado.lock:
        mudou = False
        for par, viz in estado.vizinhos.items():
            if viz.ativo and agora - viz.ultimo_hello > LIMITE_INATIVIDADE:
                viz.ativo = False
                if estado.virt_para_real.get(viz.endereco_virtual) == par:
                    del estado.virt_para_real[viz.endereco_virtual]
                log.evento(f"VIZINHO INATIVO {viz.endereco_virtual} ({par[0]}:{par[1]})")
                mudou = True
        if mudou:
            lsdb.gerar_lsp_proprio(estado, "vizinho inativo")


def vizinhos_ativos(estado: Estado) -> dict[str, int]:
    """endereço virtual -> custo, apenas dos ativos (conteúdo do LSP próprio)."""
    with estado.lock:
        return {v.endereco_virtual: v.custo
                for v in estado.vizinhos.values() if v.ativo}


def pares_ativos(estado: Estado) -> list[ParReal]:
    with estado.lock:
        return [par for par, v in estado.vizinhos.items() if v.ativo]


def enviar_para_par(estado: Estado, dados: bytes, par: ParReal) -> None:
    """Envia pelo socket único. Erros de envio só vão para o log."""
    try:
        estado.sock.sendto(dados, par)
    except OSError as e:
        log.evento(f"ERRO DE ENVIO para {par[0]}:{par[1]}: {e}", terminal=False)


def enviar(estado: Estado, dados: bytes, endereco_virtual: str) -> bool:
    """Envia ao vizinho ativo com esse endereço virtual.
    Retorna False se não houver associação (tratado como ausência de rota)."""
    with estado.lock:
        par = estado.virt_para_real.get(endereco_virtual)
        if par is None:
            return False
        enviar_para_par(estado, dados, par)
        return True
