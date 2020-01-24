import random
import time
from ClientPlayer import ClientData


class ServerPlayer:
    """
    Classe gérant le processus côté server
    """

    def __init__(self, nickname, hand):
        """
        Initialisation
        :nickname: str
        :hand: list of tuple as (str,int)
        """
        self.nickname = nickname
        self.hand = hand
        self.lastMoveTime = time.time()

    def update_last_move_time(self):
        """
        Fonction qui actualise le temps du dernier coup du joueur
        """
        self.lastMoveTime = time.time()

    def is_last_move_time_greater_than(self, delay):
        """
        Fonction qui permet de voir si le joueur a dépassé le delai
        :delay: int
        :return: bool
        """
        return time.time() - self.lastMoveTime >= delay


class BoardManager:

    def __init__(self, *player_names):
        """
        Initialisation
        :*player_names: list of str
        """
        self.available_colors = ['red', 'blue']
        self.available_values = [i for i in range(1, 10)]
        self.available_cards = []
        for color in self.available_colors:
            for value in self.available_values:
                self.available_cards += [(color, value)]    #Stock un exemplaire de chaque carte du jeu
        self.deck = BoardManager.generate_shuffled_deck(self.available_colors, self.available_values)
        self.size_grid = 7
        self.grid = [[None] * self.size_grid for i in range(self.size_grid)]  #Tableau 2D
        self.grid[self.size_grid // 2][self.size_grid // 2] = self.deck.pop()      #On place la première carte du deck sur le plateau
        self.players = [ServerPlayer(player_names[j], [self.deck.pop() for i in range(5)]) for j in
                        range(len(player_names))]   #On distribue 5 cartes à chaque joueur

    @staticmethod
    def generate_shuffled_deck(colors, values):
        """
        Fonction générant un deck mélangé
        :colors: list of str
        :value: list of int
        :return: list of tuple as (str,int)
        """
        deck = []
        for color in colors:
            for value in values:
                deck += [(color, value)]
        random.shuffle(deck)
        return deck

    def update_players_hands_from_timeout(self):
        """
        Fonction actualisant la main des joueur après un délai dépassé
        """
        if self.is_game_over():
            return self.get_winner()
        for player in self.players:
            if player.is_last_move_time_greater_than(10):   #si le delai est dépassé
                player.hand.append(self.deck.pop())     #on le fait piocher
                player.update_last_move_time()

    def update_player_hand_from_move_on(self, player_id, played_card, played_pos):
        """
        Fonction qui tente le dépot d'une carte sur une case par un joueur.
        Si le coup est permis, la carte est enlevée de la main de ce joueur et est posée sur la grille.
        Sinon, le joueur prend une carte du deck dans sa main.
        :played_id: int
        :played_card: tuple as (str,int)
        :played_pos: tuple as (int,int)
        """
        (x, y) = played_pos
        if self.is_card_playable_on(x, y, played_card):  # Teste si la carte peut être posée
            self.players[player_id].hand.remove(played_card)  # Si oui, on enlève la carte de la main
            self.grid[x][y] = played_card  # Et on la pose sur le plateau
        else:
            self.players[player_id].hand.append(self.deck.pop())  # Sinon il pioche
        self.players[player_id].update_last_move_time()
        if self.is_game_over():
            return self.get_winner()

    def is_box_filled(self, x, y):
        """
        Fonction qui retourne si une case (x,y) est remplie
        :x: int
        :y: int
        :return: bool
        """
        return self.grid[x][y] is not None

    def is_box_empty(self, x, y):
        """
        Fonction qui retourne si une case (x,y) est vide
        :x: int
        :y: int
        :return: bool
        """
        return self.grid[x][y] is None

    def is_index_not_out_of_range(self, a):
        """
        Fonction qui retourne si un index est utilisable sur le board
        :a: int
        :return: bool
        """
        return a % (self.size_grid - 1) == a

    def get_number_of_filled_neighbour(self, x, y):
        """
        Fonction qui retourne le nombre de voisin de (x,y) qui sont remplies
        :x: int
        :y: int
        :return: int
        """
        filled_neighbour = 0
        if self.is_index_not_out_of_range(x - 1):
            if self.is_box_filled(x - 1, y):
                filled_neighbour += 1
        if self.is_index_not_out_of_range(x + 1):
            if self.is_box_filled(x + 1, y):
                filled_neighbour += 1
        if self.is_index_not_out_of_range(y - 1):
            if self.is_box_filled(x, y - 1):
                filled_neighbour += 1
        if self.is_index_not_out_of_range(y + 1):
            if self.is_box_filled(x, y + 1):
                filled_neighbour += 1
        return filled_neighbour

    def is_box_playable(self, x, y):
        """
        Fonction qui retourne si une case (x,y) est jouable
        :x: int
        :y: int
        :return: bool
        """
        if self.is_box_empty(x, y):
            return self.get_number_of_filled_neighbour(x, y) >= 1   #si la case est vide, il faut au moins 1 voisin
        else:
            return self.get_number_of_filled_neighbour(x, y) <= 1   #Si la case est remplie, il faut au maximum 1 voisin

    def get_color_of(self, x, y):
        """
        Fonction qui retourne la couleur de la case (x,y)
        :x: int
        :y: int
        :return: str
        """
        return self.grid[x][y][0]

    def get_value_of(self, x, y):
        """
        Fonction qui retourne la valeur de la case (x,y)
        :x: int
        :y: int
        :return: int
        """
        return self.grid[x][y][1]

    def is_card_playable_on(self, x, y, played_card):
        """
        Fonction qui simule le dépot d'une carte à une position (x,y)
        Renvoie True si le coup est permis, False sinon.
        :x: int
        :y: int
        :played_card: tuple as (str,int)
        :return: bool
        """
        if self.is_box_playable(x, y):  # Si la case est jouable
            if self.is_box_filled(x, y):  # Si la case est déjà remplie
                if self.get_color_of(x, y) == played_card[0]:  # Si la couleur de la carte déjà posée est différente de celle de la carte à poser
                    return False
                else:
                    return self.get_value_of(x, y) == played_card[1]  # On retourne True si la valeur de la carte déjà posée est la même que celle de la carte à poser
            else:  # Si la case est vide
                return played_card in self.get_cards_playable(x, y)  # On regarde si la carte respecte les règles
        else:
            return False

    def get_cards_playable(self, x, y):
        """
        Cette méthode est appelée sur une position vide et jouable de la grille.
        Elle renvoie l'ensemble des cartes pouvant être posées en respectant les règles du jeu

        On parcours la liste des cartes du jeux
        On défini comme impossible les cartes qui ont :
        -Une couleur différente de celle de la carte de droite, de gauche, du haut ou du bas
        -Une valeur différente de la valeurs ± 1 de celle de la carte de droite, de gauche, du haut ou du bas

        :x: int
        :y: int
        :return: list of tuple as (str,int)
        """
        impossible_cards = []

        if self.is_index_not_out_of_range(x - 1):
            if self.is_box_filled(x - 1, y):
                impossible_cards += [card for card in self.available_cards if
                                     card[0] != self.get_color_of(x - 1, y) or card[1] != (
                                                 self.get_value_of(x - 1, y) - 1) and card[1] != (
                                                 self.get_value_of(x - 1, y) + 1)]
        if self.is_index_not_out_of_range(x + 1):
            if self.is_box_filled(x + 1, y):
                impossible_cards += [card for card in self.available_cards if
                                     card[0] != self.get_color_of(x + 1, y) or card[1] != (
                                                 self.get_value_of(x + 1, y) - 1) and card[1] != (
                                                 self.get_value_of(x + 1, y) + 1)]
        if self.is_index_not_out_of_range(y - 1):
            if self.is_box_filled(x, y - 1):
                impossible_cards += [card for card in self.available_cards if
                                     card[0] != self.get_color_of(x, y - 1) or card[1] != (
                                                 self.get_value_of(x, y - 1) - 1) and card[1] != (
                                                 self.get_value_of(x, y - 1) + 1)]
        if self.is_index_not_out_of_range(y + 1):
            if self.is_box_filled(x, y + 1):
                impossible_cards += [card for card in self.available_cards if
                                     card[0] != self.get_color_of(x, y + 1) or card[1] != (
                                                 self.get_value_of(x, y + 1) - 1) and card[1] != (
                                                 self.get_value_of(x, y + 1) + 1)]

        # On retourne toutes les cartes du jeu qui ne sont pas impossibles
        return [card for card in self.available_cards if not card in impossible_cards]

    def is_game_over(self):
        """
        Fonction qui retourne si le jeu est fini
        :return: bool
        """
        for player in self.players:
            if len(player.hand) == 0:
                return True
        return len(self.deck) == 0

    def get_winner(self):
        """
        Fonction qui retourne le joueur qui a gagné
        :return: ServerPlayer ou int si aucun joueur n'a gagné
        """
        for p in self.players:
            if len(p.hand) == 0:
                return p
        return -1

    def get_client_data_for(self, player_id):
        """
        Fonction qui adapte les données au format de ClientData() lisible par le client
        pour afficher le board
        :played_id: int
        :return: ClientData
        """
        cdata = ClientData()
        cdata.player_hand = self.players[player_id].hand
        cdata.current_grid = self.grid
        cdata.deck_size = len(self.deck)
        cdata.other_players.clear()
        for i in range(len(self.players)):
            if i != player_id:
                cdata.other_players.append((self.players[i].nickname, len(self.players[i].hand)))
        return cdata
