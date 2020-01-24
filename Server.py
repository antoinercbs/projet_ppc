import socket
import pickle
import sys
import traceback
import threading
from threading import Thread, RLock, Timer
from ServerBoardManager import BoardManager


class Server:
    """
    Serveur de gestion du jeu. Gère les connexions avec les clients et leurs interractions avec le plateau de jeu
    """

    board_lock = RLock()  # Verrou sur toutes les actions touchant le plateau de jeu

    def __init__(self, nb_players, ip, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.bind((ip, port))  # Créée le socket côté serveur
        except:
            print("Echec d'instanciation du serveur avec les paramètres donnés. Erreur : " + str(sys.exc_info()))
            sys.exit()
        self.name_list = []  # liste des pseudos des joueurs
        self.player_threads = []  # listes des threads associés aux joueurs
        self.clients = [] # listes des sockets de chaque client
        self.is_game_running = False  # variable indiquant si le jeu est lancé
        self.nb_players = nb_players  # nombre de joueurs
        self.board_manager = None  # gestionnaire de plateau de jeu, instancié après les connexions joueurs
        self.timeout_thread = Thread(target=self.play_timeout_updater_thread) # thread de gestions de pioche auto

        self.wait_for_connections(nb_players)  # On attend qu'un nombre donné de joueurs se connecte
        for thread in self.player_threads:  # Une fois tout le monde connecté, on lance un thread de gestion/joueur
            thread.start()
        self.timeout_thread.start()  # On lance un thread périodique gérant les timeouts

    def wait_for_connections(self, nb_connections):
        """
        Thread attendant pour un nombre de connexions TCP/IP donné et associant à chaque joueur se connectant un thread
        de gestion dédié.
        :param nb_connections: Nombre de connexion à attendre
        :return: None
        """
        self.socket.listen(5)
        connections_count = 0
        while connections_count != nb_connections:  # Tant que tous les joueurs ne sont pas là
            client, address = self.socket.accept()  # On attend une connexion
            try:  # Dès qu'un joueur se connecte, sa gestion est transférée à un thread dédié
                client.setblocking(False)
                client.settimeout(0.05)
                self.clients.append(client)
                print("{} vient de se connecter.".format(address))
                thread = Thread(target=self.client_thread, args=(connections_count, client))
                self.player_threads.append(thread)
            except:
                traceback.print_exc()
            connections_count += 1

    def play_timeout_updater_thread(self):
        """
        Thread s'executant periodiquement (4Hz) de façon récursive et qui gère la pioche automatique sur critère de temps
        :return: None
        """
        self.timeout_thread = threading.current_thread()
        with self.board_lock:
            if self.is_game_running:
                winner = self.board_manager.update_players_hands_from_timeout()
                self.manage_endgame(winner)
                Timer(0.25, self.play_timeout_updater_thread).start()

    def client_thread(self, client_id, connection):
        """
        Threed de gestion des interractions avec un client. Ce thread existe autant de fois qu'il y a de clients.
        Dans un premier temps on attend les pseudos de chaque joueur.
        Une fois que tout le monde a renseigné son pseudo (et est donc connecté), on lance la partie :
            On envoie périodiquement l'état du plateau de jeu et on écoute pour voir s'il y a une éventuelle entrée.
            On utilise un verrou RLock pour éviter les accès concurents et les effets de bord sur le plateau de jeu.
        :param client_id: l'ID du client auquel ce thread est associé
        :param connection: le socket associé à ce client
        :return: None
        """
        while not self.is_game_running:  # Avant l'initialisation du jeu, on attend les pseudos de chacun
            try:
                name_client_input = pickle.loads(connection.recv(5000))
                with self.board_lock:
                    self.name_list.insert(client_id, name_client_input)
                    if len(self.name_list) == self.nb_players and self.board_manager is None:  # Si tous les joueurs sont connectés
                        self.board_manager = BoardManager(*self.name_list)
                        self.is_game_running = True  # Lance le jeu, variable commune à tous les threads.
            except ConnectionAbortedError:  # Si un joueur se déconnecte, on déconnecte tout proprement
                self.manage_disconnection(client_name=self.name_list[client_id])
            except:
                pass
        while self.is_game_running:  # Une fois que tous les pseudos sont donnés, on lance le jeu
            try:
                with self.board_lock:
                    connection.send(pickle.dumps(self.board_manager.get_client_data_for(client_id)))
                    (played_card, played_pos) = pickle.loads(connection.recv(5000))  # On écoute pendant 50ms pour une entrée de ce client
                    winner = self.board_manager.update_player_hand_from_move_on(client_id, played_card, played_pos)
                    self.manage_endgame(winner)
            except ConnectionAbortedError:  # Si un joueur se déconnecte
                self.manage_disconnection(client_name=self.name_list[client_id])
            except:
                pass

    def manage_disconnection(self, client_name="", origin=""):
        """
        Gère la procédure de fermeture du serveur qui intervient dès qu'on détecte une déconnexion ou à la fin de la
        partie. On ferme toute les connexions et on arrête le serveur.
        :param origin: Origine de l'appel
        :param client_name: Client à l'origine de la déconnexion, s'il y a.
        :return:
        """
        self.is_game_running = False
        if client_name != "":
            print("{} s'est déconnecté.".format(client_name))
        elif origin == 'endgame':
            print("Déconnexion demandée : fin de partie fin de partie.")
        print('Arrêt de tous les threads de gestion du jeu')


        print('Fermeture du socket TCP/IP')
        self.socket.close()
        print('Arrêt du serveur.')
        sys.exit(1)

    def manage_endgame(self, winner):
        """
        Détecte et gère la fin de jeu.
        On détermine dans un premier temps le gagnant (-1 si personne) puis on envoie un message sous forme de string
        à tous les clients indiquant le nom du gagnant. Dès qu'un client récupère ce str, il répond avec un bool (qu'on
        attend) indiquant si on rejoue ou non. Si on rejoue. On relance la partie, sinon on lance la procedure de fermeture.
        :param winner: le joueur gagnant (None si partie non finie, -1 si personne)
        :return: None
        """
        if winner is not None:
                winner_name = "Le jeu" if winner == -1 else winner.nickname
                print("Le gagnant est {}".format(winner_name))
                for client in self.clients:
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
                    self.manage_disconnection(origin='endgame')

