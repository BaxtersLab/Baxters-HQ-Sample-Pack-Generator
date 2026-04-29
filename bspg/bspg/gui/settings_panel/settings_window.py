from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QTextEdit, QCheckBox, QPushButton, QScrollArea
from PySide6.QtGui import QTextOption
from PySide6.QtCore import QTimer
from typing import Optional
from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QCheckBox, QPushButton, QToolButton, QMessageBox


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

        # Auto-scroll timer: scrolls down 1px every 40ms (~25px/s), resets at bottom
        self._legal_scroll_paused = False
        self._legal_scroll_timer = QTimer(self)
        self._legal_scroll_timer.setInterval(40)
        self._legal_scroll_timer.timeout.connect(self._tick_legal_scroll)
        self._legal_scroll_timer.start()

        # Pause auto-scroll while the user is manually interacting
        self.legal_text.verticalScrollBar().sliderPressed.connect(
            lambda: setattr(self, '_legal_scroll_paused', True)
        )
        self.legal_text.verticalScrollBar().sliderReleased.connect(
            lambda: setattr(self, '_legal_scroll_paused', False)
        )

        # Acceptance checkbox
        self.legal_accept_checkbox = QCheckBox(
            "I accept these terms and understand my responsibilities."
        )
        self.legal_layout.addWidget(self.legal_accept_checkbox)

        # Save button
        self.legal_save_button = QPushButton("Save")
        self.legal_layout.addWidget(self.legal_save_button)

        # Wire UI signals to local handlers that call controller stubs
        try:
            self.legal_accept_checkbox.stateChanged.connect(self.on_legal_acceptance_changed)
        except Exception:
            pass
        try:
            self.legal_save_button.clicked.connect(self.on_legal_save_clicked)
        except Exception:
            pass

        # Add to scrollable layout
        self.scroll_layout.addWidget(self.legal_section)

        # --- Hot Rod Tuner settings section (I-4) ---
        try:
            self.hrt_section = QGroupBox()
            self.hrt_layout = QVBoxLayout()
            self.hrt_section.setLayout(self.hrt_layout)

            # Title row with help icon
            try:
                title_row = QHBoxLayout()
                title_label = QLabel('Hot Rod Tuner')
                help_btn = QToolButton()
                help_btn.setText('?')
                help_btn.setFixedSize(20, 20)
                help_btn.setStyleSheet('font-weight: bold;')
                title_row.addWidget(title_label)
                title_row.addWidget(help_btn)
                title_row.addStretch()
                self.hrt_layout.addLayout(title_row)
                try:
                    help_btn.clicked.connect(self.on_hrt_help_clicked)
                except Exception:
                    pass
            except Exception:
                pass

            # Host
            hrt_host_row = QHBoxLayout()
            hrt_host_label = QLabel('Host:')
            self.hrt_host_edit = QLineEdit()
            hrt_host_row.addWidget(hrt_host_label)
            hrt_host_row.addWidget(self.hrt_host_edit)
            self.hrt_layout.addLayout(hrt_host_row)

            # Port
            hrt_port_row = QHBoxLayout()
            hrt_port_label = QLabel('Port:')
            self.hrt_port_edit = QLineEdit()
            self.hrt_port_edit.setFixedWidth(80)
            hrt_port_row.addWidget(hrt_port_label)
            hrt_port_row.addWidget(self.hrt_port_edit)
            self.hrt_layout.addLayout(hrt_port_row)

            # Autolink checkbox
            self.hrt_autolink_checkbox = QCheckBox('Automatically link to Hot Rod Tuner on startup')
            self.hrt_layout.addWidget(self.hrt_autolink_checkbox)

            # Save button
            self.hrt_save_button = QPushButton('Save HRT Settings')
            self.hrt_layout.addWidget(self.hrt_save_button)

            # Manual Link Now button
            self.hrt_linknow_button = QPushButton('Link Now')
            self.hrt_layout.addWidget(self.hrt_linknow_button)
            # Status line and timestamps
            try:
                self.hrt_status_label = QLabel('Status: ○ Not Linked')
                self.hrt_layout.addWidget(self.hrt_status_label)

                self.hrt_timestamp_label = QLabel('Last attempt: —    Last success: —')
                self.hrt_layout.addWidget(self.hrt_timestamp_label)

                self.hrt_hint_label = QLabel('')
                self.hrt_hint_label.setStyleSheet('color: #888; font-size: 11px;')
                self.hrt_layout.addWidget(self.hrt_hint_label)
            except Exception:
                pass
            # Collapsible recent logs pane
            try:
                self.hrt_log_group = QGroupBox('Recent Connector Logs')
                self.hrt_log_group.setCheckable(True)
                self.hrt_log_group.setChecked(False)
                self.hrt_log_layout = QVBoxLayout()
                self.hrt_log_group.setLayout(self.hrt_log_layout)

                self.hrt_log_text = QTextEdit()
                self.hrt_log_text.setReadOnly(True)
                self.hrt_log_text.setMinimumHeight(120)
                self.hrt_log_text.setStyleSheet('font-size: 10px; background-color: #111; color: #ccc;')
                self.hrt_log_layout.addWidget(self.hrt_log_text)

                self.copy_logs_button = QPushButton('Copy Logs')
                self.hrt_log_layout.addWidget(self.copy_logs_button)

                self.hrt_layout.addWidget(self.hrt_log_group)

                try:
                    self.copy_logs_button.clicked.connect(self.on_copy_logs_clicked)
                except Exception:
                    pass
                try:
                    self.hrt_log_group.toggled.connect(lambda _: self.refresh_hrt_logs())
                except Exception:
                    pass
            except Exception:
                self.hrt_log_group = None

            # add section to scrollable layout
            self.scroll_layout.addWidget(self.hrt_section)

            # initialize from controller if available
            try:
                if self.controller and hasattr(self.controller, 'get_hrt_settings'):
                    try:
                        h = self.controller.get_hrt_settings()
                        self.hrt_host_edit.setText(h.get('host', '127.0.0.1'))
                        self.hrt_port_edit.setText(str(h.get('port', 5050)))
                        self.hrt_autolink_checkbox.setChecked(bool(h.get('autolink_enabled', True)))
                    except Exception:
                        pass
            except Exception:
                pass

            # wire save
            try:
                self.hrt_save_button.clicked.connect(self.on_hrt_save_clicked)
            except Exception:
                pass
            try:
                self.hrt_linknow_button.clicked.connect(self.on_hrt_link_now_clicked)
            except Exception:
                pass
            try:
                # when saving or toggling the log group, refresh status info
                try:
                    self.hrt_save_button.clicked.connect(lambda: self.refresh_hrt_status())
                except Exception:
                    pass
            except Exception:
                pass
        except Exception:
            pass

        # Initialize checkbox from controller/config if available
        try:
            if self.controller and hasattr(self.controller, 'is_terms_accepted'):
                try:
                    self.legal_accept_checkbox.setChecked(self.controller.is_terms_accepted())
                except Exception:
                    pass
        except Exception:
            pass

    def _tick_legal_scroll(self):
        """Advance the legal text auto-scroll by 1px; loop back to top after a pause."""
        if self._legal_scroll_paused:
            return
        sb = self.legal_text.verticalScrollBar()
        if sb.value() >= sb.maximum():
            # pause at bottom for ~2 s (2000ms / 40ms = 50 ticks), then reset
            if not hasattr(self, '_legal_pause_ticks'):
                self._legal_pause_ticks = 0
            self._legal_pause_ticks += 1
            if self._legal_pause_ticks >= 50:
                self._legal_pause_ticks = 0
                sb.setValue(0)
        else:
            self._legal_pause_ticks = 0
            sb.setValue(sb.value() + 1)

    def on_legal_acceptance_changed(self, state):
        try:
            if self.controller and hasattr(self.controller, 'legal_acceptance_checkbox_changed'):
                try:
                    self.controller.legal_acceptance_checkbox_changed(bool(state))
                except Exception:
                    pass
        except Exception:
            pass

    def on_legal_save_clicked(self):
        try:
            # Ensure controller sees the current checkbox state (defensive)
            try:
                state = bool(self.legal_accept_checkbox.isChecked())
                if self.controller and hasattr(self.controller, 'legal_acceptance_checkbox_changed'):
                    try:
                        self.controller.legal_acceptance_checkbox_changed(state)
                    except Exception:
                        pass
            except Exception:
                pass

            if self.controller and hasattr(self.controller, 'legal_acceptance_save_requested'):
                try:
                    self.controller.legal_acceptance_save_requested()
                except Exception:
                    pass
        except Exception:
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
            port = 5050
            try:
                host = self.hrt_host_edit.text().strip()
            except Exception:
                host = '127.0.0.1'
            try:
                port_text = self.hrt_port_edit.text().strip()
                port = int(port_text)
            except Exception:
                port = 5050
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
