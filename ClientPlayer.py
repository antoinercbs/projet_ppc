from threading import Thread
import time
import queue
import random
from PlayerGUI import PlayerGUI
from tkinter import *
import socket
import pickle


class ClientData:
    def __init__(self):
        self.player_hand = [('blue', 9), ('red', 1), ('red', 10), ('red', 2), ('red', 3)]
        self.current_card = ('blue', 5)
        self.other_players = [('Toto', 5), ('Tata',3)]
        self.deck_size = 4


class ClientPlayer:
    def __init__(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.connect((host, port))
            print('connection on {}'.format(port))
        except:
            print("Connection error")
            sys.exit()
        self.socket.settimeout(0.05)

        self.data_queue = queue.Queue()
        self.card_play_queue = queue.Queue()
        self.client_data = ClientData()
        self.tk_root = Tk()
        self.gui = PlayerGUI(self.client_data, self.card_play_queue, self.tk_root)

        self.is_running = True
        self.socket_thread = Thread(target=self.socket_interface)
        self.socket_thread.start()
        self.periodical_gui_refresh()

        self.tk_root.mainloop()

    def socket_interface(self):
        while self.is_running:
            try:
                msg = pickle.loads(self.socket.recv(5000))
                self.data_queue.put(msg)
            except:
                pass
            while self.card_play_queue.qsize():
                try:
                    played_card = self.card_play_queue.get(0)
                    self.socket.send(pickle.dumps(played_card))
                except queue.Empty:
                    pass

    def data_incoming(self):
        """Handle all messages currently in the queue, if any."""
        while self.data_queue.qsize():
            try:
                msg = self.data_queue.get(0)
                self.gui.draw_game(msg)
            except queue.Empty:
                pass

    def periodical_gui_refresh(self):
        self.data_incoming()
        if not self.is_running:
            self.socket.close()
            sys.exit(1)
        self.tk_root.after(50, self.periodical_gui_refresh)

    def kill_application(self):
        self.is_running = False
