# -*- coding: utf-8 -*-
"""Tests for Beautiful Soup's tree traversal methods.

The tree traversal methods are the main advantage of using Beautiful
Soup over other parsers.

Different parsers will build different Beautiful Soup trees given the
same markup, but all Beautiful Soup trees can be traversed with the
methods tested here.
"""

import copy
import pickle
import re
from bs4 import BeautifulSoup
from bs4.builder import builder_registry
from bs4.element import CData, SoupStrainer, Tag
from bs4.testing import SoupTest

class TreeTest(SoupTest):

    def assertSelects(self, tags, should_match):
        """Make sure that the given tags have the correct text.

        This is used in tests that define a bunch of tags, each
        containing a single string, and then select certain strings by
        some mechanism.
        """
        self.assertEqual([tag.string for tag in tags], should_match)

    def assertSelectsIDs(self, tags, should_match):
        """Make sure that the given tags have the correct IDs.

        This is used in tests that define a bunch of tags, each
        containing a single string, and then select certain strings by
        some mechanism.
        """
        self.assertEqual([tag['id'] for tag in tags], should_match)


class TestFind(TreeTest):
    """Basic tests of the find() method.

    find() just calls find_all() with limit=1, so it's not tested all
    that thouroughly here.
    """

    def test_find_tag(self):
        soup = self.soup("<a>1</a><b>2</b><a>3</a><b>4</b>")
        self.assertEqual(soup.find("b").string, "2")

    def test_unicode_text_find(self):
        soup = self.soup(u'<h1>Räksmörgås</h1>')
        self.assertEqual(soup.find(text=u'Räksmörgås'), u'Räksmörgås')


class TestFindAll(TreeTest):
    """Basic tests of the find_all() method."""

    def test_find_all_text_nodes(self):
        """You can search the tree for text nodes."""
        soup = self.soup("<html>Foo<b>bar</b>\xbb</html>")
        # Exact match.
        self.assertEqual(soup.find_all(text="bar"), [u"bar"])
        # Match any of a number of strings.
        self.assertEqual(
            soup.find_all(text=["Foo", "bar"]), [u"Foo", u"bar"])
        # Match a regular expression.
        self.assertEqual(soup.find_all(text=re.compile('.*')),
                         [u"Foo", u"bar", u'\xbb'])
        # Match anything.
        self.assertEqual(soup.find_all(text=True),
                         [u"Foo", u"bar", u'\xbb'])

    def test_find_all_limit(self):
        """You can limit the number of items returned by find_all."""
        soup = self.soup("<a>1</a><a>2</a><a>3</a><a>4</a><a>5</a>")
        self.assertSelects(soup.find_all('a', limit=3), ["1", "2", "3"])
        self.assertSelects(soup.find_all('a', limit=1), ["1"])
        self.assertSelects(
            soup.find_all('a', limit=10), ["1", "2", "3", "4", "5"])

        # A limit of 0 means no limit.
        self.assertSelects(
            soup.find_all('a', limit=0), ["1", "2", "3", "4", "5"])

class TestFindAllByName(TreeTest):
    """Test ways of finding tags by tag name."""

    def setUp(self):
        super(TreeTest, self).setUp()
        self.tree =  self.soup("""<a>First tag.</a>
                                  <b>Second tag.</b>
                                  <c>Third <a>Nested tag.</a> tag.</c>""")

    def test_find_all_by_tag_name(self):
        # Find all the <a> tags.
        self.assertSelects(
            self.tree.find_all('a'), ['First tag.', 'Nested tag.'])

    def test_find_all_on_non_root_element(self):
        # You can call find_all on any node, not just the root.
        self.assertSelects(self.tree.c.find_all('a'), ['Nested tag.'])

    def test_calling_element_invokes_find_all(self):
        self.assertSelects(self.tree('a'), ['First tag.', 'Nested tag.'])

    def test_find_all_by_tag_strainer(self):
        self.assertSelects(
            self.tree.find_all(SoupStrainer('a')),
            ['First tag.', 'Nested tag.'])

    def test_find_all_by_tag_names(self):
        self.assertSelects(
            self.tree.find_all(['a', 'b']),
            ['First tag.', 'Second tag.', 'Nested tag.'])

    def test_find_all_by_tag_dict(self):
        self.assertSelects(
            self.tree.find_all({'a' : True, 'b' : True}),
            ['First tag.', 'Second tag.', 'Nested tag.'])

    def test_find_all_by_tag_re(self):
        self.assertSelects(
            self.tree.find_all(re.compile('^[ab]$')),
            ['First tag.', 'Second tag.', 'Nested tag.'])

    def test_find_all_with_tags_matching_method(self):
        # You can define an oracle method that determines whether
        # a tag matches the search.
        def id_matches_name(tag):
            return tag.name == tag.get('id')

        tree = self.soup("""<a id="a">Match 1.</a>
                            <a id="1">Does not match.</a>
                            <b id="b">Match 2.</a>""")

        self.assertSelects(
            tree.find_all(id_matches_name), ["Match 1.", "Match 2."])


