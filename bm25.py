# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import sys
import indexing

import itertools

import time

import pickle
import os

import lepref_util

import copy

from multiprocessing import Pool

DEBUG = False

CORES = 1

TOPN = 40

maxtime = 0.0

if len(sys.argv) != 4:
    print('Python 2015')
    print('Uso: python3 bm25.py argv[1]')
    print('argv[1]: arquivo da base de dados')
    print('argv[2]: nome do arquivo onde serão salvos os dados')
    print('argv[3]: nome do arquivo onde serão salvos os resultados')
#    print('argv[x]:')
    sys.exit(-1)
else:
    dbname = sys.argv[1]
    fdataname = sys.argv[2]
    fresultname = sys.argv[3]

#Filters
filters = {
    1 : {'name': 'default(or)', 'query': True, 'posproc': False},
    2 :     {'name': 'and', 'query': True, 'posproc': True},
    3 :  {'name': 'filter', 'query': False, 'posproc': True}
}


def main():

    if os.path.exists(fdataname):
        print("Carregando dados do arquivo ", fdataname, '...',sep = '')
        queries, index = load_data(fdataname)

    else:
        #Obter dados de treino
        print("Lendo queries...")
        queries, lista_invertida = lepref_util.carregar_queries(sys.argv[1])
        print('Queries lidas:', len(queries))

        index = Bm25Index()

        print("Adicionando queries ao índice")
        index.generate_from_queries(queries)

        save_data(queries, index, fdataname)

    lepref_util.configurar_idcg_medio(queries, topN = TOPN)

###Evaluations
##Simple
#    print('MeanNDCG: ', evaluate(queries, index, topN = TOPN))
##Filters permutations
    doit = False
    if os.path.exists(fresultname):
        print("Arquivo ", fresultname, " de resultado encontrado!", sep = '')

        while (True):
            inputstring = input('Deseja calcular novamente?(N,y): ')
            if inputstring in ['Y','y']:
                doit = True
                break

            elif inputstring in ['N','n', '']:
                print('Saindo...')
                sys.exit()
            else:
                print('Opção <', inputstring, '> Invalida!', sep='')
    else:
        doit = True

#    print_idf(index)
    if doit:
        print(count_execs(queries, qiini = 1, fiini = 0, qiend = 1, fiend = 1))
        results = evaluate_filters(queries, index, topN = TOPN, qiini = 1, fiini = 0, qiend = 1, fiend = 1)

        save_results(results, fresultname)
        print('Docs lidos:', len(index.doc))
        print('AVGDL:', index.avgdl)
        print('Vocabulary Length:', len(index))

class Bm25Index (indexing.Index):
    '''
'''
    def __init__(self,):
        indexing.Index.__init__(self)

    def generate_from_queries(self, queries):
        '''
    '''
        for query in queries:

            for doc in query.doc:
                docid = doc.docid
                doclen = doc.lenbody

                self.doc[docid] = doclen

                for term in doc.term:
                    doctf = term.tfdocument
                    #if (doctf > 0):
                    try:
                        self.add_term_doctf(term.word, docid, doctf)
                    except KeyError:
                        self.add_term(term.word)
                        self.add_term_doctf(term.word, docid, doctf)

        doclensum = sum(self.doc.values())
        self.avgdl = doclensum/len(self.doc)

        self._update_idf()
        self._generate_doc_dict()

    def simple_query(self, query, topN = TOPN):
        '''
    '''
        termlist = query.split()
        acc_dict = {}

        for term in termlist:
            if self.get(term):
#                for doc in self[term].doclist:
#                    if not acc_dict.get(doc.doc):
#                        acc_dict[doc.doc] = 0
#                    acc_dict[doc.doc] += self.partial_score(self[term], doc)
                #maxtopn
                i = 0
                while i < len(self[term].doclist) and i < TOPN:
                    doc = self[term].doclist[i]
                    if not acc_dict.get(doc.doc):
                        acc_dict[doc.doc] = 0
                    acc_dict[doc.doc] += self.partial_score(self[term], doc)
                    i += 1

        rank = sorted(acc_dict.items(), reverse = True, key = lambda x : x[1])

        return rank

    def filters_query(self, query, termsfilters = None, topN = TOPN):
        '''
    '''
        termlist = query.split()
        if termsfilters:
            if len(termlist) != len(termsfilters):
                print('TermList:', termlist)
                print('TermsFilters:', termsfilters)
                raise(Exception("Número de parâmetros diferentes do número de termos"))
        else:
            termsfilters = ['default']*len(termlist)
        #filter process
        querylist = []
        posproclist = []
        for i, term in enumerate(termlist):

            termfilter = termsfilters[i]
            if filters[termfilter]['query']:
                querylist.append(term)

            if filters[termfilter]['posproc']:
                posproclist.append(term)

        #execute query
        prerank = self.simple_query(' '.join(querylist))

        #process pos query
        rank = []

