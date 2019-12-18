import socket
import pickle
import sys
import traceback
import time
import random
from threading import Thread
from ServerBoardManager import Board


class Server:

    def __init__(self, nb_players, ip, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.socket.bind((ip, port))
        except:
            print("Bind failed. Error : " + str(sys.exc_info()))
            sys.exit()
        self.name_list = []
        self.nb_players = nb_players
        self.board_manager = None #TODO : INIT APRES AVEC LA SAISIE NOMS
        self.wait_for_connections(nb_players)


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

    def client_thread(self, client_id, connection, address):
        is_game_running = False
        ip = address[0]
        port = address[1]
        connection.settimeout(0.05)

        while not is_game_running:
            try:
                name_client_input = pickle.loads(connection.recv(5000))
                self.name_list.append(name_client_input)
                if len(self.name_list) == self.nb_players:
                    self.board_manager = Board(self.name_list)
                    is_game_running = True
            except:
                pass

        while is_game_running:
            client_input = ""
            connection.send(pickle.dumps(self.board_manager.get_client_data_for(client_id)))
            try:
                client_input = pickle.loads(connection.recv(5000))
                self.board_manager.update_player_hand_from_move(client_id, client_input)
            except:
                pass
            #Gère la réception des données de jeu
            if "--QUIT--" in client_input:
                connection.close()
                print("Connection " + ip + ":" + port + " closed")
                is_game_running = False
                self.socket.close()
            elif client_input != "": #TODO : Traitement des données venant joueur
                print("Processed result: {}".format(client_input))


if __name__ == "__main__":
    serv = Server(2, 80)