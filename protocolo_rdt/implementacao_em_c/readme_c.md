# 🛰️ Implementação do Protocolo RDT 3.0 (Stop-and-Wait) em C

Este repositório contém a implementação do **protocolo de transferência de dados confiável (RDT)** na sua versão **3.0**, também conhecido como **Stop-and-Wait** ou **Protocolo de Bit Alternado**. O código foi desenvolvido em **C** e utiliza um **emulador de rede** para simular condições de **perda** e **corrupção** de pacotes.

---

## 📌 Visão Geral do Projeto

O objetivo é garantir que a comunicação entre duas entidades — **A (remetente)** e **B (receptor)** — seja **confiável**, mesmo que a rede esteja um caos (perdendo pacotes, corrompendo dados, etc.).

A lógica do protocolo corrige os problemas da camada de rede, implementando soluções diretamente na **camada de transporte**.

---

## 🔁 Como Funciona o Protocolo Stop-and-Wait

A lógica do protocolo é simples:

1. **Stop**: O remetente (A) envia **um único pacote** e aguarda.
2. **Wait**: Ele espera por um **ACK** (Acknowledgment) do receptor (B).
3. **Ação**:
   - Se o ACK chega corretamente ➜ envia o próximo pacote.
   - Se o ACK não chega (ou o pacote foi perdido) ➜ **timeout** e retransmissão.

---

## 🧰 Ferramentas Utilizadas

- **Checksum**: Verifica se o pacote foi corrompido.
- **Números de Sequência (0 e 1)**: Diferencia pacotes novos de retransmissões.
- **Timer**: Controla o tempo de espera pelo ACK.

---

### 📡 Remetente (A)

### 📥 Receptor (B)

---

## ⚙️ Detalhes da Implementação

A lógica está centralizada em **7 funções principais** no arquivo `rdt.c`.

---

### ✅ `calculate_checksum(packet)`

Calcula um **checksum simples** para detectar corrupção:

- Soma inicial = 0
- Soma com `seqnum` e `acknum`
- Soma os **20 bytes do payload**
- Retorna o valor final

```
int calculate_checksum(struct pkt packet)
{
  int sum = 0;

  sum += packet.seqnum;
  sum += packet.acknum;

  // iterando por 20 vezes pq eh o tamanho maximo do payload
  for (int i = 0; i < 20; i++)
  {
    sum += packet.payload[i];
  }

  return sum;
}
```

---

### 🧾 `A_init()`

Inicializa o estado do **Remetente (A)**:

- Define `sequence_number_a = 0`

```
A_init()
{
  sequence_number_a = 0; // vai fazer o envio do primeiro pacote (seqnum = 0)
}
```

---

### 📥 `B_init()`

Inicializa o estado do **Receptor (B)**:

- Define `sequence_number_b = 0`

```
B_init()
{
  sequence_number_b = 0; // se prepara para receber o pacote inicial
}
```

---

### 📤 `A_output(message)` — O Remetente em Ação

Função chamada quando a aplicação quer enviar uma mensagem:

1. **Checagem de envio**: Se `senderIsWaiting = true`, não envia (esperando ACK).
2. **Prepara o pacote**:
   - Define `seqnum`
   - Copia mensagem para o payload
   - Calcula o checksum
3. **Salva o pacote enviado** como `last_packet_sent`
4. **Envia com `tolayer3()`** e inicia o timer com `starttimer()`

```
A_output(message) struct msg message;
{

  if (senderIsWaiting)
  {
    printf("sender busy");

    return;
  }

  senderIsWaiting = true;

  struct pkt packet;

  packet.seqnum = sequence_number_a; // seqnum
  strcpy(packet.payload, message);   // payload
  packet.acknum = 0;                 // acknowledgement number

  packet.checksum = calculate_checksum(packet); // a fazer essa function

  last_packet_sent = packet;
  tolayer3(A, last_packet_sent);
  starttimer(A, 20.0);

  return;
}

```

