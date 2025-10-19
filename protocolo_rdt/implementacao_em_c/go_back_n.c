#include <stdio.h>
#include <string.h>
#include <stdlib.h> // Para malloc e free

#define BIDIRECTIONAL 0
#define WINDOW_SIZE 8
#define BUFFER_SIZE 50

struct msg {
  char data[20];
};

struct pkt {
  int seqnum;
  int acknum;
  int checksum;
  char payload[20];
};

/********* VARIÁVEIS GLOBAIS PARA O GO-BACK-N *********/
int base;                // Número de sequência do pacote mais antigo não confirmado
int next_seq_num;        // Próximo número de sequência a ser usado
int expected_seq_num_b;  // Número de sequência esperado no receptor B

struct pkt* window_buffer[WINDOW_SIZE]; // Buffer da janela para pacotes enviados e não confirmados
struct msg message_buffer[BUFFER_SIZE]; // Buffer para mensagens da camada de aplicação
int msg_buffer_start = 0;
int msg_buffer_end = 0;
int msg_buffer_count = 0;


/********* FUNÇÕES DO ALUNO *********/

int calculate_checksum(struct pkt *packet) {
  int sum = 0;
  sum += packet->seqnum;
  sum += packet->acknum;
  for (int i = 0; i < 20; i++) {
    sum += packet->payload[i];
  }
  return sum;
}

void send_packet(int seq_num) {
    int buffer_index = seq_num % WINDOW_SIZE;
    
    // Libera memória se já houver um pacote antigo
    if (window_buffer[buffer_index] != NULL) {
        free(window_buffer[buffer_index]);
    }

    // Aloca memória para o novo pacote
    window_buffer[buffer_index] = (struct pkt*) malloc(sizeof(struct pkt));
    if (window_buffer[buffer_index] == NULL) {
        printf("Erro: Falha ao alocar memória para o pacote.\n");
        return;
    }

    struct pkt* packet = window_buffer[buffer_index];
    packet->seqnum = seq_num;
    packet->acknum = 0;
    
    // Pega a mensagem do buffer
    strcpy(packet->payload, message_buffer[msg_buffer_start].data);
    msg_buffer_start = (msg_buffer_start + 1) % BUFFER_SIZE;
    msg_buffer_count--;

    packet->checksum = calculate_checksum(packet);

    printf("A: Enviando pacote %d\n", packet->seqnum);
    tolayer3(0, *packet);

    // Se o pacote enviado é o primeiro da janela (base), inicia o timer
    if (base == next_seq_num) {
        starttimer(0, 20.0);
    }
}


/* Chamado pela camada 5 para enviar dados */
void A_output(struct msg message) {
    if (msg_buffer_count >= BUFFER_SIZE) {
        printf("A: Buffer de mensagens cheio. Descartando mensagem.\n");
        return;
    }

    // Adiciona mensagem ao buffer
    strcpy(message_buffer[msg_buffer_end].data, message.data);
    msg_buffer_end = (msg_buffer_end + 1) % BUFFER_SIZE;
    msg_buffer_count++;
    
    // Envia pacotes enquanto a janela não estiver cheia
    while (next_seq_num < base + WINDOW_SIZE && msg_buffer_count > 0) {
        send_packet(next_seq_num);
        next_seq_num++;
    }
}

/* Chamado pela camada 3 quando um pacote chega em A (ACK) */
void A_input(struct pkt packet) {
    int checksum_result = calculate_checksum(&packet);

    if (packet.checksum != checksum_result) {
        printf("A: ACK corrompido. Ignorando.\n");
        return;
    }

    printf("A: Recebeu ACK %d\n", packet.acknum);

    if (packet.acknum >= base) {
        base = packet.acknum + 1;
        stoptimer(0);
        
        // Se ainda houver pacotes não confirmados na janela, reinicia o timer
        if (base != next_seq_num) {
            starttimer(0, 20.0);
        }

        // Envia mais pacotes se houver espaço na janela e mensagens no buffer
        while (next_seq_num < base + WINDOW_SIZE && msg_buffer_count > 0) {
            send_packet(next_seq_num);
            next_seq_num++;
        }
    }
}

/* Chamado quando o timer de A estoura (timeout) */
void A_timerinterrupt() {
    printf("A: Timeout! Reenviando janela a partir do pacote %d\n", base);
    starttimer(0, 20.0);
    for (int i = base; i < next_seq_num; i++) {
        int buffer_index = i % WINDOW_SIZE;
        printf("A: Reenviando pacote %d\n", window_buffer[buffer_index]->seqnum);
        tolayer3(0, *window_buffer[buffer_index]);
    }
}

/* Inicialização de A */
void A_init() {
    base = 0;
    next_seq_num = 0;
    for (int i = 0; i < WINDOW_SIZE; i++) {
        window_buffer[i] = NULL;
    }
}

/* Chamado pela camada 3 quando um pacote chega em B */
void B_input(struct pkt packet) {
    int checksum_result = calculate_checksum(&packet);

    if (checksum_result != packet.checksum) {
        printf("B: Pacote corrompido. Descartando.\n");
        // Não envia NACK, GBN confia no timeout do remetente
        return;
    }

    if (packet.seqnum == expected_seq_num_b) {
        printf("B: Recebeu pacote esperado %d. Enviando ACK.\n", packet.seqnum);
        tolayer5(1, packet.payload);

        struct pkt ack_packet;
        ack_packet.acknum = expected_seq_num_b;
        ack_packet.checksum = calculate_checksum(&ack_packet);
        tolayer3(1, ack_packet);

        expected_seq_num_b++;
    } else {
        printf("B: Recebeu pacote fora de ordem (esperado: %d, recebido: %d). Descartando e reenviando último ACK.\n", expected_seq_num_b, packet.seqnum);
        
        // Reenvia o ACK do último pacote recebido em ordem
        struct pkt ack_packet;
        ack_packet.acknum = expected_seq_num_b - 1; 
        ack_packet.checksum = calculate_checksum(&ack_packet);
        tolayer3(1, ack_packet);
    }
}

/* Inicialização de B */
void B_init() {
    expected_seq_num_b = 0;
}