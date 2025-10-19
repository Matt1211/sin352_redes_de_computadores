# 🛰️ Análise Comparativa: Stop-and-Wait vs. Go-Back-N em C

Este documento oferece uma análise comparativa entre as implementações dos protocolos **Stop-and-Wait (Bit Alternado)** e **Go-Back-N**, utilizando o mesmo emulador de rede em C. O objetivo é destacar como as diferenças no código-fonte refletem as distintas funcionalidades, eficiências e complexidades de cada protocolo.

---

## 📌 Visão Geral e Objetivo

Ambos os protocolos visam garantir a entrega de dados de forma confiável sobre um canal não confiável. No entanto, eles adotam estratégias fundamentalmente diferentes para alcançar esse objetivo.

-   **Stop-and-Wait**: É a simplicidade em pessoa. Envia um pacote, para e espera a confirmação (ACK) antes de enviar o próximo. É confiável, mas lento.
-   **Go-Back-N**: Busca a eficiência. Envia múltiplos pacotes (uma "janela") sem esperar por ACKs individuais, mantendo o canal de comunicação mais ocupado. É mais rápido, mas introduz maior complexidade.

A seguir, uma análise comparativa baseada nas implementações em C (`stop_and_wait.c` vs. `go_back_n.c`).

---

## ⚙️ Comparativo de Implementação em C

### 1. Gerenciamento de Estado do Remetente (A)

A diferença mais crucial está em como o remetente gerencia o que foi enviado e o que foi confirmado.

#### **Stop-and-Wait (`stop_and_wait.c`)**

O estado é mínimo e direto. O remetente só precisa saber sobre **um** pacote por vez.

-   `int sequence_number_a`: Armazena o número de sequência do próximo pacote a ser enviado (alterna entre 0 e 1).
-   `bool senderIsWaiting`: Uma flag booleana que impede o envio de novos pacotes enquanto se aguarda um ACK.
-   `struct pkt last_packet_sent`: Uma cópia do último pacote enviado, guardada exclusivamente para uma possível retransmissão em caso de timeout.

**Funcionalidade Expressa no Código:** O remetente opera em um ciclo binário: enviar ou esperar. A simplicidade dessas variáveis reflete a incapacidade do protocolo de ter mais de um pacote "em trânsito".

#### **Go-Back-N (`go_back_n.c`)**

O estado é mais complexo, pois precisa gerenciar uma **janela** de pacotes.

-   `int base`: O número de sequência do pacote mais antigo que ainda não foi confirmado. É a base da janela deslizante.
-   `int next_seq_num`: O próximo número de sequência disponível para um novo pacote.
-   `struct pkt* window_buffer[WINDOW_SIZE]`: Um buffer (array de ponteiros) que armazena todos os pacotes enviados mas ainda não confirmados. Este é o coração da janela.
-   `struct msg message_buffer[]`: Um buffer adicional para armazenar mensagens da camada 5 que chegam mais rápido do que a janela consegue processar.

**Funcionalidade Expressa no Código:** A lógica `base` e `next_seq_num` define uma janela (`base` a `next_seq_num - 1`). O `window_buffer` permite que o remetente "lembre" de múltiplos pacotes pendentes, o que é a base do *pipelining*.

### 2. Lógica de Envio (`A_output`)

#### **Stop-and-Wait (`stop_and_wait.c`)**

O envio é bloqueante.

-   A função primeiro verifica a flag `senderIsWaiting`. Se for `true`, a nova mensagem da aplicação é simplesmente descartada ou ignorada.
-   Se puder enviar, ele monta **um único pacote**, envia, inicia um timer e seta a flag `senderIsWaiting` para `true`.

**Funcionalidade Expressa no Código:** A função reflete a natureza "pare e espere". Não há paralelismo; uma operação de envio deve ser totalmente concluída (com um ACK recebido) antes que a próxima possa começar.

#### **Go-Back-N (`go_back_n.c`)**

O envio é contínuo, limitado apenas pelo tamanho da janela.

-   A função verifica se a janela não está cheia (`next_seq_num < base + WINDOW_SIZE`).
-   Usa um loop `while` para enviar todos os pacotes possíveis, seja de novas mensagens ou do buffer, até que a janela se encha.
-   Não há uma flag de "espera". A capacidade de enviar é determinada dinamicamente pela posição da `base` e `next_seq_num`.

