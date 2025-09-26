# Instruções Copilot para o Emulador de Rede RDT em Python

## Visão Geral do Projeto
Este código implementa um emulador de rede para os protocolos Alternating Bit e Go-Back-N, baseado no simulador de J.F. Kurose. Foi adaptado para Python, mantendo a lógica de simulação de transferência de dados unidirecional ou bidirecional entre duas entidades (A e B), com suporte para perda e corrupção de pacotes.

## Arquivos Principais
- `rdt.py`: Contém todo o código, incluindo a lógica do protocolo (a ser implementada pelos alunos) e a camada de emulação de rede (não modificar).

## Arquitetura e Fluxo de Dados
- **Camada 5 para Camada 4:** `A_output()` e `B_output()` são chamados quando uma mensagem chega da camada de aplicação.
- **Camada 4 para Camada 3:** Use `tolayer3()` para enviar pacotes para a camada de rede.
- **Camada 3 para Camada 4:** `A_input()` e `B_input()` são chamados quando um pacote chega da rede.
- **Camada 4 para Camada 5:** Use `tolayer5()` para entregar dados à camada de aplicação.
- **Timers:** Use `starttimer()` e `stoptimer()` para lógica de retransmissão.

## Fluxo de Trabalho do Desenvolvedor
- **Executar:** Rode com `python rdt.py` e siga os prompts interativos para definir os parâmetros da simulação.
- **Depuração:** Defina o nível de `TRACE` (solicitado na execução) para obter saída detalhada.
- **Testes:** A simulação é autônoma; teste executando e observando a saída.

## Convenções Específicas do Projeto
- **Implementação do Protocolo:** Modifique apenas as sete rotinas dos alunos (`A_output`, `A_input`, `A_timerinterrupt`, `A_init`, `B_output`, `B_input`, `B_timerinterrupt`, `B_init`).
- **Estrutura dos Pacotes:** Sempre utilize as classes `Pkt` e `Msg` fornecidas para comunicação.
- **Sem Bibliotecas Externas:** Toda a lógica deve ser implementada em Python puro usando o framework fornecido.
- **Modo Bidirecional:** Altere `BIDIRECTIONAL = 1` e implemente `B_output()` para crédito extra.
- **Não Modifique o Código do Emulador:** A seção de emulação de rede (abaixo das rotinas dos alunos) deve permanecer inalterada.

## Exemplos
- Para enviar um pacote de A: chame `tolayer3(A, packet)`
- Para iniciar um timer para A: chame `starttimer(A, timeout)`
- Para entregar dados à aplicação: chame `tolayer5(A, data)`

## Referências
- Para mais detalhes, veja os comentários em `rdt.py` e o PDF/docx da tarefa fornecido.

---
Se alguma seção estiver pouco clara ou faltar detalhes, envie seu feedback para que estas instruções possam ser aprimoradas.
