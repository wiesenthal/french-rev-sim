from random import uniform, shuffle
from simulation_help import *
from math import inf
from collections import defaultdict

# card list is a list of the cards in the game, 1 each, used mostly for selected and seen cards
with open('card_list.txt', 'r') as f:
    card_list = [l.strip().lower() for l in f.readlines()]

# free actions anyone can take any time
one_food = Card('farm', {}, {}, {'f': 1}, 0, ['n', 'b', 'p', 'c'])
one_gold = Card('sell furs', {}, {}, {'g': 1}, 0, ['n', 'b', 'p', 'c'])
free_actions = [one_gold, one_food]

# selected and seen cards are solely for determing the percent each card is taken
selected_cards = defaultdict(int)
seen_cards = defaultdict(int)

# when to start adding to selected and seen cards, make sure the agents are trained okay at least first
gen_start = 70

# these cards decrease loyalty of nobles by one. Text to complicated to be generated procedurally, easier to hard code it
noble_hurters = defaultdict(int)
noble_hurters['guillotine<br>king louis xvi'] = -1
noble_hurters['abolish feudalism'] = -1
noble_hurters['republican calendar'] = -1
noble_hurters['women\'s march on versailles'] = -1
noble_hurters['separate church and state'] = -1


# play out a full game with four agents, similar to one but with rotating turns
def full_game(agents, card_pile, trace=True):
    max_turns = 1000
    i = 0
    draw_pile = card_pile.copy()
    shuffle(draw_pile)
    discard_pile = []
    win = False
    while not win:
        # if not enough cards in draw_pile, shuffle
        if len(draw_pile) < 9:
            draw_pile.extend(discard_pile)
            discard_pile = []
            shuffle(draw_pile)
        # draw 9 cards
        cards = [draw_pile.pop() for j in range(9)]
        win, selections = full_turn(agents, cards, trace) # do a turn

        # major cards are removed from the game after one use
        for selected in selections:
            if selected.is_major:
                cards.remove(selected)

        discard_pile.extend(cards) # discard
        i += 1
        if i > max_turns:
            break
    if not win:
        return max_turns
    else:
        return win


# runs one full turn with four agents, to be used in full_game
def full_turn(agents, cards, trace=True):
    ordered_agents = sorted(agents, key=lambda a: (a.resources['a'], a.resources['w']), reverse=True)
    # shuffle(ordered_agents)
    copy_cards = cards.copy()
    selections = []

    noble = [x for x in agents if x.role == 'n'][0]
    # find out which agent is the noble

    for agent in ordered_agents:
        if trace:
            print(f'Role: {agent.role}')
        # agent takes a turn
        win, selected = agent.do_turn(copy_cards, trace)
        if win:
            return agent, selections
        if selected in copy_cards: # only other case is if they select a free action
            copy_cards.remove(selected)

        # certain cards hurt the noble, hard coded
        noble.resources['l'] += noble_hurters[selected.name]
        if selected.name == 'seize manor':
            noble.resources['f'] -= 2
        if selected.name == 'kill enemy of revolution':
            ordered_agents[0].resources['a'] -= 1

        selections.append(selected)

    return False, selections


