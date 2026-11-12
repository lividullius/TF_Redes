"""Envia pacotes arbitrários a um roteador (casos de teste 10 a 12).

Precisa usar a porta de origem de um vizinho CONFIGURADO e desligado; senão o
pacote é descartado pela regra de origem desconhecida.

Uso:
    python3 scripts/enviar_pacote.py <porta_origem> <ip_destino> <porta_destino> <texto>
    python3 scripts/enviar_pacote.py <porta_origem> <ip_destino> <porta_destino> --lixo

Depois de enviar, escuta por 3 s e mostra o que voltar (ex.: ICMP tipo 3).

Exemplos (R2 desligado, enviando como se fosse ele para R1 em 127.0.0.1:6001):
    caso 10: ... 6002 127.0.0.1 6001 --lixo
    caso 11: ... 6002 127.0.0.1 6001 "ICMP:10.1.2.1:10.99.9.1:16:99:8"
    caso 12: ... 6002 127.0.0.1 6001 "ICMP:10.1.2.1:10.1.5.1:1:98:11"
"""

import socket
import sys

LIXO = [
    b"OLA:10.1.1.1",                       # tipo desconhecido
    b"HELLO",                              # campos a menos
    b"DADOS:10.1.2.1:10.1.5.1:abc:0:oi",   # TTL abc
    b"HELLO:10.1.2.\xc3\xa9",              # bytes fora do ASCII
    b"LSP:10.1.2.1:7:10.1.1.1=0",          # custo zero
    b"DADOS:10.1.2.1:10.1.5.1:16:0:a:b",   # ':' na mensagem
    b"\xff\xfe\x00",
]

ESPERA = 3.0


def main(argv):
    if len(argv) != 4:
        print(__doc__)
        return 2
    porta_origem, ip, porta_destino, texto = int(argv[0]), argv[1], int(argv[2]), argv[3]
    pacotes = LIXO if texto == "--lixo" else [texto.encode("ascii")]

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", porta_origem))
    for p in pacotes:
        sock.sendto(p, (ip, porta_destino))
        print(f"enviado: {p!r}")

    sock.settimeout(ESPERA)
    try:
        while True:
            dados, origem = sock.recvfrom(65535)
            print(f"recebido de {origem[0]}:{origem[1]}: {dados!r}")
    except socket.timeout:
        pass
    finally:
        sock.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
