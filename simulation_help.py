reward_dict = {'national freedom': 'nf', 'gold per turn': 'gpt', 'food per turn': 'fpt', 'loyalty': 'l',
               'armaments': 'w', 'gold': 'g', 'food': 'f', 'assembly': 'a'}

starting_weights = {'g': 1.0, 'f': 0.66, 'l': 5.0, 'a': 6.0, 'nf': 2.75, 'gpt': 5.4, 'fpt': 4.8, 'w': 2.5,
                    'action': 1.7}


# mostly dealing with the cards in this file
class Card:
    def __init__(self, name, costs, requirements, results, num, roles,
                 is_major=False):  # cost and results are dictionaries
        self.name = name
        self.costs = costs
        self.requirements = requirements
        self.results = results
        self.count = num
        self.roles = roles

        self.is_major = is_major

    def value(self, weights):
        # get the value of this card based on weights
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
    # takes in text from my csv file of cards turns it into a cost dictionary
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
    # takes in text from my csv file of cards turns it into a reward dictionary
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


# hard coded cards
hard_cards = dict()
hard_cards['imperialism'] = Card('imperialism', {'w': 3, 'f': 3}, {'l': 3}, {'gpt': 1, 'fpt': 1}, 1,
                                 ['n', 'b', 'c', 'a'], True)
fake_majors = ['build factory', 'build trading post', 'build farm', 'crop rotation']


def line_to_card(line):
    #gets one line and turns it into a card
    line = line.split('\t')
    name = line[0].lower()
    if name in hard_cards.keys():
        return hard_cards[name]
    ct = line[2]
    rq = line[3]
    rt = line[4]
    who = line[5].lower()
    is_major = line[6]
    num = int(line[8])

    cost = text_to_cost(ct)
    reqs = text_to_cost(rq)
    reward = text_to_reward(rt)

    is_major = is_major == '1' or name in fake_majors

    if 'any' in who:
        roles = ['p', 'b', 'c', 'n']
    else:
        who = who.split(',')
        roles = []
        for i in who:
            roles.append(i.strip()[0])

    c = Card(name, cost, reqs, reward, num, roles, is_major)

    return c


def read(filepath):
    # reads a whole file and turns it into cards.
    # only to be used with cards.csv, a file generated from an excel sheet of all the cards
    cards = []
    with open(filepath, 'r') as f:
        lines = f.readlines()
        first = True
        for line in lines:
            if first:
                first = False
                continue
            c = line_to_card(line)
            for i in range(c.count):
                cards.append(c)
    return cards
