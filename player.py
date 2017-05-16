# coding=utf8

from __future__ import print_function
import threading
import random
from deck import Deck

class Player(threading.Thread):
    def __init__(self, game, idx):
        self.hand = []
        self.game = game
        self.idx = idx
        self.pending = []
        self.state = 0
        self.rnd = 0
        threading.Thread.__init__(self)

    def readymsg(self):
        base = '[%d] player %d ready, with [%s]'
        cards = "|".join([Deck.display(c) for c in self.hand])
        self.game.output(base % (self.rnd, self.idx, cards))

    def run(self):
        while True:
            self.pending = []
            self.state = 0
            #self.game.output('[%d] player %d enter barrier' % (self.rnd, self.idx))
            self.game.wait_for_round()
            if self.game.end: break
            self.rnd += 1
            #self.game.output('[%d] player %d leave barrier' % (self.rnd, self.idx))
            self.readymsg()
            #self.game.output('[%d] player %d wait for dispenser' % (self.rnd, self.idx))
            self.game.notify_dispenser()
            self.game.wait_for_dispenser()
            self.game.notify_dispenser()

            if self.state == 0:
                if self.game.steal:
                    card = self.game.take()
                    if card is None:
                        continue
                    else:
                        self.hand.append(card)
                        self.game.report(self.rnd, self.idx, self.state, None)

            elif self.state == 1:
                card = self.game.take()
                if card != None:
                    self.game.report(self.rnd, self.idx, self.state, self.drop(card))



    def check(self, card):
        # check for card match, and add to self.pending
        # 0: not match
        # 1: normal take

        if not self.hand:
            self.state = -1
            self.game.report(self.rnd, self.idx, self.state, None)
            return -1

        res = [c for c in self.hand if c['num'] == card['num']]
        if len(res) > 0:
            self.pending = res
            self.state = 1
            return 1

        res = [c for c in self.hand if c['suit'] == card['suit']]
        if len(res) > 0:
            self.pending = res
            self.state = 1
            return 1

        return 0

    def drop(self, card):
        disposed = random.sample(self.pending, 1)[0]
        matcher = lambda c: not (c['num'] == disposed['num'] and c['suit'] == disposed['suit'])
        self.hand = filter(matcher, self.hand)
        self.hand.append(card)
        return disposed
