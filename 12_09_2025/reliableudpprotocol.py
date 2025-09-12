import random
from socket import *
import time

serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('', 12000))
serverSocket.settimeout(1.0)  # 1 second timeout
print("O servidor está pronto para receber")

def process_message(message):
    # Simula a perda de pacotes com uma probabilidade de 39%
    if random.random() < 0.39:
        return None  # Simula perda de pacote
    return message.upper()

while True:
    try:
        message, address = serverSocket.recvfrom(1024)
        message_id = message[:4]  # Primeiros 4 bytes para ID
        payload = message[4:]     # Resto da mensagem
        
        # Processa a mensagem
        result = process_message(payload)
        
        if result is None:
            # Envia NACK
            response = message_id + b'NACK'
            print(f"Enviando NACK para mensagem {message_id}")
        else:
            # Envia ACK com a resposta
            response = message_id + b'ACK' + result
            print(f"Enviando ACK para mensagem {message_id}")
        
        serverSocket.sendto(response, address)
        
    except timeout:
        continue
    except Exception as e:
        print(f'Erro: {e}')