class TestFindAllByAttribute(TreeTest):

    def test_find_all_by_attribute_name(self):
        # You can pass in keyword arguments to find_all to search by
        # attribute.
        tree = self.soup("""
                         <a id="first">Matching a.</a>
                         <a id="second">
                          Non-matching <b id="first">Matching b.</b>a.
                         </a>""")
        self.assertSelects(tree.find_all(id='first'),
                           ["Matching a.", "Matching b."])

    def test_find_all_by_attribute_dict(self):
        # You can pass in a dictionary as the argument 'attrs'. This
        # lets you search for attributes like 'name' (a fixed argument
        # to find_all) and 'class' (a reserved word in Python.)
        tree = self.soup("""
                         <a name="name1" class="class1">Name match.</a>
                         <a name="name2" class="class2">Class match.</a>
                         <a name="name3" class="class3">Non-match.</a>
                         <name1>A tag called 'name1'.</name1>
                         """)

        # This doesn't do what you want.
        self.assertSelects(tree.find_all(name='name1'),
                           ["A tag called 'name1'."])
        # This does what you want.
        self.assertSelects(tree.find_all(attrs={'name' : 'name1'}),
                           ["Name match."])

        # Passing class='class2' would cause a syntax error.
        self.assertSelects(tree.find_all(attrs={'class' : 'class2'}),
                           ["Class match."])

    def test_find_all_by_class(self):
        # Passing in a string to 'attrs' will search the CSS class.
        tree = self.soup("""
                         <a class="1">Class 1.</a>
                         <a class="2">Class 2.</a>
                         <b class="1">Class 1.</b>
                         <c class="3 4">Class 3 and 4.</c>
                         """)
        self.assertSelects(tree.find_all('a', '1'), ['Class 1.'])
        self.assertSelects(tree.find_all(attrs='1'), ['Class 1.', 'Class 1.'])
        self.assertSelects(tree.find_all('c', '3'), ['Class 3 and 4.'])
        self.assertSelects(tree.find_all('c', '4'), ['Class 3 and 4.'])

    def test_find_all_by_attribute_soupstrainer(self):
        tree = self.soup("""
                         <a id="first">Match.</a>
                         <a id="second">Non-match.</a>""")

        strainer = SoupStrainer(attrs={'id' : 'first'})
        self.assertSelects(tree.find_all(strainer), ['Match.'])

    def test_find_all_with_missing_atribute(self):
        # You can pass in None as the value of an attribute to find_all.
        # This will match tags that do not have that attribute set.
        tree = self.soup("""<a id="1">ID present.</a>
                            <a>No ID present.</a>
                            <a id="">ID is empty.</a>""")
        self.assertSelects(tree.find_all('a', id=None), ["No ID present."])

    def test_find_all_with_defined_attribute(self):
        # You can pass in None as the value of an attribute to find_all.
        # This will match tags that have that attribute set to any value.
        tree = self.soup("""<a id="1">ID present.</a>
                            <a>No ID present.</a>
                            <a id="">ID is empty.</a>""")
        self.assertSelects(
            tree.find_all(id=True), ["ID present.", "ID is empty."])

    def test_find_all_with_numeric_attribute(self):
        # If you search for a number, it's treated as a string.
        tree = self.soup("""<a id=1>Unquoted attribute.</a>
                            <a id="1">Quoted attribute.</a>""")

        expected = ["Unquoted attribute.", "Quoted attribute."]
        self.assertSelects(tree.find_all(id=1), expected)
        self.assertSelects(tree.find_all(id="1"), expected)

    def test_find_all_with_list_attribute_values(self):
        # You can pass a list of attribute values instead of just one,
        # and you'll get tags that match any of the values.
        tree = self.soup("""<a id="1">1</a>
                            <a id="2">2</a>
                            <a id="3">3</a>
                            <a>No ID.</a>""")
        self.assertSelects(tree.find_all(id=["1", "3", "4"]),
                           ["1", "3"])

    def test_find_all_with_regular_expression_attribute_value(self):
        # You can pass a regular expression as an attribute value, and
        # you'll get tags whose values for that attribute match the
        # regular expression.
        tree = self.soup("""<a id="a">One a.</a>
                            <a id="aa">Two as.</a>
                            <a id="ab">Mixed as and bs.</a>
                            <a id="b">One b.</a>
                            <a>No ID.</a>""")

        self.assertSelects(tree.find_all(id=re.compile("^a+$")),
                           ["One a.", "Two as."])


