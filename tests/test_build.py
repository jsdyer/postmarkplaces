import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from xml.etree import ElementTree
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build import ROOT, build, metadata


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copytree(ROOT / "web", self.root / "web")
        shutil.copyfile(ROOT / "tool.json", self.root / "tool.json")
        shutil.copyfile(ROOT / "README.md", self.root / "README.md")

    def edit(self, **changes):
        tool = json.loads((self.root / "tool.json").read_text())
        tool.update(changes)
        (self.root / "tool.json").write_text(json.dumps(tool))

    def test_build_is_scoped_to_web_and_escapes_metadata(self):
        (self.root / "private.txt").write_text("must not publish")
        self.edit(title='<img src=x onerror="bad()">')
        build(self.root)
        page = (self.root / "dist/index.html").read_text()
        self.assertIn('&lt;img', page)
        self.assertNotIn('<img', page)
        self.assertNotIn('{{', page)
        self.assertIn('href="./style.css"', page)
        self.assertFalse((self.root / "dist/private.txt").exists())
        self.assertTrue((self.root / "dist/.nojekyll").exists())

    def test_sitemap_covers_offices_and_preserves_the_two_name_histories(self):
        build(self.root)
        site = self.root / "dist"
        office_ids = {o["id"] for o in json.loads((site / "data/edition.json").read_text())["offices"]}
        ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
        pages = [e.text for e in ElementTree.parse(site / "sitemap.xml").iter(ns + "loc")]
        base = "https://coolcode.ca/postmarkplaces/"
        self.assertEqual(office_ids, {u.split("/")[-2] for u in pages if "/offices/" in u})
        self.assertEqual(len(set(pages)), len(pages))
        for url in pages:
            page = (site / url.removeprefix(base) / "index.html").read_text()
            self.assertIn(f'<link rel="canonical" href="{url}">', page)
        timeline = (site / "records/names/langley-prairie/index.html").read_text()
        self.assertIn("records/offices/station-innes/", timeline)
        self.assertIn("records/offices/station-prairie/", timeline)
        self.assertIn("date=1911-05-15", timeline)
        self.assertIn("date=1911-05-16", timeline)

    def test_url_matches_tool_id(self):
        self.edit(url="/different/")
        with self.assertRaises(ValueError): metadata(self.root)

    def test_requires_a_source_sentence_and_a_guide_note(self):
        (self.root / "README.md").write_text("# A tool")
        with self.assertRaisesRegex(ValueError, "README note"):
            metadata(self.root)
        self.edit(data_info={"mode": "local", "detail": ""})
        with self.assertRaisesRegex(ValueError, "homepage card"):
            metadata(self.root)

    def test_browser_access_is_explicit(self):
        self.edit(access="install")
        with self.assertRaisesRegex(ValueError, "immediately usable"):
            metadata(self.root)

    def test_failed_build_keeps_existing_output(self):
        build(self.root)
        existing = (self.root / "dist/index.html").read_bytes()
        self.edit(source="javascript:bad()")
        with self.assertRaises(ValueError): build(self.root)
        self.assertEqual((self.root / "dist/index.html").read_bytes(), existing)


if __name__ == "__main__": unittest.main()
