from collections import defaultdict
import re
import sys

__all__ = [
    'HTMLTreeBuilder',
    'SAXTreeBuilder',
    'TreeBuilder',
    'TreeBuilderRegistry',
    ]

# Some useful features for a TreeBuilder to have.
FAST = 'fast'
PERMISSIVE = 'permissive'
STRICT = 'strict'
XML = 'xml'
HTML = 'html'
HTML_5 = 'html5'


class TreeBuilderRegistry(object):

    def __init__(self):
        self.builders_for_feature = defaultdict(list)
        self.builders = []

    def register(self, treebuilder_class):
        """Register a treebuilder based on its advertised features."""
        for feature in treebuilder_class.features:
            self.builders_for_feature[feature].insert(0, treebuilder_class)
        self.builders.insert(0, treebuilder_class)

    def lookup(self, *features):
        if len(self.builders) == 0:
            # There are no builders at all.
            return None

        if len(features) == 0:
            # They didn't ask for any features. Give them the most
            # recently registered builder.
            return self.builders[0]

        # Go down the list of features in order, and eliminate any builders
        # that don't match every feature.
        features = list(features)
        features.reverse()
        candidates = None
        candidate_set = None
        while len(features) > 0:
            feature = features.pop()
            we_have_the_feature = self.builders_for_feature.get(feature, [])
            if len(we_have_the_feature) > 0:
                if candidates is None:
                    candidates = we_have_the_feature
                    candidate_set = set(candidates)
                else:
                    # Eliminate any candidates that don't have this feature.
                    candidate_set = candidate_set.intersection(
                        set(we_have_the_feature))

        # The only valid candidates are the ones in candidate_set.
        # Go through the original list of candidates and pick the first one
        # that's in candidate_set.
        if candidate_set is None:
            return None
        for candidate in candidates:
            if candidate in candidate_set:
                return candidate
        return None

# The BeautifulSoup class will take feature lists from developers and use them
# to look up builders in this registry.
builder_registry = TreeBuilderRegistry()


class TreeBuilder(object):
    """Turn a document into a Beautiful Soup object tree."""

    features = []

    is_xml = False
    preserve_whitespace_tags = set()
    empty_element_tags = None # A tag will be considered an empty-element
                              # tag when and only when it has no contents.

    def __init__(self):
        self.soup = None

    def reset(self):
        pass

    def can_be_empty_element(self, tag_name):
        """Might a tag with this name be an empty-element tag?

        The final markup may or may not actually present this tag as
        self-closing.

        For instance: an HTMLBuilder does not consider a <p> tag to be
        an empty-element tag (it's not in
        HTMLBuilder.empty_element_tags). This means an empty <p> tag
        will be presented as "<p></p>", not "<p />".

        The default implementation has no opinion about which tags are
        empty-element tags, so a tag will be presented as an
        empty-element tag if and only if it has no contents.
        "<foo></foo>" will become "<foo />", and "<foo>bar</foo>" will
        be left alone.
        """
        if self.empty_element_tags is None:
            return True
        return tag_name in self.empty_element_tags

    def feed(self, markup):
        raise NotImplementedError()

    def prepare_markup(self, markup, user_specified_encoding=None,
                       document_declared_encoding=None):
        return markup, None, None

    def test_fragment_to_document(self, fragment):
        """Wrap an HTML fragment to make it look like a document.

        Different parsers do this differently. For instance, lxml
        introduces an empty <head> tag, and html5lib
        doesn't. Abstracting this away lets us write simple tests
        which run HTML fragments through the parser and compare the
        results against other HTML fragments.

        This method should not be used outside of tests.
        """
        return fragment

    def set_up_substitutions(self, tag):
        pass


class SAXTreeBuilder(TreeBuilder):
    """A Beautiful Soup treebuilder that listens for SAX events."""

    def feed(self, markup):
        raise NotImplementedError()

    def close(self):
        pass

    def startElement(self, name, attrs):
        attrs = dict((key[1], value) for key, value in list(attrs.items()))
        #print "Start %s, %r" % (name, attrs)
        self.soup.handle_starttag(name, attrs)

    def endElement(self, name):
        #print "End %s" % name
        self.soup.handle_endtag(name)

    def startElementNS(self, nsTuple, nodeName, attrs):
        # Throw away (ns, nodeName) for now.
        self.startElement(nodeName, attrs)

    def endElementNS(self, nsTuple, nodeName):
        # Throw away (ns, nodeName) for now.
        self.endElement(nodeName)
        #handler.endElementNS((ns, node.nodeName), node.nodeName)

    def startPrefixMapping(self, prefix, nodeValue):
        # Ignore the prefix for now.
        pass

    def endPrefixMapping(self, prefix):
        # Ignore the prefix for now.
        # handler.endPrefixMapping(prefix)
        pass

    def characters(self, content):
        self.soup.handle_data(content)

    def startDocument(self):
        pass

    def endDocument(self):
        pass


class HTMLTreeBuilder(TreeBuilder):
    """This TreeBuilder knows facts about HTML.

    Such as which tags are empty-element tags.
    """

    preserve_whitespace_tags = set(['pre', 'textarea'])
    empty_element_tags = set(['br' , 'hr', 'input', 'img', 'meta',
                              'spacer', 'link', 'frame', 'base'])

    # Used by set_up_substitutions to detect the charset in a META tag
    CHARSET_RE = re.compile("((^|;)\s*charset=)([^;]*)", re.M)

    def set_up_substitutions(self, tag):
        if tag.name != 'meta':
            return False

        http_equiv = tag.get('http-equiv')
        content = tag.get('content')

        if (http_equiv is not None
            and content is not None
            and http_equiv.lower() == 'content-type'):
            # This is an interesting meta tag.
            match = self.CHARSET_RE.search(content)
            if match:
                if (self.soup.declared_html_encoding is not None or
                    self.soup.original_encoding == self.soup.from_encoding):
                    # An HTML encoding was sniffed while converting
                    # the document to Unicode, or an HTML encoding was
                    # sniffed during a previous pass through the
                    # document, or an encoding was specified
                    # explicitly and it worked. Rewrite the meta tag.
                    def rewrite(match):
                        return match.group(1) + "%SOUP-ENCODING%"
                    tag['content'] = self.CHARSET_RE.sub(rewrite, content)
                    return True
                else:
                    # This is our first pass through the document.
                    # Go through it again with the encoding information.
                    new_charset = match.group(3)
                    if (new_charset is not None
                        and new_charset != self.soup.original_encoding):
                        self.soup.declared_html_encoding = new_charset
                        self.soup._feed(self.soup.declared_html_encoding)
                        raise StopParsing
                    pass
        return False


def register_treebuilders_from(module):
    """Copy TreeBuilders from the given module into this module."""
    # I'm fairly sure this is not the best way to do this.
    this_module = sys.modules['bs4.builder']
    for name in module.__all__:
        obj = getattr(module, name)

        if issubclass(obj, TreeBuilder):
            setattr(this_module, name, obj)
            this_module.__all__.append(name)
            # Register the builder while we're at it.
            this_module.builder_registry.register(obj)

# Builders are registered in reverse order of priority, so that custom
# builder registrations will take precedence. In general, we want
# html5lib to take precedence over lxml, because it's more
# reliable. And we only want to use HTMLParser as a last result.
from .import _htmlparser
register_treebuilders_from(_htmlparser)
try:
    from . import _lxml
    register_treebuilders_from(_lxml)
except ImportError:
    # They don't have lxml installed.
    pass
try:
    from . import _html5lib
    register_treebuilders_from(_html5lib)
except ImportError:
    # They don't have html5lib installed.
    pass