class TestIndex(TreeTest):
    """Test Tag.index"""
    def test_index(self):
        tree = self.soup("""<wrap>
                            <a>Identical</a>
                            <b>Not identical</b>
                            <a>Identical</a>

                            <c><d>Identical with child</d></c>
                            <b>Also not identical</b>
                            <c><d>Identical with child</d></c>
                            </wrap>""")
        wrap = tree.wrap
        for i, element in enumerate(wrap.contents):
            self.assertEqual(i, wrap.index(element))
        self.assertRaises(ValueError, tree.index, 1)


class TestParentOperations(TreeTest):
    """Test navigation and searching through an element's parents."""

    def setUp(self):
        super(TestParentOperations, self).setUp()
        self.tree = self.soup('''<ul id="empty"></ul>
                                 <ul id="top">
                                  <ul id="middle">
                                   <ul id="bottom">
                                    <b>Start here</b>
                                   </ul>
                                  </ul>''')
        self.start = self.tree.b


    def test_parent(self):
        self.assertEquals(self.start.parent['id'], 'bottom')
        self.assertEquals(self.start.parent.parent['id'], 'middle')
        self.assertEquals(self.start.parent.parent.parent['id'], 'top')

    def test_parent_of_top_tag_is_soup_object(self):
        top_tag = self.tree.contents[0]
        self.assertEquals(top_tag.parent, self.tree)

    def test_soup_object_has_no_parent(self):
        self.assertEquals(None, self.tree.parent)

    def test_find_parents(self):
        self.assertSelectsIDs(
            self.start.find_parents('ul'), ['bottom', 'middle', 'top'])
        self.assertSelectsIDs(
            self.start.find_parents('ul', id="middle"), ['middle'])

    def test_find_parent(self):
        self.assertEquals(self.start.find_parent('ul')['id'], 'bottom')

    def test_parent_of_text_element(self):
        text = self.tree.find(text="Start here")
        self.assertEquals(text.parent.name, 'b')

    def test_text_element_find_parent(self):
        text = self.tree.find(text="Start here")
        self.assertEquals(text.find_parent('ul')['id'], 'bottom')

    def test_parent_generator(self):
        parents = [parent['id'] for parent in self.start.parents
                   if parent is not None and 'id' in parent.attrs]
        self.assertEquals(parents, ['bottom', 'middle', 'top'])


class ProximityTest(TreeTest):

    def setUp(self):
        super(TreeTest, self).setUp()
        self.tree = self.soup(
            '<html id="start"><head></head><body><b id="1">One</b><b id="2">Two</b><b id="3">Three</b></body></html>')


class TestNextOperations(ProximityTest):

    def setUp(self):
        super(TestNextOperations, self).setUp()
        self.start = self.tree.b

    def test_next(self):
        self.assertEquals(self.start.next_element, "One")
        self.assertEquals(self.start.next_element.next_element['id'], "2")

    def test_next_of_last_item_is_none(self):
        last = self.tree.find(text="Three")
        self.assertEquals(last.next_element, None)

    def test_next_of_root_is_none(self):
        # The document root is outside the next/previous chain.
        self.assertEquals(self.tree.next_element, None)

    def test_find_all_next(self):
        self.assertSelects(self.start.find_all_next('b'), ["Two", "Three"])
        self.start.find_all_next(id=3)
        self.assertSelects(self.start.find_all_next(id=3), ["Three"])

    def test_find_next(self):
        self.assertEquals(self.start.find_next('b')['id'], '2')
        self.assertEquals(self.start.find_next(text="Three"), "Three")

    def test_find_next_for_text_element(self):
        text = self.tree.find(text="One")
        self.assertEquals(text.find_next("b").string, "Two")
        self.assertSelects(text.find_all_next("b"), ["Two", "Three"])

    def test_next_generator(self):
        start = self.tree.find(text="Two")
        successors = [node for node in start.next_elements]
        # There are two successors: the final <b> tag and its text contents.
        # Then we go off the end.
        tag, contents, none = successors
        self.assertEquals(tag['id'], '3')
        self.assertEquals(contents, "Three")
        self.assertEquals(none, None)

        # XXX Should next_elements really return None? Seems like it
        # should just stop.


