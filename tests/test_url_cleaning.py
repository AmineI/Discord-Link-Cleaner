import json
import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import MagicMock, patch


MAIN_PATH = Path(__file__).resolve().parents[1] / "main.py"


class URLCleaningTests(unittest.TestCase):
    def load_main(self, config=None, env=None):
        data_dir = self.enterContext(tempfile.TemporaryDirectory())
        if config is not None:
            Path(data_dir, "config.json").write_text(json.dumps(config), encoding="utf-8")
        self.enterContext(patch.dict(os.environ, {"DATA_DIR": data_dir, **(env or {})}, clear=True))
        discord = MagicMock()
        commands = MagicMock()
        commands.Bot.return_value.event.side_effect = lambda handler: handler
        sanitizer = MagicMock()
        sanitizer.sanitize.side_effect = lambda url: {"url": url}
        self.enterContext(patch.dict("sys.modules", {
            "discord": discord,
            "discord.ext": MagicMock(commands=commands),
            "url_sanitize": sanitizer,
        }))
        return runpy.run_path(str(MAIN_PATH)), sanitizer.sanitize

    def test_default_override_and_subdomains(self):
        main, _ = self.load_main()
        for host in ("instagram.com", "www.instagram.com", "sub.www.instagram.com",
                     "INSTAGRAM.COM", "instagram.com."):
            with self.subTest(host=host):
                url = f"https://{host}/p/ABC/?img_index=2&igsh=xyz&empty=#comments"
                self.assertEqual(main["clean_url"](url)["url"],
                                 f"https://{host}/p/ABC/#comments")

    def test_other_domains_keep_functional_parameters(self):
        main, _ = self.load_main()
        for host in ("example.com", "notinstagram.com", "instagram.com.example.com"):
            with self.subTest(host=host):
                url = f"https://{host}/?page=2&IGSI=tracker&empty=#section"
                self.assertEqual(main["clean_url"](url)["url"],
                                 f"https://{host}/?page=2&empty=#section")

    def test_override_without_extra_tracking_params(self):
        main, _ = self.load_main({"extra_tracking_params": []})
        self.assertEqual(main["clean_url"]("https://instagram.com/?page=2")["url"],
                         "https://instagram.com/")
        url = "https://example.com/?page=2&encoded=a%20b"
        self.assertEqual(main["clean_url"](url)["url"], url)

    def test_json_override_and_disable(self):
        for domains in ([], ["example.com"]):
            with self.subTest(domains=domains):
                main, _ = self.load_main({"strip_all_params_domains": domains})
                url = "https://instagram.com/?page=2"
                self.assertEqual(main["clean_url"](url)["url"], url)
                url = "https://www.example.com/?page=2#section"
                expected = "https://www.example.com/#section" if domains else url
                self.assertEqual(main["clean_url"](url)["url"], expected)

    def test_environment_overrides_json(self):
        main, _ = self.load_main(
            {"strip_all_params_domains": ["instagram.com"]},
            {"STRIP_ALL_PARAMS_DOMAINS": " EXAMPLE.COM., , example.org "},
        )
        self.assertEqual(main["STRIP_ALL_PARAMS_DOMAINS"], {"example.com", "example.org"})
        self.assertEqual(main["clean_url"]("https://sub.example.org/?page=2")["url"],
                         "https://sub.example.org/")
        url = "https://instagram.com/?page=2"
        self.assertEqual(main["clean_url"](url)["url"], url)

    def test_empty_environment_falls_back_to_config(self):
        main, _ = self.load_main(
            {"strip_all_params_domains": []},
            {"STRIP_ALL_PARAMS_DOMAINS": ""},
        )
        self.assertEqual(main["STRIP_ALL_PARAMS_DOMAINS"], set())

    def test_urls_without_query_are_unchanged(self):
        main, _ = self.load_main()
        for url in ("https://instagram.com/p/ABC/#comments",
                    "https://example.com/path#fragment"):
            with self.subTest(url=url):
                self.assertEqual(main["clean_url"](url)["url"], url)

    def test_override_applies_to_sanitizer_output(self):
        main, sanitize = self.load_main()
        sanitize.side_effect = None
        sanitize.return_value = {
            "url": "https://www.instagram.com/p/ABC/?page=2#comments",
            "metadata": "preserved",
        }
        result = main["clean_url"]("https://example.com/redirect")
        self.assertEqual(result, {
            "url": "https://www.instagram.com/p/ABC/#comments",
            "metadata": "preserved",
        })
        sanitize.assert_called_with("https://example.com/redirect")


if __name__ == "__main__":
    unittest.main()
