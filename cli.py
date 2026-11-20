"""Interface de comandos (thread principal).

    tabela                 rede, próximo salto e custo, ordenados por rede
    lsdb                   origem, sequência, vizinhos e custos, idade em s
    vizinhos               endereço virtual, IP real e porta de cada ativo
    msg <destino> <texto>  DADOS com TTL 16 e id 0; recusa ':' e não-ASCII
    ping <destino> [TTL]   ICMP 8; tipo da resposta, quem respondeu e RTT,
                           ou timeout após 2 s (Event.wait FORA do lock)
    dijkstra   (extra)     iterações do algoritmo passo a passo
    stats      (extra)     LSPs gerados, aceitos, reenviados, cópias descartadas
    ajuda, sair

Comando inválido -> uma linha de uso, sem derrubar o programa.
"""

from __future__ import annotations

import time

import dijkstra
import encaminhamento
import log
import lsdb
import pacotes
from estado import Estado, PingPendente

TIMEOUT_PING = 2.0


def _chave_endereco(endereco: str) -> tuple[int, ...]:
    """Ordena '10.1.10' depois de '10.1.9' (ordem numérica, não de texto)."""
    return tuple(int(o) for o in endereco.split("."))


def laco(estado: Estado) -> None:
    """Lê comandos com input() até EOF/Ctrl+C ou 'sair'."""
    print("Digite 'ajuda' para ver os comandos.")
    while True:
        try:
            linha = input()
        except (EOFError, KeyboardInterrupt):
            break
        # Separa o nome do comando do resto da linha.
        # Ex.: "msg 10.1.5.1 ola" -> nome="msg", resto="10.1.5.1 ola"
        partes = linha.strip().split(maxsplit=1)
        if not partes:
            continue
        nome = partes[0].lower()
        resto = partes[1] if len(partes) > 1 else ""
        if nome == "sair":
            break
        comando = COMANDOS.get(nome)
        if comando is None:
            print(f"Comando desconhecido: {nome}. Use: {', '.join(COMANDOS)}, sair")
            continue
        # Um erro dentro de um comando não pode derrubar o roteador.
        try:
            comando(estado, resto)
        except Exception as e:
            print(f"Erro ao executar {nome}: {e}")


def cmd_ajuda(estado: Estado, resto: str) -> None:
    print(__doc__.split("\n\n")[1])


def cmd_tabela(estado: Estado, resto: str) -> None:
    # Copia os dados com o lock e imprime depois, para não travar
    # as outras threads enquanto escreve na tela.
    with estado.lock:
        linhas = sorted(estado.tabela.items(), key=lambda kv: _chave_endereco(kv[0]))
    if not linhas:
        print("Tabela vazia.")
        return
    print(f"{'Rede':<16}{'Próximo salto':<16}{'Custo':>5}")
    for rede, rota in linhas:
        print(f"{rede + '.0/24':<16}{rota.proximo_salto:<16}{rota.custo:>5}")


def cmd_lsdb(estado: Estado, resto: str) -> None:
    agora = time.monotonic()
    with estado.lock:
        entradas = sorted(estado.lsdb.items(), key=lambda kv: _chave_endereco(kv[0]))
    print(f"{'Origem':<14}{'Sequência':<14}{'Idade':>6}  Vizinhos")
    for origem, e in entradas:
        idade = int(agora - e.recebido_em)  # segundos desde que o LSP chegou
        print(f"{origem:<14}{e.seq:<14}{idade:>5}s  {lsdb.formatar_vizinhos(e.vizinhos)}")


def cmd_vizinhos(estado: Estado, resto: str) -> None:
    with estado.lock:
        ativos = [(v.endereco_virtual, par, v.custo)
                  for par, v in estado.vizinhos.items() if v.ativo]
        total = len(estado.vizinhos)
    print(f"{len(ativos)} de {total} vizinhos configurados ativos.")
    if ativos:
        print(f"{'Endereço':<14}{'IP real':<16}{'Porta':>6}{'Custo':>6}")
    for virt, (ip, porta), custo in sorted(ativos, key=lambda a: _chave_endereco(a[0])):
        print(f"{virt:<14}{ip:<16}{porta:>6}{custo:>6}")


def cmd_msg(estado: Estado, resto: str) -> None:
    # Separa o destino do texto (o texto pode ter espaços).
    partes = resto.split(maxsplit=1)
    if len(partes) != 2:
        print("Uso: msg <destino> <texto>")
        return
    destino, texto = partes
    if not pacotes.endereco_valido(destino):
        print(f"Destino inválido: {destino}")
        return
    # ':' quebraria o formato do pacote; acentos não são ASCII.
    if not pacotes.mensagem_valida(texto):
        print("Mensagem recusada: não pode conter ':' nem caracteres fora do ASCII (acentos).")
        return
    # Mensagens sempre saem com TTL 16 e id 0.
    pacote = pacotes.Dados(estado.meu_endereco, destino, pacotes.TTL_PADRAO, 0, texto)
    if encaminhamento.originar(estado, pacote):
        log.evento(f"DADOS ORIGINADO {estado.meu_endereco}->{destino}")
    else:
        print(f"Destino inalcançável: sem rota para {destino}.")


