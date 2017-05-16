# coding=utf8
"""
make a poker deck (without jokers)
"""

import random

class Deck:
    """
    handles a poker deck
    """
    suits = [u'♠', u'♥', u'♦', u'♣']
    face = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']

    def __init__(self):
        self.deck = []
        self.generate()

    def generate(self):
        """
        fill the deck with 4*13 cards
        """
        self.deck = []
        for suit in range(4):
            for num in range(13):
                self.deck.append({'suit': suit, 'num': num})
        return self.deck

    def shuffle(self):
        """
        shuffle the deck
        """
        random.shuffle(self.deck)
        return self.deck

    def withdraw(self, count=1):
        """
        take {count} cards from deck
        """
        res = None
        if self.deck:
            res = [ self.deck.pop() for i in range(count) ]
        return res

    @staticmethod
    def display(card):
        """
        form the display string
        """
        return Deck.suits[card['suit']] + ' ' + Deck.face[card['num']]
