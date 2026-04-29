import logging
import os

def setup_gui_logger():
    home = os.path.expanduser('~')
    base = os.path.join(home, '.hqspg', 'logs')
    os.makedirs(base, exist_ok=True)
    path = os.path.join(base, 'gui.log')
    logger = logging.getLogger('hqspg.gui')
    if not logger.handlers:
        fh = logging.FileHandler(path, encoding='utf-8')
        fmt = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    logger.setLevel(logging.DEBUG)
    return logger
