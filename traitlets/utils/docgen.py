import inspect
from traitlets import HasTraits, TraitType
from six import with_metaclass

# - - - - - - - - - - - - - -
# Document Section Descriptor
# - - - - - - - - - - - - - -

class DocumentSection(object):

    source = None
    _fetch = None
    section = None
    _parse = None

    def __init__(self, source):
        self.source = source

    @staticmethod
    def fetch(source):
        return DocumentSection(source)

    def __call__(self, func):
        self._fetch = func

    def class_init(self, cls, name):
        self.this_class = cls
        self.section = name

    def parse(self, func):
        self._parse = func
        return self

    def __set__(self, inst, obj):
        inst._rep_content[self.section] = self._fetch(inst, getattr(obj, self.source))
        inst._str_content[self.section] = self._parse(inst, inst._content[self.section])

    def __get__(self, inst, cls=None):
        if inst is None:
            return self
        else:
            return isnt._str_content[self.section]

    @property
    def incomplete(self):
        return (callable(self._fetch) and callable(self._parse)
            and None not in (self.source, self.section))

    @staticmethod
    def new(source, getter, parser):
        return DocumentSection(source)(getter).parser(parser)


# simple abbreviated decorator name
class docsec(DocumentSection): pass

# - - - - - - - - - - - - - -
# DocLog Object and Metaclass
# - - - - - - - - - - - - - -

class MetaDocLog(type):

    def __init__(cls, *args):
        super(MetaDocLog, cls).__init__(*args)
        for k, v in inspect.getmembers(cls):
            if isinstance(v, DocumentSection):
                v.class_init(cls, k)
                if v.incomplete:
                    raise RuntimeError("Encountered an incomplete"
                        " document section defition for '%s'" % k)


class DocLog(with_metaclass(MetaDocLog, object)):

    _logs_type = None
    _from_class = False
    # public attribute with parsed content
    content = None
    # private attribute with raw content
    _content = {}

    def __init__(self, obj):
        cls = obj if inspect.isclass(obj) else obj.__class__
        if self._type is not None and not issubclass(cls, self._type):
            raise TypeError("A '%s' makes autodocs for '%s', not %r"
                        % (self.__class__.__name__, self._type.__name__, obj))
        self.obj = cls if self._from_class else obj

        self._rep_content = {}
        self._str_content = {}

        # generate docs
        self._docgen()

    def __iter__(self):
        return iter(self._str_content)

    def __len__(self):
        return len(self._str_content)

    def __repr__(self):
        return self.__class__.__name__ + '(' + repr(self._rep_content) + ')'

    def __str__(self):
        return self.__class__.__name__ + '(' + str(self._str_content) + ')'

    def _docgen(self):
        """Generate the docs"""
        for s in self.document_sections():
            setattr(self, s, getattr(self.obj, s))

    @classmethod
    def sections(cls):
        return dict([member for member in getmembers(cls) if
                    isinstance(member[1], DocumentSection)])

    @property
    def content(self):
        return self._str_content.copy()

# - - - - - - - - - - - - -
# TraitType DocLog Objects
# - - - - - - - - - - - - -

class TraitTypeDocLog(DocLog):

    _logs_type = TraitType

    def docgen(self):
        self._content['name'] = self.obj.name
        self._content['info'] = self.obj.info()

        metadata = self.obj.metadata.copy()
        self._content['help'] = metadata.pop('help')
        self._content['metadata'] = metadata

# - - - - - - - - - - - -
# HasTraits DocLog Object
# - - - - - - - - - - - -

class MetaHasTraitsDocLog(MetaDocLog):

    ttype_doclogs = {TraitType: TraitTypeDocLog}

    @classmethod
    def _get_log_obj(mcls, trait):
        for c in trait.__class__.mro():
            if c in mcls.ttype_doclogs:
                return mcls.ttype_doclogs[c](trait)
        # returns None if no log object
        # exists for the given trait
        return None

    @classmethod
    def _parser(mcls, inst, trait):
        # simple proxy for log obj getter
        return mcls._get_log_obj(trait)

    @classmethod
    def _fetcher(mcls, inst, trait):
        return trait

    def __new__(mcls, name, bases, classdict):
    	if '_logs_type' in classdict:
    		cls = classdict['_logs_type']
    	else:
    		cls = None
    		for c in bases:
    			if hasattr(c, '_logs_type'):
    				cls = getattr(c, '_logs_type')
    	if not issubclass(cls, HasTraits):
    		raise TypeError("The attribute '_logs_type' must be a 'HasTraits' subclass")
        super(MetaHasTraitsDocLog, mcls).__new__(mcls, cls.__name__ + 'DocLog',
            (DocLog,), dict([(n, docsec.new(n, mcls._fetcher, mcls._parser))
            for n in cls.class_trait_names()]))


class HasTraitsDocLog(with_metaclass(MetaHasTraitsDocLog, DocLog)): pass


def trait_documentation(obj, name=None):
    if name is not None:
        cls = obj if inspect.isclass(obj) else obj.__class__
        HasTraitsDocLog.ttype_doclogs[getattr(cls,)]