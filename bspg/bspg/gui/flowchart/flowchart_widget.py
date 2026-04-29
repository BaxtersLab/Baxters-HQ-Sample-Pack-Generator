from PySide6.QtWidgets import QWidget, QLabel, QCheckBox, QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, Signal

from bspg.core.config import AppConfig
from bspg.core.logging import bspg_logger
from bspg.gui.flowchart.chop_settings_popup import ChopSettingsPopup


class FlowchartWidget(QWidget):

    # Emitted when the gear (settings) button is clicked
    gear_clicked = Signal()
    """
    4-Lane signal routing flowchart showing audio path through pipeline.
    
    Lane Structure:
        LANE 1: [Stem Sep] — (#1)
        LANE 2: [Stem Repair] — (#2, #3)
        LANE 3: [Sample Chop] — (#4, #5, #6)
        LANE 4: Routing Gates — (#7, #8)
    
    Flow structure:
        [Stem Sep]────[1]
             \\___[2]______[Stem Repair]────[3]
        [Input stem]__[4]____/   \\____[5]___[Sample Chop]___[6]
             \\________________[7]________________/   \\______________[8]
    """
    
    def __init__(self, app_config: AppConfig = None, logger=None, parent=None):
        super().__init__(parent)
        # prefer injected AppConfig; fallback for tests
        try:
            if app_config is not None:
                self.app_config = app_config
            else:
                self.app_config = AppConfig()
        except Exception:
            self.app_config = AppConfig()
        self.logger = logger or bspg_logger
        self.initialized = False
        
        self.init_ui()

    def init_ui(self):
        if getattr(self, 'initialized', False):
            return
        self.initialized = True

        # Main vertical layout for 4 horizontal lanes (rows)
        if not self.layout():
            main_layout = QVBoxLayout(self)
            main_layout.setContentsMargins(10, 15, 10, 15)
            main_layout.setSpacing(20)
            self.setLayout(main_layout)
        else:
            main_layout = self.layout()

        inner_layout = main_layout

        # Create lanes only if missing
        if not hasattr(self, 'lanes'):
            self.lanes = []
            self.checkboxes = []
            
            # LANE 1 (top row): [Stem Sep]────[1]
            lane1 = self._create_horizontal_lane("Stem Sep", [1], inner_layout)
            self.lanes.append(lane1)
            
            # LANE 2: [2]──[Stem Repair]────[3]
            lane2 = self._create_horizontal_lane("Stem Repair", [2, 3], inner_layout)
            self.lanes.append(lane2)
            
            # LANE 3: [Input stem]__[4]...[5]__[Sample Chop]───[6]
            lane3 = self._create_horizontal_lane("Sample Chop", [4, 5, 6], inner_layout, 
                                                   show_input_stem=True)
            self.lanes.append(lane3)
            
            # LANE 4 (bottom): \────[7]────/  \────[8]
            lane4 = self._create_horizontal_lane("Routing", [7, 8], inner_layout, 
                                                   show_node=False, is_routing_lane=True)
            self.lanes.append(lane4)

            # Connect gear button to chop settings popup
            self.gear_clicked.connect(self._open_chop_settings)
    
    def _make_checkbox(self, cb_id, parent_widget):
        """Create a checkbox, store as named attribute, connect to change handler."""
        cb = QCheckBox(f"[{cb_id}]", parent_widget)
        cb.setObjectName(f"flowchart_cb_{cb_id}")
        cb.setToolTip(self._get_checkpoint_tooltip(cb_id))
        setattr(self, f"flowchart_cb_{cb_id}", cb)
        cb.stateChanged.connect(lambda _state, n=cb_id: self._on_checkbox_changed(n))
        self.checkboxes.append(cb)
        return cb

    def _create_horizontal_lane(self, label, checkbox_ids, parent_layout,
                                show_node=True, show_input_stem=False, is_routing_lane=False):
        """Create a single horizontal lane (row) with button and checkboxes flowing left-to-right."""
        lane_widget = QWidget(self)
        lane_widget.setObjectName(f"flowchart_lane_{label.lower().replace(' ', '_')}")
        lane_layout = QHBoxLayout(lane_widget)
        lane_layout.setContentsMargins(5, 8, 5, 8)
        lane_layout.setSpacing(15)
        lane_layout.setAlignment(Qt.AlignLeft)
        lane_widget.setMinimumHeight(50)  # Ensure enough height for buttons
        
        # Handle routing lane (lane 4) specially
        if is_routing_lane:
            # Render entire lane 4 as a single label with checkboxes inline
            # Format: (indent)  \______[7]_________/  \____________[8]
            lane_label = QLabel("      \\______________________", lane_widget)
            lane_label.setStyleSheet("color: #AAA; font-weight: bold; font-family: monospace; font-size: 13px;")
            lane_layout.addWidget(lane_label)
            
            # Add checkbox [7]
            if len(checkbox_ids) > 0:
                cb = self._make_checkbox(checkbox_ids[0], lane_widget)
                lane_layout.addWidget(cb)

            mid_label = QLabel("________________________/  \\____________", lane_widget)
            mid_label.setStyleSheet("color: #AAA; font-weight: bold; font-family: monospace; font-size: 13px;")
            lane_layout.addWidget(mid_label)

            # Add checkbox [8]
            if len(checkbox_ids) > 1:
                cb = self._make_checkbox(checkbox_ids[1], lane_widget)
                lane_layout.addWidget(cb)
            
            # Add stretch
            lane_layout.addStretch()
            parent_layout.addWidget(lane_widget)
            return lane_widget
        
        # Add Input Stem button if lane 3
        if show_input_stem:
            input_btn = QLabel("Input Stem", lane_widget)
            input_btn.setObjectName("node_input_stem")
            input_btn.setStyleSheet("""
                QLabel {
                    background: #4FC3FF;
                    color: #000000;
                    border: 2px solid #000000;
                    border-radius: 6px;
                    padding: 8px 12px;
                    font-weight: bold;
                    font-size: 11px;
                    min-width: 90px;
                }
            """)
            input_btn.setFixedHeight(35)
            lane_layout.addWidget(input_btn)
            
            # Add flow line after Input Stem
            flow_line = QLabel("____", lane_widget)
            flow_line.setStyleSheet("color: #AAA; font-weight: bold; font-family: monospace;")
            lane_layout.addWidget(flow_line)
        
        # Add first checkbox(es) before main node (for lane 2's [2], lane 3's [4])
        if label == "Stem Repair" and len(checkbox_ids) > 0:
            # Add spacer to show flow line coming from lane 1
            spacer = QLabel("", lane_widget)
            spacer.setFixedWidth(40)  # Indent to align with flow from Stem Sep
            lane_layout.addWidget(spacer)
            
            # Add backslash with underscores flowing to checkbox [2]
            flow_indicator = QLabel("\\_______", lane_widget)
            flow_indicator.setStyleSheet("color: #AAA; font-weight: bold; font-family: monospace;")
            lane_layout.addWidget(flow_indicator)
            
            # Add checkbox [2] before Stem Repair button
            cb = self._make_checkbox(checkbox_ids[0], lane_widget)
            lane_layout.addWidget(cb)
            checkbox_ids = checkbox_ids[1:]  # Remove first checkbox from list
            
            # Add flow line after checkbox [2]
            flow_line = QLabel("____", lane_widget)
            flow_line.setStyleSheet("color: #AAA; font-weight: bold; font-family: monospace;")
            lane_layout.addWidget(flow_line)
            
        elif show_input_stem and len(checkbox_ids) > 0:
            # Add checkbox [4] after Input Stem button
            cb = self._make_checkbox(checkbox_ids[0], lane_widget)
            lane_layout.addWidget(cb)
            checkbox_ids = checkbox_ids[1:]  # Remove [4]
            
            # Add flow line with merge point (connected underscores)
            merge_flow = QLabel("____/  \\____", lane_widget)
            merge_flow.setStyleSheet("color: #AAA; font-weight: bold; font-family: monospace;")
            lane_layout.addWidget(merge_flow)
            
            # Add checkbox [5] before Sample Chop button
            if len(checkbox_ids) > 0:
                cb = self._make_checkbox(checkbox_ids[0], lane_widget)
                lane_layout.addWidget(cb)
                checkbox_ids = checkbox_ids[1:]  # Remove [5]
                
                # Add flow line after checkbox [5]
                flow_line3 = QLabel("___", lane_widget)
                flow_line3.setStyleSheet("color: #AAA; font-weight: bold; font-family: monospace;")
                lane_layout.addWidget(flow_line3)
        
        # Add main processing node button (if not routing lane)
        if show_node:
            node_btn = QLabel(label, lane_widget)
            node_btn.setObjectName(f"node_{label.lower().replace(' ', '_')}")
            node_btn.setStyleSheet("""
                QLabel {
                    background: #4FC3FF;
                    color: #000000;
                    border: 2px solid #000000;
                    border-radius: 6px;
                    padding: 8px 12px;
                    font-weight: bold;
                    font-size: 11px;
                    min-width: 90px;
                }
            """)
            node_btn.setFixedHeight(35)
            lane_layout.addWidget(node_btn)
            
            # Add flow line after Stem Sep (lane 1) or other buttons
            if label == "Stem Sep":
                # Match the length of flow line before [7] in lane 4 (13 underscores)
                flow_line = QLabel("_" * 13, lane_widget)
                flow_line.setStyleSheet("color: #AAA; font-weight: bold; font-family: monospace;")
                lane_layout.addWidget(flow_line)
            elif label == "Stem Repair":
                # Add flow line after Stem Repair button
                flow_line = QLabel("____", lane_widget)
                flow_line.setStyleSheet("color: #AAA; font-weight: bold; font-family: monospace;")
                lane_layout.addWidget(flow_line)
            elif label == "Sample Chop":
                # Add flow line after Sample Chop button
                flow_line = QLabel("___", lane_widget)
                flow_line.setStyleSheet("color: #AAA; font-weight: bold; font-family: monospace;")
                lane_layout.addWidget(flow_line)
                
                # Add checkbox [6] after Sample Chop
                if len(checkbox_ids) > 0:
                    cb = self._make_checkbox(checkbox_ids[0], lane_widget)
                    lane_layout.addWidget(cb)
                    checkbox_ids = checkbox_ids[1:]  # Remove [6]
                
                # Add lavender gear button
                gear_btn = QPushButton("⚙", lane_widget)
                gear_btn.setObjectName("gear_settings_btn")
                gear_btn.setStyleSheet("""
                    QPushButton {
                        background: #C8A2C8;
                        color: #000000;
                        border: 2px solid #000000;
                        border-radius: 6px;
                        padding: 4px 8px;
                        font-weight: bold;
                        font-size: 16px;
                        min-width: 30px;
                    }
                """)
                gear_btn.setFixedHeight(35)
                gear_btn.clicked.connect(self.gear_clicked)
                lane_layout.addWidget(gear_btn)

        # Add remaining checkboxes after the node (cb1 for lane1, cb3 for lane2)
        for cb_id in checkbox_ids:
            cb = self._make_checkbox(cb_id, lane_widget)
            lane_layout.addWidget(cb)
        
        # Add stretch to push remaining space to right
        lane_layout.addStretch()
        
        parent_layout.addWidget(lane_widget)
        return lane_widget
    
    def _get_checkpoint_tooltip(self, idx):
        """Return tooltip description for each checkpoint."""
        tooltips = {
            1: "Stem Separation output",
            2: "Stem Sep → Stem Repair chain", 
            3: "Stem Repair function",
            4: "BYO Input stem (bypasses Stem Sep)",
            5: "Repair → Sample Chop link",
            6: "Sample Chop output gate",
            7: "BYO → Sample Chop direct (bypass Repair)",
            8: "Full Run auto-selector"
        }
        return tooltips.get(idx, f"Checkpoint {idx}")

    # ─── Gating + Config sync ─────────────────────────────────────────────────

    def _on_checkbox_changed(self, cb_id):
        """Called when any flowchart checkbox is toggled. Applies gating then syncs config."""
        self._apply_gating_rules()
        self._sync_to_config()

    def _apply_gating_rules(self):
        """
        Mutual exclusion rules (from module f block 5):
          cb2 + cb4  →  uncheck cb4  (fresh-sep path vs BYO-to-Repair conflict)
          cb2 + cb7  →  uncheck cb7  (fresh-sep vs BYO-to-Chop conflict)
          cb4 + cb7  →  uncheck cb7  (BYO can't feed Repair AND Chop simultaneously)
        """
        cb2 = getattr(self, 'flowchart_cb_2', None)
        cb4 = getattr(self, 'flowchart_cb_4', None)
        cb7 = getattr(self, 'flowchart_cb_7', None)

        if cb2 and cb4 and cb2.isChecked() and cb4.isChecked():
            cb4.blockSignals(True)
            cb4.setChecked(False)
            cb4.blockSignals(False)

        if cb2 and cb7 and cb2.isChecked() and cb7.isChecked():
            cb7.blockSignals(True)
            cb7.setChecked(False)
            cb7.blockSignals(False)

        if cb4 and cb7 and cb4.isChecked() and cb7.isChecked():
            cb7.blockSignals(True)
            cb7.setChecked(False)
            cb7.blockSignals(False)

    def _sync_to_config(self):
        """Write current checkbox states to AppConfig.flowchart."""
        if not hasattr(self.app_config, 'flowchart'):
            return
        fc = self.app_config.flowchart
        for i in range(1, 9):
            cb = getattr(self, f'flowchart_cb_{i}', None)
            if cb is not None:
                setattr(fc, f'cb{i}', cb.isChecked())
        self.logger.info('gui', 'Flowchart checkbox states synced to AppConfig.')

    def update_from_config(self):
        """Populate checkbox states from AppConfig (blocks signals to avoid gating feedback)."""
        if not hasattr(self.app_config, 'flowchart'):
            return
        fc = self.app_config.flowchart
        for i in range(1, 9):
            cb = getattr(self, f'flowchart_cb_{i}', None)
            state = getattr(fc, f'cb{i}', False)
            if cb is not None:
                cb.blockSignals(True)
                cb.setChecked(state)
                cb.blockSignals(False)

    def apply_styles(self):
        """Apply flowchart-specific styling."""
        return

    def _open_chop_settings(self):
        """Open the Sample Chop settings popup (silence threshold + transient sensitivity)."""
        popup = ChopSettingsPopup(app_config=self.app_config, parent=self)
        popup.exec()

