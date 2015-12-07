# -*- coding: utf-8 -*-
import sys
from .Query import Query
from .Document import Document
from .Term import TermQuery
from .Term import TermDocument
from math import log

ERRO_CABECALHO_QUERY = 1
ERRO_TERMO = 2
ERRO_CABECALHO_DOCUMENTO = 3
ERRO_TAMANHO_CAMPOS = 4
ERRO_FREQUENCIA_RELATIVA = 5

def carregar_queries(nome_arquivo):
    '''carregar_queries(nome_arquivo) -> Carrega as queries do formato
    especificado para uma estrutura Query. Retornar uma lista de Queries.
    '''
    try:
        arquivo = open(nome_arquivo)
    except Exception:
        raise

    queries = []
    lista_invertida = {}
    n_query = 0
    linha = 0

    #Ler arquivo (do while)
    while True:
        #Ler Query
        #ler cabeçalho da query
        buff = arquivo.readline()
        linha += 1
        if not buff: #Condição de parada: Caso chegue ao fim do arquivo
            break

        #formatar cabeçalho da query
        try:
            queryid, n_doc, n_term = _desempacotar_cabecalho_query(buff)
        except Exception:
            _msg_erro_leitura(ERRO_CABECALHO_QUERY, linha, buff)
            sys.exit(-1)

        query = Query(queryid, n_doc, n_term)
        #Ler Termos (for)
        for i in range(query.n_term):
            #ler termo
            buff = arquivo.readline()
            linha += 1
            #formatar termo
            try:
                (word, tfbody, tfanchor,
                  tftitle, tfurl, tfdocument) = _desempacotar_termo(buff)
            except Exception:
                _msg_erro_leitura(ERRO_TERMO, linha, buff)
                sys.exit(-1)
            #Calcula Idf
            idfbody = log(25205179/tfbody) if tfbody > 0 else 0
            idfanchor = log(25205179/tfanchor) if tfanchor > 0 else 0
            idftitle = log(25205179/tftitle) if tftitle > 0 else 0
            idfurl = log(25205179/tfurl) if tfurl > 0 else 0
            idfdocument = log(25205179/tfdocument) if tfdocument > 0 else 0
            term = TermQuery(word, idfbody, idfanchor, idftitle,
              idfurl, idfdocument)
            #adicionar termo na query
#            term = Term(word, tfbody, tfanchor, tftitle, tfurl, tfdocument)
            query.term.append(term)
            #Adiciona (caso ainda não exista) termo na lista invertida
            _adicionar_termo_li(lista_invertida, word)

        #Ler Documentos (for)
        for i in range(query.n_doc):
            #ler cabeçalho do documento
            buff = arquivo.readline()
            linha += 1
            #formatar cabeçalho do documento
            try:
                (label, docid, pagerank, inlink, outlink, num_slash, len_url,
                  num_child) = _desempacotar_cabecalho_documento(buff)
            except Exception:
                _msg_erro_leitura(ERRO_CABECALHO_DOCUMENTO, linha, buff)
                sys.exit(-1)
            
            #ler tamanho dos campos do documento
            buff = arquivo.readline()
            linha += 1
            #formatar tamanhos
            try:
                (lenbody, lenanchor, lentitle,
                  lenurl, lendocument) = _desempacotar_tamanho_campos(buff)
            except Exception:
                _msg_erro_leitura(ERRO_TAMANHO_CAMPOS, linha, buff)
                sys.exit(-1)

            #Calcula logs dos tamanhos
            loglenbody = log(lenbody) if lenbody > 0 else 0
            loglenanchor = log(lenanchor) if lenanchor > 0 else 0
            loglentitle = log(lentitle) if lentitle > 0 else 0
            loglenurl = log(lenurl) if lenurl > 0 else 0
            loglendocument = log(lendocument) if lendocument > 0 else 0
            document = Document(label, docid, pagerank, inlink, outlink,
              num_slash, len_url, num_child, lenbody, loglenbody, loglenanchor,
              loglentitle, loglenurl, loglendocument)

#            document = Document(label, docid, pagerank, inlink, outlink,
#              num_slash, len_url, num_child, lenbody, lenanchor, lentitle,
#              lenurl, lendocument)

            #Adiciona documento na lista invertida dos termos
            _adicionar_documento_li(lista_invertida, query.term, docid)

            #Ler frequencia relativa dos termos da consulta no documento (for)
            for i in range(query.n_term):
                #ler frequencia relativa
                buff = arquivo.readline()
                linha += 1
                #formatar frequencia relativa
                try:
                    (tfbody, tfanchor, tftitle, tfurl,
                      tfdocument) = _desempacotar_frequencia_relativa(buff)
                except Exception:
                    _msg_erro_leitura(ERRO_FREQUENCIA_RELATIVA, linha, buff)
                    sys.exit(-1)
                term = TermDocument(query.term[i].word, tfbody, tfanchor, tftitle,
                  tfurl, tfdocument)
                document.term.append(term)

            #adicionar documento na query
            query.doc.append(document)

        #Adicionar Query na lista de Queries
        queries.append(query)
        n_query += 1

    #Retornar lista de Queries
    return queries, lista_invertida

