import pyvrp as p
from pyvrp.search import (
    LocalSearch,
    NODE_OPERATORS,
    ROUTE_OPERATORS,
    compute_neighbours,
)
from pyvrp.diversity import broken_pairs_distance
from pyvrp.crossover import selective_route_exchange as srex
from pyvrp.stop import MaxRuntime
import argparse
import os


# Ej de linea de ejecucion
# python3 SolveVRP.py -i ../instancias/solomon/RC208.txt -ps 25 -gs 40 -ne 0.1 -nc 0.1 -xi 0.4 -t 10 -s 42

# Parser de argumentos
parser = argparse.ArgumentParser(prog="pyVRP-Interface",
                                 description="Executes pyVRP with a given instance to solve the routing problem")
parser.add_argument("-i", "--instance")
parser.add_argument("-ps", "--pop_size", type=int)
parser.add_argument("-gs", "--gen_size", type=int)
parser.add_argument("-ne", "--n_elite", type=float)
parser.add_argument("-nc", "--n_closest", type=float)
parser.add_argument("-xi", "--xi_ref", type=float)
parser.add_argument("-t", "--time", type=int)
parser.add_argument("-s", "--seed", type=int)
args = parser.parse_args()

#Leemos instancia (homberger tambien es formato solomon)
INSTANCE = p.read(args.instance, "solomon", "round")

#Creamos nuestra propia función solve que acepta parametros de poblacion
def solve(stop, seed, population_params):
    rng = p.RandomNumberGenerator(seed=seed)
    pm = p.PenaltyManager()
    pop = p.Population(broken_pairs_distance,population_params)
    neighbours = compute_neighbours(INSTANCE)
    ls = LocalSearch(INSTANCE, rng, neighbours)
    for node_op in NODE_OPERATORS:
        ls.add_node_operator(node_op(INSTANCE))
    for route_op in ROUTE_OPERATORS:
        ls.add_route_operator(route_op(INSTANCE))
    init = [p.Solution.make_random(INSTANCE, rng) for _ in range(population_params.min_pop_size)]
    algo = p.GeneticAlgorithm(INSTANCE, pm, rng, pop, ls, srex, init)
    return algo.run(stop)

# Lectura de parametros por argparser.
# nb_elite y nb_close entran como float proporcional a pop_size (mu).
# Luego entran a pyVRP como int para compatibilidad.
params = p.PopulationParams(min_pop_size=args.pop_size,
                          generation_size=args.gen_size,
                          nb_elite=int(args.pop_size*args.n_elite),
                          nb_close=int(args.pop_size*args.n_closest),
                          lb_diversity=float(args.xi_ref) - 0.1,
                          ub_diversity=float(args.xi_ref) + 0.1)
res = solve(stop=MaxRuntime(args.time), seed=args.seed, population_params=params)
print(res.cost())