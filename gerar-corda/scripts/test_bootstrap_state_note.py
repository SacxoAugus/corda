"""A-04: o BOOTSTRAP declara que o STATE embutido é snapshot e o disco manda."""

from __future__ import annotations

import unittest

import build_universe


class TestBootstrapStateDriftNote(unittest.TestCase):
    def test_bootstrap_marks_embedded_state_as_snapshot(self):
        text = build_universe.render_bootstrap(
            "# SYSTEM\nx", "# UNIVERSE\ny", {"status": "initialized"}
        )
        self.assertIn("STATE DRIFT WARNING", text)
        self.assertIn("SNAPSHOT of the STATE at build time", text)
        self.assertIn("the disk wins", text)
        self.assertIn('"status": "initialized"', text)
        # o aviso precede o bloco JSON embutido
        self.assertLess(text.index("STATE DRIFT WARNING"), text.index('"status"'))


if __name__ == "__main__":
    unittest.main()