class Agent:
    def __init__(self, starting_weights):
        # starting weights, usually all zeros or random
        self.weights = starting_weights # weights is the weights of the resources
        # initialize card weights
        self.card_weights = dict()
        for c in card_list:
            self.card_weights[c] = 0.0
        self.resources = dict()
        self.halved_cards = []
        self.population = 1 # population is how much food is eaten each turn
        self.num_turns = 0

        self.generation = 0

    def able(self, card):
        # determines if agent is the correct role for a card. (does not determine based on whether they can afford card)
        return self.role in card.roles

    def do_turn(self, cards, trace=False):
        # do out one turn, given cards on table
        self.num_turns += 1
        self.resources['g'] += self.resources['gpt']
        self.resources['f'] += self.resources['fpt']
        #gain food and gold equal to gold per turn and food per turn

        card = self.select(cards + free_actions)
        # select the best card on table

        # update selection percent
        if self.generation > gen_start:
            selected_cards[card.name] += 1
            for c1 in cards + free_actions:
                if self.able(c1) and self.can_afford(c1):
                    seen_cards[c1.name] += 1

        # pay for the card
        for k, v in card.costs.items():
            if card.name in self.halved_cards:
                self.resources[k] -= v // 2
            else:
                self.resources[k] -= v
        for k, v in card.results.items():
            self.resources[k] += v

        if trace:
            print(f'All options: {", ".join([c.name for c in cards])}')
            print(f'Selected: {card.name}')
            print(f'Resources: {self.resources}')

        # check win
        if self.achieved_goal():
            return True, card

        # feed the boys
        if self.resources['f'] >= self.population:
            self.resources['f'] -= self.population
        elif self.resources['l'] > 1:
            self.resources['l'] -= 1
        elif self.resources['a'] > 0:
            self.resources['a'] -= 1
        return False, card

    def can_afford(self, card):
        # determines whether a player has enough resources to buy a certain card
        # some cards have their costs halved mid game due to other action cards, so we need to account for that
        if card.name in self.halved_cards:  # check if halved
            for k, v in card.costs.items():
                if self.resources[k] < v // 2:
                    return False
            for k, v in card.requirements.items():
                if self.resources[k] < v // 2:
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
        # find best card based on its value
        max_value = -inf
        max_card = None
        for c in cards:
            if self.able(c) and self.can_afford(c):
                h = self.heuristic(c, self.weights)
                if h > max_value:
                    max_value = h
                    max_card = c
        return max_card

    def heuristic(self, card, weights):
        # uses combination of resource weights + the arbitrary weight of the card to determine the value this agent has assigned
        # the action has a weight, basically always added on to each turn to represent the value of giving up your turn to buy a card.
        if card.name in self.halved_cards:
            # for dealing with halved cards, multiply the action by two before halving everything because the card still takes a full action obviously
            temp_weights = weights.copy()
            temp_weights['action'] *= 2
            return (card.total_reward(weights) - card.total_cost(temp_weights) / 2) + self.card_weights[card.name]
        else:
            return card.value(weights) + self.card_weights[card.name]

    def duplicate(self):
        # return an exact copy of me
        obj = type(self)(self.weights.copy())
        obj.card_weights = self.card_weights.copy()
        obj.generation = self.generation + 1
        return obj

    def play_game(self, card_pile, trace=False):
        # play out a game
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
            win, selected = self.do_turn(cards, trace)

            if selected.is_major:
                cards.remove(selected)

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
        '''Mutates both resource and card weights'''
        for k, v in self.weights.items():
            self.weights[k] = v + uniform(-mutation / 2, mutation / 2)
        for k, v in self.card_weights.items():
            self.card_weights[k] = v + uniform(-mutation / 2, mutation / 2)
        return self


class Nobles(Agent):
    vc = {'nf': 13, 'g': 30, 'w': 10, 'a': 9}  # victory conditions

    def __init__(self, starting_weights):
        super().__init__(starting_weights)
        self.resources = {'w': 3, 'gpt': 1, 'fpt': 1, 'l': 2, 'g': 6, 'f': 5, 'a': 4, 'nf': 5}
        self.role = 'n'

    def achieved_goal(self):
        # national freedom 9 + 30 gold and 10 armaments
        return (int(self.resources['nf'] >= Nobles.vc['nf']) + int(
            self.resources['g'] >= Nobles.vc['g'] and self.resources['w'] >= Nobles.vc['w']) + int(
            self.resources['a'] >= Nobles.vc['a'])) >= 2

    def heuristic(self, card, weights):
        # if i have any win conditions, don't value them
        temp_weights = weights.copy()
        if self.resources['nf'] >= Nobles.vc['nf']:
            temp_weights['nf'] = 0
        if self.resources['g'] >= Nobles.vc['g'] + 3:
            temp_weights['g'] = 0
        if self.resources['w'] >= Nobles.vc['w'] + 2:
            temp_weights['w'] = 0
        if self.resources['a'] >= Nobles.vc['a'] + 1:
            temp_weights['a'] = 0
        return super().heuristic(card, temp_weights)

    def do_turn(self, cards, trace=False):

        d = super().do_turn(cards, trace)
        # randomly lose assembly to account for damage from other players. Might increase accuracy.
        # Make sure is disabled during a full run
        # if uniform(0, 1) < 0.12:
        #     if self.resources['l'] > 1:
        #         self.resources['l'] -= 1
        #     else:
        #         self.resources['a'] -= 1
        return d


