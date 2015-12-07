# -*- coding: utf-8 -*-
import sys
from math import log
from . import normalization_util

#hash table for NDCG,
hsNdcgRelScore = {  2: 3,
                    1: 1,
                    0: 0}

def lista_atributo(elementos, chave = lambda elemento: elemento):
    '''lista_atributo(elementos, chave = lambda elementos: elementos)
    -> Recebe uma lista de elementos, e retorna uma lista contendo os valores
    do atributo especificado na chave de cada elemento.
    '''
    v = []
    for elemento in elementos:
        v.append(chave(elemento))
    return v

def vetor_ganho_li(query, lista_invertida):
    '''vetor_ganho_li(query, lista_invertida) -> Retorna o vetor de ganho no
    formato (label, uti) referente aos documentos da query.
    '''
    vetor_ganho = []
    for doc in query.doc:
        uti_acc = 0.0
        for term in query.term:
            uti_acc += lista_invertida[term.word][doc.docid]
        vetor_ganho.append((doc.label,uti_acc))
    return vetor_ganho

def dcg_unico(vetor_ganho, topN = 10, chave = lambda e: e):
    '''Calcula o DCG de apenas uma consulta.
    '''
    dcg = []
    i = 0

    if topN > len(vetor_ganho):
        topN = len(vetor_ganho)

    while(i < topN):
        if i == 0:
            dcg.append(hsNdcgRelScore[chave(vetor_ganho[0])])
        else:
            dcg.append( dcg[i-1] + hsNdcgRelScore[chave(vetor_ganho[i])]/log(i+1,2) )
        i += 1

    return dcg

def ndcg_unico(vetor_ganho, best_dcg, topN = 10, chave = lambda e: e):
    '''Calcula o NDCG de apenas uma consulta.
    '''
    ndcg = []
    dcg = dcg_unico(vetor_ganho, topN, chave)

    i = 0
    while ( i < topN and i < len(vetor_ganho)):
        ndcg.append(0.0)
        try:
            if (best_dcg[i] != 0):
                ndcg[i] = dcg[i] / best_dcg[i]
        except IndexError:
            #Resultado da consulta retorna menos documentos que o topN
            #Consideirar os outros documentos com ndcg 0
            #return ndcg
            ndcg[i] = 0
        i += 1
    return ndcg

def configurar_idcg_medio(queries, topN = 10):
    '''configurar_idcg_medio(queries, topN = 10) -> Calcula o idcg individual
    de cada consulta.
    '''

    for query in queries:
        vetor_ganho = lista_atributo(query.doc, chave = lambda d: d.label)
        vetor_ganho.sort(reverse = True)
        query.idcg = dcg_unico(vetor_ganho, topN)

def ndcg_medio_unico(ndcg):
    '''ndcg_medio_unico(ndcg) -> Calcula e retorna o MEAN NDCG
    dado um vetor de ndcg.
    '''
    mean_ndcg = 0.0
    for ndcgItem in ndcg:
        mean_ndcg += ndcgItem
    try:
        mean_ndcg = mean_ndcg / len(ndcg)
    except ZeroDivisionError:
        mean_ndcg = 0

    return mean_ndcg

def ndcg_medio_queries(queries, lista_invertida, topN = 10):
    '''ndcg_medio_queries(queries, lista_invertida, topN = 10) ->
    Calcula o mean ndcg individual de cada consulta e no final retorna o
    ndcg medio para todas as consultas.
    '''
    acumulador_ndcg = 0.0

    for query in queries:
        #TODO Remover comentario
        vetor_ganho = vetor_ganho_li(query, lista_invertida)
        #vetor_ganho = lista_atributo(query.doc,
        #             chave = lambda d: (d.label,d.uti_atual))
        vetor_ganho.sort(key = lambda d: d[1], reverse = True)
        ndcg_q = ndcg_unico(vetor_ganho, query.idcg, topN,
          chave = lambda e: e[0])
        query.mean_ndcg_atual = ndcg_medio_unico(ndcg_q)
        acumulador_ndcg += query.mean_ndcg_atual

    return acumulador_ndcg/len(queries)

def aplicar_individuo(func, queries, lista_invertida,  metodo, parametros,
  UTItype = 'real', valuereturn = True):
    '''aplicar_individuo(func, queries, lista_invertida, UTItype = "real",
         metodo, parametros) -> Calcula os
    UTIs dos  documentos das consultas utilizando a funcao func
    e o metodo informado.
    '''

    for query in queries:
        for documento in query.doc:
            uti = 0.0
            for i, termo in enumerate(query.term):
                dados = formatar_features(documento, termo, documento.term[i])
                #print(dados)

                #Uti Inteiro
                uti = func(*dados)
                if metodo == 'peso':
                    uti = uti*parametros[0]
                # se metodo for 'base' ou 'peso': aplicar trunc ou round
                if (metodo == 'base' or metodo == 'peso'):
                    if UTItype == 'trunc':
                        uti = int(uti)
                    if UTItype == 'round':
                        uti = round(uti)

                lista_invertida[termo.word][documento.docid] = uti

    if   metodo == 'linear':
        _aplicar_linear(lista_invertida, parametros, UTItype, valuereturn)

    elif metodo == 'exp':
        _aplicar_exponencial(lista_invertida, parametros, UTItype, valuereturn)

    elif metodo == 'log':
        _aplicar_logaritmica(lista_invertida, parametros, UTItype, valuereturn)