---

### 📨 `B_input(packet)` — O Receptor Atento

Lógica do receptor quando um pacote chega:

1. **Verifica corrupção (checksum)**: Se inválido, ignora.
2. **Verifica número de sequência**:
   - Se esperado:
     - Entrega à aplicação com `tolayer5()`
     - Envia ACK com o mesmo `seqnum`
     - Alterna `sequence_number_b`
   - Se duplicado:
     - **Não entrega de novo!**
     - Apenas reenvia o ACK

```
B_input(packet) struct pkt packet;
{
  int checksum_result = calculate_checksum(packet);

  if ((checksum_result != packet.checksum))
  {
    printf("packet corrupted");
    return;
  }

  if (sequence_number_b == packet.seqnum) // verifica se o pacote recebido é o que eu deveria receber agora mesmo
  {
    tolayer5(B, packet.payload);                          // propaga a mensagem para a camada da aplicação
    struct pkt ack_packet;                                // cria novo pacote ack para retorno
    ack_packet.acknum = sequence_number_b;                // setta o acknum como o mesmo numero do pacote que acabou de ser verificado
    ack_packet.checksum = calculate_checksum(ack_packet); // setta o checksum, para validacao no remetente
    tolayer3(B, ack_packet);                              // manda para a camada de rede o pacote contendo o ACK -> manda pra A

    sequence_number_b = 1 - sequence_number_b; // alterna o sequence number de b -> pra que?
  }
  else // se receber duplicatas, retorna o ack mas sem duplicar na camada de application (tolayer5)
  {
    struct pkt ack_packet;
    ack_packet.acknum = packet.seqnum;
    ack_packet.checksum = calculate_checksum(ack_packet);
    tolayer3(B, ack_packet);
    printf("received duplicate. Resending ack");
  }
}
```

---

### 📬 `A_input(packet)` — A Resposta do Remetente

Chamado quando o remetente A recebe um ACK:

1. **Verifica checksum e acknum**:
   - Se inválido ➜ ignora (espera timeout)
2. **ACK válido**:
   - Para o timer com `stoptimer(A)`
   - Libera o remetente (`senderIsWaiting = false`)
   - Alterna `sequence_number_a`

```
A_input(packet) struct pkt packet;
{
  int checksum_result = calculate_checksum(packet);

  if (packet.checksum != checksum_result)
  {
    printf("deu ruim mulekeee"); // provavelmente corrompido.
    return; // retorna pra dar um timeout no timer, iniciado em starttimer no A_output
  }

  if (packet.acknum != sequence_number_a)
  {
    printf("deu ruim mulekeee"); // pacote nao foi corrompido, mas veio o ack errado.
    return; // retorna pra dar um timeout no timer, iniciado em starttimer no A_output
  }

  printf("correctly acknowledged. Next packet");
  stoptimer(A); // parar o timer, já que a requisição foi concluída com sucesso
  senderIsWaiting = false; // se prepara para enviar o proximo pacote, agora que a espera acabou
  sequence_number_a = 1 - sequence_number_a; // prepara o seqnum pro proximo pacote
}
```

---

### ⏱️ `A_timerinterrupt()` — O Plano B: Timeout!

Função chamada quando o timer estoura (sem ACK):

- Reenvia `last_packet_sent` com `tolayer3()`
- Reinicia o timer com `starttimer()`
```
A_timerinterrupt()
{
  // funcao para determinar que o tempo habil para resposta foi superado. Timed out.
  //  ack ou o proprio pacote foram perdidos e/ou corrompidos.

  tolayer3(A, last_packet_sent); // tenta reenviar o ultimo pacote enviado, ja que ele foi corrompido ou se perdeu.
  starttimer(A, 20.0)            // inicia o timer de novo, ja que essa é uma retentativa.
}
```
---

## 🧪 Como Compilar e Executar

### 💻 Compilação
Abra o terminal na pasta do projeto e execute:

```bash
gcc rdt.c -o rdt
