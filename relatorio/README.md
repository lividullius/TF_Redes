# Relatório

Relatório final em PDF, com a figura da topologia de teste e as 6 questões.

| Questão | Experimento | Evidência |
|---|---|---|
| 1. Dijkstra | Em R1: `lsdb`, `dijkstra`, `tabela` | Saída dos comandos + tabela de iterações à mão |
| 2. Inundação | Captura; encerrar um roteador | `.pcapng` filtrado por LSP + `stats` de cada roteador |
| 3. Convergência | Encerrar R3 anotando o horário | Horários nos logs |
| 4. Sequência | Reiniciar com `--seq-inicial 0` | Logs dos vizinhos descartando LSPs antigos |
| 5. Confiabilidade | `--descartar-lsp N` | LSDB divergente, corrigida em até 30 s |
| 6. TTL | Explicação sobre a topologia | Laço transitório entre dois roteadores |

Capturas `.pcapng` ficam em [capturas/](capturas/).
Filtro Wireshark (loopback): `udp.portrange == 6001-6005`; só LSPs: `udp contains "LSP:"`.
