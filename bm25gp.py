# -*- coding: utf-8 -*-
#!/usr/bin/env python3
import sys
import os

import bm25
import lepref_util

from stopwords import porter2stemedstopwords as stopwords

import aol_parser

from estatisticas import load_results

from deap import algorithms
from deap import base
from deap import creator
from deap import tools
from deap import gp

import time

import pickle
import json

import random

#import numpy
import statistics

import operator

from datetime import datetime

varAnd = algorithms.varAnd

LOG = True

def main():
    if len(sys.argv) != 2:
        print('Python LePrEF 2015')
        print('Usage: python3 %s argv[1]' % sys.argv[0])
        print('argv[1]: Execution configuration file')
        print('\tJson Execution configuration file must have the attributes below:')
        print('\t  {')
        print('\t  ftrainame:\t\ttrain file name,')
        print('\t  fvaliname:\t\tvalidation file name,')
        print('\t  ftestname:\t\ttest file name,')
        print('\t  ffiltersresults:\tfilters result file name,')
        print('\t  foutputname:\tAOL output file name,')
        print('\t  resultdir:\t\tOut directory for results,')
        print('\t  randomseed:\t\tRandom Seed,')
        print('\t  popsize:\t\tPopulation size,')
        print('\t  generations:\tGenerations number,')
        print('\t  cxprob:\t\tCrossover Probability,')
        print('\t  mutprob:\t\tMutation Probability,')
        print('\t  hoflen:\t\tHall of Fame length')
        print('\t  }')
        return 1

    #Load config file
    fexecname = sys.argv[1]
    exec_config = load_config_file(fexecname)

    ftrainame = exec_config['ftrainame']
    fvaliname = exec_config['fvaliname']
    ftestname = exec_config['ftestname']
    ffiltersresults = exec_config['ffiltersresults']
    foutputname = exec_config['foutputname']
    resultdir = exec_config['resultdir']
    randomseed = int(exec_config['randomseed'])
    popsize = int(exec_config['popsize'])
    generations = int(exec_config['generations'])
    cxprob = float(exec_config['cxprob'])
    mutprob = float(exec_config['mutprob'])
    hoflen = int(exec_config['hoflen'])
    #end load config file

    #Set pset and toolbox
    pset = create_primaryset()
    toolbox = create_toolbox(pset)
    set_gpoperator(toolbox, pset)
    #set_evaluate(toolbox, evalQuery, queries, index, aolstats, results)

    #results
    filtersresults_data = load_results(ffiltersresults)['results']

    results = create_result_dict(filtersresults_data)

    #Get train data
    queries = lepref_util.carregar_queries(ftrainame)[0]
    #lepref_util.configurar_idcg_medio(queries, topN = MAXEVAL)

    #Create Bm25 Index
    index = bm25.Bm25Index()
    index.generate_from_queries(queries)

    #Set evaluate function and data
    aoldata, featurelist = aol_parser.output_read(foutputname)
    aolstats = process_aol_stats(aoldata)

    set_evaluate(toolbox, evalQuery, queries, index, aolstats, results)

    print(len(queries), 'consultas lidas!')
    if LOG:
        log_sfile = open(resultdir + os.sep + "logfile.log", "a+")
        print(len(queries), 'consultas lidas!', file = log_sfile)
        log_sfile.close()


    if os.path.exists(resultdir + os.sep + 'checkpoint.data'):
        #Load Checkpoint
        pop, igen, stats, hof, logbook, randomstate = load_checkpoint(resultdir)
        random.setstate(randomstate)

        #Configura toolbox

    else:
        igen = 0
        logbook = None
        pop, hof, stats = prepare_gp(toolbox, randomseed, popsize, hoflen)

#    eaCheckpoint(pop, cxprob, MutProb, igen, generations, stats, halloffame=hof,
#                         logbook=logbook, cpfile_location = dirresult)
    eaCheckpoint(pop, toolbox, cxprob, mutprob, igen, generations, resultdir, stats, halloffame=hof,
             logbook=logbook)

def create_primaryset():
    ##Set Individual
    pset = gp.PrimitiveSet("MAIN", 9, "FEAT")
    pset.renameArguments(FEAT0 = "posQuery",
                         FEAT1 = "posBiGram1",
                         FEAT2 = "posBiGram2",
                         
                         FEAT3 = "queryFRel",
                         FEAT4 = "firstFRel",
                         FEAT5 = "secondFRel",
                         FEAT6 = "midFRel",
                         FEAT7 = "penultFRel",
                         FEAT8 = "lastFRel",
    )

    ##Operadores
    pset.addPrimitive(operator.add, 2)
    pset.addPrimitive(operator.sub, 2)
    pset.addPrimitive(operator.mul, 2)
    # floating point operators
    # Define a safe division function
    pset.addPrimitive(safeDiv, 2)
    pset.addPrimitive(minusSafeDiv, 2)

    return pset

def create_toolbox(pset):
    ##Set Fitness
    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMax)

    ##Set Toolbox
    toolbox = base.Toolbox()

    toolbox.register("expr", gp.genHalfAndHalf, pset=pset, min_=2, max_=6)
    toolbox.register("individual", tools.initIterate,
                        creator.Individual, toolbox.expr)
    #Population
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    toolbox.register("compile", gp.compile, pset=pset)

    return toolbox

