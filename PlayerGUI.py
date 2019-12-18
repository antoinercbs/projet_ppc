from tkinter import *
from functools import partial
import sys
from threading import Thread, RLock
import queue


class PlayerGUI:

    gui_update_lock = RLock()

    def __init__(self, client_data, card_play_queue, tk_root):
        self.card_play_queue = card_play_queue
        self.window = tk_root
        self.window.title('Freak out ! - PPC Project - Falk & Rochebois - 3TC 2020')

        self.cv = Canvas(self.window, width=1020, height=640, bg='green')


        self.cv.pack()

    def draw_game(self, client_data):
        self.cv.delete("all")
        with PlayerGUI.gui_update_lock:
            self.draw_card(250, 240, client_data.current_card)
            self.draw_deck(390, 240, client_data.deck_size)
            self.draw_player_hand(140, 500, client_data.player_hand)
            if len(client_data.other_players) >=1:
                self.draw_other_player_hand(20, 170, client_data.other_players[0])
            if len(client_data.other_players) >=2:
                self.draw_other_player_hand(580, 170, client_data.other_players[1])

    def draw_other_player_hand(self, x, y, player_infos):
        name = player_infos[0]
        self.cv.create_text(x+20, y-50, text=name, font=('Arial', 20))
        card_count = player_infos[1]
        for i in range(card_count):
            self.cv.create_rectangle(x, y + i * 50, x + 120, y + 80 + i * 50, outline='white', fill='red', width=5)

    def draw_deck(self, x, y, deck_size):
        self.cv.create_rectangle(x, y, x + 80, y + 120, outline='white', fill='black', width=5)
        self.cv.create_text(x + 40, y + 60, text=str(deck_size), fill='white', font=('Arial', 50))

    def draw_player_hand(self, x, y, player_hand):
        for i in range(len(player_hand)):
            self.draw_card(x + i * 90, y, player_hand[i], clickable=True)

    def on_click(self, *args):
        card = args[0]
        self.card_play_queue.put(card)

    def draw_card(self, x, y, card, clickable=False):
        card_color = card[0]
        card_value = card[1]
        rect = self.cv.create_rectangle(x, y, x + 80, y + 120, outline='white', fill=card_color, width=5)
        text = self.cv.create_text(x + 40, y + 60, text=str(card_value), fill='white', font=('Arial', 50))
        if clickable:
            self.cv.tag_bind(rect, "<Button-1>", partial(self.on_click, card))
            self.cv.tag_bind(text, "<Button-1>", partial(self.on_click, card))
