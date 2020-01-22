import socket
import pickle
import sys
import traceback
from threading import Thread, RLock, Timer
from ServerBoardManager import BoardManager


class Server:

    def __init__(self, nb_players, ip, port):
        self.timeout_thread = Thread(target=self.play_timeout_updater_thread)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.bind((ip, port))
        except:
            print("Echec d'association. Erreur : " + str(sys.exc_info()))
            sys.exit()
        self.name_list = []
        self.player_threads = []
        self.clients = []
        self.is_game_running = False
        self.nb_players = nb_players
        self.board_lock = RLock()
        self.board_manager = None
        self.wait_for_connections(nb_players)

    def wait_for_connections(self, nb_connections):
        self.socket.listen(5)
        connections_count = 0
        while connections_count != nb_connections:  # Tant que tous les joueurs ne sont pas là
            client, address = self.socket.accept()  # On attend une connexion
            client.setblocking(False)
            client.settimeout(0.05)
            self.clients.append(client)
            print("{} vient de se connecter.".format(address))
            try:  # Dès qu'un joueur se connecte, sa gestion est transférée à un thread dédié
                thread = Thread(target=self.client_thread, args=(connections_count, client))
                self.player_threads.append(thread)
                thread.start()
            except:
                traceback.print_exc()
            connections_count += 1
        self.timeout_thread.start()

    def play_timeout_updater_thread(self):
        if self.is_game_running:
            with self.board_lock:
                winner = self.board_manager.update_players_hands_from_timeout()
                self.manage_endgame(winner)
            Timer(0.25, self.play_timeout_updater_thread).start()

    def client_thread(self, client_id, connection):
        while not self.is_game_running:  # Avant l'initialisation du jeu, on attend les pseudos de chacun
            try:
                name_client_input = pickle.loads(connection.recv(5000))
                with self.board_lock:
                    self.name_list.append(name_client_input)
                    if len(self.name_list) == self.nb_players:  # Si tous les joueurs sont connectés
                        self.board_manager = BoardManager(*self.name_list)
                        self.is_game_running = True  # Lance le jeu, variable commune à tous les threads.
            except ConnectionAbortedError:  # Si un joueur se déconnecte
                self.manage_disconnection(client_name=self.name_list[client_id])
            except:
                pass
        while self.is_game_running:  # Une fois que tous les pseudos sont donnés, on lance le jeu
            try:
                connection.send(pickle.dumps(self.board_manager.get_client_data_for(client_id)))
                (played_card, played_pos) = pickle.loads(connection.recv(5000))  # On écoute pendant 50ms pour une entrée de ce client
                with self.board_lock:
                    winner = self.board_manager.update_player_hand_from_move_on(client_id, played_card, played_pos)
                    self.manage_endgame(winner)
            except ConnectionAbortedError:  # Si un joueur se déconnecte
                self.manage_disconnection(client_name=self.name_list[client_id])
            except:
                pass

    def manage_disconnection(self, client_name=""):
        if client_name != "":
            print("{} s'est déconnecté.".format(client_name))
        else:
            print("Déconnexion d'origine inconnue/fin de partie.")
        print('Arrêt de tous les threads de gestion du jeu')
        self.is_game_running = False
        print('Fermeture du socket TCP/IP')
        self.socket.close()
        print('Arrêt du serveur.')
        sys.exit(1)

    def manage_endgame(self, winner):
        if winner is not None:
            winner_name = "Le jeu" if winner == -1 else winner.nickname
            print("Le gagnant est {}".format(winner_name))
            for client in self.clients:
                print(client)
                client.send(pickle.dumps(winner_name))
            print("Demande de nouvelle partie aux joueurs.")
            replay = None
            while not isinstance(replay, bool):
                try:
                    for client in self.clients:
                        replay = pickle.loads(client.recv(5000))
                        break
                except ConnectionAbortedError:  # Si un joueur se déconnecte
                    self.manage_disconnection()
                except:
                    pass
            if replay:
                print('Le joueur principal lance une nouvelle partie')
                self.board_manager = BoardManager(*self.name_list)
            else:
                print('Le joueur principal a demandé la fin de jeu.')
                self.manage_disconnection()
