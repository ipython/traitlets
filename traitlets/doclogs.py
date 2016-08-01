import six

from .traitlets import *
from utils.docgen import (DocLog, DocLogMap,
	Content, content, Template, ThisTemplate)


if six.PY3:
    def copy_func(f, name=None):
        return types.FunctionType(f.__code__, f.__globals__,
        	name or f.__name__, f.__defaults__, f.__closure__)
else:
    def copy_func(f, name=None):
        return types.FunctionType(f.func_code, f.func_globals,
        	name or f.func_name, f.func_defaults, f.func_closure)

def write_docs_to_class(cls, docs):
    """Write traitlet documentation for this class to __init__"""
    im_func = copy_func(cls.__init__.im_func)
    im_func.__doc__ = trim_docstring(im_func.__doc__) + "\n\n" + docs
    cls.__init__ = types.MethodType(im_func, None, cls)


def trim_docstring(docstring):
	if not docstring:
		return ''
	# Convert tabs to spaces (following the normal Python rules)
	# and split into a list of lines:
	lines = docstring.expandtabs().splitlines()
	# Determine minimum indentation (first line doesn't count):
	indent = sys.maxint
	for line in lines[1:]:
		stripped = line.lstrip()
		if stripped:
			indent = min(indent, len(line) - len(stripped))
	# Remove indentation (first line is special):
	trimmed = [lines[0].strip()]
	if indent < sys.maxint:
		for line in lines[1:]:
			trimmed.append(line[indent:].rstrip())
	# Strip off trailing and leading blank lines:
	while trimmed and not trimmed[-1]:
		trimmed.pop()
	while trimmed and not trimmed[0]:
		trimmed.pop(0)
	# Return a single string:
	return '\n'.join(trimmed)

def full_type_name(obj):
	if not inspect.isclass(obj):
		klass = obj.__class__
	else:
		klass = obj
	m_n = klass.__module__
	if m_n != "__main__":
		return m_n + '.' + klass.__name__
	else:
		return klass.__name__


class BaseDescriptorDocLog(DocLog):

	template = Template()

	logs_type = BaseDescriptor

	_from_instances = True
	name = Content('name')

class TraitDocLog(BaseDescriptorDocLog):

	logs_type = TraitType

	read_only = Content('read_only')
	allow_none = Content('allow_none')

	template = ThisTemplate().extend([
		"{name} : {info}",
		"    :help: {help}",
		"    :read only: {read_only}",
		"    :allow none: {allow_none}",
		"",
		"    **trait metadata:**",
		"        {metadata}",
		"",
		"    **event handlers:**",
		"        {events}"
		])

	@content
	def info(self, source):
		return source.info()

	@content('help')
	def help(self, trait):
		return self.metadata.pop('help', None)

	@content('default_value')
	def default_value(self, value):
		if 'default_value' in self.metadata:
			# pop from given metadata if present
			return self.metadata.pop('default_value')
		else:
			return value

	@content("metadata")
	def metadata(self, metadata):
		return metadata.copy()

	@metadata.format
	def metadata(self, value):
		series = []
		for k, v in self.metadata.items():
			series.append('* %s: %r' % (k, v))
		return '\n'.join(series) or None

	@content
	def events(self, source):
		series = []
		if isinstance(self.parent, HasTraitsDocLog):
			for e in self.parent.events.values():
				if source.name in e.trait_names:
					series.append("* " + e.document())
		return '\n'.join(series) or None


class EventHandlerDocLog(BaseDescriptorDocLog):

	logs_type = EventHandler

	template = Template(":meth:`{event_owner}.{name}` : {info}")
	
	@content
	def event_owner(self, source):
		return full_type_name(source.this_class)
	
	@content
	def info(self, source):
		return source.info()

	@content
	def trait_names(self, source):
		try:
			return source.trait_names
		except:
			return [source.trait_name]


class ClassBasedTraitDocLog(TraitDocLog):

	logs_type = ClassBasedTraitType
	klass = Content('klass')

	@klass.format
	def klass(self, content):
		return (full_type_name(content)
			if inspect.isclass(content)
			else content)

