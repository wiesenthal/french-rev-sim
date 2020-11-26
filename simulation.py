from random import uniform, shuffle
from simulation_help import *
from math import inf
from collections import defaultdict

with open('card_list.txt', 'r') as f:
    card_list = [l.strip().lower() for l in f.readlines()]

one_food = Card('farm', {}, {}, {'f': 1}, 0, ['n', 'b', 'p', 'c'])
one_gold = Card('sell furs', {}, {}, {'g': 1}, 0, ['n', 'b', 'p', 'c'])
free_actions = [one_gold, one_food]

selected_cards = defaultdict(int)
seen_cards = defaultdict(int)

gen_start = 100


class Agent:

    def __init__(self, starting_weights):
        self.weights = starting_weights
        # initialize card weights
        self.card_weights = dict()
        for c in card_list:
            self.card_weights[c] = 0.0
        self.resources = dict()
        self.halved_cards = []
        self.population = 1
        self.num_turns = 0

        self.generation = 0

        self.trace = False

    def able(self, card):
        return self.role in card.roles

    def do_turn(self, cards, trace=False):
        self.num_turns += 1
        self.resources['g'] += self.resources['gpt']
        self.resources['f'] += self.resources['fpt']

        card = self.select(cards + free_actions)

        # update selection percent
        if self.generation > gen_start:
            selected_cards[card.name] += 1
            for c1 in cards + free_actions:
                if self.able(c1) and self.can_afford(c1):
                    seen_cards[c1.name] += 1

        if card.is_major:
            cards.remove(card)

        for k, v in card.costs.items():
            self.resources[k] -= v
        for k, v in card.results.items():
            self.resources[k] += v

        if trace:
            print(f'All options: {", ".join([c.name for c in cards])}')
            print(f'Selected: {card.name}')
            print(f'Resources: {self.resources}')

        # check win
        if self.achieved_goal():
            return True

        # feed the boys
        if self.resources['f'] >= self.population:
            self.resources['f'] -= self.population
        elif self.resources['l'] > 1:
            self.resources['l'] -= 1
        elif self.resources['a'] > 0:
            self.resources['a'] -= 1
        return False

    def can_afford(self, card):
        if card.name in self.halved_cards: # check if halved
            for k, v in card.costs.items():
                if self.resources[k] < v/2:
                    return False
            for k, v in card.requirements.items():
                if self.resources[k] < v/2:
                    return False
        else:
            for k, v in card.costs.items():
                if self.resources[k] < v:
                    return False
            for k, v in card.requirements.items():
                if self.resources[k] < v:
                    return False
        return True

    def select(self, cards):
        # find best card
        max_value = -inf
        max_card = None
        for c in cards:
            if self.able(c) and self.can_afford(c):
                if c in self.halved_cards:
                    h = self.half_heuristic(c)
                else:
                    h = self.heuristic(c)
                if h > max_value:
                    max_value = h
                    max_card = c
        return max_card

    def heuristic(self, card):
        return card.value(self.weights) + self.card_weights[card.name]

    def half_heuristic(self, card):
        temp_weights = self.weights.copy()
        temp_weights['action'] *= 2
        return (card.total_reward(self.weights) - card.total_cost(temp_weights)/2) + self.card_weights[card.name]

    def duplicate(self):
        obj = type(self)(self.weights.copy())
        obj.card_weights = self.card_weights.copy()
        obj.generation = self.generation + 1
        return obj

    def play_game(self, card_pile, trace=False):
        max_turns = 1000
        i = 0
        draw_pile = card_pile.copy()
        shuffle(draw_pile)
        discard_pile = []
        win = False
        while not win:
            if len(draw_pile) < 9:
                draw_pile.extend(discard_pile)
                discard_pile = []
                shuffle(draw_pile)
            cards = [draw_pile.pop() for j in range(9)]
            win = self.do_turn(cards, trace)
            discard_pile.extend(cards)
            i += 1
            if i > max_turns:
                break

        return self.num_turns

    def mutate(self, mutation):
        """Mutates me in place"""
        for k, v in self.weights.items():
            self.weights[k] = v + uniform(-mutation / 2, mutation / 2)
        return self

    def mutate_c(self, mutation):
        """Mutates my card weights"""
        for k, v in self.card_weights.items():
            self.card_weights[k] = v + uniform(-mutation / 2, mutation / 2)
        return self

    def mutate_both(self, mutation):
        for k, v in self.weights.items():
            self.weights[k] = v + uniform(-mutation / 2, mutation / 2)
        for k, v in self.card_weights.items():
            self.card_weights[k] = v + uniform(-mutation / 2, mutation / 2)
        return self


