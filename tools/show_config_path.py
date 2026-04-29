from bspg.core.config import AppConfig
import inspect, os

sig_save = inspect.signature(AppConfig.save)
sig_load = inspect.signature(AppConfig.load)

def default_param(sig, name):
    try:
        return sig.parameters[name].default
    except Exception:
        return None

save_default = default_param(sig_save, 'path')
load_default = default_param(sig_load, 'path')

print('AppConfig.save default param:', save_default)
print('AppConfig.load default param:', load_default)

abs_save_path = os.path.abspath(save_default) if save_default else None
abs_load_path = os.path.abspath(load_default) if load_default else None

print('Resolved save path:', abs_save_path)
print('Resolved load path:', abs_load_path)

# attempt to save to default and print result and file exists
c = AppConfig()
res = c.save()
print('save() returned:', res)
print('file exists after save?', os.path.exists(abs_save_path))

# call load and print result
res2 = c.load()
print('load() returned:', res2)
