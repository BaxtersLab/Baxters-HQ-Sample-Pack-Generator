from bspg.gui.logic.gui_controller import GUIController
from bspg.core.config import AppConfig

class DummyMW:
    def log_debug_message(self,msg):
        print("MW_LOG:",msg)
    def show_toast(self,msg,duration_ms=0):
        print("TOAST:",msg)
    def set_hrt_beacon_green(self): pass
    def set_hrt_beacon_red(self): pass
    def update_hrt_status_ui(self): pass

app_config = AppConfig()
try:
    # load persisted values into the instance
    app_config.load()
except Exception:
    pass
print("DEBUG: app_config.terms_accepted (raw) =", getattr(app_config,'terms_accepted', None))

c = GUIController(main_window=DummyMW(), app_config=app_config)

print("DEBUG: terms_accepted =", c.is_terms_accepted())
print("DEBUG: loaded terms_accepted from config:", getattr(c.app_config,'terms_accepted', None))

print("check_terms_gate ->", c.check_terms_gate())

# simulate user acceptance
c.legal_acceptance_checkbox_changed(True)
print("After checkbox change (in-memory):", getattr(c.app_config,'terms_accepted', None))

c.legal_acceptance_save_requested()
print("After save (persisted if save exists):", getattr(c.app_config,'terms_accepted', None))
