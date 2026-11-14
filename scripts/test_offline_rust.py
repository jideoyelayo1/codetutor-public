import unittest
from pathlib import Path
from prepare_offline_rust import Content, TOC


class OfflineRustTests(unittest.TestCase):
    def test_active_content_is_removed_without_losing_following_prose(self):
        p=Content(Path('/docs/book/page.html'),Path('/docs'),{})
        p.feed('<h2 id="topic">A &amp; B</h2><script>alert(1)</script><form><input/><button>run</button></form><p>After &lt;T&gt;</p>')
        html=''.join(p.parts)
        self.assertNotIn('alert',html);self.assertNotIn('<form',html)
        self.assertIn('After &lt;T&gt;',html)
        self.assertEqual(p.headings,[{'anchor':'topic','title':'A & B'}])
    def test_local_links_are_rewritten_and_active_schemes_are_rejected(self):
        p=Content(Path('/docs/book/page.html'),Path('/docs'),{Path('/docs/book/next.html'):'ref-next.html'})
        p.feed('<a href="next.html#topic">Next</a><a href="javascript:alert(1)">Bad</a><a href="../../private">Escape</a>')
        html=''.join(p.parts)
        self.assertIn('href="ref-next.html#topic"',html)
        self.assertNotIn('javascript:',html);self.assertNotIn('../../private',html)
    def test_toc_keeps_internal_pages_and_ignores_external_urls(self):
        p=TOC();p.feed('<a href="one.html"><strong>1.</strong> One</a><a href="https://example.com/two.html">External</a>')
        self.assertEqual(p.items,[('one.html','1. One')])
    def test_official_absolute_links_and_manual_aliases_stay_offline(self):
        names={Path('/docs/cargo/reference/profiles.html'):'ref-profiles.html',
               Path('/docs/nomicon/index.html'):'ref-nomicon.html',
               Path('/docs/nomicon'):'ref-nomicon.html'}
        p=Content(Path('/docs/book/page.html'),Path('/docs'),names)
        for prefix in ['', '1.99.0/', 'stable/', 'latest/']:
            self.assertEqual(p.link('https://doc.rust-lang.org/'+prefix+'cargo/reference/profiles.html#dev'), 'ref-profiles.html#dev')
        self.assertEqual(p.link('//doc.rust-lang.org/nomicon/'),'ref-nomicon.html')
        self.assertEqual(p.link('../nomicon/index.html'),'ref-nomicon.html')
        self.assertEqual(p.link('../nomicon/'),'ref-nomicon.html')
        older='https://doc.rust-lang.org/1.80.0/cargo/reference/profiles.html'
        self.assertEqual(p.link(older),older)
        foreign='https://example.com/cargo/reference/profiles.html'
        self.assertEqual(p.link(foreign),foreign)
    def test_svg_keeps_geometry_but_removes_events_and_external_styles(self):
        p=Content(Path('/docs/reference/page.html'),Path('/docs'),{})
        p.feed('<svg viewBox="0 0 40 40" width="40" onload="run()"><path d="M0 0L40 40" stroke="black" style="fill:none"/><rect x="2" y="3" width="4" height="5" style="fill:url(https://example.com)"/></svg>')
        html=''.join(p.parts)
        self.assertIn('viewBox="0 0 40 40"',html);self.assertIn('d="M0 0L40 40"',html)
        self.assertIn('stroke="black"',html);self.assertIn('x="2"',html)
        self.assertNotIn('onload',html);self.assertNotIn('https://example.com',html)
    def test_railroad_keeps_readable_size_and_cross_page_links(self):
        p=Content(Path('/docs/reference/page.html'),Path('/docs'),{Path('/docs/reference/next.html'):'ref-next.html'})
        p.feed('<svg class="railroad" viewbox="0 0 786 255"><a xlink:href="next.html#rule"><text>Next</text></a></svg>')
        html=''.join(p.parts)
        self.assertIn('width="786"',html);self.assertIn('height="255"',html)
        self.assertIn('xlink:href="ref-next.html#rule"',html)
    def test_remote_version_badge_has_offline_text_and_missing_images_fail(self):
        p=Content(Path('/docs/reference/page.html'),Path('/docs'),{})
        p.feed('<img src="https://example.com/badge.svg" alt="Minimum Rust Version: 1.31">')
        self.assertIn('Minimum Rust Version: 1.31',''.join(p.parts))
        self.assertNotIn('<img',''.join(p.parts))
        with self.assertRaises(ValueError): p.feed('<img src="missing.png" alt="Diagram">')


if __name__=='__main__': unittest.main()