def cmd_ping(estado: Estado, resto: str) -> None:
    partes = resto.split()
    if not 1 <= len(partes) <= 2:
        print("Uso: ping <destino> [TTL]")
        return
    destino = partes[0]
    if not pacotes.endereco_valido(destino):
        print(f"Destino inválido: {destino}")
        return
    # O TTL é opcional (padrão 16). Com TTL pequeno dá para ver o caminho.
    ttl = pacotes.TTL_PADRAO
    if len(partes) == 2:
        if not partes[1].isdigit() or int(partes[1]) < 1:
            print("TTL deve ser um inteiro positivo.")
            return
        ttl = int(partes[1])

    with estado.lock:
        # Cada ping tem um id diferente; a resposta volta com o mesmo id.
        id_ = estado.prox_id
        estado.prox_id += 1
        # Anota o ping como "esperando resposta" ANTES de enviar,
        # porque a resposta pode chegar muito rápido.
        pendente = PingPendente(enviado_em=time.monotonic(), destino=destino)
        estado.pings_pendentes[id_] = pendente
        pedido = pacotes.ICMP(estado.meu_endereco, destino, ttl, id_,
                              pacotes.ICMP_ECO_PEDIDO)
        enviado = encaminhamento.originar(estado, pedido)
        if enviado:
            log.evento(f"ICMP GERADO tipo=8 para={destino} id={id_}")
        else:
            del estado.pings_pendentes[id_]
    if not enviado:
        print(f"Destino inalcançável: sem rota para {destino}.")
        return

    # Espera a resposta por até 2 s. Isso fica FORA do lock: quem recebe a
    # resposta é a thread receptora, e ela precisa do lock para isso.
    pendente.evento.wait(TIMEOUT_PING)

    with estado.lock:
        estado.pings_pendentes.pop(id_, None)
        resposta, recebido_em = pendente.resposta, pendente.recebido_em
    if resposta is None:
        print(f"ping {destino} id={id_} ttl={ttl}: timeout após {TIMEOUT_PING:.0f} s")
        return
    # RTT = tempo entre enviar o pedido e receber a resposta, em ms.
    rtt = (recebido_em - pendente.enviado_em) * 1000
    descricao = {
        pacotes.ICMP_ECO_RESPOSTA: "resposta de eco",
        pacotes.ICMP_TEMPO_EXCEDIDO: "tempo excedido",
        pacotes.ICMP_INALCANCAVEL: "destino inalcançável",
    }[resposta.tipo]
    print(f"ping {destino} id={id_} ttl={ttl}: {descricao} (tipo {resposta.tipo}) "
          f"de {resposta.origem}, rtt={rtt:.1f} ms")


def cmd_dijkstra(estado: Estado, resto: str) -> None:
    """Mostra cada iteração do Dijkstra (para a questão 1 do relatório)."""
    simples = lsdb.lsdb_simples(estado)
    eu = estado.meu_endereco
    colunas: list[str] = []
    largura = 16

    # Chamada pelo Dijkstra a cada iteração; imprime uma linha da tabela.
    def mostrar(it: dict) -> None:
        # Na primeira iteração, imprime o cabeçalho com um roteador por coluna.
        if not colunas:
            colunas.extend(sorted((n for n in it["distancias"] if n != eu),
                                  key=_chave_endereco))
            print("Cada coluna: D(v),p(v)   * = finalizado")
            print(f"{'It':<4}{'Finalizado':<12}" +
                  "".join(f"{n:<{largura}}" for n in colunas))
        # Cada célula: distância e predecessor (de onde se chega a esse nó).
        celulas = []
        for n in colunas:
            d = it["distancias"][n]
            p = it["predecessores"][n]
            marca = "*" if n in it["finalizados"] else ""
            celulas.append("∞" if d == dijkstra.INFINITO else f"{int(d)},{p}{marca}")
        print(f"{it['iteracao']:<4}{it['finalizado']:<12}" +
              "".join(f"{c:<{largura}}" for c in celulas))

    tabela = dijkstra.calcular_tabela(simples, eu, mostrar)
    print()
    print(f"{'Rede':<16}{'Próximo salto':<16}{'Custo':>5}")
    for rede, (prox, custo) in sorted(tabela.items(), key=lambda kv: _chave_endereco(kv[0])):
        print(f"{rede + '.0/24':<16}{prox:<16}{custo:>5}")


def cmd_stats(estado: Estado, resto: str) -> None:
    """Contadores de LSP (para a questão 2 do relatório)."""
    with estado.lock:
        c = estado.contadores
        print(f"LSPs gerados:             {c.lsp_gerados}")
        print(f"LSPs aceitos (novos):     {c.lsp_aceitos}")
        print(f"LSPs reenviados:          {c.lsp_reenviados}")
        print(f"LSPs descartados (cópia): {c.lsp_copias_descartadas}")


# Liga o nome digitado à função que executa o comando.
COMANDOS = {
    "tabela": cmd_tabela,
    "lsdb": cmd_lsdb,
    "vizinhos": cmd_vizinhos,
    "msg": cmd_msg,
    "ping": cmd_ping,
    "dijkstra": cmd_dijkstra,
    "stats": cmd_stats,
    "ajuda": cmd_ajuda,
}