class Nobles(Agent):
    vc = {'nf': 13, 'g': 30, 'w': 10, 'a': 9}  # victory conditions

    def __init__(self, starting_weights):
        super().__init__(starting_weights)
        self.resources = {'w': 3, 'gpt': 1, 'fpt': 1, 'l': 2, 'g': 6, 'f': 6, 'a': 4, 'nf': 5}
        self.role = 'n'

    def achieved_goal(self):
        # national freedom 9 + 30 gold and 10 armaments
        return (int(self.resources['nf'] >= Nobles.vc['nf']) + int(
            self.resources['g'] >= Nobles.vc['g'] and self.resources['w'] >= Nobles.vc['w']) + int(
            self.resources['a'] >= Nobles.vc['a'])) >= 2

    def heuristic(self, card):
        temp_weights = self.weights.copy()
        if self.resources['nf'] >= Nobles.vc['nf']:
            temp_weights['nf'] = 0
        if self.resources['g'] >= Nobles.vc['g'] + 3:
            temp_weights['g'] = 0
        if self.resources['w'] >= Nobles.vc['w'] + 2:
            temp_weights['w'] = 0
        if self.resources['a'] >= Nobles.vc['a'] + 1:
            temp_weights['a'] = 0
        return card.value(temp_weights) + self.card_weights[card.name]

    def do_turn(self, cards, trace=False):
        # randomly lose assembly to account for damage
        d = super().do_turn(cards, trace)
        if uniform(0, 1) < 0.12:
            if self.resources['l'] > 1:
                self.resources['l'] -= 1
            else:
                self.resources['a'] -= 1
        return d


class Peasants(Agent):
    vc = {'f': 15, 'a': 10}  # victory conditions

    def __init__(self, starting_weights):
        super().__init__(starting_weights)
        self.resources = {'w': 3, 'gpt': 1, 'fpt': 1, 'l': 2, 'g': 1, 'f': 3, 'a': 1, 'nf': 5}
        self.role = 'p'
        self.card_weights['abolish feudalism'] = 30
        self.population = 3
        self.feudalism_abolished = False

    def achieved_goal(self):
        # 15 food, 10 assembly, abolish feudalis
        return (int(self.feudalism_abolished) + int(
            self.resources['f'] >= Peasants.vc['f']) + int(
            self.resources['a'] >= Peasants.vc['a'])) >= 2

    def heuristic(self, card):
        temp_weights = self.weights.copy()
        if self.resources['f'] >= Peasants.vc['f'] + 3:
            temp_weights['g'] = 0
        if self.resources['a'] >= Peasants.vc['a'] + 1:
            temp_weights['a'] = 0
        return card.value(temp_weights) + self.card_weights[card.name]

    def select(self, cards):
        card = super().select(cards)
        if card.name == 'abolish feudalism':
            self.feudalism_abolished = True
        return card


class Bourgeoisie(Agent):
    vc = {'nf': 13, 'a': 9, 'l': 7}  # victory conditions

    def __init__(self, starting_weights):
        super().__init__(starting_weights)
        self.resources = {'w': 2, 'gpt': 1, 'fpt': 1, 'l': 2, 'g': 4, 'f': 3, 'a': 3, 'nf': 5}
        self.role = 'b'
        self.card_weights['enlightenment'] = 30
        self.card_weights['tennis court oath'] = 3
        self.enlightenment = False

    def achieved_goal(self):
        # 15 food, 10 assembly, abolish feudalis
        return (int(self.resources['a'] >= Bourgeoisie.vc['a']) + int(
            self.enlightenment and self.resources['l'] >= Bourgeoisie.vc['l']) + int(
            self.resources['nf'] >= Bourgeoisie.vc['nf'])) >= 2

    def heuristic(self, card):
        temp_weights = self.weights.copy()

        if self.resources['nf'] >= Bourgeoisie.vc['nf']:
            temp_weights['nf'] = 0
        if self.resources['a'] >= Bourgeoisie.vc['a'] + 1:
            temp_weights['a'] = 0
        if self.resources['l'] >= Bourgeoisie.vc['l']:
            temp_weights['l'] = 0
        return card.value(temp_weights) + self.card_weights[card.name]

    def select(self, cards):
        card = super().select(cards)
        if card.name == 'enlightenment':
            self.enlightenment = True
        if card.name == 'tennis court oath':
            self.halved_cards.extend(['constitution', 'enlightenment'])
        return card


class Committee(Agent):
    vc = {'w': 15, 'k': 4}  # victory conditions

    def __init__(self, starting_weights):
        super().__init__(starting_weights)
        self.resources = {'w': 4, 'gpt': 1, 'fpt': 1, 'l': 2, 'g': 3, 'f': 3, 'a': 2, 'nf': 5}
        self.role = 'c'
        self.card_weights['guillotine<br>king louis xvi'] = 10
        self.card_weights['kill enemy of revolution'] = 5
        self.card_weights['committee of general security'] = 3
        self.card_weights['enter reign of terror'] = 3
        self.kills = 0
        self.population = 1
        self.dead_king = False

    def achieved_goal(self):
        # 15 food, 10 assembly, abolish feudalis
        return (int(self.resources['w'] >= Committee.vc['w']) + int(
            self.dead_king) + int(
            self.kills >= Committee.vc['k'])) >= 2

    def heuristic(self, card):
        temp_weights = self.weights.copy()

        if self.resources['nf'] >= Bourgeoisie.vc['nf']:
            temp_weights['nf'] = 0
        if self.resources['a'] >= Bourgeoisie.vc['a'] + 1:
            temp_weights['a'] = 0
        if self.resources['l'] >= Bourgeoisie.vc['l']:
            temp_weights['l'] = 0
        return card.value(temp_weights) + self.card_weights[card.name]

    def select(self, cards):
        card = super().select(cards)
        if card.name == 'enlightenment':
            self.enlightenment = True
        return card

# def simulate(agent, num_sims):
#     total = 0
#     card_pile = read('cards.tsv')
#     for j in range(num_sims):
#         p = agent.duplicate()
#         result = play_game(p, card_pile)
#         total += result.num_turns
#     return float(total / num_sims)
