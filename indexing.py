# -*- coding: utf-8 -*-
#!/usr/bin/env python3
import sys
import math

import porter
import func

class Index(dict):
    '''Index Description
'''
    def __init__(self): 
        dict.__init__(self)
        self.doc = {}
        self.avgdl = 0
        self.k = 1.5
        self.b = 0.75

    def set_k(self, k):
        '''
    '''
        self.k = k

    def set_b(self, b):
        '''
    '''
        self.b = b

    def add_term_doctf(self, term, doc, doctf):
        '''
    '''
        try:
            term_object = self[term]
        except KeyError:
            raise

        term_object.add_doctf(doc, doctf)

    def add_term(self, term):
        '''
    '''
        if (not self.get(term)):
            new_term = Term(term)
            self[term] = new_term

    def add_doctfdict(self, docid, doclen, doctfdict):
        '''
    '''
        if docid not in self.doc:
            for term in doctfdict:
                if not self.get(term):
                    new_term = Term(term)
                    self[term] = new_term
                self[term].add_doctf(docid, doctfdict[term])

            self.doc[docid] = doclen

    def add_docstf(self, doctflist):
        '''
    '''
        for doc in doctflist:
            self.add_doctfdict(*doctflist[doc])

        doclensum = sum(self.doc.values())
        self.avgdl = doclensum/len(self.doc)

        self._update_idf()

    def increment_ndoc(self, ndoc):
        '''
    '''
        self.ndoc += ndoc

    def _update_idf(self):
        '''
    '''
        #TODO 
        for term in self:
            
            self[term].idf = math.log( (len(self.doc) - len(self[term].doclist) + 0.5) / (len(self[term].doclist) + 0.5) , 2)

            for i, docterm in enumerate(self[term].doclist):
                self[term].doclist[i].score = self.partial_score(self[term], docterm)

            self[term].docdict = {doc.doc: (doc.doctf, doc.score) for doc in self[term].doclist}


    def query(self, querystring):
        '''
    '''
        query_no_puct = func.replace_punctuation(querystring)
        query_termlist = func.remove_multiple_space(query_no_puct).strip().split()

        acc = list()
        for term in query_termlist:
            term_processed = porter2.stem(term)
            acc.append((term, self[term].doclist))

    def partial_score(self, term, doc):
        '''
    '''
        partial_scr = term.idf * ( doc.doctf * (self.k + 1) / (doc.doctf + self.k * (1 - self.b + self.b*(len(self.doc)/self.avgdl) )) ) 
        
        return partial_scr

class Term():
    '''Term Description
'''
    def __init__(self, term):
        self.term = term
        self.idf = 0
        self.doclist = list()
        self.docdict = dict()

    def add_doctf(self, doc, doctf):
        '''
    '''
        try:
            docindex = self.doclist.index(doc)
        except ValueError:
            new_doc = Doc(doc)
            self.doclist.append(new_doc)
            docindex = len(self.doclist) - 1
        self.doclist[docindex].increment_doctf(doctf)

    def in_doc(self, docid):
        '''
    '''
#        try:
#            docindex = self.doclist.index(docid)
#            isin = True
#        except ValueError:
#            isin = False
#        return isin
        if self.docdict.get(docid):
            return True
        else:
            return False

class Doc (object):
    '''Doc Description
'''
    def __init__(self, doc):
        self.doc = doc
        self.doctf = 0
        self.score = 0.0

    def __eq__(self, other):
        return other == self.doc

    def increment_doctf(self, doctf):
        '''
    '''
        self.doctf += doctf

    def __repr__(self):
        return str(self.doc) + ": " + str(self.score)
