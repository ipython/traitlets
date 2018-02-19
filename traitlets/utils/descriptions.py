import re
import six
import types
import inspect


def describe(article, value, name=None, verbose=False, capital=False):
    """Return string that describes a value

    Parameters
    ----------
    article: str or None
        A definite or indefinite article. If the article is
        indefinite (i.e. ends with "a" or "an") the appropriate
        one will be infered. Thus, the arguments of ``describe``
        can themselves represent what the resulting string
        will actually look like. If None, then no article
        will be prepended to the result. For non-articled
        description, values that are instances are treated
        definitely, while classes are handled indefinitely.
    value: any
        The value which will be named.
    name: str, or None (default: None)
        Only applies when ``article`` is "the" - this
        ``name`` is a definite reference to the value.
        By default one will be infered from the value's
        type and repr methods.
    verbose: bool (default: False)
        Whether the name should be concise or verbose. When
        possible, verbose names include the module, and/or
        class name where an object was defined.
    capital: bool (default: False)
        Whether the first letter of the article should
        be capitalized or not. By default it is not.

    Examples
    --------
    **Indefinite description:**
    >>> describe("a", object())
    'an object'
    >>> describe("a", object)
    'an object'
    >>> describe("a", type(object))
    'a type'

    **Definite description:**
    >>> describe("the", object())
    "the object at '0x10741f1b0'"
    >>> describe("the", object)
    "the type 'object'"
    >>> describe("the", type(object))
    "the type 'type'"

    **Definitely named description:**
    >>> describe("the", object(), "I made")
    'the object I made'
    >>> describe("the", object, "I will use")
    'the object I will use'

    **Arbitrarily articled description:**
    >>> describe("the element of a", object())
    'the element of an object'
    """
    if isinstance(article, str):
        article = article.lower()

    if not inspect.isclass(value):
        typename = type(value).__name__
    else:
        typename = value.__name__
    if verbose:
        typename = _prefix(value) + typename

    if article is None:
        article = "the" if inspect.isclass(value) else "a"
        temp = describe(article, value, name, verbose)
        final = temp.split(" ", 1)[1]
    elif not _indefinite(article):
        if name is None:
            final = describe(article, type(value), _name(value, verbose), verbose)
        else:
            final = _articled(article, "%s %s" % (typename, name))
    else:
        final = _articled(article, typename + (
            "" if name is None else " " + name))
    if capital:
        final = final[:1].upper() + final[1:]
    return final.strip()


def class_of(value):
    """Returns a string of the value's type with an indefinite article.
    For example 'an Image' or 'a PlotValue'.
    """
    if inspect.isclass(value):
        return add_article(value.__name__)
    else:
        return class_of(type(value))


def add_article(name, definite=False, capital=False):
    """Returns the string with a prepended article.

    Parameters
    ----------
    definite: bool (default: False)
        Whether the article is definite or not.
        Indefinite articles being 'a' and 'an',
        while 'the' is definite.
    capital: bool (default: False)
        Whether the added article should have
        its first letter capitalized or not.
    """
    if definite:
        result = "the " + name
    else:
        if name[:1].lower() in 'aeiou':
            result = 'an ' + name
        else:
            result = 'a ' + name
    if capital:
        return result[0].upper() + result[1:]
    else:
        return result
    return result


def repr_type(obj):
    """Return a string representation of a value and its type for readable
    error messages.
    """
    the_type = type(obj)
    if six.PY2 and the_type is types.InstanceType:
        # Old-style class.
        the_type = obj.__class__
    msg = '%r %r' % (obj, the_type)
    return msg


def _articled(article, value):
    if article == "a" or article.endswith(" a"):
        if value[:1] in "aeiou":
            article = article[:-1] + "an"
    elif article == "an" or article.endswith(" an"):
        if value[:1] not in "aeiou":
            article = article[:-2] + "a"
    return "%s %s" % (article, value)


def _indefinite(article):
    for char in ("a", "an"):
        if article == char or article.endswith(" " + char):
            return True
    else:
        if (article == "the" or
            article.endswith(" the") or
            article.startswith("the ")):
            return False
        else:
            raise ValueError("Expected an indefinite article string that "
                "ends in 'a' or 'an', or a definite article that starts or "
                "ends with 'the', not %s" % describe("the", article))


def _name(value, verbose):
    tick_wrap = False
    if inspect.isclass(value):
        name = value.__name__
    elif isinstance(value, types.FunctionType):
        name = value.__name__
        tick_wrap = True
    elif isinstance(value, types.MethodType):
        name = value.__func__.__name__
        tick_wrap = True
    elif type(value).__repr__ in (object.__repr__, type.__repr__):
        name = "at '%s'" % hex(id(value))
        verbose = False
    else:
        name = repr(value)
        verbose = False
    if verbose:
        name = _prefix(value) + name
    if tick_wrap:
        name = name.join("''")
    return name


def _prefix(value):
    if isinstance(value, types.MethodType):
        name = describe(None, value.__self__, verbose=True) + '.'
    else:
        module = inspect.getmodule(value)
        if module is not None and module.__name__ != "builtins":
            name = module.__name__ + '.'
        else:
            name = ""
    return name
