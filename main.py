#!/usr/bin/env python2
# coding=utf8

from threading import Lock, Event
from deck import Deck
from barrier import Barrier
from player import Player
from counter_lock import CounterLock
import time
import sys

class Game:
    def __init__(self, count):
        self.deck = Deck()
        self.players = []
        self.player_count = count
        self.__round_barrier = Barrier(count+1)
        self.__jack_lock = Lock()
        self.__dispenser_event = Event()
        self.__dispenser_lock = CounterLock(self.player_count)

        self.steal = False
        self.table_top = None
        self.last_card = None

        self.end = False
        self.player_reports = [[] for i in range(self.player_count)]
        self.player_finnished = []

        self.round = 0
        self.output_mutex = Lock()

        self.deck.shuffle()
        self.players = [Player(self, i) for i in range(self.player_count)]

    def output(self, msg):
        with self.output_mutex:
            print("%s" % msg)

    def dispense(self):
        card = self.deck.withdraw()
        with self.__jack_lock:
            if card:
                card = card[0]
                self.table_top = card
                self.output('dispenser: round %d' % self.round )
                self.output('dispenser: %s dispensed. Let\'s go' % Deck.display(self.table_top))
                self.output('dispenser: %d cards left in deck' % len(self.deck.deck))
            else:
                self.end = True
        
        return card

    def wait_for_players(self):
        #self.output('dispenser: wait for players')
        self.__dispenser_lock.wait()
        #self.output('dispenser: player all settled')
        self.__dispenser_lock.reset()

    def notify_dispenser(self):
        self.__dispenser_lock.touch()

    def wait_for_dispenser(self):
        self.__dispenser_event.wait()

    def wait_for_round(self):
        self.__round_barrier.wait()

    def take(self):
        if self.__jack_lock.acquire(False):
            card = self.table_top
            if not card is None: self.last_card = card
            self.table_top = None
            self.__jack_lock.release()
            return card
        return None


    def report(self, rnd, idx, state, card):
        state_acts = ['stole', 'took']
        place_score = [50,20,10,0]
        score = self.card_score(card)

        if state == -1:
            self.player_finnished.append(idx)
            self.player_reports[idx].append(place_score[len(self.player_finnished)])
            self.output('[%d] player %d finished the game! No.%d!', (rnd, idx, len(self.player_finnished)+1))

        self.output('[%d] player %d %s the card! +%d' % (rnd, idx, state_acts[state], score))
        if not self.steal:
            self.output('[%d] player %d dropped card "%s"' % (rnd, idx, Deck.display(card)))

        self.player_reports[idx].append(score)

    def card_score(self, card):
        score_type = ''
        score = 0
        if card is None:
            score = 5
        elif card['suit'] == self.last_card['suit']:
            score = 10
        elif card['num'] == self.last_card['num']:
            score = 30
        else:
            score = 0
        
        return score

    def round_check(self):
        pass

    def game_end(self):
        score_types = [(5, 'steal'), (10, 'same suit'), (30, 'same number')]
        for idx, rept in enumerate(self.player_reports):
            self.output('player %d scored %d' % (idx, sum(rept)))
            if idx in self.player_finnished:
                place = self.player_finnished.index[idx]+1
                place_score = [50,20,10,0]
                self.output('player %d finnished in %d-st place!, +$d' % (idx, place, place_score[place-1]))
            for score_type in score_types:
                times = rept.count(score_type[0])
                self.output('player %d has %d times of %s, +%d' % (idx, times, score_type[1], score_type[0]*times))
                

    def mainloop(self):

        self.output('game start')
        self.output('dispenser: %d cards left in deck' % len(self.deck.deck))
        for player in self.players:
            player.hand = self.deck.withdraw(3)
            player.start()

        while not game.end:
            if not self.deck.deck: # check if there are still cards to dispense
                  self.end = True
                  break
            self.__dispenser_event.clear()
            #self.output('dispenser enter barrier')
            self.__round_barrier.wait()  # syncing dispenser and all players
            #self.output('dispenser leave barrier')

            self.steal = False   # reset the steal mode indicator

            self.round += 1

            self.wait_for_players() # make sure all players waiting

            self.dispense()

            player_state = set([player.check(self.table_top) for player in self.players])
            if len(player_state) == 1:
                if 0 in player_state:    # all player has no card matching
                    self.steal = True
                elif -1 in player_state: # all players has no card in hand
                    self.end = True

            self.__round_barrier = Barrier(4) # reset barrier
            self.__dispenser_event.set() # wake all players
            self.wait_for_players()
            #time.sleep(0.001)  # wait for player sleep in
        
        self.__round_barrier.wait()
        print('It\'s over!')
        self.game_end()

if __name__ == '__main__':
    game = Game(4)

    game.mainloop()
    sys.exit(0)