def _aplicar_linear(lista_invertida, parametros, UTItype, valuereturn):
    '''
    '''
    for termo in lista_invertida:
        #obter lista de utis dos docs
        lista_utis = lista_atributo(lista_invertida[termo].items(),
          chave = lambda elemento: elemento[1])
        #obter maximo
        maximo = max(lista_utis)
        for doc in lista_invertida[termo]:
            #uti = linear(lista_invertida[termo][doc], maximo, parametro)
            uti = normalization_util.linear(lista_invertida[termo][doc], maximo, parametros[0])

            #uti = int(uti)
            if UTItype == 'trunc':
                uti = int(uti)
            if UTItype == 'round':
                uti = round(uti)

            if valuereturn:
                #uti = return_linear(uti, maximo, parametro)
                uti = normalization_util.return_linear(uti, maximo, parametros[0])

            #lista_invertida[termo][doc] = uti
            lista_invertida[termo][doc] = uti

def _aplicar_logaritmica(lista_invertida, parametros, UTItype, valuereturn):
    '''
    '''
    for termo in lista_invertida:
        #obter lista de utis dos docs
        lista_utis = lista_atributo(lista_invertida[termo].items(),
          chave = lambda elemento: elemento[1])
        #obter maximo
        maximo = max(lista_utis)
        for doc in lista_invertida[termo]:
            #uti = lgrt(lista_invertida[termo][doc], maximo, parametro)
            uti = normalization_util.lgrt(lista_invertida[termo][doc], maximo, parametros[0])

            #uti = int(uti)
            if UTItype == 'trunc':
                uti = int(uti)
            if UTItype == 'round':
                uti = round(uti)

            if valuereturn:
                #uti = uti = return_lgrt(uti, maximo, parametro)
                uti = normalization_util.return_lgrt(uti, maximo, parametros[0])

            #lista_invertida[termo][doc] = uti
            lista_invertida[termo][doc] = uti

def _aplicar_exponencial(lista_invertida, parametros, UTItype, valuereturn):
    '''
    '''
    for termo in lista_invertida:
        #obter lista de utis dos docs
        lista_utis = lista_atributo(lista_invertida[termo].items(),
          chave = lambda elemento: elemento[1])
        #obter maximo
        maximo = max(lista_utis)
        for doc in lista_invertida[termo]:
            #uti = exp(lista_invertida[termo][doc], maximo, parametro)
            uti = normalization_util.exp(lista_invertida[termo][doc], maximo, parametros[0])

            #uti = int(uti)
            if UTItype == 'trunc':
                uti = int(uti)
            if UTItype == 'round':
                uti = round(uti)

            if valuereturn:
                #uti = return_exp(uti, maximo, parametro)
                uti = normalization_util.return_exp(uti, maximo, parametros[0])

            #lista_invertida[termo][doc] = uti
            lista_invertida[termo][doc] = uti

def formatar_features(documento, termo, termo_documento):
    '''Mesmo que fillData, porem retorna uma lista contendo os features
    computados.
    '''
    return [
        # Idf do termo
        termo.idfbody,
        termo.idfanchor,
        termo.idftitle,
        termo.idfurl,
        termo.idfdocument,
#        log(25205179/termo.tfbody) if termo.tfbody > 0 else 0,
#        log(25205179/termo.tfanchor) if termo.tfanchor > 0 else 0,
#        log(25205179/termo.tftitle) if termo.tftitle > 0 else 0,
#        log(25205179/termo.tfurl) if termo.tfurl > 0 else 0,
#        log(25205179/termo.tfdocument) if termo.tfdocument > 0 else 0,

        # Frequencia do termo do documento
        termo_documento.tfbody,
        termo_documento.tfanchor,
        termo_documento.tftitle,
        termo_documento.tfurl,
        termo_documento.tfdocument,

        #Tamanho do documento
        documento.loglenbody,
        documento.loglenanchor,
        documento.loglentitle,
        documento.loglenurl,
        documento.loglendocument,
#        log(documento.lenbody) if documento.lenbody > 0 else 0,
#        log(documento.lenanchor) if documento.lenanchor > 0 else 0,
#        log(documento.lentitle) if documento.lentitle > 0 else 0,
#        log(documento.lenurl) if documento.lenurl > 0 else 0,
#        log(documento.lendocument) if documento.lendocument > 0 else 0,

        #Features do documento
        documento.pagerank,
        documento.inlink,
        documento.outlink,
        documento.num_slash,
        documento.len_url,
        documento.num_child
    ]