def set_gpoperator(toolbox, pset):
    toolbox.register("select", tools.selTournament, tournsize=6) #Tamanho do torneio
    toolbox.register("mate", gp.cxOnePoint)
    toolbox.register("expr_mut", gp.genHalfAndHalf, min_=0, max_=4)
    toolbox.register("mutate", gp.mutUniform, expr=toolbox.expr_mut, pset=pset)
    toolbox.decorate("mate",
      gp.staticLimit(operator.attrgetter('height'), 12)) # Profundidade da arvore
    toolbox.decorate("mutate",
      gp.staticLimit(operator.attrgetter('height'), 12)) # Profundidade da arvore

def set_evaluate(toolbox, function, queries, index, aolstats, results):
    ##Configuração evaluate
    toolbox.register("evaluate", function, toolbox,
      queries = queries, index = index, aolstats = aolstats, results = results)

def prepare_gp(toolbox, randomseed, popsize, hoflen):
    random.seed(randomseed)
    pop = toolbox.population(n=popsize)
    hof = tools.HallOfFame(hoflen)
    stats = tools.Statistics(fitnessvalues)
#    stats.register("avg", numpy.mean)
#    stats.register("std", numpy.std)
#    #stats.register("min", numpy.min)
#    stats.register("max", numpy.max)
    #lambda data: max(x[0] for x in data)
    stats.register("avg", mean)
    stats.register("std", pstdev)
    #stats.register("min", numpy.min)
    stats.register("best", statmax)
    stats.register("time", tempo)
    return pop, hof, stats

def statmax(data):
    return max(x[0] for x in data)

#lambda data: statistics.mean(x[0] for x in data)
def mean(data):
    return statistics.mean(x[0] for x in data)

#lambda data: statistics.pstdev(x[0] for x in data)
def pstdev(data):
    return statistics.pstdev(x[0] for x in data)

done = 0
#Evaluation
def evalQuery(toolbox, individual, queries, index, aolstats, results):
#    global func
#    if not func:
#        func = toolbox.compile(expr=individual)
#    elif random.uniform(0,1) < 0.001:
#        func = toolbox.compile(expr=individual)
    funccompile_start = time.time()
    func = toolbox.compile(expr=individual)


    mean_ndcg = meanFilterBm25(func, queries, index, aolstats, results)

    funccompile_end = time.time()
    global done
    done += 1
    sys.stdout.write("\r\033[K")
    print('\rEval time: %f\tDone: %d/%d' %  (funccompile_end - funccompile_start, done, tobedone), end = '')
    if done == tobedone:
        sys.stdout.write("\r\033[K")
        done = 0
    return mean_ndcg,

def meanFilterBm25(func, queries, index, aolstats, results):
    mean_ndcg_acc = 0.0
    for qi, query_object in enumerate(queries):
        query = ' '.join(term.word for term in query_object.term)
        filters = calc_filter(func, query, index = index, aolstats = aolstats)
        mean_ndcg_acc += results[query_object.queryid][filters]

    return mean_ndcg_acc / len(queries)
    #return statistics.mean(results[query.queryid][calc_filter(func, ' '.join(term.word for term in query.term))] for query in queries)

def calc_filter(func, query, index = None, aolstats = None):
    terms_features = find_features(query, index, aolstats)
    #remove_stopwords
    nw_features = (term_feature[1] for term_feature in terms_features if term_feature[0] not in stopwords)
    #for each term calc_filter with func
    terms_filters = (apply_fitness_filter_rule(func(*term_feature)) for term_feature in nw_features)
    return tuple(terms_filters)

def apply_fitness_filter_rule(fitness_value):
    if -1 <= fitness_value <= 1:
        return 1
    elif fitness_value > 1:
        return 2
    else:
        return 3

def find_ngrams(input_list, n):
  return list(zip(*[input_list[i:] for i in range(n)]))

def find_features(query, index, aolstats):
    term_list = query.split()
    bigrams = find_ngrams(term_list, 2)
    features = list()
    for pos, term in enumerate(term_list):
            term_features = list()
            term_features.append(relative_pos(term, term_list))
            term_bigrams = find_rest(pos, len(term_list), 2, bigrams)
            for term_bigram in term_bigrams:
                term_features.append(relative_pos(term, term_bigram,))

            stats = aolstats['stats']
            termstats = aolstats['termstats']
            for stat in stats:
                term_features.append(termstats[term][stat[0]])

            features.append((term, term_features,))
    return features

def relative_pos(term, term_list):
    if not term_list:
        return 0
    if term == term_list[0]:
        return 5
        #return 0
    if term == term_list[-1]:
        return 4
        #return -1
    if term == term_list[1]:
        return 3
        #return  1
    if term == term_list[-2]:
        return 2
        #return -2
    try:
        term_list.index(term)
        return 1
        #return 3
    except ValueError as err:
        #print('list>', term_list)
        #raise err
        return 0

