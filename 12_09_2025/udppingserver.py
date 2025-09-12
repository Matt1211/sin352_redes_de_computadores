# UDPPingerServer.py
# Precisaremos do seguinte módulo para gerar pacotes perdidos aleatórios
import random
from socket import *
# Cria um socket UDP
# Perceba o uso de SOCK_DGRAM para pacotes UD
serverSocket = socket(AF_INET, SOCK_DGRAM)
# Atribui um endereço IP e número de porta para o socket
serverSocket.bind(('', 12000))
print("O servidor está pronto para receber")
while True:
    message, address = serverSocket.recvfrom(1024)
    # Transforma a mensagem do cliente em maiúsculo
    message = message.upper()
    serverSocket.sendto(message, address)
