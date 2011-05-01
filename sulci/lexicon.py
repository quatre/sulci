"""
Define the Lexicon class.
"""
# -*- coding:Utf-8 -*-

from collections import defaultdict
from operator import itemgetter

from base import TextManager
from utils import load_file, save_to_file
from sulci.log import sulci_logger
from corpus import Corpus

class Lexicon(TextManager):
    """
    The lexicon is a list of unique words and theirs possible POS tags.
    """
    
    def __init__(self):
        self.VALID_EXT = ".lxc.lem.crp"
        self.PATH = "corpus"
        self._loaded = None
        self._raw_content = ""
        self._prefixes = None
        self._suffixes = None
        self.factors = set()
    
    def __iter__(self):
        return self.loaded.__iter__()
    
    def __getitem__(self, item):
        return self.loaded.__getitem__(item)
    
    def __len__(self):
        return len(self.loaded)
    
    def items(self):
        return self.loaded.items()
    
    def __contains__(self, key):
        if isinstance(key, object) and key.__class__.__name__ == "Token":
            key = key.original
        return key in self.loaded
    
    @property
    def loaded(self):
        """
        Load lexicon in RAM, from file.
        """
        if self._loaded is None:#Caching and lazy loading
            sulci_logger.debug("Loading lexicon...", "RED", True)
            lx = load_file("corpus/lexicon.lxc")
            self._loaded = {}
            for line in lx.split("\n"):
                els = line.split("\t")
                if len(els) == 2:
                    cat = els[1].split()
                    self._loaded[els[0]] = cat
                    self.add_factors(els[0])
        return self._loaded
    
    def add_factors(self, token):
        prefix = token
        while prefix:
            suffix = prefix
            while suffix:
                if not suffix == token:#Don't add the initial graph
                    self.factors.add(suffix)
                suffix = suffix[1:]
            prefix = prefix[:-1]
    
    def make(self):
        """
        Build the lexicon.
        """
        final = {}
        lemme_to_original = {}
        C = Corpus(self.VALID_EXT)
        for tk in C.tokens:
            # Don't take Proper nouns (SBP) in lexicon
            if tk.verified_tag[:3] == "SBP":
                continue
            # Manage tags frequences
            if not tk.original in final:
                final[tk.original] = defaultdict(int)
            final[tk.original][tk.verified_tag] += 1
            # Manage lemmes frequences
            if not tk.original in lemme_to_original:
                lemme_to_original[tk.original] = {}
            if not tk.verified_tag in lemme_to_original[tk.original]:
                lemme_to_original[tk.original][tk.verified_tag] = defaultdict(int)
            # Frequence of this lemme for this tag for this word...
            lemme_to_original[tk.original][tk.verified_tag][tk.verified_lemme] += 1
        
        def get_one_line(key):
            """
            Return one line of the lexicon.
            Take the token.original string in parameter.
            """
            return u"%s\t%s" % (key, get_tags(key))
        
        def get_tags(key):
            """
            Return sorted tags for a original word compiled in a string :
            tag/lemme tag/lemme
            """
            # Retrieve tags
            tags = sorted([(k, v) for k, v in final[key].iteritems()], 
                                             key=itemgetter(1), reverse=True)
            # Build final datas
            final_data = []
            for tag, score in tags:
                computed_lemmes = get_lemmes(key, tag)
                lemme, score = computed_lemmes[0]
                final_data.append(u"%s/%s" % (tag, lemme))
            
            # Return it as a string
            return u" ".join(final_data)
        
        def get_lemmes(key, tag):
            """
            Return sorted lemmes for one word with one POS tag.
            """
            return sorted(((k, v) for k, v in lemme_to_original[key][tag].iteritems()), 
                                                key=itemgetter(1), reverse=True)
        
        d = []
        for k, v in sorted(final.iteritems()):
            d.append(get_one_line(k))
        final_d = u"\n".join(d)
#            d +=  u"%s\t%s\n" % (k, " ".join([u"%s/%s" % (tp[0], sorted(lemme_to_original[k][tp[0]], key=itemgetter(1), reverse=True)[0]) for tp in sorted([(k2, v2) for k2, v2 in v.iteritems()], key=itemgetter(1), reverse=True)]))
        save_to_file("corpus/lexicon.pdg", unicode(final_d))
    
    def create_afixes(self):
        """
        We determinate here the most frequent prefixes and suffixes.
        """
        prefixes = defaultdict(int)
        suffixes = defaultdict(int)
        max_prefix_length = 3
        max_suffix_length = 5
        for tokenstring, _ in self.items():
            tlen = len(tokenstring)
            for i in xrange(1, min(max_prefix_length + 1, tlen)):
                prefix = tokenstring[0:i]
                prefixes[prefix] += len(prefix)
            for i in xrange(1, min(max_suffix_length + 1, tlen)):
                suffix = tokenstring[tlen - i:tlen]
                suffixes[suffix] += len(suffix)
        #We make a set, to speed contains, so sorted doesn't meens nothing
        self._prefixes = set(key for key, value in \
                         sorted(((k, v) for k, v in prefixes.items() if v > len(k) * 2), 
                         key=itemgetter(1), reverse=True))
        self._suffixes = set(key for key, value in \
                         sorted(((k, v) for k, v in suffixes.items() if v > len(k) * 2), 
                         key=itemgetter(1), reverse=True))
    
    @property
    def prefixes(self):
        if self._prefixes is None:
            self.create_afixes()
        return self._prefixes
    
    @property
    def suffixes(self):
        if self._suffixes is None:
            self.create_afixes()
        return self._suffixes
    
    def get_entry(self, entry):
        if entry in self:
            sulci_logger.info(u"%s => %s" % (entry, self[entry]), "WHITE")
        else:
            sulci_logger.info(u'No entry for "%s"' % entry, "WHITE")