class TypeTraitDocLog(ClassBasedTraitDocLog):

	logs_type = Type

	template = ThisTemplate().insert(
		2, "    :subclass of: {klass}")

class InstanceTraitDocLog(TraitDocLog):

	logs_type = Instance
	klass = Content('klass')

	template = ThisTemplate().insert(
		2, "    :instance of: {klass}")

class UnionTraitDocLog(TraitDocLog):

	logs_type = Union

# not stored in trait_doc_log_map
class NumberTraitDocLog(TraitDocLog):

	template = ThisTemplate().insert(
		2, "    :range: [{minimum}, {maximum}]")

	minimum = Content('min')
	@content('min')
	def minimum(self, m):
		if m is None:
			return '-inf'
		else:
			return m

	@content('max')
	def maximum(self, m):
		if m is None:
			return 'inf'
		else:
			return m

class IntTraitDocLog(NumberTraitDocLog):

	logs_type = Int

class FloatTraitDocLog(NumberTraitDocLog):

	logs_type = Float

class EnumTraitDocLog(TraitDocLog):

	logs_type = Enum

	template = ThisTemplate().insert(
		2, "    :valid input: {values}")

	values = Content('values')

class ContainerTraitDocLog(ClassBasedTraitDocLog):

	logs_type = Container

	template = ThisTemplate().insert(
		2, "    :valid input: {trait_info}")

	@content('_trait')
	def trait_info(self, trait):
		return None if trait is None else traitlet_doclog_mapping(trait)

	@trait_info.format
	def trait_info(self, doclog):
		return 'any' if doclog is None else doclog.info

class ListTraitDocLog(ContainerTraitDocLog):

	logs_type = List

	template = ThisTemplate().insert(2, (
		"    :length range: [{minimum_"
		"length}, {minimum_length}]"))

	@content('_minlen')
	def minimum_length(self, l):
		if l is None:
			return 0
		else:
			return l

	@content('_maxlen')
	def minimum_length(self, l):
		if l is None:
			return 'inf'
		else:
			return l

class TupleTraitDocLog(ContainerTraitDocLog):

	template = ThisTemplate().insert(2,
		"    :elements: {traits}")

	trait = None

	@content
	def traits(self, traits):
		return [trait_doclog_mapping(t) for t in traits]

	@traits.format
	def traits(self, doclogs):
		series = []
		for dl in doclogs:
			series.append(dl.info)
		return str(series)

class DictTraitDocLog(Instance):

	template = ThisTemplate().insert(2, "    valid types: {trait_info}")

	@content('_trait')
	def trait_info(self, trait):
		return trait_doclog_mapping(trait)

	@trait_info.format
	def trait_info(self, doclog):
		return doclog.info

class UseEnumTraitDoclog(TraitDocLog):
	# unfinished

	enum_class = Content('enum_class')
	name_prefix = Content('name_prefix')

# ----------------------------------------------------------------------------
# HasTraits DocLog Object
# ----------------------------------------------------------------------------

traitlet_doclog_mapping = DocLogMap(
	[v for v in globals().values()
	if inspect.isclass(v) and
	issubclass(v, BaseDescriptorDocLog)
	and 'logs_type' in v.__dict__])

class HasTraitsDocLog(DocLog):

	_from_classes = True

	template = ThisTemplate().extend(["{traits}"])

	def _members_to_doclogs(self, member_type):
		return {name: traitlet_doclog_mapping(member, parent=self)
			for name, member in inspect.getmembers(self.source)
			if isinstance(member, member_type)}

	@content(None)
	def traits(self, source):
		return self._members_to_doclogs(TraitType)

	@traits.format
	def traits(self, content):
		if content:
			header = "Traits of ``%s`` Instances" % full_type_name(self.source)
			header += "\n" + "-"*len(header) + "\n"
			return header + "\n\n".join(dl.document() for dl in content.values())
		return ""

	@content(None)
	def events(self, source):
		return self._members_to_doclogs(EventHandler)
