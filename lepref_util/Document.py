class Document (object):

    def __init__(self,
      label = 0,
      docid = "",

      pagerank = 0.0,
      inlink = 0.0,
      outlink = 0.0,
      num_slash = 0.0,
      len_url = 0.0,
      num_child = 0.0,

      lenbody = 0.0,

      loglenbody = 0.0,
      loglenanchor = 0.0,
      loglentitle = 0.0,
      loglenurl = 0.0,
      loglendocument = 0.0):

#      lenanchor = 0.0,
#      lentitle = 0.0,
#      lenurl = 0.0,
#      lendocument = 0.0):

        self.label = label
        self.docid = docid

        self.pagerank = pagerank
        self.inlink = inlink
        self.outlink = outlink
        self.num_slash = num_slash
        self.len_url = len_url
        self.num_child = num_child

        self.lenbody = lenbody

        self.loglenbody = loglenbody
        self.loglenanchor = loglenanchor
        self.loglentitle = loglentitle
        self.loglenurl = loglenurl
        self.loglendocument = loglendocument
#        self.lenbody = lenbody
#        self.lenanchor = lenanchor
#        self.lentitle = lentitle
#        self.lenurl = lenurl
#        self.lendocument = lendocument

        self.term = []

        self.uti_atual = 0.0
