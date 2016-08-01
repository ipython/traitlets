import re
import sys
import inspect
import types

from six import with_metaclass

import string

_vformat = string.Formatter().vformat

def format_map(string, *args, **kwargs):
	return _vformat(string, args, kwargs)

# ----------------------------------------------------------------------------
# Document Section Descriptor
# ----------------------------------------------------------------------------

class DocLogMember(object):

	def class_init(self, cls, name):
		self.this_class = cls
		self.name = name


class Content(DocLogMember):

	source = None
	content = None
	_renderer = None
	_format_content = None

	def __init__(self, source=None):
		if isinstance(source, types.FunctionType):
			self._renderer = source
			self.source = None
		elif source is not None:
			self.source = source

	def __call__(self, func):
		self._renderer = func
		return self

	def __get__(self, inst, cls=None):
		if inst is None:
			return self
		elif self.content is None:
			raise RuntimeError("Improper metaclass setup for %s descriptor '%s'"
							   " on type object %s" % (self.__class__.__name__,
								self.name, inst.__class__.__name__))
		elif self.content in inst._source_content:
			return inst._source_content[self.content]
		elif self.source is None:
			value = self._renderer(inst, inst.source)
		else:
			value = getattr(inst.source, self.source, None)
			if self._renderer is not None:
				value = self._renderer(inst, value)
		inst._source_content[self.content] = value
		return value

	def format(self, func):
		self._format_content = func
		return self

	def format_content(self, inst):
		if self._format_content is None:
			return str(getattr(inst, self.content))
		else:
			return str(self._format_content(inst, getattr(inst, self.content)))

	def class_init(self, cls, name):
		super(Content, self).class_init(cls, name)
		# a more informative attr
		self.content = self.name


def content(source):
	"""Simple decorator returning a Content with a parser"""
	return Content(source)

# ----------------------------------------------------------------------------
# DocLog Template Classes
# ----------------------------------------------------------------------------

class TemplateUtils(object):

	tab = 4

	def __setitem__(self, index, value):
		if not isinstance(index, slice):
			value = Line(value)
		self._lines[index] = value

	def __delitem__(self, index):
		del self._lines[index]

	def _to_line(self, lines):
		out = []
		for l in lines:
			if isinstance(l, Line):
				out.append(l)
			else:
				out.extend(Line(l) for l in l.split('\n'))
		return out

	def setitem(self, index, value):
		self[index] = value
		return self

	def delitem(self, index):
		del self[index]
		return self

	def extend(self, lines):
		self._lines.extend(self._to_line(lines))
		return self

	def insert(self, index, *lines):
		self[index:index] = self._to_line(lines)
		return self

	def replace(self, index, *lines):
		self[index:len(lines)] = self._to_line(lines)
		return self


class Template(TemplateUtils):

	def __init__(self, *lines):
		self._lines = self._to_line(lines)

	def __repr__(self):
		return '\n'.join(repr(l) for l in self._lines)

	def __iter__(self):
		return iter(self._lines)

class Line(object):

	# spaces per tab
	space2tab = 4

	def __init__(self, text, tab=4):
		self.tab, spaces = 0, 0
		for char in text:
			if char == '\t':
				self.tab += 1
			elif char == ' ':
				spaces += 1
			else:
				break
		self.tab += spaces//self.space2tab
		self.fields = []
		for match in re.findall(r'{([^{}]*?)}', text):
			for i in range(len(match)):
				if match[i] in ".[!:":
					break
			self.fields.append(match[:i+1])
		self.text = text

	def __repr__(self):
		return self.text


class ThisTemplate(type("ThisTemplateUtils",
	(DocLogMember,), {k: (lambda k=k:
	lambda self, *args, **kwargs: None if
	self._actions.append([k, args, kwargs]) else self)()
	for k, v in TemplateUtils.__dict__.items()
	if isinstance(v, types.FunctionType)})):

	def class_init(self, cls, name):
		for c in cls.mro()[1:]:
			last = getattr(c, name, None)
			if isinstance(last, Template):
				template = Template(*last)
				break
		else:
			template = Template()
		for a in self._actions:
			# apply all postponed template actions
			getattr(template, a[0])(*a[1], **a[2])
		setattr(cls, name, template)

	def __init__(self):
		self._actions = []

	__iter__ = None
	_to_line = None


# ----------------------------------------------------------------------------
# DocLog Object and Metaclass
# ----------------------------------------------------------------------------


class DocLogBase(object):

	# attributes that cannot
	# be Content instances
	parent = None
	children = None
	logs_type = None
	template = None

	_from_instances = None
	_source_content = None

