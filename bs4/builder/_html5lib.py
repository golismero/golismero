__all__ = [
    'HTML5TreeBuilder',
    ]

from bs4.builder import (
    PERMISSIVE,
    HTML,
    HTML_5,
    HTMLTreeBuilder,
    )
import html5lib
from html5lib.constants import DataLossWarning
import warnings
from bs4.element import (
    Comment,
    Doctype,
    NavigableString,
    Tag,
    )

class HTML5TreeBuilder(HTMLTreeBuilder):
    """Use html5lib to build a tree."""

    features = ['html5lib', PERMISSIVE, HTML_5, HTML]

    def prepare_markup(self, markup, user_specified_encoding):
        # Store the user-specified encoding for use later on.
        self.user_specified_encoding = user_specified_encoding
        return markup, None, None

    # These methods are defined by Beautiful Soup.
    def feed(self, markup):
        parser = html5lib.HTMLParser(tree=self.create_treebuilder)
        doc = parser.parse(markup, encoding=self.user_specified_encoding)

        # Set the character encoding detected by the tokenizer.
        if isinstance(markup, unicode):
            # We need to special-case this because html5lib sets
            # charEncoding to UTF-8 if it gets Unicode input.
            doc.original_encoding = None
        else:
            doc.original_encoding = parser.tokenizer.stream.charEncoding[0]

    def create_treebuilder(self, namespaceHTMLElements):
        self.underlying_builder = TreeBuilderForHtml5lib(
            self.soup, namespaceHTMLElements)
        return self.underlying_builder

    def test_fragment_to_document(self, fragment):
        """See `TreeBuilder`."""
        return u'<html><head></head><body>%s</body></html>' % fragment


class TreeBuilderForHtml5lib(html5lib.treebuilders._base.TreeBuilder):

    def __init__(self, soup, namespaceHTMLElements):
        self.soup = soup
        if namespaceHTMLElements:
            warnings.warn("namespaceHTMLElements not supported yet",
                          DataLossWarning)
        super(TreeBuilderForHtml5lib, self).__init__(namespaceHTMLElements)

    def documentClass(self):
        self.soup.reset()
        return Element(self.soup, self.soup, None)

    def insertDoctype(self, token):
        name = token["name"]
        publicId = token["publicId"]
        systemId = token["systemId"]

        doctype = Doctype.for_name_and_ids(name, publicId, systemId)
        self.soup.object_was_parsed(doctype)

    def elementClass(self, name, namespace):
        if namespace is not None:
            warnings.warn("BeautifulSoup cannot represent elements in any namespace", DataLossWarning)
        return Element(Tag(self.soup, self.soup.builder, name), self.soup, namespace)

    def commentClass(self, data):
        return TextNode(Comment(data), self.soup)

    def fragmentClass(self):
        self.soup = BeautifulSoup("")
        self.soup.name = "[document_fragment]"
        return Element(self.soup, self.soup, None)

    def appendChild(self, node):
        self.soup.insert(len(self.soup.contents), node.element)

    def testSerializer(self, element):
        return testSerializer(element)

    def getDocument(self):
        return self.soup

    def getFragment(self):
        return html5lib.treebuilders._base.TreeBuilder.getFragment(self).element

class AttrList(object):
    def __init__(self, element):
        self.element = element
        self.attrs = dict(self.element.attrs)
    def __iter__(self):
        return list(self.attrs.items()).__iter__()
    def __setitem__(self, name, value):
        "set attr", name, value
        self.element[name] = value
    def items(self):
        return list(self.attrs.items())
    def keys(self):
        return list(self.attrs.keys())
    def __getitem__(self, name):
        return self.attrs[name]
    def __contains__(self, name):
        return name in list(self.attrs.keys())


class Element(html5lib.treebuilders._base.Node):
    def __init__(self, element, soup, namespace):
        html5lib.treebuilders._base.Node.__init__(self, element.name)
        self.element = element
        self.soup = soup
        self.namespace = namespace

    def _nodeIndex(self, node, refNode):
        # Finds a node by identity rather than equality
        for index in range(len(self.element.contents)):
            if id(self.element.contents[index]) == id(refNode.element):
                return index
        return None

    def appendChild(self, node):
        if (node.element.__class__ == NavigableString and self.element.contents
            and self.element.contents[-1].__class__ == NavigableString):
            # Concatenate new text onto old text node
            # (TODO: This has O(n^2) performance, for input like "a</a>a</a>a</a>...")
            newStr = NavigableString(self.element.contents[-1]+node.element)

            # Remove the old text node
            # (Can't simply use .extract() by itself, because it fails if
            # an equal text node exists within the parent node)
            oldElement = self.element.contents[-1]
            del self.element.contents[-1]
            oldElement.parent = None
            oldElement.extract()

            self.element.insert(len(self.element.contents), newStr)
        else:
            self.element.insert(len(self.element.contents), node.element)
            node.parent = self

    def getAttributes(self):
        return AttrList(self.element)

    def setAttributes(self, attributes):
        if attributes is not None and attributes != {}:
            for name, value in list(attributes.items()):
                self.element[name] =  value
            # The attributes may contain variables that need substitution.
            # Call set_up_substitutions manually.
            # The Tag constructor calls this method automatically,
            # but html5lib creates a Tag object before setting up
            # the attributes.
            self.element.contains_substitutions = (
                self.soup.builder.set_up_substitutions(
                    self.element))
    attributes = property(getAttributes, setAttributes)

    def insertText(self, data, insertBefore=None):
        text = TextNode(NavigableString(data), self.soup)
        if insertBefore:
            self.insertBefore(text, insertBefore)
        else:
            self.appendChild(text)

    def insertBefore(self, node, refNode):
        index = self._nodeIndex(node, refNode)
        if (node.element.__class__ == NavigableString and self.element.contents
            and self.element.contents[index-1].__class__ == NavigableString):
            # (See comments in appendChild)
            newStr = NavigableString(self.element.contents[index-1]+node.element)
            oldNode = self.element.contents[index-1]
            del self.element.contents[index-1]
            oldNode.parent = None
            oldNode.extract()

            self.element.insert(index-1, newStr)
        else:
            self.element.insert(index, node.element)
            node.parent = self

    def removeChild(self, node):
        index = self._nodeIndex(node.parent, node)
        del node.parent.element.contents[index]
        node.element.parent = None
        node.element.extract()
        node.parent = None

    def reparentChildren(self, newParent):
        while self.element.contents:
            child = self.element.contents[0]
            child.extract()
            if isinstance(child, Tag):
                newParent.appendChild(Element(child, self.soup, namespaces["html"]))
            else:
                newParent.appendChild(TextNode(child, self.soup))

    def cloneNode(self):
        node = Element(Tag(self.soup, self.soup.builder, self.element.name), self.soup, self.namespace)
        for key,value in self.attributes:
            node.attributes[key] = value
        return node

    def hasContent(self):
        return self.element.contents

    def getNameTuple(self):
        if self.namespace == None:
            return namespaces["html"], self.name
        else:
            return self.namespace, self.name

    nameTuple = property(getNameTuple)

class TextNode(Element):
    def __init__(self, element, soup):
        html5lib.treebuilders._base.Node.__init__(self, None)
        self.element = element
        self.soup = soup

    def cloneNode(self):
        raise NotImplementedError
