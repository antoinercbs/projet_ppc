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


class Board:

    def __init__(self, *player_names):
        self.deck = Board.generate_shuffled_deck()
        self.current_card = self.deck.pop()
        self.players = [ServerPlayer(player_names[j], [self.deck.pop() for i in range(5)]) for j in
                        range(len(player_names))]

    @staticmethod
    def generate_shuffled_deck():
        deck = [('red', i // 2) if i % 2 == 0 else ('blue', i // 2) for i in range(2, 22)]
        random.shuffle(deck)
        return deck

    def update_player_hand_from_move(self, player_id, played_card):
        """
        Simule le dépot par ce joueur de cette carte.
        Si le coup est permis, la carte est enlevée de la main de ce joueur et devient la carte courante.
        Sinon, le joueur prend une carte du deck dans sa main.
        """
        if self.is_card_playable(played_card):
            self.players[player_id].hand.remove(played_card)
            self.current_card = played_card
            print(self.players[player_id].hand)
        else:
            self.players[player_id].hand.append(self.deck.pop())

    def is_card_playable(self, played_card):
        """
        Vérifie si cette carte peut être jouée au dessus du tas.
        Renvoie True si oui, False sinon
        """
        color = played_card[0]
        value = played_card[1]
        if color == self.current_card[0]:  # Si même couleur
            return value == self.current_card[1] - 1 or played_card[1] == self.current_card[1] + 1  # Vrai si valeur =  +/- 1 courante
        else:
            return value == self.current_card[1]  # Vrai si valeur = celle courante

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
        cdata.current_card = self.current_card
        cdata.deck_size = len(self.deck)
        cdata.other_players.clear()
        for i in range(len(self.players)):
            if i != player_id:
                cdata.other_players.append((self.players[i].nickname, len(self.players[i].hand)))
        return cdata





if __name__ == "__main__":
    board = Board('Jean', 'Robert', 'Fabrice')
    print(board.deck)
    print(board.current_card)
    print(board.players[1].hand)
