# -*- coding: utf-8 -*-
import random
import logging
import itertools

log = logging.getLogger()


class Card(object):
    def __init__(self):
        self.suits = ['♥', '♦', '♠', '♣']
        self.rank = {x + 2: str(x + 2) for x in list(range(9))}
        self.face_cards = {11: 'J', 12: 'Q', 13: 'K', 14: 'A'}
        self.rank.update(self.face_cards)


class Deck(object):
    def __init__(self):
        self.suits = ['♥', '♦', '♠', '♣']
        self.rank = {x + 2: str(x + 2).encode("utf-8").decode("utf-8")
                     for x in list(range(9))}
        self.face_cards = {11: 'J', 12: 'Q', 13: 'K', 14: 'A'}
        self.rank.update(self.face_cards)
        self.community = []
        self.deck = []
        self.shuffle()

    def shuffle(self):
        logging.info('Shuffling deck.')
        self.community = []
        self.deck = list(itertools.product(self.rank, self.suits))

    def draw_card(self):
        sr = random.SystemRandom()
        card = sr.choice(self.deck)
        self.deck.remove(card)
        return card

    def flop(self):
        for x in range(3):
            self.add_community_card()

    def add_community_card(self):
        card = self.draw_card()
        self.community.append(card)
        logging.info('Adding community card: {}'.format(card))


class Table(object):
    def __init__(self, players):
        logging.info('Seating {} players at the table.'.format(players))
        self.players = [Player(player_id=x, hand=[]) for x in range(players)]

    def deal(self, deck):
        logging.info('Dealing cards.')
        for player in (self.players + self.players):
            card = deck.draw_card()
            player.hand.append(card)

    def evaluate_hands(self, community):
        for player in self.players:
            player.classify_hand(community)

    def best_hand(self):
        best_player = max(x for x in self.players)
        logging.info('Player {} has the best hand with a {}.'
                     .format(best_player.player_id, best_player.hand_name))


class Player(object):
    def __init__(self, player_id=None, hand=None):
        self.player_id = player_id
        self.hand = hand
        self.hand_rank = None
        self.hand_name = None
        self.hand_kicker = None
        if not self.hand:
            self.hand = []

    def classify_hand(self, community):
        hc = HandClassifier(hand=self.hand, community=community)
        self.hand_rank = hc.hand_classification[0]
        self.hand_name = hc.hand_classification[1]
        self.hand_kicker = hc.kicker
        logging.info('Player {} has a {}.  With a kicker {} \n'
                     'All cards: \n {}'.format(self.player_id, self.hand_name,
                                               self.hand_kicker,
                                               hc.total_cards))

    def __eq__(self, other):
        return (self.hand_rank == other.hand_rank and
                self.hand_kicker == other.hand_kicker)

    def __lt__(self, other):
        return (self.hand_rank < other.hand_rank or
                ((self.hand_rank == other.hand_rank) and
                 self.hand_kicker < other.hand_kicker))

    def __gt__(self, other):
        return (self.hand_rank > other.hand_rank or
                ((self.hand_rank == other.hand_rank) and
                 self.hand_kicker > other.hand_kicker))

    def hand_rank(self):
        pass

    def fold(self):
        pass

    def check(self):
        pass

    def bet(self):
        pass


class HandClassifier(object):
    def __init__(self, hand=None, community=None):
        self.hand = hand
        self.community = community
        self.total_cards = self.hand + self.community
        self.ranks = []
        self.suits = []
        self.high_card = [0, 'High Card']
        self.pair = [1, 'Pair']
        self.two_pair = [2, 'Two Pair']
        self.three_of_a_kind = [3, 'Three of a Kind']
        self.straight = [4, 'Straight']
        self.flush = [5, 'Flush']
        self.full_house = [6, 'Full House']
        self.four_of_a_kind = [7, 'Four of a Kind']
        self.straight_flush = [8, 'Straight Flush']
        self.hand_classification = None
        self.full_hand_rank = None
        self.kicker = []
        self.flush_cards = []
        self.straight_cards = []
        self.sep_ranks_and_suits()
        self.evaluate()

    def sep_ranks_and_suits(self):
        for card in self.total_cards:
            self.ranks.append(card[0])
            self.suits.append(card[1])

    def evaluate(self):
        straight = self.check_straight(self.ranks)
        flush = self.check_flush(self.suits)
        rank_counts = {x: self.ranks.count(x) for x in self.ranks}
        max_rank = max(rank_counts.values())
        if straight and flush:
            self.hand_classification = self.straight_flush
            self.kicker = [max(self.ranks)]
        elif max_rank == 4:
            self.hand_classification = self.four_of_a_kind
            self.kicker = self.get_kicker(rank_counts, 4)
        elif max_rank == 3 and ((2 in rank_counts.values()) or
                                list(rank_counts.values()).count(3) > 1):
            self.hand_classification = self.full_house
            self.kicker = self.get_kicker(rank_counts, 3, rank_exc=[1])
        elif flush:
            self.hand_classification = self.flush
            self.kicker = sorted(list(set(x[0] for x in self.flush_cards))
                                 [-5:], reverse=True)
        elif straight:
            self.hand_classification = self.straight
            self.kicker = sorted(list(set(x[0] for x in self.straight_cards))
                                 [-5:], reverse=True)
        elif max_rank == 3:
            self.hand_classification = self.three_of_a_kind
            self.kicker = self.get_kicker(rank_counts, 3)
        elif max_rank == 2 and (list(rank_counts.values()).count(2) >= 2):
            self.hand_classification = self.two_pair
            self.kicker = self.get_kicker(rank_counts, 2, max_rank_count=2)
        elif max_rank == 2:
            self.hand_classification = self.pair
            self.kicker = self.get_kicker(rank_counts, 2)
        else:
            self.hand_classification = self.high_card
            self.kicker = self.get_kicker(rank_counts, 1)
        self.full_hand_rank = (self.hand_classification[0], self.kicker)

    @staticmethod
    def get_kicker(rank_counts, max_rank, max_rank_count=1, rank_exc=None):
        if not rank_exc:
            rank_exc = []
        kicker = sorted([x for x in rank_counts if rank_counts[x] == max_rank],
                        reverse=True)[:max_rank_count]
        rem_kickers = 5 - (max_rank * max_rank_count) - len(rank_exc)
        kicker.extend(sorted([x for x in rank_counts if rank_counts[x]
                              not in rank_exc and x not in kicker],
                             reverse=True)[:rem_kickers])
        return kicker

    def check_straight(self, ranks):
        straight_rank = ranks[:]
        if 14 in straight_rank:
            straight_rank.append(1)
        for rank in sorted((set(straight_rank)), reverse=True):
            straight = [x + rank for x in list(range(5))]
            if set(straight).issubset(straight_rank):
                self.straight_cards = [x for x in self.total_cards
                                       if x[0] in straight]
                return True

    def check_flush(self, suits):
        for suit in set(suits):
            if suits.count(suit) >= 5:
                self.flush_cards = [x for x in self.total_cards
                                    if x[1] == suit]
                return True
