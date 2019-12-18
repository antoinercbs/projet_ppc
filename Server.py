import socket
import pickle
import sys
import traceback
import time
import random
from threading import Thread
from ServerBoardManager import Board


class Server:

    def __init__(self, nb_players):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.bind(('127.0.0.1', 8888))
        except:
            print("Bind failed. Error : " + str(sys.exc_info()))
            sys.exit()
        self.wait_for_connections(nb_players)
        self.board_manager = Board('Toto')

    def wait_for_connections(self, nb_connections):
        self.socket.listen(5)
        connections_count = 0
        while connections_count != nb_connections:
            client, address = self.socket.accept()
            print("{} connected".format(address))

            try:
                Thread(target=self.client_thread, args=(connections_count, client, address)).start()
            except:
                print("Thread did not start.")
                traceback.print_exc()
            connections_count += 1
        self.socket.settimeout(0.05)

    def client_thread(self, client_id, connection, address):
        is_active = True
        ip = address[0]
        port = address[1]

        while is_active:
            try:
                client_input = pickle.loads(connection.recv(5000))
                self.board_manager.update_player_hand_from_move(client_id, client_input)
            except:
                pass
            connection.send(pickle.dumps(self.board_manager.get_client_data_for(client_id)))
            #Gère la réception des données de jeu
            if "--QUIT--" in client_input:
                connection.close()
                print("Connection " + ip + ":" + port + " closed")
                is_active = False
                self.socket.close()
            else: #TODO : Traitement des données venant joueur
                print("Processed result: {}".format(client_input))


if __name__ == "__main__":
    serv = Server(1)