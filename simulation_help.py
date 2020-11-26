reward_dict = {'national freedom': 'nf', 'gold per turn': 'gpt', 'food per turn': 'fpt', 'loyalty': 'l',
               'armaments': 'w', 'gold': 'g', 'food': 'f', 'assembly': 'a'}

starting_weights = {'g': 1.0, 'f': 0.66, 'l': 5.0, 'a': 6.0, 'nf': 2.75, 'gpt': 5.4, 'fpt': 4.8, 'w': 2.5,
                    'action': 1.7}


class Card:
    def __init__(self, name, costs, requirements, results, num):  # cost and results are dictionaries
        self.name = name
        self.costs = costs
        self.requirements = requirements
        self.results = results
        self.count = num
        self.roles = []

    def value(self, weights):
        return round(self.total_reward(weights) - self.total_cost(weights), 3)

    def total_cost(self, weights):
        c = 0
        for k, v in self.costs.items():
            c += weights[k] * v
        c += weights['action']
        return c

    def total_reward(self, weights):
        r = 0
        for k, v in self.results.items():
            r += weights[k] * v
        return r


def text_to_cost(cost_text):
    if cost_text == '':
        return dict()
    cost = cost_text.split(',')
    cdict = dict()
    for c in cost:
        c = c.split(':')
        a = c[0].strip().lower()
        b = int(c[1].strip())
        cdict[a] = b

    return (cdict)


def text_to_reward(text_reward):
    reward_list = ['national freedom', 'gold per turn', 'food per turn', 'loyalty', 'armaments', 'gold', 'food',
                   'assembly']
    numbers = [str(i) for i in range(1, 10)]
    rdict = dict()
    text_reward = text_reward.lower()
    if 'or' in text_reward:
        text_reward = text_reward.split('or')[1]
    for re in reward_list:
        if re in text_reward:
            splitted = text_reward.split(re)
            after = splitted[1]
            num = -1
            broken = False
            while after[0] not in numbers:
                if after[0] == ' ':
                    # skip
                    pass
                elif after[0] == '+':
                    # good to go
                    if after[1] == '/':  # for national freedom
                        after = after[2:]
                elif after[0] == '-' and re == 'national freedom':
                    pass
                else:
                    broken = True
                    break
                after = after[1:]
            if not broken:
                num = int(after[0])
                rdict[reward_dict[re]] = num

    return rdict


def line_to_card(line):
    line = line.split('\t')
    name = line[0].lower()
    ct = line[2]
    rq = line[3]
    rt = line[4]
    who = line[5].lower()
    num = line[8]
    cost = text_to_cost(ct)
    reqs = text_to_cost(rq)
    reward = text_to_reward(rt)
    c = Card(name, cost, reqs, reward, num)
    if 'any' in who:
        c.roles = ['p', 'b', 'c', 'n']
    else:
        who = who.split(',')
        c.roles = []
        for i in who:
            c.roles.append(i.strip()[0])
    return c


def read(filepath):
    cards = []
    with open(filepath, 'r') as f:
        lines = f.readlines()
        first = True
        for line in lines:
            if first:
                first = False
                continue
            cards.append(line_to_card(line))
    return cards


# cards = read('cards.tsv')
# cards = sorted(cards, key=lambda c: c.value(starting_weights))


def search():
    i = ''
    while i != 'q':
        i = input("pick a card: ")
        found = None
        for c in cards:
            if c.name.lower() == i:
                found = c
        if not found:
            print('not found')
        else:
            print(found.name)
            print('value :', found.value(starting_weights))
            print('cost :', found.total_cost(starting_weights))
            print('reward :', found.results)

