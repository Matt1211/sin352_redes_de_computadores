# 🛰️ Implementação do Protocolo RDT (Go-Back-N) em C

Este repositório contém a implementação do **protocolo de transferência de dados confiável (RDT)** utilizando o algoritmo **Go-Back-N (GBN)**. O código foi desenvolvido em **C** e utiliza o mesmo **emulador de rede** para simular condições de **perda** e **corrupção** de pacotes, permitindo uma comparação direta com a abordagem Stop-and-Wait.

---

## 📌 Visão Geral do Projeto

O objetivo do Go-Back-N é melhorar a eficiência da comunicação em relação ao Stop-and-Wait, permitindo que o remetente envie múltiplos pacotes (uma "janela") sem esperar por uma confirmação individual para cada um. Isso mantém o "pipeline" de comunicação mais cheio, aumentando a vazão.

A lógica do protocolo, assim como no Stop-and-Wait, corrige os problemas da camada de rede implementando soluções diretamente na **camada de transporte**.

---

## 🚀 Como Funciona o Protocolo Go-Back-N

O Go-Back-N utiliza um mecanismo de **janela deslizante** para controlar o fluxo de pacotes.

1.  **Pipelining**: O remetente (A) pode enviar até **N** pacotes sem receber um ACK. Esse **N** é o **tamanho da janela**.
2.  **ACKs Cumulativos**: O receptor (B) envia um **ACK** para o pacote de maior número de sequência que ele recebeu **em ordem**. Um `ACK(n)` confirma o recebimento de todos os pacotes até o número `n`.
3.  **Timer Único**: O remetente (A) mantém um **único timer** para o pacote mais antigo ainda não confirmado (conhecido como `base`).
4.  **Ação em Timeout**: Se o timer estoura (timeout), o remetente assume que o pacote `base` e todos os pacotes subsequentes na janela foram perdidos. Ele então **volta atrás (Go-Back)** e reenvia todos os pacotes a partir de `base`.
5.  **Receptor Simples**: O receptor (B) só aceita pacotes em ordem. Se ele espera o pacote `n` e recebe `n+1`, ele descarta `n+1` (e todos os seguintes) e reenviando o `ACK(n-1)`.

---

## 🧰 Ferramentas Utilizadas

-   **Checksum**: Verifica se o pacote foi corrompido.
-   **Números de Sequência**: Utiliza um espaço de números de sequência maior para identificar os pacotes dentro da janela.
-   **Janela Deslizante**: Um buffer no remetente que armazena os pacotes enviados, mas ainda não confirmados.
-   **Timer (para o pacote base)**: Controla o tempo de espera pelo ACK cumulativo.

---

## ⚙️ Detalhes da Implementação

A lógica está centralizada nas mesmas funções do emulador, mas com uma lógica interna diferente para gerenciar a janela.

### Variáveis-Chave do Remetente (A)

-   `base`: O número de sequência do pacote mais antigo não confirmado.
-   `next_seq_num`: O próximo número de sequência a ser usado para um novo pacote.
-   `WINDOW_SIZE`: Define o número máximo de pacotes não confirmados permitidos.

### 📤 `A_output(message)` — Enviando em Pipeline

1.  **Verifica a Janela**: Antes de enviar, verifica se a janela não está cheia (`next_seq_num < base + WINDOW_SIZE`).
2.  **Prepara e Envia**: Se houver espaço, cria o pacote, calcula o `checksum` e o envia com `tolayer3()`.
3.  **Inicia o Timer**: Se o pacote enviado for o primeiro da janela (`base == next_seq_num`), o timer é iniciado.
4.  **Avança o ponteiro**: `next_seq_num` é incrementado.

### 📬 `A_input(packet)` — Processando ACKs Cumulativos

1.  **ACK Válido**: Recebe um ACK e verifica se ele não está corrompido.
2.  **Desliza a Janela**: O `ACK(n)` faz com que o remetente atualize sua `base` para `n + 1`, efetivamente "deslizando" a janela para frente.
3.  **Reinicia o Timer**: O timer é parado e, se ainda houver pacotes em trânsito na nova janela, ele é reiniciado para a nova `base`.

### ⏱️ `A_timerinterrupt()` — O Plano B: Go-Back-N!

1.  **Timeout**: Se o timer estoura, o remetente assume que o pacote `base` (e todos os subsequentes) foi perdido.
2.  **Reenvia Tudo**: Ele reenvia **todos** os pacotes que estão na janela atual, começando pela `base`.
3.  **Reinicia o Timer**: Um novo timer é iniciado.

### 📨 `B_input(packet)` — Receptor em Ordem

1.  **Verifica Corrupção e Ordem**: O receptor verifica o `checksum` e se o `seqnum` do pacote é o esperado (`expected_seq_num_b`).
2.  **Pacote Correto**: Se for o pacote esperado:
    -   Entrega os dados para a camada de aplicação (`tolayer5()`).
    -   Envia um `ACK` com o número de sequência recebido.
    -   Incrementa o número de sequência esperado (`expected_seq_num_b++`).
3.  **Pacote Fora de Ordem**: Se o pacote recebido não for o esperado (seja um pacote adiantado ou duplicado):
    -   **Descarta o pacote**.
    -   Reenvia o `ACK` do último pacote que foi recebido em ordem. Isso informa ao remetente qual sequência ele está esperando.