**Funcionalidade Expressa no Código:** Esta implementação permite que o remetente preencha o *pipeline* da rede, enviando pacotes continuamente, o que leva a uma utilização muito maior da largura de banda.

### 3. Gerenciamento de Timer

#### **Stop-and-Wait (`stop_and_wait.c`)**

Um timer por pacote.

-   `starttimer(A, 20.0)` é chamado toda vez que um pacote é enviado.
-   `stoptimer(A)` é chamado quando o ACK correspondente chega.
-   Em `A_timerinterrupt()`, o `last_packet_sent` é reenviado.

**Funcionalidade Expressa no Código:** O timer está diretamente associado a um único pacote pendente. Se ele dispara, a causa é clara: o pacote ou seu ACK se perdeu.

#### **Go-Back-N (`go_back_n.c`)**

Um único timer para a janela inteira.

-   `starttimer(A, 20.0)` é chamado **apenas** quando o primeiro pacote de uma nova janela é enviado (`base == next_seq_num`).
-   O timer é reiniciado quando um ACK que move a `base` é recebido.
-   Em `A_timerinterrupt()`, um loop varre o `window_buffer` e reenvia **todos** os pacotes a partir da `base` até `next_seq_num - 1`.

**Funcionalidade Expressa no Código:** O timer agora protege o pacote mais antigo. Um timeout sinaliza um problema com o pacote `base`, e o protocolo assume que todos os pacotes subsequentes também precisam ser reenviados, mesmo que tenham chegado corretamente. Esta é a essência do "Go-Back-N".

### 4. Lógica do Receptor (`B_input`)

#### **Stop-and-Wait (`stop_and_wait.c`)**

O receptor é simples e sem memória de longo prazo.

-   Ele apenas verifica se o `seqnum` do pacote recebido é o que ele espera (`sequence_number_b`).
-   Se for o pacote esperado, ele o entrega à camada 5 e envia um ACK.
-   Se for um pacote duplicado (o `seqnum` é o do pacote anterior), ele **não entrega** novamente, mas reenvia o ACK para o remetente saber que ele foi recebido.

**Funcionalidade Expressa no Código:** O receptor só precisa de um inteiro (`sequence_number_b`) para funcionar. Ele não armazena pacotes fora de ordem.

#### **Go-Back-N (`go_back_n.c`)**

O receptor é ainda mais simples, mas rigoroso.

-   Ele também só tem uma variável de estado: `expected_seq_num_b`.
-   Se o `packet.seqnum == expected_seq_num_b`, o pacote é aceito, entregue, e um ACK para esse número é enviado. `expected_seq_num_b` é incrementado.
-   Se um pacote chega fora de ordem (`packet.seqnum > expected_seq_num_b`), ele é **descartado**. O receptor então reenvia o ACK do último pacote recebido em ordem (`expected_seq_num_b - 1`).

**Funcionalidade Expressa no Código:** A simplicidade do receptor do GBN é sua maior fraqueza. Ao descartar pacotes que chegam fora de ordem, mesmo que estejam corretos, ele força o remetente a retransmitir pacotes que podem ter sido recebidos com sucesso, desperdiçando largura de banda.

---

## 📊 Tabela Comparativa

| Funcionalidade | Stop-and-Wait (Bit Alternado) | Go-Back-N |
| :--- | :--- | :--- |
| **Envio de Pacotes** | Um por vez; espera ACK para enviar o próximo. | Múltiplos pacotes (janela N); envio contínuo. |
| **Pipelining** | Não utilizado. | Utilizado (essência do protocolo). |
| **Uso de Timer** | Um timer por pacote enviado. | Um único timer para o pacote mais antigo na janela. |
| **ACKs** | Confirmação individual para cada pacote. | Cumulativo. `ACK(n)` confirma todos até `n`. |
| **Complexidade (Remetente)** | Baixa. Gerencia apenas um pacote e um timer. | Alta. Gerencia uma janela, múltiplos pacotes e buffers. |
| **Complexidade (Receptor)** | Baixa. Apenas verifica duplicatas. | Muito baixa. Descarta qualquer pacote fora de ordem. |
| **Retransmissão (Timeout)** | Reenvia um único pacote. | Reenvia a janela inteira a partir da base (`Go-Back-N`). |
| **Eficiência** | Baixa, especialmente em redes com alto atraso. | Alta, melhora significativamente a vazão. |