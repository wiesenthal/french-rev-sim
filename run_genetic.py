import simulation
from simulation_help import read
from random import uniform
from collections import defaultdict

CARD_PILE = read('cards.tsv')

# a generation is a generation of one role. Has many agents which are all of that role.
# The agents do not compete directly, they play the game themselves and the players who finish the fastest reproduce.
class Generation:
    # stores how many total generations have been run (not just this role)
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
        # the below line runs each agent in the generation and sorts them by how many turns it took to win
        self.agents.sort(key=lambda agent: agent.play_game(CARD_PILE))
        self.best = self.agents[0]
        self.median = self.agents[int(len(self.agents) / 2)]
        self.worst = self.agents[-1]

    def next(self, ANNEALING_RATE=0.99): # returns the next generation, only mutating resource weights
        # assume I have already been run, my agents are sorted
        num_survivors = int(self.survival_rate * len(self.agents))
        new_agents = []
        for i in range(len(self.agents)):
            new_agents.append(self.agents[i % num_survivors].duplicate().mutate(self.mutation_rate))

        g = Generation(new_agents, self.mutation_rate * ANNEALING_RATE, self.survival_rate)
        g.run_all()
        return g

    def next_c(self, ANNEALING_RATE=0.99): # returns the next generation, only mutating card weights
        # training on card weights
        num_survivors = int(self.survival_rate * len(self.agents))
        new_agents = []
        for i in range(len(self.agents)):
            new_agents.append(self.agents[i % num_survivors].duplicate().mutate_c(self.mutation_rate))

        g = Generation(new_agents, self.mutation_rate * ANNEALING_RATE, self.survival_rate)
        g.run_all()
        return g

    def next_both(self, ANNEALING_RATE=0.99): # returns the next generation, mutating both resource and individual card_weights
        # training on both
        num_survivors = int(self.survival_rate * len(self.agents))
        new_agents = []
        for i in range(len(self.agents)):
            new_agents.append(self.agents[i % num_survivors].duplicate().mutate_both(self.mutation_rate))

        g = Generation(new_agents, self.mutation_rate * ANNEALING_RATE, self.survival_rate)
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


def train_agent(cls, num_agents=500, num_generations=200, mutation_rate=0.5, survival_rate=0.75, annealing_rate=0.99):
    class_tested = cls

    first_agents = [class_tested(random_weights()) for i in range(num_agents)]
    gen = Generation(first_agents, mutation_rate, survival_rate)
    for i in range(num_generations):
        if i % 10 == 0:
            print(
                f'Generation #{gen.gen_number} best: {gen.best.num_turns}, median: {gen.median.num_turns}, worst: {gen.worst.num_turns}')
        gen = gen.next_both(annealing_rate)
    print(normalize(gen.median.weights, gen.median.weights['action']))
    return gen


# win conditions they ended with by printing out resource counts
def print_win_cons(gen):
    for a in gen.agents:
        r = a.resources
        print(r)


# print card weights, normalized to cost of one action
def print_card_weights(gen):
    cw = gen.median.card_weights
    cw = normalize(cw, gen.median.weights['action'])
    cwt = [(k, v) for k, v in cw.items()]
    cwt.sort(key=lambda x: x[1])
    print(cwt)


# print weights of resources, normalized to cost of one action
def print_resource_weights(gen):
    print(normalize(gen.median.weights, gen.median.weights['action']))


from sys import argv

# for getting arguments:
potential_options = ['card_weights', 'resource_weights', 'end_resources', 'card_rates', 'full_game']
potential_roles = ['b', 'c', 'n', 'p']
tested_roles = []
options = []
hyperparameters = dict()
hyperparameters['num_agents'] = 500
hyperparameters['num_generations'] = 200
hyperparameters['mutation_rate'] = 0.5
hyperparameters['survival_rate'] = 0.75
hyperparameters['annealing_rate'] = 0.99

