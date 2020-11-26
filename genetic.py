import simulation
from simulation_help import read
from random import uniform

CARD_PILE = read('cards.tsv')
ANNEALING_RATE = 0.99


class Generation:
    generations = 0

    def __init__(self, agents, mutation_rate, survival_rate):
        self.gen_number = Generation.generations
        Generation.generations += 1

        self.agents = agents
        self.best = -1
        self.worst = -1
        self.median = -1
        self.mutation_rate = mutation_rate
        self.survival_rate = survival_rate

        self.run_all()

    def run_all(self):
        self.agents.sort(key=lambda agent: agent.play_game(CARD_PILE))
        self.best = self.agents[0]
        self.median = self.agents[int(len(self.agents) / 2)]
        self.worst = self.agents[-1]

    def next(self):
        # assume I have already been run, my agents are sorted
        num_survivors = int(self.survival_rate * len(self.agents))
        new_agents = []
        for i in range(len(self.agents)):
            new_agents.append(self.agents[i % num_survivors].duplicate().mutate(self.mutation_rate))

        g = Generation(new_agents, self.mutation_rate*ANNEALING_RATE, self.survival_rate)
        g.run_all()
        return g

    def next_c(self):
        # training on card weights
        num_survivors = int(self.survival_rate * len(self.agents))
        new_agents = []
        for i in range(len(self.agents)):
            new_agents.append(self.agents[i % num_survivors].duplicate().mutate_c(self.mutation_rate))

        g = Generation(new_agents, self.mutation_rate*ANNEALING_RATE, self.survival_rate)
        g.run_all()
        return g

    def next_both(self):
        # training on both
        num_survivors = int(self.survival_rate * len(self.agents))
        new_agents = []
        for i in range(len(self.agents)):
            new_agents.append(self.agents[i % num_survivors].duplicate().mutate_both(self.mutation_rate))

        g = Generation(new_agents, self.mutation_rate*ANNEALING_RATE, self.survival_rate)
        g.run_all()
        return g


def random_weights():
    keys = ['g', 'f', 'l', 'a', 'nf', 'gpt', 'fpt', 'w', 'action']
    d = dict()
    for k in keys:
        d[k] = uniform(0, 10)
    return d


def zero_weights():
    keys = ['g', 'f', 'l', 'a', 'nf', 'gpt', 'fpt', 'w', 'action']
    d = dict()
    for k in keys:
        d[k] = 0
    return d


def normalize(weights, val):
    new_weights = dict()
    for k in weights.keys():
        new_weights[k] = weights[k] / val
    return new_weights


class_tested = simulation.Bourgeoisie

num_agents = 500
num_generations = 150
first_agents = [class_tested(random_weights()) for i in range(num_agents)]
gen = Generation(first_agents, .5, 0.75)
for i in range(num_generations):
    print(
        f'Generation #{gen.gen_number} best: {gen.best.num_turns}, median: {gen.median.num_turns}, worst: {gen.worst.num_turns}')
    gen = gen.next_both()
print(normalize(gen.median.weights, gen.median.weights['action']))

# simulation.seen_cards = simulation.defaultdict(int)
# simulation.selected_cards = simulation.defaultdict(int)

# # card weight training
# new_agents = []
# for i in range(num_agents):
#     new_agents.append(gen.best.duplicate())
# cardgen = Generation(new_agents, 0.3, 0.8)
# for i in range(num_generations):
#     print(
#         f'Generation #{cardgen.gen_number} best: {cardgen.best.num_turns}, median: {cardgen.median.num_turns}, worst: {cardgen.worst.num_turns}')
#     cardgen = cardgen.next_c()
# print(normalize(cardgen.median.weights, gen.median.weights['action']))

# print card weights
cw = gen.median.card_weights
cw = normalize(cw, gen.median.weights['action'])
cwt = [(k, v) for k, v in cw.items()]
cwt.sort(key=lambda x: x[1])
print(cwt)
print()

# print card rates
rates = []
for k, v in simulation.seen_cards.items():
    rates.append((k, simulation.selected_cards[k]/v))
for k, v in sorted(rates, key=lambda x: x[1]):
    print(f'{k}: {round(v,4)*100}%')

# win conditions
for a in gen.agents:
    r = a.resources
    print(r)
    # print(f'gold: {r["g"]}, weapons: {r["w"]}, nf: {r["nf"]}, assembly: {r["a"]}')

# print()
# print("BEST")
# b = gen.best.duplicate()
# b.trace = True
# print(b.play_game(CARD_PILE, True))
# print()
# print('MEDIAN')
# c = gen.median.duplicate()
# c.trace = True
# print(c.play_game(CARD_PILE, True))


# to do:
# hard coded cards
# victory cards
# other classes
# visualize population with clustering
