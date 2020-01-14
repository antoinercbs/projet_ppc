import socket
import pickle
import sys
import traceback
import time
import random
from threading import Thread
from ServerBoardManager import BoardManager


class Server:

    def __init__(self, nb_players, ip, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.bind((ip, port))
        except:
            print("Bind failed. Error : " + str(sys.exc_info()))
            sys.exit()
        self.name_list = []
        self.is_game_running = False
        self.nb_players = nb_players
        self.board_manager = None
        self.wait_for_connections(nb_players)

    def wait_for_connections(self, nb_connections):
        self.socket.listen(5)
        connections_count = 0
        while connections_count != nb_connections: #Tant que tous les joueurs ne sont pas là
            client, address = self.socket.accept() #On attend une connexion
            print("{} connected".format(address))
            try: #Dès qu'un joueur se connecte, sa gestion est transférée à un thread dédié
                Thread(target=self.client_thread, args=(connections_count, client, address)).start()
            except:
                traceback.print_exc()
            connections_count += 1

    def client_thread(self, client_id, connection, address):
        ip = address[0]
        port = address[1]
        connection.settimeout(0.05) #Bancal, temporaire, pour éviter les blocages d'attente

        while not self.is_game_running: #Avant l'initialisation du jeu, on attend les pseudos de chacun
            try:
                name_client_input = pickle.loads(connection.recv(5000))
                self.name_list.append(name_client_input)
                if len(self.name_list) == self.nb_players:
                    self.board_manager = BoardManager(*self.name_list)
                    self.is_game_running = True #Lance le jeu, variable commune à tous les threads.
            except:
                pass

        while self.is_game_running: #Une fois que tous les pseudos sont donnés, on lance le jeu
            client_input = "" #On envoie périodiquement l'état du plateau au joueur
            connection.send(pickle.dumps(self.board_manager.get_client_data_for(client_id)))
            try:
                client_input = pickle.loads(connection.recv(5000)) #On écoute pendant 50ms pour une entrée de ce client
                self.board_manager.update_player_hand_from_move(client_id, client_input)
            except: #Si on a pas d'entrée joueur durant l'att
                pass

