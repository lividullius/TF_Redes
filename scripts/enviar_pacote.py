"""Envia pacotes arbitrários a um roteador (casos de teste 10 a 12).

Precisa usar a porta de origem de um vizinho CONFIGURADO e desligado; senão o
pacote é descartado pela regra de origem desconhecida.

Uso previsto:
    python3 scripts/enviar_pacote.py <porta_origem> <ip_destino> <porta_destino> <texto|--lixo>

Casos:
    10  lixo: tipo desconhecido, campos a menos, TTL 'abc', bytes fora do ASCII
    11  pedido de eco para rede inexistente -> esperar ICMP tipo 3 com o mesmo id
    12  ICMP tipo 11 com TTL 1 para destino distante -> descartado sem novo erro
"""


def main(argv):
    raise NotImplementedError


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]))