class TestPreviousOperations(ProximityTest):

    def setUp(self):
        super(TestPreviousOperations, self).setUp()
        self.end = self.tree.find(text="Three")

    def test_previous(self):
        self.assertEquals(self.end.previous_element['id'], "3")
        self.assertEquals(self.end.previous_element.previous_element, "Two")

    def test_previous_of_first_item_is_none(self):
        first = self.tree.find('html')
        self.assertEquals(first.previous_element, None)

    def test_previous_of_root_is_none(self):
        # The document root is outside the next/previous chain.
        # XXX This is broken!
        #self.assertEquals(self.tree.previous_element, None)
        pass

    def test_find_all_previous(self):
        # The <b> tag containing the "Three" node is the predecessor
        # of the "Three" node itself, which is why "Three" shows up
        # here.
        self.assertSelects(
            self.end.find_all_previous('b'), ["Three", "Two", "One"])
        self.assertSelects(self.end.find_all_previous(id=1), ["One"])

    def test_find_previous(self):
        self.assertEquals(self.end.find_previous('b')['id'], '3')
        self.assertEquals(self.end.find_previous(text="One"), "One")

    def test_find_previous_for_text_element(self):
        text = self.tree.find(text="Three")
        self.assertEquals(text.find_previous("b").string, "Three")
        self.assertSelects(
            text.find_all_previous("b"), ["Three", "Two", "One"])

    def test_previous_generator(self):
        start = self.tree.find(text="One")
        predecessors = [node for node in start.previous_elements]

        # There are four predecessors: the <b> tag containing "One"
        # the <body> tag, the <head> tag, and the <html> tag. Then we
        # go off the end.
        b, body, head, html, none = predecessors
        self.assertEquals(b['id'], '1')
        self.assertEquals(body.name, "body")
        self.assertEquals(head.name, "head")
        self.assertEquals(html.name, "html")
        self.assertEquals(none, None)

        # Again, we shouldn't be returning None.


class SiblingTest(TreeTest):

    def setUp(self):
        super(SiblingTest, self).setUp()
        markup = '''<html>
                    <span id="1">
                     <span id="1.1"></span>
                    </span>
                    <span id="2">
                     <span id="2.1"></span>
                    </span>
                    <span id="3">
                     <span id="3.1"></span>
                    </span>
                    <span id="4"></span>
                    </html>'''
        # All that whitespace looks good but makes the tests more
        # difficult. Get rid of it.
        markup = re.compile("\n\s*").sub("", markup)
        self.tree = self.soup(markup)


class TestNextSibling(SiblingTest):

    def setUp(self):
        super(TestNextSibling, self).setUp()
        self.start = self.tree.find(id="1")

    def test_next_sibling_of_root_is_none(self):
        self.assertEquals(self.tree.next_sibling, None)

    def test_next_sibling(self):
        self.assertEquals(self.start.next_sibling['id'], '2')
        self.assertEquals(self.start.next_sibling.next_sibling['id'], '3')

        # Note the difference between next_sibling and next_element.
        self.assertEquals(self.start.next_element['id'], '1.1')

    def test_next_sibling_may_not_exist(self):
        self.assertEquals(self.tree.html.next_sibling, None)

        nested_span = self.tree.find(id="1.1")
        self.assertEquals(nested_span.next_sibling, None)

        last_span = self.tree.find(id="4")
        self.assertEquals(last_span.next_sibling, None)

    def test_find_next_sibling(self):
        self.assertEquals(self.start.find_next_sibling('span')['id'], '2')

    def test_next_siblings(self):
        self.assertSelectsIDs(self.start.find_next_siblings("span"),
                              ['2', '3', '4'])

        self.assertSelectsIDs(self.start.find_next_siblings(id='3'), ['3'])

    def test_next_sibling_for_text_element(self):
        soup = self.soup("Foo<b>bar</b>baz")
        start = soup.find(text="Foo")
        self.assertEquals(start.next_sibling.name, 'b')
        self.assertEquals(start.next_sibling.next_sibling, 'baz')

        self.assertSelects(start.find_next_siblings('b'), ['bar'])
        self.assertEquals(start.find_next_sibling(text="baz"), "baz")
        self.assertEquals(start.find_next_sibling(text="nonesuch"), None)


class TestPreviousSibling(SiblingTest):

    def setUp(self):
        super(TestPreviousSibling, self).setUp()
        self.end = self.tree.find(id="4")

    def test_previous_sibling_of_root_is_none(self):
        self.assertEquals(self.tree.previous_sibling, None)

    def test_previous_sibling(self):
        self.assertEquals(self.end.previous_sibling['id'], '3')
        self.assertEquals(self.end.previous_sibling.previous_sibling['id'], '2')

        # Note the difference between previous_sibling and previous_element.
        self.assertEquals(self.end.previous_element['id'], '3.1')

    def test_previous_sibling_may_not_exist(self):
        self.assertEquals(self.tree.html.previous_sibling, None)

        nested_span = self.tree.find(id="1.1")
        self.assertEquals(nested_span.previous_sibling, None)

        first_span = self.tree.find(id="1")
        self.assertEquals(first_span.previous_sibling, None)

    def test_find_previous_sibling(self):
        self.assertEquals(self.end.find_previous_sibling('span')['id'], '3')

    def test_previous_siblings(self):
        self.assertSelectsIDs(self.end.find_previous_siblings("span"),
                              ['3', '2', '1'])

        self.assertSelectsIDs(self.end.find_previous_siblings(id='1'), ['1'])

    def test_previous_sibling_for_text_element(self):
        soup = self.soup("Foo<b>bar</b>baz")
        start = soup.find(text="baz")
        self.assertEquals(start.previous_sibling.name, 'b')
        self.assertEquals(start.previous_sibling.previous_sibling, 'Foo')

        self.assertSelects(start.find_previous_siblings('b'), ['bar'])
        self.assertEquals(start.find_previous_sibling(text="Foo"), "Foo")
        self.assertEquals(start.find_previous_sibling(text="nonesuch"), None)


