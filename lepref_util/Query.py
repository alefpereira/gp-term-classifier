class Query (object):

    def __init__(self, queryid = 0, n_doc = 0, n_term = 0):
        self.queryid = queryid
        self.n_doc = n_doc
        self.n_term = n_term
        self.term = []
        self.doc = []
        self.idcg = []
        self.mean_ndcg_atual = 0.0
