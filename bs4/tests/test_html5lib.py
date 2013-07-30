from bs4.builder import HTML5TreeBuilder
from bs4.element import Comment, SoupStrainer
from test_lxml import (
    TestLXMLBuilder,
    TestLXMLBuilderInvalidMarkup,
    TestLXMLBuilderEncodingConversion,
    )

class TestHTML5Builder(TestLXMLBuilder):
    """See `BuilderSmokeTest`."""

    @property
    def default_builder(self):
        return HTML5TreeBuilder()

    def test_soupstrainer(self):
        # The html5lib tree builder does not support SoupStrainers.
        strainer = SoupStrainer("b")
        markup = "<p>A <b>bold</b> statement.</p>"
        soup = self.soup(markup,
                         parse_only=strainer)
        self.assertEquals(
            soup.decode(), self.document_for(markup))

    def test_bare_string(self):
        # A bare string is turned into some kind of HTML document or
        # fragment recognizable as the original string.
        #
        # In this case, lxml puts a <p> tag around the bare string.
        self.assertSoupEquals(
            "A bare string", "A bare string")

    def test_correctly_nested_tables(self):
        markup = ('<table id="1">'
                  '<tr>'
                  "<td>Here's another table:"
                  '<table id="2">'
                  '<tr><td>foo</td></tr>'
                  '</table></td>')

        self.assertSoupEquals(
            markup,
            '<table id="1"><tbody><tr><td>Here\'s another table:'
            '<table id="2"><tbody><tr><td>foo</td></tr></tbody></table>'
            '</td></tr></tbody></table>')

        self.assertSoupEquals(
            "<table><thead><tr><td>Foo</td></tr></thead>"
            "<tbody><tr><td>Bar</td></tr></tbody>"
            "<tfoot><tr><td>Baz</td></tr></tfoot></table>")

    def test_literal_in_textarea(self):
        markup = '<textarea>Junk like <b> tags and <&<&amp;</textarea>'
        soup = self.soup(markup)
        self.assertEquals(
            soup.textarea.contents, ["Junk like <b> tags and <&<&"])

    def test_collapsed_whitespace(self):
        """Whitespace is preserved even in tags that don't require it."""
        self.assertSoupEquals("<p>   </p>")
        self.assertSoupEquals("<b>   </b>")

    def test_cdata_where_its_ok(self):
        # In html5lib 0.9.0, all CDATA sections are converted into
        # comments.  In a later version (unreleased as of this
        # writing), CDATA sections in tags like <svg> and <math> will
        # be preserved. BUT, I'm not sure how Beautiful Soup needs to
        # adjust to transform this preservation into the construction
        # of a BS CData object.
        markup = "<svg><![CDATA[foobar]]>"

        # Eventually we should be able to do a find(text="foobar") and
        # get a CData object.
        self.assertSoupEquals(markup, "<svg><!--[CDATA[foobar]]--></svg>")