class TestTreeModification(SoupTest):

    def test_attribute_modification(self):
        soup = self.soup('<a id="1"></a>')
        soup.a['id'] = 2
        self.assertEqual(soup.decode(), self.document_for('<a id="2"></a>'))
        del(soup.a['id'])
        self.assertEqual(soup.decode(), self.document_for('<a></a>'))
        soup.a['id2'] = 'foo'
        self.assertEqual(soup.decode(), self.document_for('<a id2="foo"></a>'))

    def test_new_tag_creation(self):
        builder = builder_registry.lookup('html5lib')()
        soup = self.soup("<body></body>", builder=builder)
        a = Tag(soup, builder, 'a')
        ol = Tag(soup, builder, 'ol')
        a['href'] = 'http://foo.com/'
        soup.body.insert(0, a)
        soup.body.insert(1, ol)
        self.assertEqual(
            soup.body.encode(),
            b'<body><a href="http://foo.com/"></a><ol></ol></body>')

    def test_append_to_contents_moves_tag(self):
        doc = """<p id="1">Don't leave me <b>here</b>.</p>
                <p id="2">Don\'t leave!</p>"""
        soup = self.soup(doc)
        second_para = soup.find(id='2')
        bold = soup.b

        # Move the <b> tag to the end of the second paragraph.
        soup.find(id='2').append(soup.b)

        # The <b> tag is now a child of the second paragraph.
        self.assertEqual(bold.parent, second_para)

        self.assertEqual(
            soup.decode(), self.document_for(
                '<p id="1">Don\'t leave me .</p>\n'
                '<p id="2">Don\'t leave!<b>here</b></p>'))

    def test_replace_tag_with_itself(self):
        text = "<a><b></b><c>Foo<d></d></c></a><a><e></e></a>"
        soup = self.soup(text)
        c = soup.c
        soup.c.replace_with(c)
        self.assertEquals(soup.decode(), self.document_for(text))

    def test_replace_final_node(self):
        soup = self.soup("<b>Argh!</b>")
        soup.find(text="Argh!").replace_with("Hooray!")
        new_text = soup.find(text="Hooray!")
        b = soup.b
        self.assertEqual(new_text.previous_element, b)
        self.assertEqual(new_text.parent, b)
        self.assertEqual(new_text.previous_element.next_element, new_text)
        self.assertEqual(new_text.next_element, None)

    def test_consecutive_text_nodes(self):
        # A builder should never create two consecutive text nodes,
        # but if you insert one next to another, Beautiful Soup will
        # handle it correctly.
        soup = self.soup("<a><b>Argh!</b><c></c></a>")
        soup.b.insert(1, "Hooray!")

        self.assertEqual(
            soup.decode(), self.document_for(
                "<a><b>Argh!Hooray!</b><c></c></a>"))

        new_text = soup.find(text="Hooray!")
        self.assertEqual(new_text.previous_element, "Argh!")
        self.assertEqual(new_text.previous_element.next_element, new_text)

        self.assertEqual(new_text.previous_sibling, "Argh!")
        self.assertEqual(new_text.previous_sibling.next_sibling, new_text)

        self.assertEqual(new_text.next_sibling, None)
        self.assertEqual(new_text.next_element, soup.c)

    def test_insert_tag(self):
        builder = self.default_builder
        soup = self.soup(
            "<a><b>Find</b><c>lady!</c><d></d></a>", builder=builder)
        magic_tag = Tag(soup, builder, 'magictag')
        magic_tag.insert(0, "the")
        soup.a.insert(1, magic_tag)

        self.assertEqual(
            soup.decode(), self.document_for(
                "<a><b>Find</b><magictag>the</magictag><c>lady!</c><d></d></a>"))

        # Make sure all the relationships are hooked up correctly.
        b_tag = soup.b
        self.assertEqual(b_tag.next_sibling, magic_tag)
        self.assertEqual(magic_tag.previous_sibling, b_tag)

        find = b_tag.find(text="Find")
        self.assertEqual(find.next_element, magic_tag)
        self.assertEqual(magic_tag.previous_element, find)

        c_tag = soup.c
        self.assertEqual(magic_tag.next_sibling, c_tag)
        self.assertEqual(c_tag.previous_sibling, magic_tag)

        the = magic_tag.find(text="the")
        self.assertEqual(the.parent, magic_tag)
        self.assertEqual(the.next_element, c_tag)
        self.assertEqual(c_tag.previous_element, the)

    def test_insert_works_on_empty_element_tag(self):
        # This is a little strange, since most HTML parsers don't allow
        # markup like this to come through. But in general, we don't
        # know what the parser would or wouldn't have allowed, so
        # I'm letting this succeed for now.
        soup = self.soup("<br />")
        soup.br.insert(1, "Contents")
        self.assertEquals(str(soup.br), "<br>Contents</br>")

    def test_replace_with(self):
        soup = self.soup(
                "<p>There's <b>no</b> business like <b>show</b> business</p>")
        no, show = soup.find_all('b')
        show.replace_with(no)
        self.assertEquals(
            soup.decode(),
            self.document_for(
                "<p>There's  business like <b>no</b> business</p>"))

        self.assertEquals(show.parent, None)
        self.assertEquals(no.parent, soup.p)
        self.assertEquals(no.next_element, "no")
        self.assertEquals(no.next_sibling, " business")

    def test_nested_tag_replace_with(self):
        soup = self.soup(
            """<a>We<b>reserve<c>the</c><d>right</d></b></a><e>to<f>refuse</f><g>service</g></e>""")

        # Replace the entire <b> tag and its contents ("reserve the
        # right") with the <f> tag ("refuse").
        remove_tag = soup.b
        move_tag = soup.f
        remove_tag.replace_with(move_tag)

        self.assertEqual(
            soup.decode(), self.document_for(
                "<a>We<f>refuse</f></a><e>to<g>service</g></e>"))

        # The <b> tag is now an orphan.
        self.assertEqual(remove_tag.parent, None)
        self.assertEqual(remove_tag.find(text="right").next_element, None)
        self.assertEqual(remove_tag.previous_element, None)
        self.assertEqual(remove_tag.next_sibling, None)
        self.assertEqual(remove_tag.previous_sibling, None)

        # The <f> tag is now connected to the <a> tag.
        self.assertEqual(move_tag.parent, soup.a)
        self.assertEqual(move_tag.previous_element, "We")
        self.assertEqual(move_tag.next_element.next_element, soup.e)
        self.assertEqual(move_tag.next_sibling, None)

        # The gap where the <f> tag used to be has been mended, and
        # the word "to" is now connected to the <g> tag.
        to_text = soup.find(text="to")
        g_tag = soup.g
        self.assertEqual(to_text.next_element, g_tag)
        self.assertEqual(to_text.next_sibling, g_tag)
        self.assertEqual(g_tag.previous_element, to_text)
        self.assertEqual(g_tag.previous_sibling, to_text)

    def test_replace_with_children(self):
        tree = self.soup("""
            <p>Unneeded <em>formatting</em> is unneeded</p>
            """)
        tree.em.replace_with_children()
        self.assertEqual(tree.em, None)
        self.assertEqual(tree.p.text, "Unneeded formatting is unneeded")

    def test_extract(self):
        soup = self.soup(
            '<html><body>Some content. <div id="nav">Nav crap</div> More content.</body></html>')

        self.assertEqual(len(soup.body.contents), 3)
        extracted = soup.find(id="nav").extract()

        self.assertEqual(
            soup.decode(), "<html><body>Some content.  More content.</body></html>")
        self.assertEqual(extracted.decode(), '<div id="nav">Nav crap</div>')

        # The extracted tag is now an orphan.
        self.assertEqual(len(soup.body.contents), 2)
        self.assertEqual(extracted.parent, None)
        self.assertEqual(extracted.previous_element, None)
        self.assertEqual(extracted.next_element.next_element, None)

        # The gap where the extracted tag used to be has been mended.
        content_1 = soup.find(text="Some content. ")
        content_2 = soup.find(text=" More content.")
        self.assertEquals(content_1.next_element, content_2)
        self.assertEquals(content_1.next_sibling, content_2)
        self.assertEquals(content_2.previous_element, content_1)
        self.assertEquals(content_2.previous_sibling, content_1)

    def test_clear(self):
        """Tag.clear()"""
        soup = self.soup("<p><a>String <em>Italicized</em></a> and another</p>")
        # clear using extract()
        a = soup.a
        soup.p.clear()
        self.assertEqual(len(soup.p.contents), 0)
        self.assertTrue(hasattr(a, "contents"))

        # clear using decompose()
        em = a.em
        a.clear(decompose=True)
        self.assertFalse(hasattr(em, "contents"))

    def test_string_set(self):
        """Tag.string = 'string'"""
        soup = self.soup("<a></a> <b><c></c></b>")
        soup.a.string = "foo"
        self.assertEqual(soup.a.contents, ["foo"])
        soup.b.string = "bar"
        self.assertEqual(soup.b.contents, ["bar"])


