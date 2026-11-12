"""LSDB, geração do LSP próprio, inundação, sincronização e envelhecimento.

Geração:
    primeira sequência = int(time.time()) (ou --seq-inicial); depois +1.
    LSP lista apenas vizinhos ativos. Gravado na própria LSDB, enviado a todos
    os vizinhos ativos, tabela recalculada.
    Gatilhos: vizinho ativo, vizinho inativo, renovação a cada 30 s.

Recebimento do vizinho V, nesta ordem:
    1. origem == eu                         -> descartar
    2. LSDB tem seq >= da mesma origem      -> descartar, log como cópia
    3. caso contrário                       -> substituir, anotar horário,
                                               reenviar TEXTO ORIGINAL a todos os
                                               ativos exceto V, recalcular tabela

Envelhecimento: a cada 1 s, remover LSPs de OUTROS recebidos há mais de 90 s.
O LSP próprio nunca envelhece; cópia descartada não renova o horário.
"""

from __future__ import annotations

import time
from typing import Optional

import dijkstra
import log
import pacotes
import vizinhos
from estado import EntradaLSDB, Estado, ParReal, Rota

INTERVALO_RENOVACAO = 30.0
IDADE_MAXIMA = 90.0


def formatar_vizinhos(viz: dict[str, int]) -> str:
    return ",".join(f"{v}={c}" for v, c in sorted(viz.items())) or "(nenhum)"


def gerar_lsp_proprio(estado: Estado, motivo: str) -> None:
    with estado.lock:
        agora = time.monotonic()
        estado.seq_proprio += 1
        viz = vizinhos.vizinhos_ativos(estado)
        dados = pacotes.montar_lsp(estado.meu_endereco, estado.seq_proprio, viz)
        estado.lsdb[estado.meu_endereco] = EntradaLSDB(
            seq=estado.seq_proprio,
            vizinhos=viz,
            recebido_em=agora,
            texto_original=dados.decode("ascii"),
        )
        estado.contadores.lsp_gerados += 1
        estado.proxima_renovacao = agora + INTERVALO_RENOVACAO
        log.evento(f"LSP GERADO seq={estado.seq_proprio} "
                   f"vizinhos={formatar_vizinhos(viz)} ({motivo})")
        for par in vizinhos.pares_ativos(estado):
            vizinhos.enviar_para_par(estado, dados, par)
        recalcular_tabela(estado, "LSP próprio gerado")


def receber_lsp(estado: Estado, lsp: pacotes.LSP, origem_real: ParReal) -> None:
    """Aplica as três regras de recebimento (e --descartar-lsp, se ligado)."""
    with estado.lock:
        via = estado.vizinhos[origem_real].endereco_virtual or \
            f"{origem_real[0]}:{origem_real[1]}"

        # Regra 1: o meu próprio LSP voltando pela inundação.
        if lsp.origem == estado.meu_endereco:
            log.evento(f"LSP PROPRIO DESCARTADO seq={lsp.seq} via={via}", terminal=False)
            return

        # Regra 2: cópia ou LSP antigo.
        atual = estado.lsdb.get(lsp.origem)
        if atual is not None and atual.seq >= lsp.seq:
            estado.contadores.lsp_copias_descartadas += 1
            log.evento(f"LSP COPIA origem={lsp.origem} seq={lsp.seq} via={via} "
                       f"(armazenado seq={atual.seq})")
            return

        # Experimento da questão 5: perder de propósito o N-ésimo LSP novo.
        estado.lsps_novos_recebidos += 1
        if estado.descartar_lsp and estado.lsps_novos_recebidos == estado.descartar_lsp:
            log.evento(f"LSP DESCARTADO DE PROPOSITO origem={lsp.origem} "
                       f"seq={lsp.seq} via={via} (--descartar-lsp)")
            return

        # Regra 3: LSP novo.
        estado.lsdb[lsp.origem] = EntradaLSDB(
            seq=lsp.seq,
            vizinhos=dict(lsp.vizinhos),
            recebido_em=time.monotonic(),
            texto_original=lsp.texto_original,
        )
        estado.contadores.lsp_aceitos += 1
        log.evento(f"LSP NOVO origem={lsp.origem} seq={lsp.seq} via={via} "
                   f"vizinhos={formatar_vizinhos(lsp.vizinhos)}")
        inundar(estado, lsp.texto_original, exceto=origem_real)
        recalcular_tabela(estado, f"LSP novo de {lsp.origem}")


def inundar(estado: Estado, texto_original: str, exceto: Optional[ParReal]) -> None:
    """Reenvia o texto original, sem alterar nada, a todos os ativos exceto V."""
    dados = texto_original.encode("ascii")
    with estado.lock:
        for par in vizinhos.pares_ativos(estado):
            if par == exceto:
                continue
            vizinhos.enviar_para_par(estado, dados, par)
            estado.contadores.lsp_reenviados += 1


def sincronizar_vizinho(estado: Estado, par: ParReal) -> None:
    """Envia ao vizinho recém-ativo uma cópia de todos os LSPs da LSDB."""
    with estado.lock:
        for entrada in estado.lsdb.values():
            vizinhos.enviar_para_par(estado, entrada.texto_original.encode("ascii"), par)


def renovar_se_preciso(estado: Estado, agora: float) -> None:
    with estado.lock:
        if agora >= estado.proxima_renovacao:
            gerar_lsp_proprio(estado, "renovação")


def envelhecer(estado: Estado, agora: float) -> None:
    with estado.lock:
        velhos = [origem for origem, e in estado.lsdb.items()
                  if origem != estado.meu_endereco
                  and agora - e.recebido_em > IDADE_MAXIMA]
        for origem in velhos:
            entrada = estado.lsdb.pop(origem)
            log.evento(f"LSP ENVELHECIDO origem={origem} seq={entrada.seq} removido")
        if velhos:
            recalcular_tabela(estado, "LSP envelhecido")


def lsdb_simples(estado: Estado) -> dict[str, dict[str, int]]:
    """Converte a LSDB para o formato de dijkstra.py: origem -> {vizinho: custo}."""
    with estado.lock:
        return {origem: dict(e.vizinhos) for origem, e in estado.lsdb.items()}


def recalcular_tabela(estado: Estado, motivo: str) -> None:
    """Chama dijkstra.calcular_tabela e grava em estado.tabela, com log."""
    with estado.lock:
        nova = dijkstra.calcular_tabela(lsdb_simples(estado), estado.meu_endereco)
        estado.tabela = {rede: Rota(prox, custo) for rede, (prox, custo) in nova.items()}
        log.evento(f"TABELA RECALCULADA {len(estado.tabela)} rotas ({motivo})")
