
# ******************************************************************
# EMULADOR DE REDE ALTERNATING BIT E GO-BACK-N: VERSÃO 1.1  J.F.Kurose
#
# Este código deve ser usado para PA2, protocolos de transferência de dados
# unidirecional ou bidirecional (de A para B. Transferência bidirecional é
# extra e não obrigatória). Propriedades da rede:
# - O atraso médio de rede é de cinco unidades de tempo (pode ser maior se
#   houver outras mensagens no canal para GBN)
# - Pacotes podem ser corrompidos (cabeçalho ou dados) ou perdidos, de acordo
#   com probabilidades definidas pelo usuário
# - Pacotes serão entregues na ordem em que foram enviados (embora alguns
#   possam ser perdidos)
# ******************************************************************

import random
import time


# Constantes
BIDIRECTIONAL = 0  # Altere para 1 se for implementar transferência bidirecional
TIMER_INTERRUPT = 0  # Interrupção de timer
FROM_LAYER5 = 1     # Evento vindo da camada 5
FROM_LAYER3 = 2     # Evento vindo da camada 3
A = 0               # Identificador da entidade A
B = 1               # Identificador da entidade B


# Uma "Msg" é a unidade de dados passada da camada 5 (código do professor)
# para a camada 4 (código do aluno). Contém os dados (caracteres) a serem
# entregues à camada 5 via entidades do protocolo de transporte dos alunos.
class Msg:
    def __init__(self, data):
        self.data = data  # string de até 20 caracteres


# Um "Pkt" é a unidade de dados passada da camada 4 (código do aluno)
# para a camada 3 (código do professor). Estrutura de pacote pré-definida.
class Pkt:
    def __init__(self, seqnum, acknum, checksum, payload):
        self.seqnum = seqnum
        self.acknum = acknum
        self.checksum = checksum
        self.payload = payload  # string de até 20 caracteres


# Estrutura de evento para simulação
class Event:
    def __init__(self, evtime, evtype, eventity, pktptr=None):
        self.evtime = evtime      # tempo do evento
        self.evtype = evtype      # tipo do evento
        self.eventity = eventity  # entidade onde ocorre o evento
        self.pktptr = pktptr      # ponteiro para pacote (se houver)

#################################################################
# Abaixo está o código que emula o ambiente de rede das camadas 3 e inferiores:
# - Emula a transmissão e entrega (possivelmente com corrupção de bits e perda de pacotes)
#   de pacotes pela interface camada 3/4
# - Gerencia o início/parada de timers e gera interrupções de timer (chamando o handler do aluno)
# - Gera mensagens para serem enviadas (passadas da camada 5 para a 4)
#
# NÃO É NECESSÁRIO QUE O ALUNO LEIA OU MODIFIQUE O CÓDIGO ABAIXO.
# NÃO TOQUE OU REFERENCIE NENHUMA DAS ESTRUTURAS DE DADOS ABAIXO EM SEU CÓDIGO.
# Se quiser entender como o emulador foi projetado, fique à vontade para ler,
# mas não é necessário e definitivamente não deve modificar.
#################################################################