class TestElementObjects(SoupTest):
    """Test various features of element objects."""

    def test_len(self):
        """The length of an element is its number of children."""
        soup = self.soup("<top>1<b>2</b>3</top>")

        # The BeautifulSoup object itself contains one element: the
        # <top> tag.
        self.assertEquals(len(soup.contents), 1)
        self.assertEquals(len(soup), 1)

        # The <top> tag contains three elements: the text node "1", the
        # <b> tag, and the text node "3".
        self.assertEquals(len(soup.top), 3)
        self.assertEquals(len(soup.top.contents), 3)

    def test_member_access_invokes_find(self):
        """Accessing a Python member .foo or .fooTag invokes find('foo')"""
        soup = self.soup('<b><i></i></b>')
        self.assertEqual(soup.b, soup.find('b'))
        self.assertEqual(soup.bTag, soup.find('b'))
        self.assertEqual(soup.b.i, soup.find('b').find('i'))
        self.assertEqual(soup.bTag.iTag, soup.find('b').find('i'))
        self.assertEqual(soup.a, None)
        self.assertEqual(soup.aTag, None)

    def test_has_attr(self):
        """has_attr() checks for the presence of an attribute.

        Please note note: has_attr() is different from
        __in__. has_attr() checks the tag's attributes and __in__
        checks the tag's chidlren.
        """
        soup = self.soup("<foo attr='bar'>")
        self.assertTrue(soup.foo.has_attr('attr'))
        self.assertFalse(soup.foo.has_attr('attr2'))


    def test_attributes_come_out_in_alphabetical_order(self):
        markup = '<b a="1" z="5" m="3" f="2" y="4"></b>'
        self.assertSoupEquals(markup, '<b a="1" f="2" m="3" y="4" z="5"></b>')

    def test_multiple_values_for_the_same_attribute_are_collapsed(self):
        markup = '<b b="20" a="1" b="10" a="2" a="3" a="4"></b>'
        self.assertSoupEquals(markup, '<b a="1" b="20"></b>')

    def test_string(self):
        # A tag that contains only a text node makes that node
        # available as .string.
        soup = self.soup("<b>foo</b>")
        self.assertEquals(soup.b.string, 'foo')

    def test_empty_tag_has_no_string(self):
        # A tag with no children has no .stirng.
        soup = self.soup("<b></b>")
        self.assertEqual(soup.b.string, None)

    def test_tag_with_multiple_children_has_no_string(self):
        # A tag with no children has no .string.
        soup = self.soup("<a>foo<b></b><b></b></b>")
        self.assertEqual(soup.b.string, None)

        soup = self.soup("<a>foo<b></b>bar</b>")
        self.assertEqual(soup.b.string, None)

        # Even if all the children are strings, due to trickery,
        # it won't work--but this would be a good optimization.
        soup = self.soup("<a>foo</b>")
        soup.a.insert(1, "bar")
        self.assertEqual(soup.a.string, None)

    def test_tag_with_recursive_string_has_string(self):
        # A tag with a single child which has a .string inherits that
        # .string.
        soup = self.soup("<a><b>foo</b></a>")
        self.assertEqual(soup.a.string, "foo")
        self.assertEqual(soup.string, "foo")

    def test_lack_of_string(self):
        """Only a tag containing a single text node has a .string."""
        soup = self.soup("<b>f<i>e</i>o</b>")
        self.assertFalse(soup.b.string)

        soup = self.soup("<b></b>")
        self.assertFalse(soup.b.string)

    def test_all_text(self):
        """Tag.text and Tag.get_text(sep=u"") -> all child text, concatenated"""
        soup = self.soup("<a>a<b>r</b>   <r> t </r></a>")
        self.assertEqual(soup.a.text, "ar  t ")
        self.assertEqual(soup.a.get_text(strip=True), "art")
        self.assertEqual(soup.a.get_text(","), "a,r, , t ")
        self.assertEqual(soup.a.get_text(",", strip=True), "a,r,t")


