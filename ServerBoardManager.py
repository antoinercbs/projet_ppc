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
        #self.current_card = self.deck.pop()
        self.size_grid = 7
        self.grid = [[[False,False,None]] * self.size_grid for i in range(self.size_grid)]
        update_board(self.size_grid//2,self.size_grid//2,self.deck.pop())
        self.players = [ServerPlayer(player_names[j], [self.deck.pop() for i in range(5)]) for j in
                        range(len(player_names))]

    @staticmethod
    def generate_shuffled_deck():
        deck = [('red', i // 2) if i % 2 == 0 else ('blue', i // 2) for i in range(2, 22)]
        random.shuffle(deck)
        return deck

    def update_board(self,x,y,new_card):
        self.grid[x][y][0]=True
        self.grid[x][y][1]=True
        self.grid[x][y][2]=new_card
        try :
            if self.grid[x-1][y][1]==False:
                self.grid[x-1][y][0]=True
        except IndexError:
            pass
        try :
            if self.grid[x+1][y][1]==False:
                self.grid[x+1][y][0]=True
        except IndexError:
            pass
        try :
            if self.grid[x][y-1][1]==False:
                self.grid[x][y-1][0]=True
        except IndexError:
            pass
        try :
            if self.grid[x][y+1][1]==False:
                self.grid[x][y+1][0]=True
        except IndexError:
            pass

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

    def is_card_playable_on(self, played_card, x, y):
        color = played_card[0]
        value = played_card[1]

        is_playable=self.grid[x][y][0]
        is_filled=self.grid[x][y][1]
        case_color=self.grid[x][y][2][0]
        case_value=self.grid[x][y][2][1]

        if is_playable:
            if is_filled:
                if case_color!=color:
                    return value==case_value
                else :
                    return False
            else :
                return get_value_playable(x,y).contains(value)
        return False

    def get_value_playable(self,x,y):
        impossible_values=[]
        possible_values=[1,2,3,4,5,6,7,8,9]
        try :
            if grid[x-1][y][1]:
                impossible_values+=[x for x in possible_values if x!=grid[x-1][y][2][1]-1 and x!=grid[x-1][y][2][1]+1]
        except IndexError:
            pass
        try :
            if grid[x+1][y][1]:
                impossible_values+=[x for x in possible_values if x!=grid[x+1][y][2][1]-1 and x!=grid[x+1][y][2][1]+1]
        except IndexError:
            pass
        try :
            if grid[x][y-1][1]:
                impossible_values+=[x for x in possible_values if x!=grid[x][y-1][2][1]-1 and x!=grid[x][y-1][2][1]+1]
        except IndexError:
            pass
        try :
            if grid[x][y+1][1]:
                impossible_values+=[x for x in possible_values if x!=grid[x][y+1][2][1]-1 and x!=grid[x][y+1][2][1]+1]
        except IndexError:
            pass
        return [i for i in possible_values if not i in impossible_values]

    def is_card_playable(self, played_card):
        """
        Vérifie si cette carte peut être jouée au dessus d'une position du board.
        Renvoie True si oui, False sinon
        """
        color = played_card[0]
        value = played_card[1]
        if color != self.current_card[0]:  # Si même couleur
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
