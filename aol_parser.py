# -*- coding: utf-8 -*-
#!/usr/bin/env python3
import sys
import os
import porter2
import pickle
from bm25 import Bm25Index

def main():
    if len(sys.argv) != 3:
        print('AOL Parser - Load aol file directory and then print formated output')
        print('    Use: python3 %s arg[1] arg[2]' % sys.argv[0])
        print('        arg[1]: AOL files directory')
        print('        arg[2]: Queries data file')
        return 1
    aoldirname = sys.argv[1]
    datafname = sys.argv[2]

    #Configure Futures
    features = dict()
    featurelist = [('count', _count),
                   ('countq', _countq),
                   ('first', _count_first),
                   ('second', _count_second),
                   ('mid', _count_mid),
                   ('penult', _count_penult),
                   ('last', _count_last)
                   ]

    for featurename, featurefunction in featurelist:
        add_feature(features, featurename, featurefunction)
#    add_feature(features, 'count', _count)
#    add_feature(features, 'first', _count_first)
#    add_feature(features, 'second', _count_second)
#    add_feature(features, 'penult', _count_penult)
#    add_feature(features, 'mid', _count_mid)

    queries, index = load_data(datafname)
    aoldate = read_aol(aoldirname, features, index)
    print_data(aoldate, [feat[0] for feat in featurelist])

#Features
def _countq(querylist, aoldata, index, features):
    querylistset = set(querylist)
    for pos, term in enumerate(querylistset):
        #Validate term [Not part of the feature define yet]
        if index.get(term):
            aolterm = load_term(aoldata, term, features)
        #End
            #Feature definition
            aolterm['countq'] += 1

def _count(querylist, aoldata, index, features):
    for pos, term in enumerate(querylist):
        #Validate term [Not part of the feature define yet]
        if index.get(term):
            aolterm = load_term(aoldata, term, features)
        #End
            #Feature definition
            aolterm['count'] += 1

def _count_first(querylist, aoldata, index, features):
    for pos, term in enumerate(querylist):
        #Validate term [Not part of the feature define yet]
        if index.get(term):
            aolterm = load_term(aoldata, term, features)
        #End

            #Feature definition
            if pos == 0:
                aolterm['first'] += 1

def _count_second(querylist, aoldata, index, features):
    for pos, term in enumerate(querylist):
        #Validate term [Not part of the feature define yet]
        if index.get(term):
            aolterm = load_term(aoldata, term, features)
        #End
            #Feature definition
            if len(querylist) > 1 and pos == 1:
                aolterm['second'] += 1

def _count_penult(querylist, aoldata, index, features):
    for pos, term in enumerate(querylist):
        #Validate term [Not part of the feature define yet]
        if index.get(term):
            aolterm = load_term(aoldata, term, features)
        #End
            #Feature definition
            if pos == len(querylist) - 2:
                aolterm['penult'] += 1

def _count_last(querylist, aoldata, index, features):
    for pos, term in enumerate(querylist):
        #Validate term [Not part of the feature define yet]
        if index.get(term):
            aolterm = load_term(aoldata, term, features)
        #End
            #Feature definition
            if pos == len(querylist) - 1:
                aolterm['last'] += 1

def _count_mid(querylist, aoldata, index, features):
    for pos, term in enumerate(querylist):
        #Validate term [Not part of the feature define yet]
        if index.get(term):
            aolterm = load_term(aoldata, term, features)
        #End
            #Feature definition
            if pos >= 2 and pos < len(querylist) - 2:
                aolterm['mid'] += 1

def load_term(aoldata, term, features):
    if aoldata['aolterms'].get(term) == None:
        aoldata['aolterms'][term] = dict()
        for feature in features:
            aoldata['aolterms'][term][feature] = 0
    return aoldata['aolterms'][term]


def add_feature(features, featurename, featurefunction):
    if not features.get(featurename):
        features[featurename] = featurefunction
    else:
        raise(Exception('Feature already exists.'))

def read_aol(aoldirname, features, index):
    aoldirflist = os.listdir(aoldirname)
    ignorelist = [fname for fname in aoldirflist if fname.split('.')[-1] != 'txt']
    aolfnamelist = [fname for fname in aoldirflist if fname.split('.')[-1] == 'txt']
    if ignorelist:
        print(Ignoring)
        for ignore in ignorelist:
            print('#' + ignore)

    aoldata = {'aolterms': dict(),
               'nqueries': 0}

    for aolfname in aolfnamelist:
        print('#' + 'Processing %s...' % aolfname)
        run_aol(aoldirname + os.sep + aolfname, features, aoldata, index)

    return aoldata

def output_read(foutputname):
    aolterms = dict()
    nqueries = 0
    featurelist = None
    with open(foutputname, "r") as output:
        for nline, line in enumerate(output):
            if line:
                if featurelist != None and nqueries!= 0 and line[0] != '#':
                    linelist = line.rstrip().split()
                    term = linelist[0]
                    term_features = [int(feature) for feature in linelist[1:]]
                    aolterms[term] = dict(zip(featurelist, term_features))
                else:
                    if line[0] == '#':
                        linelist = line.rstrip().replace('#','', 1).split()
                        if linelist[0] == 'term':
                            featurelist = linelist[1:]
                        elif linelist[0] == 'nqueries:':
                            nqueries = int(linelist[1])
                    else:
                        raise ValueError('Unexpected entry on line %s: %s' % (str( nline + 1), line))
    aoldata = dict(aolterms = aolterms, nqueries = nqueries)
    return aoldata, featurelist

def load_aol(faoldataname):
    with open(faoldataname, "rb") as data_file:
        aoldata = pickle.load(data_file)
    return aoldata

def save_aol(aoldata, faoldataname, featurelist):
    data_buff = dict(aoldata = aoldata, featurelist = featurelist)
    with open(faoldataname, "wb") as data_file:
        pickle.dump(data_buff, data_file)

def run_aol(aolfname, features, aoldata, index):
    with open(aolfname, 'r') as aoffile:
        for line in aoffile:
            #Get only AnonID and Query
            anonid, query = line.split('\t', 2)[:2]
            if anonid.isnumeric():
                listterm = pre_process(query, stem = True)
                for feature in features:
                    function = features[feature]
                    function(listterm, aoldata, index, features)
                aoldata['nqueries'] += 1

def pre_process(query, stem = True):
    listterm = list()
    if stem:
        listterm = [porter2.stem(term) for term in query.split()]
    else:
        listterm = query.split()
    return listterm

def find_ngrams(input_list, n):
  return zip(*[input_list[i:] for i in range(n)])

def print_data(aoldata, featurelist):
    print('#nqueries:', aoldata['nqueries'])
    print('#nterms:', len(aoldata['aolterms']))
    print('#' + '\t'.join(['term'] + featurelist))
    for aolterm in aoldata['aolterms']:
        print('\t'.join([aolterm] + [str(aoldata['aolterms'][aolterm][feat]) for feat in featurelist]))

def load_data(fdataname):
    '''
'''
    with open(fdataname, "rb") as data_file:
            data = pickle.load(data_file)
    return data['queries'], data['index']

if __name__ == '__main__':
    sys.exit(main())