class TestPersistence(SoupTest):
    "Testing features like pickle and deepcopy."

    def setUp(self):
        super(TestPersistence, self).setUp()
        self.page = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN"
"http://www.w3.org/TR/REC-html40/transitional.dtd">
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>Beautiful Soup: We called him Tortoise because he taught us.</title>
<link rev="made" href="mailto:leonardr@segfault.org">
<meta name="Description" content="Beautiful Soup: an HTML parser optimized for screen-scraping.">
<meta name="generator" content="Markov Approximation 1.4 (module: leonardr)">
<meta name="author" content="Leonard Richardson">
</head>
<body>
<a href="foo">foo</a>
<a href="foo"><b>bar</b></a>
</body>
</html>"""
        self.tree = self.soup(self.page)

    def test_pickle_and_unpickle_identity(self):
        # Pickling a tree, then unpickling it, yields a tree identical
        # to the original.
        dumped = pickle.dumps(self.tree, 2)
        loaded = pickle.loads(dumped)
        self.assertEqual(loaded.__class__, BeautifulSoup)
        self.assertEqual(loaded.decode(), self.tree.decode())

    def test_deepcopy_identity(self):
        # Making a deepcopy of a tree yields an identical tree.
        copied = copy.deepcopy(self.tree)
        self.assertEqual(copied.decode(), self.tree.decode())

    def test_unicode_pickle(self):
        # A tree containing Unicode characters can be pickled.
        html = u"<b>\N{SNOWMAN}</b>"
        soup = self.soup(html)
        dumped = pickle.dumps(soup, pickle.HIGHEST_PROTOCOL)
        loaded = pickle.loads(dumped)
        self.assertEqual(loaded.decode(), soup.decode())


class TestSubstitutions(SoupTest):

    def test_html_entity_substitution(self):
        soup = self.soup(
            u"<b>Sacr\N{LATIN SMALL LETTER E WITH ACUTE} bleu!</b>")
        decoded = soup.decode(substitute_html_entities=True)
        self.assertEquals(decoded,
                          self.document_for("<b>Sacr&eacute; bleu!</b>"))

    def test_html_entity_substitution_off_by_default(self):
        markup = u"<b>Sacr\N{LATIN SMALL LETTER E WITH ACUTE} bleu!</b>"
        soup = self.soup(markup)
        encoded = soup.b.encode("utf-8")
        self.assertEquals(encoded, markup.encode('utf-8'))

    def test_encoding_substitution(self):
        # Here's the <meta> tag saying that a document is
        # encoded in Shift-JIS.
        meta_tag = ('<meta content="text/html; charset=x-sjis" '
                    'http-equiv="Content-type" />')
        soup = self.soup(meta_tag)

        # Parse the document, and the charset is replaced with a
        # generic value.
        self.assertEquals(soup.meta['content'],
                          'text/html; charset=%SOUP-ENCODING%')

        # Encode the document into some encoding, and the encoding is
        # substituted into the meta tag.
        utf_8 = soup.encode("utf-8")
        self.assertTrue(b"charset=utf-8" in utf_8)

        euc_jp = soup.encode("euc_jp")
        self.assertTrue(b"charset=euc_jp" in euc_jp)

        shift_jis = soup.encode("shift-jis")
        self.assertTrue(b"charset=shift-jis" in shift_jis)

        utf_16_u = soup.encode("utf-16").decode("utf-16")
        self.assertTrue("charset=utf-16" in utf_16_u)

    def test_encoding_substitution_doesnt_happen_if_tag_is_strained(self):
        markup = ('<head><meta content="text/html; charset=x-sjis" '
                    'http-equiv="Content-type" /></head><pre>foo</pre>')

        # Beautiful Soup used to try to rewrite the meta tag even if the
        # meta tag got filtered out by the strainer. This test makes
        # sure that doesn't happen.
        strainer = SoupStrainer('pre')
        soup = self.soup(markup, parse_only=strainer)
        self.assertEquals(soup.contents[0].name, 'pre')


class TestEncoding(SoupTest):
    """Test the ability to encode objects into strings."""

    def test_unicode_string_can_be_encoded(self):
        html = u"<b>\N{SNOWMAN}</b>"
        soup = self.soup(html)
        self.assertEquals(soup.b.string.encode("utf-8"),
                          u"\N{SNOWMAN}".encode("utf-8"))

    def test_tag_containing_unicode_string_can_be_encoded(self):
        html = u"<b>\N{SNOWMAN}</b>"
        soup = self.soup(html)
        self.assertEquals(
            soup.b.encode("utf-8"), html.encode("utf-8"))


class TestNavigableStringSubclasses(SoupTest):

    def test_cdata(self):
        # None of the current builders turn CDATA sections into CData
        # objects, but you can create them manually.
        soup = self.soup("")
        cdata = CData("foo")
        soup.insert(1, cdata)
        self.assertEquals(str(soup), "<![CDATA[foo]]>")
        self.assertEquals(soup.find(text="foo"), "foo")
        self.assertEquals(soup.contents[0], "foo")
