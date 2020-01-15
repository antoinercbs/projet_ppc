import random
import time
from ClientPlayer import ClientData


class ServerPlayer:

    def __init__(self, nickname, hand):
        self.nickname = nickname
        self.hand = hand
        self.lastMoveTime = time.time()

    def update_last_move_time(self):
        self.lastMoveTime = time.time()

    def is_last_move_time_greater_than(self, delay):
        return time.time() - self.lastMoveTime >= delay


class BoardManager:

    def __init__(self, *player_names):
        self.available_colors=['red','blue']
        self.available_values=[i for i in range(1,10)]
        self.available_cards=[]
        for color in self.available_colors :
            for value in self.available_values :
                self.available_cards+=[(color,value)]
        self.deck = BoardManager.generate_shuffled_deck(self.available_colors, self.available_values)
        self.size_grid = 7
        self.grid = [[None]*self.size_grid for i in range(self.size_grid)]
        self.grid[self.size_grid//2][self.size_grid//2] = self.deck.pop()
        self.players = [ServerPlayer(player_names[j], [self.deck.pop() for i in range(5)]) for j in
                        range(len(player_names))]

    @staticmethod
    def generate_shuffled_deck(colors,values):
        deck=[]
        for color in colors :
            for value in values :
                deck+=[(color,value)]
        random.shuffle(deck)
        return deck

    def update_player_hand_from_move_on(self, player_id, played_card, played_pos):
        """
        Tente le dépot d'une carte sur une case par un joueur.
        Si le coup est permis, la carte est enlevée de la main de ce joueur et est posée sur la grille.
        Sinon, le joueur prend une carte du deck dans sa main.
        """
        x, y = played_pos
        if self.is_card_playable_on(x,y,played_card):   #Teste si la carte peut être posée
            self.players[player_id].hand.remove(played_card)    #Si oui, on enlève la carte de la main
            self.grid[x][y]=played_card  #Et on la pose sur le plateau
            print(self.players[player_id].hand)
        else:
            self.players[player_id].hand.append(self.deck.pop())    #Sinon il pioche

    def is_box_filled(self,x,y):
        return self.grid[x][y]!=None

    def is_box_empty(self,x,y):
        return self.grid[x][y]==None

    def is_index_not_out_of_range(self,a):
        return a % (self.size_grid-1) == a

    def get_number_of_filled_neighbour(self,x,y):
        filled_neighbour=0
        if self.is_index_not_out_of_range(x-1):
            if self.is_box_filled(x-1,y):
                filled_neighbour+=1
        if self.is_index_not_out_of_range(x+1):
            if self.is_box_filled(x+1,y):
                filled_neighbour+=1
        if self.is_index_not_out_of_range(y-1):
            if self.is_box_filled(x,y-1):
                filled_neighbour+=1
        if self.is_index_not_out_of_range(y+1):
            if self.is_box_filled(x,y+1):
                filled_neighbour+=1
        return filled_neighbour

    def is_box_playable(self,x,y):
        if self.is_box_empty(x,y):
            return self.get_number_of_filled_neighbour(x,y)>=1
        else :
            return self.get_number_of_filled_neighbour(x,y)==1

    def get_color_of(self,x,y):
        return self.grid[x][y][0]

    def get_value_of(self,x,y):
        return self.grid[x][y][1]

    def is_card_playable_on(self, x, y, played_card):
        """
        Simule le dépot d'une carte à une position (x,y)
        Renvoie True si le coup est permis, False sinon.
        """
        if self.is_box_playable(x,y):  #Si la case est jouable
            if self.is_box_filled(x,y):  #Si la case est déjà remplie
                if self.get_color_of(x,y) == played_card[0]:   #Si la couleur de la carte déjà posée est différente de celle de la carte à poser
                    return False
                else :
                    return self.get_value_of(x,y) == played_card[1] #On retourne True si la valeur de la carte déjà posée est la même que celle de la carte à poser
            else :  #Si la case est vide
                return played_card in self.get_cards_playable(x,y)  #On regarde si la carte respecte les règles
        else :
            return False

    def get_cards_playable(self,x,y):
        """
        Cette méthode est appelée sur une position vide et jouable de la grille.
        Elle renvoie l'ensemble des cartes pouvant être posées en respectant les règles du jeu

        On parcours la liste des cartes du jeux
        On défini comme impossible les cartes qui ont :
        -Une couleur différente de celle de la carte de droite, de gauche, du haut ou du bas
        -Une valeur différente de la valeurs ± 1 de celle de la carte de droite, de gauche, du haut ou du bas
        """
        impossible_cards=[]

        if self.is_index_not_out_of_range(x-1):
            if self.is_box_filled(x-1,y):
                impossible_cards+=[card for card in self.available_cards if card[0]!=self.get_color_of(x-1,y) or card[1]!=(self.get_value_of(x-1,y)-1) and card[1]!=(self.get_value_of(x-1,y)+1)]
        if self.is_index_not_out_of_range(x+1):
            if self.is_box_filled(x+1,y):
                impossible_cards+=[card for card in self.available_cards if card[0]!=self.get_color_of(x+1,y) or card[1]!=(self.get_value_of(x+1,y)-1) and card[1]!=(self.get_value_of(x+1,y)+1)]
        if self.is_index_not_out_of_range(y-1):
            if self.is_box_filled(x,y-1):
                impossible_cards+=[card for card in self.available_cards if card[0]!=self.get_color_of(x,y-1) or card[1]!=(self.get_value_of(x,y-1)-1) and card[1]!=(self.get_value_of(x,y-1)+1)]
        if self.is_index_not_out_of_range(y+1):
            if self.is_box_filled(x,y+1):
                impossible_cards+=[card for card in self.available_cards if card[0]!=self.get_color_of(x,y+1) or card[1]!=(self.get_value_of(x,y+1)-1) and card[1]!=(self.get_value_of(x,y+1)+1)]

        #On retourne toutes les cartes du jeu qui ne sont pas impossibles
        return [card for card in self.available_cards if not card in impossible_cards]

    def is_game_over(self):
        for hand in self.players.hand:
            if len(hand) == 0:
                return True
        return len(self.deck) == 0

    def get_winner(self):
        for p in self.players:
            if len(p.hand) == 0:
                return p
        return None

    def get_client_data_for(self, player_id):
        cdata = ClientData()
        cdata.player_hand = self.players[player_id].hand
        cdata.current_grid = self.grid
        cdata.deck_size = len(self.deck)
        cdata.other_players.clear()
        for i in range(len(self.players)):
            if i != player_id:
                cdata.other_players.append((self.players[i].nickname, len(self.players[i].hand)))
        return cdata


if __name__ == "__main__":
    board = BoardManager('Jean')

    print(board.deck)
    for i in range(board.size_grid):
        for j in range(board.size_grid):
            print(str(i)+"-"+str(j)+" "+str(board.grid[i][j]))
    print(board.players[0].hand)

""" #pour tester, mettre en commentaire random.shuffle(deck)
    board.update_player_hand_from_move_on(3, 3, 0, ('blue',6))
    board.update_player_hand_from_move_on(3, 3, 0, ('blue',6))
    board.update_player_hand_from_move_on(3, 3, 0, ('blue',6))
    board.update_player_hand_from_move_on(3, 3, 0, ('blue',6))
    board.update_player_hand_from_move_on(3, 3, 0, ('blue',6))
    board.update_player_hand_from_move_on(4, 1, 0, ('blue',6))
    board.update_player_hand_from_move_on(3, 3, 0, ('blue',6))
    board.update_player_hand_from_move_on(3, 2, 0, ('blue',8))
    board.update_player_hand_from_move_on(3, 1, 0, ('blue',7))
    board.update_player_hand_from_move_on(4, 1, 0, ('blue',6))
    board.update_player_hand_from_move_on(4, 1, 0, ('red',6))
    board.update_player_hand_from_move_on(4, 2, 0, ('red',7))
    board.update_player_hand_from_move_on(4, 0, 0, ('red',7))
    for i in range(board.size_grid):
        for j in range(board.size_grid):
            print(str(i)+"-"+str(j)+" "+str(board.grid[i][j]))
    print(board.players[0].hand)"""