#        for rankresult in prerank:
#            global maxtime
#            start_time = time.clock()

#            if self.doc_has_terms(rankresult[0], posproclist):
#                rank.append(rankresult)

#            difftime = (time.clock() - start_time)
#            if difftime > maxtime:
#                maxtime = difftime
        #maxtopn
        i = 0
        while i < len(prerank) and len(rank) < topN:
            rankresult = prerank[i]
            global maxtime
            start_time = time.clock()

            if self.doc_has_terms(rankresult[0], posproclist):
                rank.append(rankresult)

            difftime = (time.clock() - start_time)
            if difftime > maxtime:
                maxtime = difftime
            i += 1

        return rank

    def doc_has_terms(self, docid, termslist):
        '''
    '''
        for term in termslist:
            try:
                if not self[term].in_doc(docid):
                    return False
            except KeyError:
                return False
        return True

    def _generate_doc_dict(self):
        '''
    '''
        for term in self:
            #maxtopn
            self[term].doclist.sort(reverse = True, key = lambda doc : doc.score)

            self[term].docdict = {doc.doc: (doc.doctf, doc.score) for doc in self[term].doclist}

def print_idf(index):
    for term in index:
        print(term+':', index[term].idf, end =  ' ')
        print("Ndocs:", len(index[term].doclist))

def print_doc(term):
    for i, doc in enumerate(term.doclist):
        print(i+1, doc)

def print_termdoc(queries):
    for query in queries:
        print('Query id:', query.queryid)
        print('Termos')
        for term in query.term:
            print(term.word)
        for doc in query.doc:
            print(doc.docid)
            termlist = [term.word for term in doc.term]
            print(termlist)

#            doclist = [doc.docid for doc in query.doc]
#            print(doclist)

def debug(*args, **kargs):
    '''
'''
    if DEBUG:
        print(*args, **kargs)

def save_data(queries, index, fdataname):
    '''
'''
    data_buff = dict(queries = queries, index = index)
    with open(fdataname, "wb") as data_file:
        pickle.dump(data_buff, data_file)

def load_data(fdataname):
    '''
'''
    with open(fdataname, "rb") as data_file:
            data = pickle.load(data_file)
    return data['queries'], data['index']

def save_results(results, fresultname):
    '''
'''
    result_buff = dict(results = results)
    with open(fresultname, "wb") as result_file:
        pickle.dump(result_buff, result_file)

def load_results(fresultname):
    '''
'''
    with open(fresultname, "rb") as result_file:
            data = pickle.load(result_file)
    return data['results']

def obter_vetor_ganho(rank, query):
    '''Description
'''
    vetor_ganho = []
    for doc in rank:
        vetor_ganho.append(obter_doc_label(doc[0], query))
    return vetor_ganho

def obter_doc_label(doc, query):
    #XXX Funciona mas não é a melhor forma
    for qdoc in query.doc:
        if doc == qdoc.docid:
            return qdoc.label
    return 0

def evaluate(queries, index, topN = TOPN):
    acumulador_ndcg = 0.0
    for query in queries:
        #rank = efetuar consulta
        rank = index.simple_query(' '.join([term.word for term in query.term]))
        ##computados
        #vetor_ganho_consulta = obter_vetor_ganho(rank, queries)
        vetor_ganho_consulta = obter_vetor_ganho(rank, query)
        #ndcg_q = lepref_util.ndcg_unico(vetor_ganho, query.idcg, topN, chave = lambda e: e[0])
        if (len(query.idcg) != 40): #TODO remover
            print(len(query.idcg), query.queryid)
        ndcg_q = lepref_util.ndcg_unico(vetor_ganho_consulta, query.idcg, topN, chave = lambda e: e)
        #query.mean_ndcg_atual = lepref_util.ndcg_medio_unico(ndcg_q)
        query.mean_ndcg_atual = lepref_util.ndcg_medio_unico(ndcg_q)
        #acumulador_ndcg += query.mean_ndcg_atual
        acumulador_ndcg += query.mean_ndcg_atual

    return acumulador_ndcg/len(queries)

def evaluate_filters(queries, index, topN = TOPN, qiini = None, fiini = None, qiend = None, fiend = None):
    start_time = time.time()
    print(time.strftime("Start at: %a, %d %b %Y %H:%M:%S", time.localtime()))