def _desempacotar_cabecalho_query(buff):
    '''_desempacotar_cabecalho_query(buff) -> Espera uma string (buff)
    no formato '%d %d %d' e retorna uma tupla (queryid, n_doc, n_term).
    '''
    buff = buff.rstrip()
    queryid, n_doc, n_term = map(int,buff.split())
    return queryid, n_doc, n_term

def _desempacotar_termo(buff):
    '''_desempacotar_termo(buff) -> Espera uma string (buff) no formato
    '%s %d %d %d %d %d' e retorna uma tupla
    (word, tfbody, tfanchor, tftitle, tfurl, tfdocument)
    '''
    buff = buff.rstrip()
    word, tfbody, tfanchor, tftitle, tfurl, tfdocument = buff.split()
    tfbody = int(tfbody)
    tfanchor = int(tfanchor)
    tftitle = int(tftitle)
    tfurl = int(tfurl)
    tfdocument = int(tfdocument)
    return word, tfbody, tfanchor, tftitle, tfurl, tfdocument

def _desempacotar_cabecalho_documento(buff):
    '''_desempacotar_cabecalho_documento(buff) -> Espera uma string (buff)
    no formato '%d %s %lf %lf %lf %lf %lf %lf' e retorna uma tupla
    (label, docid, pagerank, inlink, outlink, num_slash, len_url, num_child)
    '''
    buff = buff.rstrip()
    (label, docid, pagerank, inlink, outlink,
      num_slash, len_url, num_child) = buff.split()
    label = int(label)
    pagerank = float(pagerank)
    inlink = float(inlink)
    outlink = float(outlink)
    num_slash = float(num_slash)
    len_url = float(len_url)
    num_child = float(num_child)
    return (label, docid, pagerank, inlink, outlink,
      num_slash, len_url, num_child)

def _desempacotar_tamanho_campos(buff):
    '''_desempacotar_tamanho_campos(buff) -> Espera uma string (buff)
    no formato '%lf %lf %lf %lf %lf' e retorna uma tupla
    (lenbody, lenanchor, lentitle, lenurl, lendocument)
    '''
    buff = buff.rstrip()
    lenbody, lenanchor, lentitle, lenurl, lendocument = map(float,buff.split())
    return lenbody, lenanchor, lentitle, lenurl, lendocument

def _desempacotar_frequencia_relativa(buff):
    '''_desempacotar_frequencia_relativa(buff) -> Espera uma string (buff)
    no formato '%d %d %d %d %d' e retorna uma tupla
    (term_tfbody, term_tfanchor, term_tftitle, term_tfurl, term_tfdocument)
    '''
    buff = buff.rstrip()
    (term_tfbody, term_tfanchor, term_tftitle,
      term_tfurl, term_tfdocument) = map(int,buff.split())
    return (term_tfbody, term_tfanchor, term_tftitle,
      term_tfurl, term_tfdocument)

def _msg_erro_leitura(tipo, linha = 0, buff = ''):
    '''Exibe uma mensagemd de erro de formato do buff, de acordo com o tipo
    de leitura esperada. Os tipos erros que podem ser:
    ERRO_CABECALHO_QUERY = 1
    ERRO_TERMO = 2
    ERRO_CABECALHO_DOCUMENTO = 3
    ERRO_TAMANHO_CAMPOS = 4
    ERRO_FREQUENCIA_RELATIVA = 5
    '''
    if linha:
        print('Erro ao ler a linha:', linha)
    if buff:
        print('Conteúdo lido:', buff.rstrip())
    if tipo == ERRO_CABECALHO_QUERY:
        print("Formato esperado: '%d %d %d' (queryid, n_doc, n_term)")
    elif tipo == ERRO_TERMO:
        print("Formato esperado: '%s %d %d %d %d %d'", end = ' ')
        print("(word, tfbody, tfanchor, tftitle, tfurl, tfdocument)")
    elif tipo == ERRO_CABECALHO_DOCUMENTO:
        print("Formato esperado: '%d %s %lf %lf %lf %lf %lf %lf'", end = ' ')
        print("(label, docid, pagerank, inlink, outlink,", end = ' ')
        print("num_slash, len_url, num_child)")
    elif tipo == ERRO_TAMANHO_CAMPOS:
        print("Formato esperado: '%lf %lf %lf %lf %lf'", end = ' ')
        print("(lenbody, lenanchor, lentitle, lenurl, lendocument)")
    elif tipo == ERRO_FREQUENCIA_RELATIVA:
        print("Formato esperado: '%d %d %d %d %d'", end = ' ')
        print("(term_tfbody, term_tfanchor, term_tftitle,", end = ' ') 
        print("term_tfurl, term_tfdocument)")

def _possui_termo_li(lista_invertida, termo):
    '''Retorna True caso a lista invertida possua o termo procurado, False
    caso não possua.
    '''
    return lista_invertida.get(termo) != None

def _adicionar_termo_li(lista_invertida, termo):
    '''Adiciona termo na lista invertida apenas no caso de o mesmo não estar
    presente. Caso já esteja, a função não faz nada.
    '''
    if not _possui_termo_li(lista_invertida, termo):
        lista_invertida[termo] = {}

def _adicionar_documento_li(lista_invertida, termos, docid):
    '''Adiciona o documento na lista de cada termo passado em termos.
    Caso um termo não exista, o documento não é adicionado.
    '''
    for termo in termos:
        if _possui_termo_li(lista_invertida, termo.word):
            lista_invertida[termo.word][docid] = 0

