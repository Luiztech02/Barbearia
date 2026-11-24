# Proposta do projeto Santo Bigode

## Problema e público

A rotina da barbearia combina organização de horários, disponibilidade de insumos, acompanhamento de resultados e orientação de estilo. Para o cliente, a dificuldade é visualizar possibilidades e escolher um serviço. Para o barbeiro, é integrar a demanda à operação. Para o responsável, é enxergar o resultado dos três profissionais e controlar acessos.

## Objetivo

Construir uma experiência web que conecte a decisão do cliente ao atendimento e à gestão, com áreas separadas e uma prévia de visagismo assistida por visão computacional. O projeto evoluiu do aplicativo Java recebido para uma interface web em JavaScript/CSS, uma instalação Python/SQLite e uma operação online com API TypeScript/D1.

## Hipótese de valor

Referências visuais contextualizadas podem facilitar a conversa sobre o corte, enquanto agendamento e administração integrados podem reduzir a fragmentação da rotina. São hipóteses do produto: ainda não existem métricas de conversão, produtividade, aumento de receita ou satisfação coletadas.

## Papel da inteligência artificial

A IA entra na detecção de pontos faciais com modelos pré-treinados executados no dispositivo. A aplicação usa esses pontos para calcular proporções por uma heurística e selecionar um pequeno conjunto de referências por regras e curadoria. A recomendação considera também a textura e a preferência informadas pelo cliente. Não há treinamento próprio, reconhecimento de identidade ou geração de cabelo sobre a foto.

A escolha por processamento local reduz a necessidade de enviar imagens faciais a um servidor e dispensa uma API externa paga de análise. Essa arquitetura exige compatibilidade do navegador e pode variar em desempenho conforme o dispositivo. A alternativa Face-API em CPU oferece outro caminho de execução quando não há WebGL2.

## Jornada proposta

1. Conhecer serviços e explorar o portfólio.
2. Enviar foto/câmera e autorizar a análise local.
3. Informar textura e preferência de estilo.
4. Visualizar duas ou três referências, seus motivos e fontes.
5. Selecionar uma referência e agendar o serviço ou apenas a consulta.
6. Adaptar a proposta com o profissional durante o atendimento.
7. Concluir o atendimento para atualizar os indicadores administrativos.

## Serviço e receita

A prévia digital é gratuita. A consulta de visagismo custa R$ 100 e tem duração de 60 minutos. Quando adicionada a corte ou barba, soma R$ 100 e 60 minutos ao serviço. O valor é pago na barbearia; não há checkout online implementado. Esse desenho cria uma oferta adicional no catálogo, mas não é uma projeção de receita nem garantia de venda.

## Limites e entregas

O protótipo entrega agenda, estoque, financeiro semanal por profissional, acesso administrativo por equipe, links de reserva, carrossel, chatbot por regras e análise orientativa com referências. O financeiro é estimado e depende de custos/despesas lançados. As fotografias dos prints são externas e não representam trabalhos da barbearia. O código para divulgação usa placeholders próprios.

A fonte pública inclui a versão Python executável e o núcleo da API online para estudo. A infraestrutura completa da hospedagem não está empacotada como implantação automática em outro provedor. O banco local é independente do online.

## Validação seguinte

Avaliar as sugestões com profissionais e diferentes usuários; medir aceitação das referências, qualidade percebida, tempo até o agendamento e abandono. Testar pose, iluminação, texturas e desempenho em celulares. Revisar limiares com critérios documentados e ampliar o catálogo com fotos autorizadas. Pagamentos e WhatsApp oficial são possibilidades futuras.

As suítes funcionais aprovadas são descritas em `Validacao.md`; não constituem validação científica do visagismo ou comprovação de resultado comercial.
