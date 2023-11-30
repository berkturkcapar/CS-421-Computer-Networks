import socket
import threading

class TicTacToeServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = None
        self.client_connections = []
        self.client_addresses = []
        self.score = [0, 0]
        self.restartStatus = [False, False]
        self.board = [[' ' for _ in range(3)] for _ in range(3)]
        self.player_symbols = ['X', 'O']
        self.current_turn = 0

    def initialize_parameters(self):
        self.restartStatus = [False, False]
        self.board = [[' ' for _ in range(3)] for _ in range(3)]
        self.current_turn = 0
    
    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(2)
        print("Server started. Waiting for connections...")
        for client_socket in self.client_connections:
            client_socket.close()

        while len(self.client_connections) < 2:
            client_socket, client_address = self.server_socket.accept()
            self.client_connections.append(client_socket)
            self.client_addresses.append(client_address)
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()
            print(f"Thread for Player {self.client_connections.index(client_socket)} started.")

        self.start_game()

    def handle_client(self, client_socket):
        try:
            client_id = self.client_connections.index(client_socket)
            print(f"A client is connected, and it is assigned with the symbol {self.player_symbols[client_id]} and ID={client_id}")
            self.send_message(client_socket, f"You are player {client_id} with symbol {self.player_symbols[client_id]}")
        except Exception as e:
            print("Error handling client:", e)
            self.disconnect_client(client_socket)

        while True:
            try:
                data = client_socket.recv(1024).decode('utf-8')
                if data.startswith('MOVE'):
                    # to check the case in which the player only presses enter without any input
                    if len(data.split()) != 2:
                        move = ""
                    else:
                        move = data.split()[1]
                    self.process_move(client_socket, move)
                elif data.startswith('QUIT'):
                    print("Player", client_id, "quitted!")
                    print(f"The final score is: \nPlayer 0: {self.score[0]}\nPlayer 1: {self.score[1]}\n----- Game Over -----")
                    self.send_message(
                        self.client_connections[client_id], 
                        f"You Quitted!\nThe final score is: \nPlayer 0: {self.score[0]}\nPlayer 1: {self.score[1]}\n----- Game Over -----")
                    self.send_message(
                        self.client_connections[1 - client_id], 
                        f"The other player quitted!\nThe final score is: \nPlayer 0: {self.score[0]}\nPlayer 1: {self.score[1]}\n----- Game Over -----")
                    self.disconnect_clients()
                    return
                elif data.startswith('RESTART'):
                    self.restartStatus[client_id] = True
                    print("Player", client_id, "wants to restart!")
                    if self.restartStatus[0] and self.restartStatus[1]:
                        print("Restarting game...")
                        self.start_game()
                    else:
                        self.send_message(self.client_connections[client_id], "Waiting for the other player's decision...")
            except Exception as e:
                self.disconnect_client(client_socket)
                break

    def send_message(self, client_socket, message):
        client_socket.send(message.encode('utf-8'))

    def send_state(self, client_socket):
        client_id = self.client_connections.index(client_socket)
        state = self.get_state()
        turn_message = "Your turn!" if client_id == self.current_turn else "Wait for the other player's move..."
        self.send_message(client_socket, f"\n{state}\n{turn_message}")

    def get_state(self):
        state = '-' * 9 + '\n'
        for row in self.board:
            state += ' | '.join(row) + '\n'
            state += '-' * 9 + '\n'
        return state

    def process_move(self, client_socket, move):
        client_id = self.client_connections.index(client_socket)
        if client_id != self.current_turn:
            self.send_message(client_socket, "Invalid move. It's not your turn.")
            return
        if not move.isdigit() or not move:
            self.send_message(client_socket, "Invalid move. Move must be a number.")
            return
        try:
            move = int(move)
            row = (move - 1) // 3
            col = (move - 1) % 3
            print("Player {} placed a {} at position ({}, {})".format(client_id, self.player_symbols[client_id], row, col))
            if row < 0 or row > 2 or col < 0 or col > 2:
                raise ValueError

            if self.board[row][col] != ' ':
                raise ValueError

            self.board[row][col] = self.player_symbols[client_id]
            self.current_turn = 1 - self.current_turn

            if self.check_winner():
                print("Player", client_id, "wins!")
                self.score[client_id] += 1
                self.send_message(self.client_connections[client_id], "Congratulations! You won!")
                self.send_message(self.client_connections[1 - client_id], "You lost. Better luck next time!")
            elif self.check_tie():
                print("It's a tie!")
                self.send_message(self.client_connections[0], "It's a tie!")
                self.send_message(self.client_connections[1], "It's a tie!")
            else:
                self.send_state_to_all()
        except ValueError:
            print("Illegal move")
            self.send_message(client_socket, "Invalid move. Please change your move.")

    def check_winner(self):
        winning_conditions = [
            ((0, 0), (0, 1), (0, 2)),  # Rows
            ((1, 0), (1, 1), (1, 2)),
            ((2, 0), (2, 1), (2, 2)),
            ((0, 0), (1, 0), (2, 0)),  # Columns
            ((0, 1), (1, 1), (2, 1)),
            ((0, 2), (1, 2), (2, 2)),
            ((0, 0), (1, 1), (2, 2)),  # Diagonals
            ((0, 2), (1, 1), (2, 0))
        ]

        for condition in winning_conditions:
            symbols = [self.board[row][col] for row, col in condition]
            if symbols[0] == symbols[1] == symbols[2] != ' ':
                return True

        return False

    def check_tie(self):
        for row in self.board:
            if ' ' in row:
                return False
        return True

    def send_state_to_all(self):
        print(f"Waiting for Player {self.current_turn}'s move...")
        for client_socket in self.client_connections:
            self.send_state(client_socket)

    def start_game(self):
        self.initialize_parameters()
        print("The game is started.")
        print(f"The current score is: \nPlayer 0: {self.score[0]}\nPlayer 1: {self.score[1]}")
        self.send_message(self.client_connections[0], f"You start the game.\nThe current score is: \nPlayer 0: {self.score[0]}\nPlayer 1: {self.score[1]}")
        self.send_message(self.client_connections[1], f"The other player starts.\nThe current score is: \nPlayer 0: {self.score[0]}\nPlayer 1: {self.score[1]}")
        self.send_state_to_all()

    def disconnect_clients(self):
        for client_socket in self.client_connections:
            client_socket.close()
        self.server_socket.close()
        return

    def disconnect_client(self, client_socket):
        client_id = self.client_connections.index(client_socket)
        client_address = self.client_addresses[client_id]
        self.client_connections.remove(client_socket)
        self.client_addresses.remove(client_address)
        client_socket.close()

if __name__ == '__main__':
    import sys

    if len(sys.argv) != 2:
        print("Usage: python TicTacToeServer.py <port_number>")
        sys.exit(1)

    port = int(sys.argv[1])
    server = TicTacToeServer('localhost', port)
    server.start()
