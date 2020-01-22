from threading import Thread
import queue
from tkinter import *
import socket
import pickle
from tkinter import messagebox


class ClientData:
    def __init__(self):
        grid_size = 7
        self.player_hand = [('blue', 9), ('red', 1), ('red', 10), ('red', 2), ('red', 3)]
        self.current_grid = [[None for i in range(grid_size)] for j in range(grid_size)]
        self.current_grid[3][3] = ('blue', 9)
        self.current_grid[2][1] = ('red', 5)
        self.other_players = [('Toto', 5), ('Tata', 3)]
        self.deck_size = 4


from PlayerGUI import PlayerGUI


class ClientPlayer:
    def __init__(self, nickname, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.connect((host, port))
            print('connection on {}'.format(port))
            self.socket.send(pickle.dumps(nickname))
        except:
            print("Connection error")
            sys.exit()
        self.socket.settimeout(0.05)

        self.data_queue = queue.Queue()
        self.card_play_queue = queue.Queue()
        self.client_data = ClientData()
        self.tk_root = Tk()
        self.tk_root.protocol("WM_DELETE_WINDOW", self.kill_application)
        self.gui = PlayerGUI(self.client_data, self.card_play_queue, self.tk_root)

        self.is_running = True
        self.socket_thread = Thread(target=self.socket_interface)
        self.socket_thread.start()
        self.periodical_gui_refresh()

        self.tk_root.mainloop()

    def socket_interface(self):  # Fonction executée sur un thread par le constructeur
        while self.is_running:  # Tant que le programme est en cours d'execution
            try:
                msg = pickle.loads(self.socket.recv(5000))  # On essaye de lire le message
                if isinstance(msg, str):
                    root = Tk()
                    root.withdraw()
                    replay = messagebox.askyesno("Partie terminée !", "{} a gagné ! Voulez vous rejouer ?".format(msg))
                    self.socket.send(pickle.dumps(replay))
                elif isinstance(msg, ClientData):
                    self.data_queue.put(msg)  # Si on en reçoit un, on le transmet à l'interface par la queue
            except:
                pass
            while self.card_play_queue.qsize():  # Tant qu'on a des messages dans la queue venant dans l'interface
                try:  # On envoie ces messages (cartes à jouer) sur au serveur par le socket
                    played_move = self.card_play_queue.get()
                    self.socket.send(pickle.dumps(played_move))
                except queue.Empty:
                    pass

    # NB : Ces deux méthodes sont brouillons et leur séparation gagnerait à être clarifiée
    def periodical_gui_refresh(self):
        """Met à jour périodiquement (50ms) le jeu avec les données arrivant ou ferme le jeu"""
        self.data_incoming()
        if not self.is_running:
            self.socket.close()
            sys.exit(1)
        self.tk_root.after(50, self.periodical_gui_refresh)

    def data_incoming(self):
        """Fonction mettant à jour l'interface si des données sont présente dans la queue correspondante."""
        while self.data_queue.qsize():
            try:
                msg = self.data_queue.get()
                self.gui.draw_game(msg)
            except queue.Empty:
                pass

    def kill_application(self):
        print("Arrêt du client.")
        self.is_running = False