class TestHTML5BuilderInvalidMarkup(TestLXMLBuilderInvalidMarkup):
    """See `BuilderInvalidMarkupSmokeTest`."""

    @property
    def default_builder(self):
        return HTML5TreeBuilder()

    def test_unclosed_block_level_elements(self):
        # The unclosed <b> tag is closed so that the block-level tag
        # can be closed, and another <b> tag is inserted after the
        # next block-level tag begins.
        self.assertSoupEquals(
            '<blockquote><p><b>Foo</blockquote><p>Bar',
            '<blockquote><p><b>Foo</b></p></blockquote><p><b>Bar</b></p>')

    def test_table_containing_bare_markup(self):
        # Markup should be in table cells, not directly in the table.
        self.assertSoupEquals("<table><div>Foo</div></table>",
                              "<div>Foo</div><table></table>")

    def test_incorrectly_nested_tables(self):
        self.assertSoupEquals(
            '<table><tr><table><tr id="nested">',
            ('<table><tbody><tr></tr></tbody></table>'
             '<table><tbody><tr id="nested"></tr></tbody></table>'))

    def test_empty_element_tag_with_contents(self):
        self.assertSoupEquals("<br>foo</br>", "<br />foo<br />")

    def test_doctype_in_body(self):
        markup = "<p>one<!DOCTYPE foobar>two</p>"
        self.assertSoupEquals(markup, "<p>onetwo</p>")

    def test_cdata_where_it_doesnt_belong(self):
        # Random CDATA sections are converted into comments.
        markup = "<div><![CDATA[foo]]>"
        soup = self.soup(markup)
        data = soup.find(text="[CDATA[foo]]")
        self.assertEquals(data.__class__, Comment)

    def test_nonsensical_declaration(self):
        # Declarations that don't make any sense are turned into comments.
        soup = self.soup('<! Foo = -8><p>a</p>')
        self.assertEquals(str(soup),
                          ("<!-- Foo = -8-->"
                           "<html><head></head><body><p>a</p></body></html>"))

        soup = self.soup('<p>a</p><! Foo = -8>')
        self.assertEquals(str(soup),
                          ("<html><head></head><body><p>a</p>"
                           "<!-- Foo = -8--></body></html>"))

    def test_whitespace_in_doctype(self):
        # A declaration that has extra whitespace is turned into a comment.
        soup = self.soup((
                '<! DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN">'
                '<p>foo</p>'))
        self.assertEquals(
            str(soup),
            ('<!-- DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"-->'
             '<html><head></head><body><p>foo</p></body></html>'))

    def test_incomplete_declaration(self):
        # An incomplete declaration is treated as a comment.
        markup = 'a<!b <p>c'
        self.assertSoupEquals(markup, "a<!--b <p-->c")

        # Let's spell that out a little more explicitly.
        soup = self.soup(markup)
        str1, comment, str2 = soup.body.contents
        self.assertEquals(str1, 'a')
        self.assertEquals(comment.__class__, Comment)
        self.assertEquals(comment, 'b <p')
        self.assertEquals(str2, 'c')

    def test_document_starts_with_bogus_declaration(self):
        soup = self.soup('<! Foo >a')
        # 'Foo' becomes a comment that appears before the HTML.
        comment = soup.contents[0]
        self.assertTrue(isinstance(comment, Comment))
        self.assertEquals(comment, 'Foo')

        self.assertEquals(self.find(text="a") == "a")

    def test_attribute_value_was_closed_by_subsequent_tag(self):
        markup = """<a href="foo</a>, </a><a href="bar">baz</a>"""
        soup = self.soup(markup)
        # The string between the first and second quotes was interpreted
        # as the value of the 'href' attribute.
        self.assertEquals(soup.a['href'], 'foo</a>, </a><a href=')

        #The string after the second quote (bar"), was treated as an
        #empty attribute called bar".
        self.assertEquals(soup.a['bar"'], '')
        self.assertEquals(soup.a.string, "baz")

    def test_document_starts_with_bogus_declaration(self):
        soup = self.soup('<! Foo ><p>a</p>')
        # The declaration becomes a comment.
        comment = soup.contents[0]
        self.assertTrue(isinstance(comment, Comment))
        self.assertEquals(comment, ' Foo ')
        self.assertEquals(soup.p.string, 'a')

    def test_document_ends_with_incomplete_declaration(self):
        soup = self.soup('<p>a<!b')
        # This becomes a string 'a'. The incomplete declaration is ignored.
        # Compare html5lib, which turns it into a comment.
        s, comment = soup.p.contents
        self.assertEquals(s, 'a')
        self.assertTrue(isinstance(comment, Comment))
        self.assertEquals(comment, 'b')

    def test_entity_was_not_finished(self):
        soup = self.soup("<p>&lt;Hello&gt")
        # Compare html5lib, which completes the entity.
        self.assertEquals(soup.p.string, "<Hello>")

    def test_nonexistent_entity(self):
        soup = self.soup("<p>foo&#bar;baz</p>")
        self.assertEquals(soup.p.string, "foo&#bar;baz")

        # Compare a real entity.
        soup = self.soup("<p>foo&#100;baz</p>")
        self.assertEquals(soup.p.string, "foodbaz")

    def test_entity_out_of_range(self):
        # An entity that's out of range will be converted to
        # REPLACEMENT CHARACTER.
        soup = self.soup("<p>&#10000000000000;</p>")
        self.assertEquals(soup.p.string, u"\N{REPLACEMENT CHARACTER}")

        soup = self.soup("<p>&#x1000000000000;</p>")
        self.assertEquals(soup.p.string, u"\N{REPLACEMENT CHARACTER}")


class TestHTML5LibEncodingConversion(TestLXMLBuilderEncodingConversion):
    @property
    def default_builder(self):
        return HTML5TreeBuilder()

    def test_real_hebrew_document(self):
        # A real-world test to make sure we can convert ISO-8859-8 (a
        # Hebrew encoding) to UTF-8.
        soup = self.soup(self.HEBREW_DOCUMENT,
                         from_encoding="iso-8859-8")
        self.assertEquals(soup.original_encoding, 'iso8859-8')
        self.assertEquals(
            soup.encode('utf-8'),
            self.HEBREW_DOCUMENT.decode("iso-8859-8").encode("utf-8"))
