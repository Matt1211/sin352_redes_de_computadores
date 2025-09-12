from socket import *
import time

# Create UDP client socket
clientSocket = socket(AF_INET, SOCK_DGRAM)
# Set socket timeout to 1 second
clientSocket.settimeout(1.0)

# Server address
serverName = 'localhost'
serverPort = 12000

# Statistics variables
rtts = []
packets_sent = 0
packets_received = 0

# Configuration
num_pings = 10
max_retries = 3
sequence = 1

while sequence <= num_pings:
    retries = 0
    while retries < max_retries:
        try:
            # Create message ID (4 bytes) and message
            message_id = f'{sequence:04d}'.encode()  # Convert sequence to 4-digit string and encode
            message_content = f'Ping {sequence} {time.time()}'.encode()
            full_message = message_id + message_content
            packets_sent += 1
            
            # Record start time
            start_time = time.time()
            
            # Send message to server
            clientSocket.sendto(full_message, (serverName, serverPort))
            
            # Receive response from server
            modifiedMessage, serverAddress = clientSocket.recvfrom(1024)
            
            # Extract message ID and response content
            received_id = modifiedMessage[:4].decode()
            response = modifiedMessage[4:].decode()
            
            # Verify message ID matches before processing response
            if received_id != f'{sequence:04d}':
                print(f'ID da mensagem não corresponde: esperado {sequence:04d}, recebido {received_id}')
                continue

            # Check if response is ACK or NACK
            if response.startswith('ACK'):
                # Calculate RTT
                rtt = time.time() - start_time
                rtts.append(rtt)
                packets_received += 1
                
                # Print server response and RTT
                print(f'Resposta do servidor: {response}')
                print(f'RTT: {rtt:.6f} segundos\n')
                break  # Success, move to next sequence
            
            elif response.startswith('NACK'):
                print(f'NACK recebido para Ping {sequence}, tentativa {retries + 1}')
                retries += 1
                if retries == max_retries:
                    print(f'Ping {sequence}: Máximo de tentativas atingido\n')
            
        except timeout:
            print(f'Ping {sequence}: Timeout na tentativa {retries + 1}')
            retries += 1
            if retries == max_retries:
                print(f'Ping {sequence}: Máximo de tentativas atingido\n')

    time.sleep(2)  # Wait for 2 seconds before next ping
    sequence += 1

# Calculate statistics
if rtts:
    min_rtt = min(rtts)
    max_rtt = max(rtts)
    avg_rtt = sum(rtts) / len(rtts)
    packet_loss = ((packets_sent - packets_received) / packets_sent) * 100
    
    print("---- Estatísticas do Ping ----")
    print(f"Pacotes: Enviados = {packets_sent}, Recebidos = {packets_received}, "
          f"Perdidos = {packets_sent - packets_received} ({packet_loss:.1f}% de perda)")
    print(f"RTT min/med/max = {min_rtt*1000:.3f}/{avg_rtt*1000:.3f}/{max_rtt*1000:.3f} ms")
else:
    print("Nenhum pacote recebido - não é possível calcular estatísticas")

# Close the socket
clientSocket.close()