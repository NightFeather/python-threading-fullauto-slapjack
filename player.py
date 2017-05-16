# coding=utf8

from __future__ import print_function
import threading
import random
from deck import Deck

class Player(threading.Thread):
    def __init__(self, game, idx):
        self.hand = []          # 玩家手上的卡
        self.game = game        # 遊戲狀態
        self.idx = idx          # 玩家編號
        self.pending = []       # 搶到之後可以丟的卡
        self.state = 0          # 狀態 0: 沒對應的卡, 1: 有卡, -1: 兩手空空
        self.rnd = 0            # 回合計數器
        threading.Thread.__init__(self)

    def readymsg(self):
        """
        安安我準備好了
        還有這是我的牌
        """
        base = '[%d] player %d ready, with [%s]'
        cards = "|".join([Deck.display(c) for c in self.hand])
        self.game.output(base % (self.rnd, self.idx, cards))

    def run(self):
        while True:
            self.pending = []               # 重置狀態
            self.state = 0                  # 重置狀態
            self.game.wait_for_round()      # 等待其他玩家
            if self.game.end: break         # 幹 收工了噢
            self.rnd += 1                   # 計數器加一
            self.readymsg()                 # 我好了
            self.game.notify_dispenser()    # 安安可以準備發牌了噢
            self.game.wait_for_dispenser()  # 等你發牌噢
            self.game.notify_dispenser()    # 安安我知道你發牌了噢

            if self.state == 0:             # 沒牌可用
                if self.game.steal:         # 可以用偷的
                    card = self.game.take()
                    if card is None:
                        continue
                    else:
                        self.hand.append(card)
                        self.game.report(self.rnd, self.idx, self.state, None)

            elif self.state == 1:           # 有牌可用
                card = self.game.take()
                if card != None:
                    self.game.report(self.rnd, self.idx, self.state, self.drop(card))



    def check(self, card):
        """
        check for card match, and add to self.pending
        -1: no card
        0: not match
        1: normal take
        """

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
        """
        pick a card
        and drop it
        """
        disposed = random.sample(self.pending, 1)[0]
        matcher = lambda c: not (c['num'] == disposed['num'] and c['suit'] == disposed['suit'])
        self.hand = filter(matcher, self.hand)
        self.hand.append(card)
        return disposed