class MetaDocLog(type):

	def __new__(mcls, name, bases, classdict):
		for n in dir(DocLogBase):
			if not name.startswith("__") and isinstance(classdict.get(n), Content):
				raise RuntimeError("The attribute '%s' cannot be Content" % n)
		return super(MetaDocLog, mcls).__new__(mcls, name, bases, classdict)

	def __init__(cls, name, bases, classdict):
		"""Simple metaclass for assigning content names"""
		for k, v in classdict.items():
			if isinstance(v, DocLogMember):
				v.class_init(cls, k)

class DocLog(with_metaclass(MetaDocLog, DocLogBase)):

	def __init__(self, source, parent=None):
		# make parent-child link
		self.children = []
		if parent is not None:
			if not isinstance(parent, DocLog):
				raise TypeError("parent must be a DocLog instance")
			parent.children.append(self)
			self.parent = parent

		# handle the source type
		if self._from_instances:
			if self.logs_type is not None and not isinstance(source, self.logs_type):
				TypeError("A '%s' makes autodocs for '%s' instances, not %r"
					% (self.__class__.__name__, self.logs_type.__name__, source))
		else:
			if not inspect.isclass(source):
				source = source.__class__
			if self.logs_type is not None and not issubclass(source, self.logs_type):
				TypeError("A '%s' makes autodocs for '%s' subclasses, not %r"
					% (self.__class__.__name__, self.logs_type.__name__, source))
		self.source = source
		self._source_content = {}

	def __iter__(self):
		return iter(self.content)

	def __len__(self):
		return len(self.content)

	def __str__(self):
		return self.__class__.__name__ + "(%s)" % str(list(self))[1:-1]

	@classmethod
	def content_members(cls):
		return dict([member for member in inspect.getmembers(cls)
						if isinstance(member[1], Content)])

	@property
	def content(self):
		content_members = self.content_members()
		if len(self._source_content) != len(content_members):
			c = {}
			for name in content_members:
				c[name] = getattr(self, name)
		else:
			c = self._source_content.copy()
		return c

	def reset(self, *content_members):
		"""Force all, or the given content members, to be recomposed"""
		if self.template is None:
			raise ValueError("Type object '%s' has no defined"
						" template" % self.__class__.__name__)
		if len(content_members):
			for s in secitons:
				del self._source_content[s]
		else:
			self._source_content = {}

	def formated_content(self, name, tabs=0):
		return self.content_members()[name].format_content(self, tabs)

	def document(self):
		"""Return a string of merged, and content filled sections"""
		lines = []
		members = self.content_members()
		for line in self.template:
			d = {}
			for f in line.fields:
				text = members[f].format_content(self)
				tabbed = text.replace('\n', '\n'+' '*(line.tab*line.space2tab))
				d[f] = FormatRepr(getattr(self, f), tabbed)
			lines.append(line.text.format(**d))
		return '\n'.join(lines)


class FormatRepr(object):

	def __init__(self, raw, doc=None):
		if doc is None:
			doc = str(raw)
		self._raw = raw
		self._doc = doc

	def __getitem__(self, key):
		return self._raw[key]

	def __getattr__(self, key):
		return getattr(self._raw, key)

	def __repr__(self):
		return self._doc


class DocLogMap(object):

	def __init__(self, doclog_types):
		self._d = {}
		for dlt in doclog_types:
			if not inspect.isclass(dlt) and not issubclass(dlt, DocLog):
				raise TypeError("Expected subclasses of DocLog, not %r" % dlt)
			if 'logs_type' not in dlt.__dict__:
				raise TypeError("The 'logs_type' attribute is not "
					"explicitely defined for '%s'" % dlt.__name__)
			self._d[self._to_name(dlt.logs_type)] = dlt

	def __iter__(self):
		return iter(self._d)

	def __call__(self, obj, *args, **kwargs):
		"""A factory returning a correctly mapped DocLog instance"""
		return self[obj](obj, *args, **kwargs)

	def __getitem__(self, obj):
		for c in self._to_class(obj).mro():
			dlt = self._get(c)
			if dlt is not None:
				return dlt
		else:
			raise KeyError(repr(obj))

	def get(self, obj, default=None):
		for c in self._to_class(obj).mro():
			dlt = self._get(c)
			if dlt is not None:
				return dlt
		else:
			return default

	def _get(self, cls):
		return self._d.get(self._to_name(cls))

	@staticmethod
	def _to_class(obj):
		if inspect.isclass(obj):
			return obj
		else:
			return obj.__class__

	@staticmethod
	def _to_name(key):
		if inspect.isclass(key):
			name = key.__module__ + '.' + key.__name__
		else:
			TypeError("Expected a class")
		return name

	def __repr__(self):
		return repr(self._d)
