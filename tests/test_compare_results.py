from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from compare_results import compare_results  # noqa: E402


class ResultComparisonTests(unittest.TestCase):
    @staticmethod
    def _write(root: Path, relative: str, content: str) -> None:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_identical_deterministic_trees_match(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            expected, actual = root / "expected", root / "actual"
            for target in (expected, actual):
                self._write(target, "dimensions.csv", "n,b,rank\n2,1,1\n")
                self._write(target, "matrices/n2_b1.csv", "action,y1\n1|2,1\n")
            matched = compare_results(expected, actual)
            self.assertEqual(
                matched,
                [Path("dimensions.csv"), Path("matrices/n2_b1.csv")],
            )

    def test_content_mutation_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            expected, actual = root / "expected", root / "actual"
            self._write(expected, "dimensions.csv", "rank=1\n")
            self._write(actual, "dimensions.csv", "rank=2\n")
            with self.assertRaisesRegex(ValueError, "changed"):
                compare_results(expected, actual)

    def test_missing_and_extra_files_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            expected, actual = root / "expected", root / "actual"
            self._write(expected, "a.csv", "a\n")
            self._write(actual, "b.csv", "b\n")
            with self.assertRaisesRegex(ValueError, "missing.*extra"):
                compare_results(expected, actual)

    def test_host_resource_records_are_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            expected, actual = root / "expected", root / "actual"
            for target in (expected, actual):
                self._write(target, "dimensions.csv", "rank=1\n")
            self._write(expected, "resources.json", '{"cpu": 1}\n')
            self._write(actual, "resources.json", '{"cpu": 999}\n')
            self._write(expected, "reproduction.json", '{"host": "a"}\n')
            self._write(actual, "reproduction.json", '{"host": "b"}\n')
            self.assertEqual(compare_results(expected, actual), [Path("dimensions.csv")])


if __name__ == "__main__":
    unittest.main()
