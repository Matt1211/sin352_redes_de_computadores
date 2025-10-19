# ******************************************************************
# EMULADOR DE REDE GO-BACK-N: VERSÃO 1.1 J.F.Kurose
#
# Este código deve ser usado para PA2, adaptado para o protocolo Go-Back-N.
# ******************************************************************

import random
import time
from collections import deque

# Constantes
BIDIRECTIONAL = 0
TIMER_INTERRUPT = 0
FROM_LAYER5 = 1
FROM_LAYER3 = 2
A = 0
B = 1

class Msg:
    def __init__(self, data):
        self.data = data

class Pkt:
    def __init__(self, seqnum, acknum, checksum, payload=""):
        self.seqnum = seqnum
        self.acknum = acknum
        self.checksum = checksum
        self.payload = payload

class Event:
    def __init__(self, evtime, evtype, eventity, pktptr=None):
        self.evtime = evtime
        self.evtype = evtype
        self.eventity = eventity
        self.pktptr = pktptr

#################################################################
# CÓDIGO DO EMULADOR DE REDE (Não modificar)
#################################################################

class RDTEmulator:
    def __init__(self):
        # --- Variáveis de Simulação ---
        self.evlist = []
        self.TRACE = 1
        self.nsim = 0
        self.nsimmax = 0
        self.lossprob = 0.0
        self.corruptprob = 0.0
        self.lambda_ = 0.0
        self.ntolayer3 = 0
        self.nlost = 0
        self.ncorrupt = 0
        self.time = 0.0

        # --- Variáveis de Estado do Protocolo Go-Back-N ---
        self.WINDOW_SIZE = 8
        self.base = 0
        self.next_seq_num = 0
        self.expected_seq_num_b = 0
        self.last_ack_sent_b = -1 # Para reenviar o último ACK em caso de pacotes fora de ordem
        
        # Buffers
        self.window_buffer = {} # Dicionário para armazenar pacotes enviados mas não confirmados
        self.message_buffer = deque() # Fila para mensagens da camada 5 aguardando envio

    def jimsrand(self):
        return random.random()

    def init(self):
        print("-----  Emulador Go-Back-N Versão Python -------- \n")
        self.nsimmax = int(input("Digite o número de mensagens para simular: "))
        self.lossprob = float(input("Digite a probabilidade de perda de pacote [0.0 para sem perda]: "))
        self.corruptprob = float(input("Digite a probabilidade de corrupção de pacote [0.0 para sem corrupção]: "))
        self.lambda_ = float(input("Digite o tempo médio entre mensagens da camada 5 [> 0.0]: "))
        self.TRACE = int(input("Digite o nível de TRACE: "))
        self.WINDOW_SIZE = int(input("Digite o tamanho da janela [N]: "))
        random.seed(9999)
        self.time = 0.0
        self.generate_next_arrival()

    def generate_next_arrival(self):
        x = self.lambda_ * self.jimsrand() * 2
        evtime = self.time + x
        ev = Event(evtime, FROM_LAYER5, A)
        self.insertevent(ev)

    def insertevent(self, event):
        self.evlist.append(event)
        self.evlist.sort(key=lambda e: e.evtime)

    def starttimer(self, AorB, increment):
        evtime = self.time + increment
        ev = Event(evtime, TIMER_INTERRUPT, AorB)
        self.insertevent(ev)

    def stoptimer(self, AorB):
        self.evlist = [ev for ev in self.evlist if not (ev.evtype == TIMER_INTERRUPT and ev.eventity == AorB)]

    def tolayer3(self, AorB, packet):
        self.ntolayer3 += 1
        if self.jimsrand() < self.lossprob:
            self.nlost += 1
            if self.TRACE > 0: print("          TOLAYER3: pacote perdido")
            return
        mypkt = Pkt(packet.seqnum, packet.acknum, packet.checksum, packet.payload)
        evtime = self.time + 1 + 9 * self.jimsrand()
        eventity = (AorB + 1) % 2
        ev = Event(evtime, FROM_LAYER3, eventity, mypkt)
        if self.jimsrand() < self.corruptprob:
            self.ncorrupt += 1
            x = self.jimsrand()
            if x < 0.75:
                if len(mypkt.payload) > 0: mypkt.payload = 'Z' + mypkt.payload[1:]
                else: mypkt.payload = 'Z'
            elif x < 0.875: mypkt.seqnum = 999999
            else: mypkt.acknum = 999999
            if self.TRACE > 0: print("          TOLAYER3: pacote corrompido")
        self.insertevent(ev)

    def tolayer5(self, AorB, datasent):
        if self.TRACE > 2:
            print(f"          TOLAYER5: dados recebidos: {datasent}")

    ############################################################################
    # As próximas sete rotinas devem ser implementadas pelo aluno (adaptadas para GBN)
    ############################################################################
    
    def calculate_checksum(self, packet):
        soma = packet.seqnum + packet.acknum
        for char in packet.payload:
            soma += ord(char)
        return soma

    def A_output(self, message):
        # Adiciona a mensagem a um buffer e tenta enviar pacotes
        self.message_buffer.append(message)
        
        while self.next_seq_num < self.base + self.WINDOW_SIZE and self.message_buffer:
            msg_to_send = self.message_buffer.popleft()
            
            packet = Pkt(seqnum=self.next_seq_num, 
                         acknum=0, 
                         checksum=0, 
                         payload=msg_to_send.data)
            packet.checksum = self.calculate_checksum(packet)
            
            # Armazena o pacote na janela e envia
            self.window_buffer[self.next_seq_num] = packet
            self.tolayer3(A, packet)
            print(f"A: Enviando pacote {self.next_seq_num}")

            if self.base == self.next_seq_num:
                self.starttimer(A, 20.0)
            
            self.next_seq_num += 1

    def B_output(self, message):
        pass # Não usado em transferência unidirecional

    def A_input(self, packet):
        checksum_result = self.calculate_checksum(packet)

        if packet.checksum != checksum_result:
            print("A: Recebeu ACK corrompido. Ignorando.")
            return

        print(f"A: Recebeu ACK {packet.acknum}")
        
        # ACK cumulativo: atualiza a base da janela
        if packet.acknum >= self.base:
            self.base = packet.acknum + 1
            self.stoptimer(A)
            if self.base != self.next_seq_num:
                self.starttimer(A, 20.0)
            
            # Tenta enviar mais pacotes se houver espaço na janela e mensagens no buffer
            while self.next_seq_num < self.base + self.WINDOW_SIZE and self.message_buffer:
                 self.A_output(Msg("")) # Chama A_output para processar o buffer

    def B_input(self, packet):
        checksum_result = self.calculate_checksum(packet)

        if packet.checksum != checksum_result:
            print(f"B: Pacote {packet.seqnum} corrompido. Descartando.")
            return

        if packet.seqnum == self.expected_seq_num_b:
            print(f"B: Recebeu pacote esperado {packet.seqnum}. Enviando ACK.")
            self.tolayer5(B, packet.payload)
            
            ack_packet = Pkt(seqnum=0, acknum=self.expected_seq_num_b, checksum=0)
            ack_packet.checksum = self.calculate_checksum(ack_packet)
            self.tolayer3(B, ack_packet)
            
            self.last_ack_sent_b = self.expected_seq_num_b
            self.expected_seq_num_b += 1
        else:
            print(f"B: Pacote fora de ordem (esperado: {self.expected_seq_num_b}, recebido: {packet.seqnum}). Descartando e reenviando último ACK.")
            # Reenvia o ACK do último pacote recebido em ordem
            if self.last_ack_sent_b != -1:
                ack_packet = Pkt(seqnum=0, acknum=self.last_ack_sent_b, checksum=0)
                ack_packet.checksum = self.calculate_checksum(ack_packet)
                self.tolayer3(B, ack_packet)

    def A_timerinterrupt(self):
        print(f"A: Timeout! Reenviando janela a partir do pacote {self.base}")
        self.starttimer(A, 20.0)
        for i in range(self.base, self.next_seq_num):
            packet_to_resend = self.window_buffer[i]
            print(f"A: Reenviando pacote {packet_to_resend.seqnum}")
            self.tolayer3(A, packet_to_resend)

    def B_timerinterrupt(self):
        pass # Não usado em GBN

    def A_init(self):
        self.base = 0
        self.next_seq_num = 0
        self.window_buffer.clear()
        self.message_buffer.clear()

    def B_init(self):
        self.expected_seq_num_b = 0
        self.last_ack_sent_b = -1


    # Loop principal do simulador (Não modificar)
    def run(self):
        self.init()
        self.A_init()
        self.B_init()
        while True:
            if not self.evlist: break
            event = self.evlist.pop(0)
            self.time = event.evtime
            if self.nsim >= self.nsimmax:
                print("Simulation limit reached.")
                break
            if event.evtype == FROM_LAYER5:
                self.generate_next_arrival()
                j = self.nsim % 26
                data = chr(97 + j) * 20
                msg = Msg(data)
                self.nsim += 1
                if event.eventity == A: self.A_output(msg)
                else: self.B_output(msg)
            elif event.evtype == FROM_LAYER3:
                pkt = event.pktptr
                if event.eventity == A: self.A_input(pkt)
                else: self.B_input(pkt)
            elif event.evtype == TIMER_INTERRUPT:
                if event.eventity == A: self.A_timerinterrupt()
                else: self.B_timerinterrupt()
            else:
                print("ERRO INTERNO: tipo de evento desconhecido")
        print(f"Simulador encerrado no tempo {self.time} após enviar {self.nsim} mensagens da camada 5")

if __name__ == "__main__":
    emulator = RDTEmulator()
    emulator.run()