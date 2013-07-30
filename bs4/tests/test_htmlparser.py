from HTMLParser import HTMLParseError
from bs4.builder import HTMLParserTreeBuilder
from bs4.element import CData
from test_lxml import (
    TestLXMLBuilder,
    TestLXMLBuilderEncodingConversion,
    TestLXMLBuilderInvalidMarkup,
    )

class TestHTMLParserTreeBuilder(TestLXMLBuilder):
    """See `BuilderSmokeTest`."""

    @property
    def default_builder(self):
        return HTMLParserTreeBuilder()

    def test_bare_string(self):
        # A bare string is turned into some kind of HTML document or
        # fragment recognizable as the original string.
        #
        # HTMLParser does not modify the bare string at all.
        self.assertSoupEquals("A bare string")

    def test_cdata_where_its_ok(self):
        # HTMLParser recognizes CDATA sections and passes them through.
        markup = "<svg><![CDATA[foobar]]></svg>"
        self.assertSoupEquals(markup)
        soup = self.soup(markup)
        string = soup.svg.string
        self.assertEquals(string, "foobar")
        self.assertTrue(isinstance(string, CData))

    # These are tests that could be 'fixed' by improving the
    # HTMLParserTreeBuilder, but I don't think it's worth it. Users
    # will have fewer headaches if they use one of the other tree
    # builders.

    def test_empty_element(self):
        # HTML's empty-element tags are not recognized as such
        # unless they are presented as empty-element tags.
        self.assertSoupEquals(
            "<p>A <meta> tag</p>", "<p>A <meta> tag</meta></p>")

        self.assertSoupEquals(
            "<p>Foo<br/>bar</p>", "<p>Foo<br />bar</p>")

    def test_entities_in_attribute_values_converted_during_parsing(self):

        # The numeric entity isn't recognized without the closing
        # semicolon.
        text = '<x t="pi&#241ata">'
        expected = u"pi\N{LATIN SMALL LETTER N WITH TILDE}ata"
        soup = self.soup(text)
        self.assertEquals(soup.x['t'], "pi&#241ata")

        text = '<x t="pi&#241;ata">'
        expected = u"pi\N{LATIN SMALL LETTER N WITH TILDE}ata"
        soup = self.soup(text)
        self.assertEquals(soup.x['t'], u"pi\xf1ata")

        text = '<x t="pi&#xf1;ata">'
        soup = self.soup(text)
        self.assertEquals(soup.x['t'], expected)

        text = '<x t="sacr&eacute; bleu">'
        soup = self.soup(text)
        self.assertEquals(
            soup.x['t'],
            u"sacr\N{LATIN SMALL LETTER E WITH ACUTE} bleu")

        # This can cause valid HTML to become invalid.
        valid_url = '<a href="http://example.org?a=1&amp;b=2;3">foo</a>'
        soup = self.soup(valid_url)
        self.assertEquals(soup.a['href'], "http://example.org?a=1&b=2;3")

    # I think it would be very difficult to 'fix' these tests, judging
    # from my experience with previous versions of Beautiful Soup.
    def test_naked_ampersands(self):
        # Ampersands are treated as entities.
        text = "<p>AT&T</p>"
        soup = self.soup(text)
        self.assertEquals(soup.p.string, "AT&T;")

    def test_literal_in_textarea(self):
        # Anything inside a <textarea> is supposed to be treated as
        # the literal value of the field, (XXX citation
        # needed). html5lib does this correctly. But, HTMLParser does its
        # best to parse the contents of a <textarea> as HTML.
        text = '<textarea>Junk like <b> tags and <&<&amp;</textarea>'
        soup = self.soup(text)
        self.assertEquals(len(soup.textarea.contents), 2)
        self.assertEquals(soup.textarea.contents[0], u"Junk like ")
        self.assertEquals(soup.textarea.contents[1].name, 'b')
        self.assertEquals(soup.textarea.b.string, u" tags and <&<&")

    def test_literal_in_script(self):
        # The contents of a <script> tag are supposed to be treated as
        # a literal string, even if that string contains HTML. But
        # HTMLParser attempts to parse some of the HTML, causing much
        # pain.
        javascript = 'if (i < 2) { alert("<b>foo</b>"); }'
        soup = self.soup('<script>%s</script>' % javascript)
        self.assertEquals(soup.script.contents,
                          ['if (i < 2) { alert("<b>foo',
                           '"); }'])

    # Namespaced doctypes cause an HTMLParseError
    def test_namespaced_system_doctype(self):
        self.assertRaises(HTMLParseError, self._test_doctype,
                          'xsl:stylesheet SYSTEM "htmlent.dtd"')

    def test_namespaced_public_doctype(self):
        self.assertRaises(HTMLParseError, self._test_doctype,
                          'xsl:stylesheet PUBLIC "htmlent.dtd"')


class TestHTMLParserTreeBuilderInvalidMarkup(TestLXMLBuilderInvalidMarkup):
    # Oddly enough, HTMLParser seems to handle invalid markup exactly
    # the same as lxml.
    pass


class TestHTMLParserTreeBuilderEncodingConversion(
    TestLXMLBuilderEncodingConversion):
    # Re-run the lxml tests for HTMLParser
    pass
