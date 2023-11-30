import socket

class TicTacToeClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client_socket = None
        self.client_id = None
        self.symbol = None

    def start(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            self.send_message("CONNECT")
            self.receive_messages()
        except Exception as e:
            print("Error connecting to the server:", e)

    def send_message(self, message):
        self.client_socket.send(message.encode('utf-8'))

    def receive_messages(self):
        while True:
            try:
                data = self.client_socket.recv(1024).decode('utf-8')
                print(data)
                if "won" in data or "lost" in data or "tie" in data:
                    print("Would you like to play again?")
                    selection = input("Enter 1 to play again, or 0 to quit: ")
                    if selection == "1":
                        self.send_message("RESTART")
                    else:
                        self.send_message("QUIT")
                elif "You are player" in data:
                    self.client_id = int(data.split()[3])
                    self.symbol = data.split()[-1]
                elif "Your turn!" in data:
                    self.make_move()
                elif "Invalid" in data:
                    self.make_move()
                elif "Over" in data:
                    return
            except Exception as e:
                print("Error receiving message:", e)
                self.close_connection()
                break

    def make_move(self):
        move = input("Enter your move (1-9): ")
        self.send_message(str('MOVE ' + move))

    def close_connection(self):
        if self.client_socket:
            self.client_socket.close()
        print("Connection closed.")


if __name__ == '__main__':
    import sys

    if len(sys.argv) != 2:
        print("Usage: python TicTacToeClient.py <port_number>")
        sys.exit(1)

    port = int(sys.argv[1])
    client = TicTacToeClient('localhost', port)
    client.start()
