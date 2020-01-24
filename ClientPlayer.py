from threading import Thread
import queue
from tkinter import *
import socket
import pickle
from tkinter import messagebox


class ClientData:
    """
    Classe définissant le format des données de jeu intelligibles par le client. C'est sous cette forme que transite
    l'information entre serveur et client.
    Le remplissage par défaut fait office d'écran d'attente lors de l'attente de connexion des joueurs
    """
    def __init__(self):
        grid_size = 7
        self.player_hand = [('red', 1), ('orange', 2), ('yellow', 3), ('green', 4), ('blue', 5), ('purple', 6)]
        self.current_grid = [[None for _ in range(grid_size)] for _ in range(grid_size)]
        self.other_players = [('En attente...', 5), ('En attente...', 5)] # Nom et nombre de cartes en main
        self.deck_size = 42


from PlayerGUI import PlayerGUI


class ClientPlayer:
    """
    Classe gérant le processus côté client
    """
    def __init__(self, nickname, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try: # Initialisation de la connexion
            self.socket.connect((host, port))
            print('connection on {}'.format(port))
            self.socket.send(pickle.dumps(nickname))
        except:
            print("Connection error")
            sys.exit()
        self.socket.settimeout(0.05) # Pour éviter d'attendre indéfiniment qu'un joueur joue

        self.board_data_queue = queue.Queue() # Queue des infos allant vers l'interface de jeu (ClientData)
        self.card_play_queue = queue.Queue() # Queue des infos venant de l'interface (consigne du joueur)
        self.client_data = ClientData()
        self.tk_root = Tk()  # Initialisation de l'instance de l'interface
        self.tk_root.protocol("WM_DELETE_WINDOW", self.kill_application)
        self.gui = PlayerGUI(self.client_data, self.card_play_queue, self.tk_root)

        self.is_running = True
        self.socket_thread = Thread(target=self.socket_interface)  # Lancement du thread de dialogue avec le serv
        self.socket_thread.start()
        self.periodical_gui_refresh()  # On gère les consignes à l'IHM sur ce thread (TKinter génèrera lui même un autre thread)

        self.tk_root.mainloop()

    def socket_interface(self):  # Fonction executée sur un thread par le constructeur
        """
        Fonction gérant les échanges entre le serveur et le client en faisant les transitions entre les queues et le socket
        C'est également cette fonction qui gère l'affichage du gagant et la gestion du rematch.
        :return: None
        """
        while self.is_running:  # Tant que le programme est en cours d'execution
            try:
                msg = pickle.loads(self.socket.recv(5000))  # On essaye de lire le message*
                if isinstance(msg, str):
                    replay = messagebox.askyesno("Partie terminée !", "{} a gagné ! Voulez vous rejouer ?".format(msg))
                    self.socket.send(pickle.dumps(replay))
                elif isinstance(msg, ClientData):
                    self.board_data_queue.put(msg)  # Si on en reçoit un, on le transmet à l'interface par la queue
            except ConnectionAbortedError: #Si le serveur se déconnecte, on arrête le client
                self.kill_application()
            except:
                pass
            while self.card_play_queue.qsize():  # Tant qu'on a des messages dans la queue venant dans l'interface
                try:  # On envoie ces messages (cartes à jouer) sur au serveur par le socket
                    played_move = self.card_play_queue.get()
                    self.socket.send(pickle.dumps(played_move))
                except ConnectionAbortedError:  # Si le serveur se déconnecte, on arrête le client
                    self.kill_application()
                except queue.Empty:
                    pass

    # NB : Ces deux méthodes sont brouillons et leur séparation gagnerait à être clarifiée
    def periodical_gui_refresh(self):
        """Met à jour périodiquement (50ms) le jeu avec les données arrivant ou ferme le jeu"""
        self.gui_refresh()
        if not self.is_running:
            sys.exit(1)  # Fermer ici est préconnisé par la doc tkinter
        self.tk_root.after(50, self.periodical_gui_refresh)

    def gui_refresh(self):
        """Fonction mettant à jour l'interface si des données sont présente dans la queue correspondante.
        On attend qu'il y ait un message dans la queue des données plateaux et on s'en sert pour mettre à jour l'interface
        """
        while self.board_data_queue.qsize():
            try:
                msg = self.board_data_queue.get()
                self.gui.draw_game(msg)
            except queue.Empty:
                pass

    def kill_application(self):
        """
        Arrête le socket et donne l'ordre d'arrêter le client.
        :return:
        """
        print("Fermeture du socket client.")
        self.socket.close()
        self.is_running = False
        print('Arrêt du client.')

