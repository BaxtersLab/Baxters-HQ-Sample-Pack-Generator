from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QTextEdit, QCheckBox, QPushButton, QScrollArea, QMessageBox,
)
from PySide6.QtGui import QTextOption

from typing import Optional


class SettingsWindow(QWidget):
    def __init__(self, controller: Optional[object] = None, parent=None):
        super().__init__(parent)
        self.controller = controller
        
        # Main layout for the settings window
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Set minimum size so panel is usable when shown
        self.setMinimumHeight(400)
        
        # Create a scroll area for all settings content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        
        # Create container widget for scrollable content
        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout()
        scroll_content.setLayout(self.scroll_layout)
        scroll_area.setWidget(scroll_content)
        
        main_layout.addWidget(scroll_area)

        # Placeholder for other settings widgets

        # --- Legal & Responsible Use section (H-1 placeholder -> H-3/H-4 additions) ---
        self.legal_section = QGroupBox("Legal & Responsible Use")
        self.legal_layout = QVBoxLayout()
        self.legal_section.setLayout(self.legal_layout)

        # Scrollable legal text
        self.legal_text = QTextEdit()
        self.legal_text.setReadOnly(True)
        self.legal_text.setMinimumHeight(180)
        self.legal_text.setWordWrapMode(QTextOption.WordWrap)
        # Real legal disclaimer text (H-4)
        self.legal_text.setPlainText(
            "Legal & Responsible Use\n"
            "-------------------------\n"
            "HQSPG provides tools for audio processing, stem separation, enhancement,\n"
            "and sample-pack creation. Baxters HQ does not provide legal advice and is\n"
            "not responsible for how end users apply these tools.\n\n"
            "You are solely responsible for ensuring that:\n"
            "- You have the legal right to process, modify, or deconstruct any audio\n"
            "  you load into HQSPG.\n"
            "- Your use of HQSPG complies with copyright law, licensing agreements,\n"
            "  and fair-use rules in your region.\n"
            "- Any redistributed audio (samples, stems, remixes, derivatives) is\n"
            "  cleared, licensed, or original.\n\n"
            "Baxters HQ is not liable for copyright violations, misuse, or any legal\n"
            "consequences arising from user-generated content.\n\n"
            "HQSPG is provided as-is, under an open-source license, for respectful and\n"
            "responsible use."
        )
        self.legal_layout.addWidget(self.legal_text)

        # Status indicator label — shows acknowledged state at a glance
        self.legal_status_label = QLabel('⚠️  Not Yet Acknowledged — Run button is locked')
        self.legal_status_label.setStyleSheet(
            'color: #cc8800; font-weight: bold; padding: 4px 0px;'
        )
        self.legal_layout.addWidget(self.legal_status_label)

        # Single permanent-acknowledge button (no checkbox needed)
        self.legal_acknowledge_button = QPushButton('Permanently Acknowledge Legal Agreement')
        self.legal_acknowledge_button.setMinimumHeight(36)
        self.legal_acknowledge_button.setToolTip(
            'Click once to permanently record your acknowledgement.\n'
            'This persists until the app is uninstalled/reinstalled.'
        )
        self.legal_layout.addWidget(self.legal_acknowledge_button)

        try:
            self.legal_acknowledge_button.clicked.connect(self.on_legal_acknowledge_clicked)
        except Exception:
            pass

        # Add to scrollable layout
        self.scroll_layout.addWidget(self.legal_section)

        # --- GUI Tooltips toggle section ---
        try:
            self.tooltip_section = QGroupBox('GUI Tooltips')
            tooltip_layout = QVBoxLayout()
            self.tooltip_section.setLayout(tooltip_layout)

            self.tooltip_toggle = QCheckBox(
                'Enable hover tooltips on flowchart nodes and checkboxes'
            )
            self.tooltip_toggle.setChecked(True)  # on by default
            self.tooltip_toggle.setToolTip(
                'When checked, hovering over flowchart buttons and gates\n'
                'shows a description of what each element does.\n'
                'Uncheck this once you are familiar with the pipeline.'
            )
            tooltip_layout.addWidget(self.tooltip_toggle)

            hint = QLabel('Tip: disable once you know how the pipeline works to reduce visual clutter.')
            hint.setStyleSheet('color: #888; font-size: 10px;')
            tooltip_layout.addWidget(hint)

            self.scroll_layout.addWidget(self.tooltip_section)

            try:
                self.tooltip_toggle.stateChanged.connect(self._on_tooltip_toggle_changed)
            except Exception:
                pass
        except Exception:
            self.tooltip_toggle = None

        # --- Hot Rod Tuner settings section ---
        try:
            self.hrt_section = QGroupBox()
            self.hrt_layout = QVBoxLayout()
            self.hrt_section.setLayout(self.hrt_layout)

            hrt_title = QLabel('Hot Rod Tuner')
            self.hrt_layout.addWidget(hrt_title)

            # Single manual-link button — replaces old host/port/save/link-now cluster
            self.hrt_linknow_button = QPushButton('Manually Link to HRT')
            self.hrt_linknow_button.setMinimumHeight(34)
            self.hrt_layout.addWidget(self.hrt_linknow_button)

            # Status feedback label
            self.hrt_status_label = QLabel('Status: ○ Not Linked')
            self.hrt_layout.addWidget(self.hrt_status_label)

            # add section to scrollable layout
            self.scroll_layout.addWidget(self.hrt_section)

            # wire button
            try:
                self.hrt_linknow_button.clicked.connect(self.on_hrt_link_now_clicked)
            except Exception:
                pass
        except Exception:
            pass

        # If already accepted (persisted from a previous run), freeze the button immediately
        try:
            if self.controller and hasattr(self.controller, 'is_terms_accepted'):
                if self.controller.is_terms_accepted():
                    self._apply_acknowledged_ui()
        except Exception:
            pass

    def on_legal_acknowledge_clicked(self):
        """User clicked the permanent-acknowledge button — persist and freeze."""
        try:
            if self.controller and hasattr(self.controller, 'legal_acceptance_save_requested'):
                self.controller.legal_acceptance_save_requested()
        except Exception:
            pass
        self._apply_acknowledged_ui()

    def _apply_acknowledged_ui(self):
        """Freeze the acknowledge button and flip status label to green once saved."""
        try:
            self.legal_status_label.setText('✅  Legal Agreement Acknowledged — Run button unlocked')
            self.legal_status_label.setStyleSheet(
                'color: #228822; font-weight: bold; padding: 4px 0px;'
            )
        except Exception:
            pass
        try:
            self.legal_acknowledge_button.setText('✓ Legal Agreement Acknowledged')
            self.legal_acknowledge_button.setEnabled(False)
            self.legal_acknowledge_button.setToolTip(
                'You have permanently acknowledged the legal agreement.'
            )
        except Exception:
            pass

    def on_legal_save_clicked(self):
        """Legacy stub — no-op, kept so any surviving connections don\'t crash."""
        pass

    def scroll_to_legal_section(self):
        try:
            self.legal_section.setFocus()
            self.legal_text.verticalScrollBar().setValue(0)
        except Exception:
            pass

    def on_hrt_save_clicked(self):
        try:
            if not self.controller:
                return
            host = ''
            port = 8090
            try:
                host = self.hrt_host_edit.text().strip()
            except Exception:
                host = '127.0.0.1'
            try:
                port_text = self.hrt_port_edit.text().strip()
                port = int(port_text)
            except Exception:
                port = 8090
            try:
                autolink = bool(self.hrt_autolink_checkbox.isChecked())
            except Exception:
                autolink = True

            if hasattr(self.controller, 'update_hrt_settings'):
                try:
                    self.controller.update_hrt_settings(host=host, port=port, autolink_enabled=autolink)
                except Exception:
                    pass
            try:
                self.refresh_hrt_status()
            except Exception:
                pass
        except Exception:
            pass

    def on_hrt_help_clicked(self):
        try:
            QMessageBox.information(
                self,
                "What is Hot Rod Tuner?",
                (
                    "Hot Rod Tuner (HRT) is a separate safety application that monitors "
                    "your computer's temperature.\n\n"
                    "If your system becomes too hot, HRT may automatically close connected "
                    "apps — including HQSPG — to protect your hardware.\n\n"
                    "Linking HQSPG to HRT is optional. When linked, HQSPG simply allows "
                    "HRT to close it if your CPU exceeds HRT's safety threshold.\n\n"
                    "HRT does not send temperature data to HQSPG, and HQSPG does not "
                    "control HRT. They remain fully independent apps."
                )
            )
        except Exception:
            pass

    def on_hrt_link_now_clicked(self):
        try:
            if not self.controller:
                return
            host = self.hrt_host_edit.text().strip() if hasattr(self, 'hrt_host_edit') else '127.0.0.1'
            try:
                port = int(self.hrt_port_edit.text().strip())
            except Exception:
                port = int(getattr(self.controller, 'get_hrt_settings', lambda: {'port': 8080})().get('port', 8080))

            # Use controller helper to perform manual non-blocking link and logging
            try:
                if hasattr(self.controller, 'manual_hrt_link'):
                    try:
                        self.controller.manual_hrt_link(host=host, port=port)
                    except Exception:
                        pass
                else:
                    # fallback: start connector directly
                    try:
                        if hasattr(self.controller, 'hrt') and self.controller.hrt is not None:
                            try:
                                self.controller.hrt.start_autolink(host=host, port=port)
                            except Exception:
                                pass
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception:
            pass

    def refresh_hrt_logs(self):
        try:
            if not self.controller:
                return
            if not hasattr(self, 'hrt_log_text') or self.hrt_log_text is None:
                return
            try:
                logs = []
                if hasattr(self.controller, 'get_recent_hrt_logs'):
                    try:
                        logs = self.controller.get_recent_hrt_logs()
                    except Exception:
                        logs = []
                self.hrt_log_text.setPlainText('\n'.join(logs))
            except Exception:
                pass
        except Exception:
            pass

    def refresh_hrt_status(self):
        try:
            if not self.controller:
                return
            try:
                info = self.controller.get_hrt_status_info() if hasattr(self.controller, 'get_hrt_status_info') else {
                    'linked': False, 'last_attempt': None, 'last_success': None
                }
            except Exception:
                info = {'linked': False, 'last_attempt': None, 'last_success': None}

            # Linked / Not Linked
            try:
                if info.get('linked'):
                    self.hrt_status_label.setText('Status: ● Linked')
                else:
                    self.hrt_status_label.setText('Status: ○ Not Linked')
            except Exception:
                pass

            # Timestamps
            try:
                attempt = info.get('last_attempt')
                success = info.get('last_success')
                attempt_str = attempt.toString('HH:mm:ss') if attempt is not None else '—'
                success_str = success.toString('HH:mm:ss') if success is not None else '—'
                self.hrt_timestamp_label.setText(f'Last attempt: {attempt_str}    Last success: {success_str}')
            except Exception:
                pass

            # Passive hint
            try:
                if not info.get('linked'):
                    self.hrt_hint_label.setText('Hint: Hot Rod Tuner is not currently running or reachable.')
                else:
                    self.hrt_hint_label.setText('')
            except Exception:
                pass
        except Exception:
            pass

    def on_copy_logs_clicked(self):
        try:
            if not self.controller:
                return
            logs = []
            try:
                if hasattr(self.controller, 'get_recent_hrt_logs'):
                    logs = self.controller.get_recent_hrt_logs()
            except Exception:
                logs = []
            text = '\n'.join(logs)
            try:
                if hasattr(self, 'hrt_log_text') and self.hrt_log_text is not None:
                    self.hrt_log_text.setPlainText(text)
                    self.hrt_log_text.selectAll()
                    self.hrt_log_text.copy()
            except Exception:
                pass
        except Exception:
            pass

    def _on_tooltip_toggle_changed(self, state):
        """Enable or disable tooltips on all flowchart widgets when the toggle changes."""
        enabled = bool(state)
        try:
            # Walk up to main window and find flowchart_widget
            mw = self.parent()
            while mw is not None and not hasattr(mw, 'flowchart_widget'):
                mw = mw.parent()
            if mw is None:
                return
            fw = getattr(mw, 'flowchart_widget', None)
            if fw is None:
                return
            # Toggle tooltips on all checkboxes
            for i in range(1, 9):
                cb = getattr(fw, f'flowchart_cb_{i}', None)
                if cb is not None:
                    if enabled:
                        cb.setToolTip(fw._get_checkpoint_tooltip(i))
                    else:
                        cb.setToolTip('')
            # Toggle tooltips on node labels (identified by objectName)
            node_names = {
                'node_stem_sep', 'node_stem_repair', 'node_sample_chop', 'node_input_stem',
            }
            for child in fw.findChildren(__import__('PySide6.QtWidgets', fromlist=['QLabel']).QLabel):
                if child.objectName() in node_names:
                    if not enabled:
                        child.setToolTip('')
                    # re-enable: tooltips were set at construction; re-build from label text
                    elif child.objectName() == 'node_stem_sep':
                        child.setToolTip(
                            "Stem Separation \u2014 Stage 1\n\nRuns Demucs (htdemucs_6s) on your input mix to separate it into:\n"
                            "  vocals \u00b7 drums \u00b7 bass \u00b7 guitar \u00b7 piano \u00b7 other\n\n"
                            "Outputs raw stem files to: <output>/<song>_stems/\n"
                            "Use Gate [1] to pass results to the next stage."
                        )
                    elif child.objectName() == 'node_stem_repair':
                        child.setToolTip(
                            "Stem Repair \u2014 Stage 2\n\nRuns the HQ Glimmer Repair engine on separated stems.\n"
                            "Detects and removes short high-frequency transient artifacts (glimmers).\n\n"
                            "Modes: fast (median spectral filter) \u00b7 balanced (FFT inpainting)\n"
                            "Outputs to: <output>/<song>_repaired/\n"
                            "Use Gate [3] to pass results to Sample Chop."
                        )
                    elif child.objectName() == 'node_sample_chop':
                        child.setToolTip(
                            "Sample Chop \u2014 Stage 3\n\nSlices stems into individual hit/sample files.\n"
                            "Uses silence detection and transient/onset detection.\n\n"
                            "Each sample is zero-cross aligned, normalized, faded, and saved as:\n"
                            "<song>_<stem>_NNNN.wav\n"
                            "Outputs to: <output>/<song>_samples/<stem>/\n"
                            "Use Gate [6] to write results to output folder."
                        )
                    elif child.objectName() == 'node_input_stem':
                        child.setToolTip(
                            "Input Stem \u2014 Bring Your Own Stem\n\n"
                            "Load a pre-separated or custom stem file directly into the pipeline.\n"
                            "Bypasses Stem Separation entirely.\n\n"
                            "Use Gate [4] to route into Stem Repair.\n"
                            "Use Gate [7] to route directly into Sample Chop (skip Repair)."
                        )
            # Toggle gear button tooltip
            for child in fw.findChildren(__import__('PySide6.QtWidgets', fromlist=['QPushButton']).QPushButton):
                if child.objectName() == 'gear_settings_btn':
                    if not enabled:
                        child.setToolTip('')
                    else:
                        child.setToolTip(
                            "Sample Chop Settings\n\nConfigure slicing parameters for Stage 3:\n"
                            "  \u00b7 Silence threshold\n  \u00b7 Min silence duration\n"
                            "  \u00b7 Transient sensitivity\n  \u00b7 Min event length (ms)"
                        )
        except Exception:
            pass