class RDTEmulator:
    def __init__(self):
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


    # jimsrand(): retorna um float no intervalo [0,1].
    # Isola toda a geração de números aleatórios em um só local.
    def jimsrand(self):
        return random.random()


    # Inicializa o simulador
    def init(self):
        print("-----  Emulador Stop and Wait Versão Python -------- \n")
        self.nsimmax = int(input("Digite o número de mensagens para simular: "))
        self.lossprob = float(input("Digite a probabilidade de perda de pacote [0.0 para sem perda]: "))
        self.corruptprob = float(input("Digite a probabilidade de corrupção de pacote [0.0 para sem corrupção]: "))
        self.lambda_ = float(input("Digite o tempo médio entre mensagens da camada 5 [> 0.0]: "))
        self.TRACE = int(input("Digite o nível de TRACE: "))
        random.seed(9999)  # inicializa gerador de números aleatórios
        self.time = 0.0    # inicializa tempo
        self.generate_next_arrival()  # inicializa lista de eventos


    # Gera o próximo evento de chegada da camada 5
    def generate_next_arrival(self):
        x = self.lambda_ * self.jimsrand() * 2  # x é uniforme em [0,2*lambda], média lambda
        evtime = self.time + x
        eventity = B if BIDIRECTIONAL and self.jimsrand() > 0.5 else A
        ev = Event(evtime, FROM_LAYER5, eventity)
        self.insertevent(ev)


    # Insere evento na lista de eventos, ordenando por tempo
    def insertevent(self, event):
        self.evlist.append(event)
        self.evlist.sort(key=lambda e: e.evtime)


    # Inicia timer para retransmissão
    def starttimer(self, AorB, increment):
        evtime = self.time + increment
        ev = Event(evtime, TIMER_INTERRUPT, AorB)
        self.insertevent(ev)


    # Cancela timer previamente iniciado
    def stoptimer(self, AorB):
        self.evlist = [ev for ev in self.evlist if not (ev.evtype == TIMER_INTERRUPT and ev.eventity == AorB)]


    # Envia pacote para a camada 3 (simula perdas e corrupção)
    def tolayer3(self, AorB, packet):
        self.ntolayer3 += 1
        # Simula perdas
        if self.jimsrand() < self.lossprob:
            self.nlost += 1
            if self.TRACE > 0:
                print("          TOLAYER3: pacote perdido")
            return
        # Faz uma cópia do pacote
        mypkt = Pkt(packet.seqnum, packet.acknum, packet.checksum, packet.payload)
        evtime = self.time + 1 + 9 * self.jimsrand()
        eventity = (AorB + 1) % 2
        ev = Event(evtime, FROM_LAYER3, eventity, mypkt)
        # Simula corrupção
        if self.jimsrand() < self.corruptprob:
            self.ncorrupt += 1
            x = self.jimsrand()
            if x < 0.75:
                mypkt.payload = 'Z' + mypkt.payload[1:]
            elif x < 0.875:
                mypkt.seqnum = 999999
            else:
                mypkt.acknum = 999999
            if self.TRACE > 0:
                print("          TOLAYER3: pacote corrompido")
        self.insertevent(ev)


    # Entrega dados à camada 5
    def tolayer5(self, AorB, datasent):
        if self.TRACE > 2:
            print(f"          TOLAYER5: dados recebidos: {datasent}")


    # As próximas sete rotinas devem ser implementadas pelo aluno
    #
    # Chamado pela camada 5, recebe os dados para enviar ao outro lado
    def A_output(self, message):
        pass

    # Chamado pela camada 5, apenas se for modo bidirecional (crédito extra)
    def B_output(self, message):
        pass

    # Chamado pela camada 3, quando um pacote chega para a camada 4
    def A_input(self, packet):
        pass

    # Chamado pela camada 3, quando um pacote chega para a camada 4 em B
    def B_input(self, packet):
        pass

    # Chamado quando o timer de A dispara
    def A_timerinterrupt(self):
        pass

    # Chamado quando o timer de B dispara
    def B_timerinterrupt(self):
        pass

    # Chamado uma vez antes de qualquer rotina de A ser chamada (inicialização)
    def A_init(self):
        pass

    # Chamado uma vez antes de qualquer rotina de B ser chamada (inicialização)
    def B_init(self):
        pass


    # Loop principal do simulador
    def run(self):
        self.init()
        self.A_init()
        self.B_init()
        while True:
            if not self.evlist:
                break
            event = self.evlist.pop(0)  # pega próximo evento
            self.time = event.evtime    # atualiza tempo
            if self.nsim == self.nsimmax:
                break
            if event.evtype == FROM_LAYER5:
                self.generate_next_arrival()  # agenda próxima chegada
                j = self.nsim % 26
                data = chr(97 + j) * 20  # preenche msg com mesma letra
                msg = Msg(data)
                self.nsim += 1
                if event.eventity == A:
                    self.A_output(msg)
                else:
                    self.B_output(msg)
            elif event.evtype == FROM_LAYER3:
                pkt = event.pktptr
                if event.eventity == A:
                    self.A_input(pkt)
                else:
                    self.B_input(pkt)
            elif event.evtype == TIMER_INTERRUPT:
                if event.eventity == A:
                    self.A_timerinterrupt()
                else:
                    self.B_timerinterrupt()
            else:
                print("ERRO INTERNO: tipo de evento desconhecido")
        print(f"Simulador encerrado no tempo {self.time} após enviar {self.nsim} mensagens da camada 5")

if __name__ == "__main__":
    emulator = RDTEmulator()
    emulator.run()
