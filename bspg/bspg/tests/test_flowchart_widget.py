import sys
import pytest

from bspg.core.config import AppConfig


@pytest.fixture(scope="module")
def qapp():
    """Single QApplication for the whole module — required for QWidget tests."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    yield app


@pytest.fixture()
def widget(qapp):
    from bspg.gui.flowchart.flowchart_widget import FlowchartWidget
    cfg = AppConfig()
    w = FlowchartWidget(app_config=cfg)
    return w


# ── Structure ────────────────────────────────────────────────────────────────

def test_four_lanes(widget):
    assert len(widget.lanes) == 4

def test_eight_checkboxes(widget):
    assert len(widget.checkboxes) == 8

def test_named_checkbox_attributes(widget):
    """Each cb must be accessible as widget.flowchart_cb_N."""
    for i in range(1, 9):
        assert hasattr(widget, f'flowchart_cb_{i}'), f'Missing flowchart_cb_{i}'

def test_gear_signal_exists(widget):
    assert hasattr(widget, 'gear_clicked')


# ── Gating rules ─────────────────────────────────────────────────────────────

def test_gate_cb2_blocks_cb4(widget):
    """If cb2 is checked, checking cb4 must auto-uncheck cb4."""
    cb2 = widget.flowchart_cb_2
    cb4 = widget.flowchart_cb_4
    cb2.setChecked(True)
    cb4.setChecked(True)   # triggers gating
    assert not cb4.isChecked(), "cb4 should be unchecked when cb2 is active"

def test_gate_cb2_blocks_cb7(widget):
    """If cb2 is checked, checking cb7 must auto-uncheck cb7."""
    cb2 = widget.flowchart_cb_2
    cb7 = widget.flowchart_cb_7
    cb2.setChecked(True)
    cb7.setChecked(True)
    assert not cb7.isChecked(), "cb7 should be unchecked when cb2 is active"

def test_gate_cb4_blocks_cb7(widget):
    """If cb4 is checked, checking cb7 must auto-uncheck cb7."""
    cb2 = widget.flowchart_cb_2
    cb4 = widget.flowchart_cb_4
    cb7 = widget.flowchart_cb_7
    # Ensure cb2 is off so cb4 can be checked first
    cb2.setChecked(False)
    cb4.setChecked(True)
    cb7.setChecked(True)
    assert not cb7.isChecked(), "cb7 should be unchecked when cb4 is active"

def test_non_conflicting_pair_allowed(widget):
    """cb1 and cb3 can both be checked without conflict."""
    widget.flowchart_cb_1.setChecked(True)
    widget.flowchart_cb_3.setChecked(True)
    assert widget.flowchart_cb_1.isChecked()
    assert widget.flowchart_cb_3.isChecked()


# ── Config sync ───────────────────────────────────────────────────────────────

def test_sync_to_config(widget):
    """Toggling a checkbox must update AppConfig.flowchart."""
    widget.flowchart_cb_1.setChecked(False)
    widget.flowchart_cb_1.setChecked(True)
    assert widget.app_config.flowchart.cb1 is True

def test_update_from_config(widget):
    """update_from_config() must load AppConfig values into checkboxes."""
    widget.app_config.flowchart.cb3 = False
    widget.app_config.flowchart.cb5 = True
    widget.update_from_config()
    assert not widget.flowchart_cb_3.isChecked()
    assert widget.flowchart_cb_5.isChecked()

