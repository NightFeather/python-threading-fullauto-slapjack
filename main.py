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
        self.deck = Deck()                          # 牌堆
        self.players = []                           # 玩家清單
        self.player_count = count                   # 玩家數量
        self.__round_barrier = Barrier(count+1)     # 每回合末同步狀態用
        self.__jack_lock = Lock()                   # 搶牌鎖定
        self.__dispenser_event = Event()            # 牌發了沒
        self.__dispenser_lock = CounterLock(self.player_count) # 發牌員等玩家用的鎖

        self.steal = False                          # 大家來偷牌
        self.table_top = None                       # 桌面上可以搶的那張牌
        self.last_card = None                       # 被搶走的牌

        self.end = False                            # GG?
        self.player_reports = [[] for i in range(self.player_count)] # 得分記錄
        self.player_finnished = []                  # 排名

        self.round = 0                              # 回合計數器
        self.output_mutex = Lock()                  # log 用的 lock, 不然你看想看意大利麵般的輸出嗎

        self.deck.shuffle()                         # 洗牌
        self.players = [Player(self, i) for i in range(self.player_count)] # 建立玩家

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

    def wait_for_round(self,idx):
        #if idx == -1:
        #    self.output('[%d] dispenser enter barrier' % self.round)
        #else:
        #    self.output('[%d] player %d enter barrier' % (self.round, idx))
        self.__round_barrier.wait()
        #if idx == -1:
        #    self.output('[%d] dispenser leave barrier' % self.round)
        #else:
        #    self.output('[%d] player %d leave barrier' % (self.round, idx))

    def take(self):
        if self.__jack_lock.acquire(False):
            card = self.table_top
            if not card is None: self.last_card = card
            self.table_top = None
            self.__jack_lock.release()
            return card
        return None


    def report(self, idx, state, card):
        state_acts = ['stole', 'took']
        place_score = [50,20,10,0]
        score = self.card_score(card)
        rnd = self.round

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

    def game_end(self):
        """
        結算
        """
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
            if not self.deck.deck:                      # 牌堆空了沒
                  self.end = True
                  break
            self.__dispenser_event.clear()              # 搶有就有 沒有就等下一輪
            self.round += 1                             # 新回合
            self.wait_for_round(-1)                     # 阿你是好了沒

            self.steal = False                          # 關於偷牌這件事我們再評估

            self.wait_for_players()                     # 大家都好了嗎

            self.dispense()                             # 發牌！

            player_state = set([player.check(self.table_top) for player in self.players])
            if len(player_state) == 1:                  # 大家都一樣
                if 0 in player_state:                   # 都沒牌好搶
                    self.steal = True
                elif -1 in player_state:                # 都兩手空空
                    self.end = True

            self.__round_barrier = Barrier(4)           # 重置同步
            self.__dispenser_event.set()                # 牌發了 大家都看好了 來搶噢
            self.wait_for_players()                     # 所以架打完了嗎
        
        self.wait_for_round(-1)                         # 好了收工啦
        self.output('It\'s over!')
        self.game_end()

if __name__ == '__main__':
    game = Game(4)

    game.mainloop()
    sys.exit(0)