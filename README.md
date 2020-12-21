# french-rev-sim

Months ago, I designed a physical paper board game based on the French Revolution with my brother. There are four classes/roles each with orthogonal goals and they compete to finish them first.

The game has 6 resources: Gold, Food, Weapons, Assembly seats, Loyalty, and National Freedom (National Freedom is a shared resource which can go up and down).
The four agents are Nobles, Bourgeoisie, Committee of Public Safety, and Peasants
Each agent must complete 2 out of the 3 of its possible goals
Some of the goals are simply reaching a number of resources, others are reached by taking a specific action card
Nobles:
1. Have the plurality of assembly seats (in simulation, >= 10)
2. National Freedom is at 1 (it starts at 5)
3. 30 Gold and 10 Weapons
Bourgeoisie:
1. Have the plurality of assembly seats (in simulation, >= 10)
2. Enter Enlightenment (action card, costs 2 Assembly seats and 4 Food) and have 7 loyalty
3. National Freedom is at 9 (it starts at 5)
Committee of Public Safety:
1. Guillotine King Louis XVI (action card, costs 2 Weapons and 1 Loyalty)
2. Kill enemy of revolution 3 times (action card, costs 2 Weapons and 2 Loyalty)
3. Control the majority of Weapons in play (in simulation, >= 15)
Peasants:
1. Abolish Feudalism (action card, costs 3 Weapons and 2 Assembly Seats)
2. Have more assembly seats than the nobles (in the simulation, just >= 10)
3. Have 15 Food
I can provide a list of actions, but there are 67 of them. I have them in a .tsv format where it is easy to parse in order to get the requirements, cost, and reward. Each action essentially just modifies the resources of an agent.
The game works by drawing 9 from the deck at a time and the player picks one.
An example of an action card is:
Guillotine Marie Antionette
Requires: 4 Weapons, 3 Loyalty (you must have at least this amount, but does not spend it)
Costs: 2 Weapons (Spend 2 weapons)
Reward: Food + 5, National Freedom + 1
 
The cards' costs and effects apply instantly upon choosing.


The first step was digitizing the rules of the board game such that a simulation would be an effective measure of role power. It was quite conducive to this step because of the relatively simple gameplay loop and because I already had all the action cards stored in a tsv format.
Then, I created a simulation of one agent playing a game by itself. The game does not have too much interactivity among the players, so this simulation style provides an easy way to test the agent’s efficacy. The simulation is entirely turn based, so all the events happen in a programmatically predictable manner, thus I don’t have to use any time-based simulation techniques. Each agent has a stored representation of how much it weights each resource in the game, as well as weights for each card. The agents make actions based on their heuristic “value” of a card. They estimate how good a card is by taking their internal resource weights (as well as the card weight for that card), and projecting them onto the cards costs and effects. Essentially, the (weights * results) - (weights * costs). Because a good card will result in good resources, so the individual card weights are somewhat redundant except for unique cards.
I chose to use a heuristic rather than something like MCTS or Alpha Beta pruning because of simplicity, speed, and its fit to the particular problem. Weighting each resource resembles how a human would determine which cards to play, so we get a good representation of the “reason” the agent is picking certain cards.
The genetic algorithm consists of generations of hundreds of agents (all the same role), that play out games by themselves. The survival of agents in each generation is determined by the number of turns it takes to reach their goals. The surviving agents are reproduced and their internal weights of resources and cards are mutated. After a few hundred generations, only the agents with an accurate representation of how much the cards and resources are worth survive, and tend to finish in a number of turns comparable to that of a real game. I’ve played this game with friends and family, the average number of turns it takes is around 25, similar to the simulated 20-30 turns of the agents. 
We made rule adjustments in the board game based on results of the simulation, and after more playtesting we could tell it was more balanced than before, showing its validity.


How to Run my Board Game Simulation:

Run the file "run_genetic.py"

python3 run_genetic.py
(with optional arguments listed below)


Use 	-b,	-c,	-n,	-p	 as arguments for training Bourgiousie, Committee of Public Safety, Nobles, and Peasants respectively
Training agents without any other arguments will be useless. Add an option beginning with a hyphen to see various resulting statistics
Optional arguments:
	"-resource_weights": for each trained agent at the end, print the weights that it has for each resource after training (very useful)
		Note: g is gold, f is food, w is weapons (sometimes called armaments), l is loyalty, a is assemby seats, nf is national freedom
	"-card_weights": for each trained agent at the end, print the weights that it has for each card after training (long)
	"-end_resources": for each final generation, print the final resource counts for each agent in the generation. Useful for finding how they won.
	"-card_rates": print the percentage that each card was picked any time someone had the ability to buy it. (including its costs) Useful for finding cards that are over or under powered.(long)
	"-full_game": must enable all four agents for this option to work. Carries out 1000 full games with each agent taking turns in order and prints out win rates. After, it prints one run through of the game turn by turn.
		Note: The majority winner changes a lot depending on how well each agent learns the design space. Sometimes one class will win every time, but that class can be different on a different run of the sim.

The hyperparameters of the genetic algorithm can also be adjusted, but these have reasonable default values.
Hyperparameters are specified with the format [paramter]=[value], ex. mutation_rate=0.1
	"num_agents": default=500. Specifies number of agents in each generation
	"num_generations": default=200. Specifies number of generations per training of each role.
	"mutation_rate": default=0.5. Specifies how much the weights mutate each generation.
	"survival_rate": default=0.75. Specifies what proportion of the population of each generation survives each iteration.
	"annealing_rate": default=0.99. Specifies the annealing rate of mutation.

If no arguments are used, all four agents will be trained, then a simulation of a full game will be carried out.