class Peasants(Agent):
    vc = {'f': 13, 'a': 10}  # victory conditions

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

    def heuristic(self, card, weights):
        # if i have any win conditions, don't value them
        temp_weights = weights.copy()
        if self.resources['f'] >= Peasants.vc['f'] + 3:
            temp_weights['g'] = 0
        if self.resources['a'] >= Peasants.vc['a'] + 1:
            temp_weights['a'] = 0
        return super().heuristic(card, temp_weights)

    def select(self, cards):
        card = super().select(cards)
        if card.name == 'abolish feudalism': # hard code victory condition
            self.feudalism_abolished = True
        return card


class Bourgeoisie(Agent):
    vc = {'nf': 11, 'a': 9, 'l': 6}  # victory conditions

    def __init__(self, starting_weights):
        super().__init__(starting_weights)
        self.resources = {'w': 2, 'gpt': 1, 'fpt': 1, 'l': 2, 'g': 4, 'f': 5, 'a': 3, 'nf': 5}
        self.role = 'b'
        self.card_weights['enlightenment'] = 30 # make sure victory condition is weighted highly
        self.card_weights['tennis court oath'] = 3 # this card is better than it seems because it halves the cost of other cards
        self.enlightenment = False

    def achieved_goal(self):
        return (int(self.resources['a'] >= Bourgeoisie.vc['a']) + int(
            self.enlightenment and self.resources['l'] >= Bourgeoisie.vc['l']) + int(
            self.resources['nf'] >= Bourgeoisie.vc['nf'])) >= 2

    def heuristic(self, card, weights):
        # if i have any win conditions, don't value them
        temp_weights = weights.copy()

        if self.resources['nf'] >= Bourgeoisie.vc['nf']:
            temp_weights['nf'] = 0
        if self.resources['a'] >= Bourgeoisie.vc['a'] + 1:
            temp_weights['a'] = 0
        if self.resources['l'] >= Bourgeoisie.vc['l']:
            temp_weights['l'] = 0
        return super().heuristic(card, temp_weights)

    def select(self, cards):
        card = super().select(cards)
        if card.name == 'enlightenment':
            self.enlightenment = True
        if card.name == 'tennis court oath':
            self.halved_cards.extend(['constitution', 'enlightenment'])
        return card


class Committee(Agent):
    vc = {'w': 14, 'k': 3}  # victory conditions

    def __init__(self, starting_weights):
        super().__init__(starting_weights)
        self.resources = {'w': 4, 'gpt': 1, 'fpt': 1, 'l': 2, 'g': 3, 'f': 3, 'a': 2, 'nf': 5}
        self.role = 'c'
        self.card_weights['guillotine<br>king louis xvi'] = 10 # win condition
        self.card_weights['kill enemy of revolution'] = 0
        self.card_weights['committee of general security'] = 3 # this card is better than it seems because it halves the cost of other cards
        self.card_weights['enter reign of terror'] = 1000 # this card is better than it seems because it halves the cost of other cards
        self.card_weights['post reign'] = 1000 # committee kept underperforming because it is optimal to take kill enemy cards after reign of terror has commenced,
        # this weight is added because the agents do not know the time of the game or what cards have been played before
        self.kills = 0

        self.reign = False
        self.dead_king = False

    def achieved_goal(self):
        return (int(self.resources['w'] >= Committee.vc['w']) + int(
            self.dead_king) + int(
            self.kills >= Committee.vc['k'])) >= 2

    def heuristic(self, card, weights):
        # if i have any win conditions, don't value them
        temp_weights = weights.copy()

        if self.reign and card.name == 'kill enemy of revolution':
            return self.card_weights['post reign'] + self.card_weights['kill enemy of revolution']
        if self.kills >= Committee.vc['k'] and card.name == 'kill enemy of revolution':
            return -100
        if self.resources['w'] >= Committee.vc['w'] + 2:
            temp_weights['w'] = 0
        return super().heuristic(card, temp_weights)

    def select(self, cards):
        card = super().select(cards)
        if card.name == 'kill enemy of revolution': # hard code the killing cards
            self.kills += 1
        if card.name == 'guillotine marie antionette':
            self.kills += 2
        if card.name == 'guillotine<br>king louis xvi':
            self.dead_king = True
        if card.name == 'committee of general security':
            self.resources['l'] += 2
        if card.name == 'enter reign of terror':
            self.halved_cards.append('kill enemy of revolution')
            self.reign = True
        return card

# def simulate(agent, num_sims):
#     total = 0
#     card_pile = read('cards.tsv')
#     for j in range(num_sims):
#         p = agent.duplicate()
#         result = play_game(p, card_pile)
#         total += result.num_turns
#     return float(total / num_sims)