#    products = {}
    results = []
    countdict, totalqueries = count_execs(queries, qiini, fiini, qiend, fiend)
    queriesdone = 0

    try:
        queries = queries[qiini:qiend+1]
    except TypeError as error:
        if type(qiend) == type(None):
            queries = queries[qiini:]
        else:
            raise(error)

    for qi, query in enumerate(queries):
        termslist = [term.word for term in query.term]

        #n_jobs = len(productslist)
        n_jobs = len(filters) ** len(termslist)
        done = 0

        productsresults = []

        filteriterator = itertools.product(filters.keys(), repeat = len(termslist))
        if qi == 0 and fiini:
            if fiini < 0:
                print('fiini não pode ser negativo')
                print('fiini:', fiini)
                sys.exit()

            if fiini >= n_jobs:
                print('O número inicial do filtro não pode ser maior ou igual a quantidade de filtros ')
                print('fiini:', fiini)
                print('Nfiltros:', n_jobs)
                sys.exit()
            filteriterator = itertools.islice(filteriterator, fiini, n_jobs)

        if qi == len(queries)-1 and fiend:
            if fiend < 0:
                print('fiend não pode ser negativo')
                print('fiend:', fiend)
                sys.exit()

            if fiend >= n_jobs:
                print('O índice final de filtros não pode ser maior ou igual a quantidade de filtros ')
                print('fiend:', fiend)
                print('Nfiltros:', 3**query.n_term)
                sys.exit()
            filteriterator = itertools.islice(filteriterator, fiend+1)

        for fi, filterproduct in enumerate(filteriterator):

            #Evalue query
            rank = index.filters_query(' '.join(termslist), filterproduct)
            vetor_ganho_consulta = obter_vetor_ganho(rank, query)
            ndcg_q = lepref_util.ndcg_unico(vetor_ganho_consulta, query.idcg, topN, chave = lambda e: e)
            query.mean_ndcg_atual = lepref_util.ndcg_medio_unico(ndcg_q)

            queriesdone += 1
            #Process tracker
            #(56%) 1541 of 5125 queries. Query 650 processing (34%) 14 of 59 filters...
            print('\rExecs: %d/%d (%2.2f%%) Query: %d/%d (%2.2f%%) Processing %d/%d (%2.2f%%) %.1fq/s' % (
                  queriesdone + done, totalqueries, (queriesdone + done)/totalqueries * 100,
                  (qi+1), len(queries), (qi+1)/len(queries)  * 100,
                  fi+1, n_jobs, (fi+1)/n_jobs * 100
                  , (queriesdone) / (time.time() - start_time)), 
                  end = '')
            #Add result to products results
            
            productsresults.append((fi, query.mean_ndcg_atual))

        #Add query results to final results
        queryresult = (query.queryid, termslist, productsresults)
        results.append(queryresult)
    print('')
    print(time.strftime("Ends at: %a, %d %b %Y %H:%M:%S", time.localtime()))
    print("--- %s seconds ---" % (time.time() - start_time))
    return results

def evaluate_function(query, index, filterproduct, termslist, topN = TOPN):
    '''
'''
    rank = index.filters_query(' '.join(termslist), filterproduct)
    vetor_ganho_consulta = obter_vetor_ganho(rank, query)
    ndcg_q = lepref_util.ndcg_unico(vetor_ganho_consulta, query.idcg, topN, chave = lambda e: e)
    mean_ndcg_atual = lepref_util.ndcg_medio_unico(ndcg_q)

    return (filterproduct, mean_ndcg_atual)

def count_execs(queries, qiini = None, fiini = None, qiend = None, fiend = None):
    '''
'''
    nterm_count = dict()

    try:
        queries = queries[qiini:qiend+1]
    except TypeError as error:
        if type(qiend) == type(None):
            queries = queries[qiini:]
        else:
            raise(error)

    for query in queries:
        try:
            nterm_count[query.n_term] += 1
        except KeyError:
            nterm_count[query.n_term] = 0
            nterm_count[query.n_term] += 1

    #cálculo do desconto para execuções parciais
    discount = 0

    if fiini:
        if fiini < 0:
            print('fiini não pode ser negativo')
            print('fiini:', fiini)
            sys.exit()

        query = queries[0]
        if fiini >= 3**query.n_term:
            print('O número inicial do filtro não pode ser maior ou igual a quantidade de filtros ')
            print('fiini:', fiini)
            print('Nfiltros:', 3**query.n_term)
            sys.exit()
        discount -= fiini

    if fiend:
        if fiend < 0:
            print('fiend não pode ser negativo')
            print('fiend:', fiend)
            sys.exit()

        query = queries[-1]
        res = 3**query.n_term - (fiend + 1)
        if res < 0:
            print('O índice final de filtros não pode ser maior ou igual a quantidade de filtros ')
            print('fiend:', fiend)
            print('Nfiltros:', 3**query.n_term)
            sys.exit()
        discount -= res

    total = discount
    for nterm in nterm_count:
        #print('%d with %d terms' % (nterm_count[nterm], nterm) )
        total += nterm_count[nterm] * (3**nterm)

    return nterm_count, total

if __name__ == "__main__":
    main()
    #sys.exit(main())
