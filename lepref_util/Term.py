class Term (object):

    def __init__(self, word = ""):
        self.word = word

class TermQuery (Term):

    def __init__(self, word = "", idfbody = 0, idfanchor = 0, idftitle = 0,
      idfurl = 0, idfdocument = 0):
        Term.__init__(self, word)
        self.idfbody = idfbody
        self.idfanchor = idfanchor
        self.idftitle = idftitle
        self.idfurl = idfurl
        self.idfdocument = idfdocument

class TermDocument(Term):

    def __init__(self, word = "", tfbody = 0, tfanchor = 0, tftitle = 0,
      tfurl = 0, tfdocument = 0):
        Term.__init__(self, word)
        self.tfbody = tfbody
        self.tfanchor = tfanchor
        self.tftitle = tftitle
        self.tfurl = tfurl
        self.tfdocument = tfdocument