find_index_first = lambda x, n: 0 if x < n else x-n+1

def find_rest(pos, nterms, n, ngrams):
    before = 0
    after = 0
    if pos + 1 - n < 0:
        before =  n - pos -1
    if n - (nterms - pos) > 0:
        after =  n - (nterms - pos) 
    first = find_index_first(pos, n)
    rest = [None] * before + list(ngrams)[first: first +n - before - after] + [None] * after
    return rest

def process_aol_stats(aoldata):
    nqueries = aoldata['nqueries']
    aolterms = aoldata['aolterms']
    termstats = dict()
    stats = [
        ('queryfrel', lambda **args: args['count']/args['countq']),
        ('firstfrel', lambda **args: args['first']/args['count']),
        ('secondfrel', lambda **args: args['second']/args['count']),
        ('midfrel', lambda **args: args['mid']/args['count']),
        ('penultfrel', lambda **args: args['penult']/args['count']),
        ('lastfrel', lambda **args: args['last']/args['count']),
    ]
    
    for term in aolterms:
        termstats[term] = dict((stat[0], stat[1](**aolterms[term])) for stat in stats)

    aolstats = dict(termstats = termstats, stats = stats)
    return aolstats

def create_result_dict(filtersresults):

    results_data = dict()

    #query.queryid, termslist, productsresults
    for queryid, termslist, productsresults in filtersresults:
        results_data[queryid] = dict()
        for filterproduct, filterresult in productsresults:
            results_data[queryid][filterproduct] = filterresult

    return results_data

#Evolution
def eaCheckpoint(population, toolbox, cxpb, mutpb, igen, ngen, dirresult, stats=None, halloffame=None,
             logbook=None, verbose=__debug__):

    global tobedone

    if igen == 0:
        logbook = tools.Logbook()
        logbook.header = ['gen', 'nevals'] + (stats.fields if stats else [])

        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in population if not ind.fitness.valid]
        tobedone = len(invalid_ind)
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        if halloffame is not None:
            halloffame.update(population)

        record = stats.compile(population) if stats else {}
        logbook.record(gen=0, nevals=len(invalid_ind), **record)
        igen = 1 #Incrementa o igen para continuar a evolucao

        if verbose:
            print(logbook.stream)

        if LOG:
            log_sfile = open(dirresult + os.sep + "logfile.log", "a+")
            print(logbook.__str__(len(logbook)-1), file = log_sfile)
            log_sfile.close()

        checkpoint(population, 0, stats, halloffame, logbook, cpfile_location = dirresult)

    # Begin the generational process
    for gen in range(igen, ngen+1):
        # Select the next generation individuals
        offspring = toolbox.select(population, len(population))
        
        # Vary the pool of individuals
        offspring = varAnd(offspring, toolbox, cxpb, mutpb)
        
        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        tobedone = len(invalid_ind)
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit
        
        # Update the hall of fame with the generated individuals
        if halloffame is not None:
            halloffame.update(offspring)
            
        # Replace the current population by the offspring
        population[:] = offspring
        
        # Append the current generation statistics to the logbook
        record = stats.compile(population) if stats else {}
        logbook.record(gen=gen, nevals=len(invalid_ind), **record)

        if verbose:
            print(logbook.stream)

        if LOG:
            log_sfile = open(dirresult + os.sep + "logfile.log", "a+")
            print(logbook.__str__(len(logbook)-1), file = log_sfile)
            log_sfile.close()

        checkpoint(population, gen, stats, halloffame, logbook, cpfile_location = dirresult)

    return population, logbook

def checkpoint(population, gen, stats,
               halloffame, logbook, cpfile_location):
    dadoscp = dict(population = population, gen = gen,
          stats = stats, halloffame = halloffame, logbook = logbook,
          rndstate = random.getstate())
    with open(cpfile_location + os.sep + 'checkpoint.data', "wb") as cp_file:
        pickle.dump(dadoscp, cp_file)

def load_checkpoint(cpfile_location):
    # Se sim, carrega o checkpoint
    with open(cpfile_location + os.sep + 'checkpoint.data', "rb") as cp_file:
        dadoscp = pickle.load(cp_file)
    pop = dadoscp["population"]
    igen = dadoscp["gen"] + 1
    stats = dadoscp["stats"]
    hof = dadoscp["halloffame"]
    logbook = dadoscp["logbook"]
    randomstate = dadoscp["rndstate"]
    return pop, igen, stats, hof, logbook, randomstate

def load_config_file(fexecname):
    with open(fexecname, 'r') as config_file:
        config_string=config_file.read()

    return json.loads(config_string)

#lambda x, y : x/y if y != 0 else 0
def safeDiv(left, right):
    if right == 0:
        return 0
    else:
        #return operator.itruediv(left , right)
        return left / right

#lambda x, y : x/y if y != 0 else 0
def minusSafeDiv(left, right):
    return -safeDiv(left, right)

#lambda tempo: datetime.now()
def tempo(*args):
    return datetime.now()

#lambda ind: ind.fitness.values
def fitnessvalues(ind):
    return ind.fitness.values

if __name__ == '__main__':
    sys.exit(main())
