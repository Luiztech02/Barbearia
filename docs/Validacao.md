# Validação do material e do código de divulgação

Executada em 24/11/2026 sobre a pasta `github/` deste pacote.

| Verificação | Resultado |
| --- | --- |
| `python3 -m unittest test_server.py` | 11 testes aprovados |
| `node test_store.mjs` | Financeiro, clientes únicos, adicional, duração, conflitos, equipe e importação: aprovados |
| `node test_access.mjs` | Projeção pública, preço, conflito e 60 combinações de referências com assets: aprovados |
| `node --experimental-strip-types test_team.mts` | Autorização, bloqueio, administração, revogação, reativação e links: aprovados |
| Análise no navegador | Executada com uma foto de demonstração; resultado e três referências capturados |
| Apresentação PDF | 12 páginas renderizadas e inspecionadas |

O teste dos assets usa SVG porque o código de divulgação substitui fotografias externas por placeholders. Os prints mostram a interface com as imagens de referência da demonstração. A cópia isolada usada para capturar as telas não integra a fonte pública.

Esta verificação não mede acurácia do formato facial, satisfação, conversão, faturamento real ou desempenho em todos os dispositivos.