if '-h' in argv:
    print(
        'Use \t-b,\t-c,\t-n,\t-p\t as arguments for training Bourgiousie, Committee of Public Safety, Nobles, and Peasants respectively')
    print(
        'Training agents without any other arguments will be useless. Add an option beginning with a hyphen to see various resulting statistics')
    print('Optional arguments:')
    print(
        '\t"-resource_weights": for each trained agent at the end, print the weights that it has for each resource after training (very useful)')
    print(
        '\t"-card_weights": for each trained agent at the end, print the weights that it has for each card after training (long)')
    print(
        '\t"-end_resources": for each final generation, print the final resource counts for each agent in the generation. Useful for finding how they won.')
    print(
        '\t"-card_rates": print the percentage that each card was picked any time someone had the ability to buy it. (including its costs) Useful for finding cards that are over or under powered.(long)')

    print(
        '\t"-full_game": must enable all four agents for this option to work. Carries out 1000 full games with each agent taking turns in order and prints out win rates. After, it prints one run through of the game turn by turn.')
    print(
        '\t\tNote: The majority winner changes a lot depending on how well each agent learns the design space. Sometimes one class will win every time, but that class can be different on a different run of the sim.')
    print()
    print(
        'The hyperparameters of the genetic algorithm can also be adjusted, but these have reasonable default values.')
    print('Hyperparameters are specified with the format [paramter]=[value], ex. mutation_rate=0.1')
    print('\t"num_agents": default=500. Specifies number of agents in each generation')
    print('\t"num_generations": default=200. Specifies number of generations per training of each role.')
    print('\t"mutation_rate": default=0.5. Specifies how much the weights mutate each generation.')
    print(
        '\t"survival_rate": default=0.75. Specifies what proportion of the population of each generation survives each iteration.')
    print('\t"annealing_rate": default=0.99. Specifies the annealing rate of mutation.')

    print()
    print(
        'If no arguments are used, all four agents will be trained, then a simulation of a full game will be carried out.')

    quit()

for i in range(1, len(argv)):
    if argv[i][0] == '-':
        arg = argv[i][1:]
        if arg in potential_options:
            options.append(arg)
        elif arg in potential_roles:
            tested_roles.append(arg)
        else:
            print(f'INVALID PARAMETER: {argv[i]}')
            quit()
    elif '=' in argv[i] and argv[i].split('=')[0] in hyperparameters.keys():
        if argv[i].split('=')[0] in ('num_agents', 'num_generations'):
            hyperparameters[argv[i].split('=')[0]] = int(argv[i].split('=')[1])
        else:
            hyperparameters[argv[i].split('=')[0]] = float(argv[i].split('=')[1])
    else:
        print(f'INVALID PARAMETER: {argv[i]}')
        quit()

if len(argv) == 1:
    # no arguments
    tested_roles.extend(['b', 'c', 'p', 'n'])
    options.append('resource_weights')
    options.append('full_game')

if len(tested_roles) < 1:
    print('No roles selected to be trained. Use -h for help.')
    quit()

if 'full_game' in options and len(tested_roles) < 4:
    print('To simulate a full game, you need to enable all four roles. (-b, -c, -n, -p)')
    quit()
# for commuting the argument to the classes
agent_dict = {'b': ('Bourgeoisie', simulation.Bourgeoisie), 'c': ('Committee', simulation.Committee),
              'n': ('Nobles', simulation.Nobles), 'p': ('Peasants', simulation.Peasants)}

trained_agents = []
for role in tested_roles:
    print(f'training {agent_dict[role][0]}')
    # get the last generation, trained
    a = train_agent(agent_dict[role][1], hyperparameters['num_agents'], hyperparameters['num_generations'],
                    hyperparameters['mutation_rate'], hyperparameters['survival_rate'],
                    hyperparameters['annealing_rate'])
    # get a copy of the median agent in the generation
    trained_agents.append(a.median.duplicate())

    if 'card_weights' in options:
        print()
        print_card_weights(a)
    if 'resource_weights' in options:
        print()
        print_resource_weights(a)
    if 'end_resources' in options:
        print()
        print_win_cons(a)

    print(
        f'Number of turns to win for best: {a.best.num_turns}, median: {a.median.num_turns}, worst: {a.worst.num_turns}')
    print()

if 'full_game' in options:
    winners = defaultdict(int)
    for i in range(1000):
        victor = simulation.full_game(trained_agents, CARD_PILE, False)  # run a sim of the entire game
        winners[victor.__class__] += 1
        # print(victor.__class__)
    print(winners.items())  # print their win numbers

# print card rates
if 'card_rates' in options:
    rates = []
    for k, v in simulation.seen_cards.items():
        rates.append((k, simulation.selected_cards[k] / v))
    for k, v in sorted(rates, key=lambda x: x[1]):
        print(f'{k}: {round(v, 4) * 100}%')
