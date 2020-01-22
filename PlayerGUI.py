from tkinter import *
from functools import partial
from threading import RLock
import queue

from ClientPlayer import ClientData


class PlayerGUI:

    gui_update_lock = RLock()

    def __init__(self, client_data, card_play_queue, tk_root):
        self.card_play_queue = card_play_queue
        self.selected_card = None

        self.window = tk_root
        self.window.title('Freak out ! - PPC Project - Falk & Rochebois - 3TC 2020')

        self.cv = Canvas(self.window, width=1100, height=900, bg='green')
        self.draw_game(client_data)
        self.cv.pack()

    def on_click(self, *args):
        nature = args[0]
        if nature == 'player_hand':
            card = args[1]
            self.selected_card = card;
        elif nature == 'grid_card' and self.selected_card is not None:
            pos = args[2]
            self.card_play_queue.put((self.selected_card, pos))
            self.selected_card = None
        elif nature == 'grid':
            pos = args[1]
            self.card_play_queue.put((self.selected_card, pos))
            self.selected_card = None

    def draw_game(self, client_data):
        self.cv.delete("all")
        with PlayerGUI.gui_update_lock:
            self.draw_grid(200, 50, client_data.current_grid)
            self.draw_deck(60, 630, client_data.deck_size)
            self.draw_player_hand(60, 790, client_data.player_hand)
            if len(client_data.other_players) >=1:
                self.draw_other_player_hand(30, 170, client_data.other_players[0])
            if len(client_data.other_players) >=2:
                self.draw_other_player_hand(950, 170, client_data.other_players[1])

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
            self.draw_card(x + i * 90, y, player_hand[i], nature='player_hand')

    def draw_grid(self, x, y, card_grid):
        for i in range(len(card_grid)):
            for j in range(len(card_grid[0])):
                cur_x =x+100*i
                cur_y =y+100*j
                case = self.cv.create_rectangle(cur_x, cur_y, cur_x + 100, cur_y + 100, outline = 'white', width = 3, fill = 'green')
                self.cv.tag_bind(case, "<Button-1>", partial(self.on_click, 'grid', (i,j)))
                if card_grid[i][j] is not None:
                    self.draw_card(cur_x+10, cur_y+10, card_grid[i][j], nature='grid_card', grid_x=i, grid_y=j)

    def draw_card(self, x, y, card, nature=None, grid_x=None, grid_y=None):
        card_color = card[0]
        card_value = card[1]
        rect = self.cv.create_rectangle(x, y, x + 80, y + 80, outline='white', fill=card_color, width=5)
        text = self.cv.create_text(x + 40, y + 40, text=str(card_value), fill='white', font=('Arial', 50))
        if nature is not None:
            self.cv.tag_bind(rect, "<Button-1>", partial(self.on_click, nature, card, (grid_x, grid_y)))
            self.cv.tag_bind(text, "<Button-1>", partial(self.on_click, nature, card, (grid_x, grid_y)))


if __name__ == "__main__":
    card_play_queue = queue.Queue()
    client_data = ClientData()
    tk_root = Tk()
    gui = PlayerGUI(client_data, card_play_queue, tk_root)
    gui.draw_game(client_data)
    tk_root.mainloop()