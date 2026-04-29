import os
try:
    from appdirs import user_data_dir
    base = user_data_dir('HQSPG','BaxtersHQ')
except Exception:
    base = os.path.join(os.path.expanduser('~'), '.hqspg')
path = os.path.join(base, 'hqspg_instance.lock')
print('LOCKFILE:', path)
if os.path.exists(path):
    try:
        os.remove(path)
        print('Removed lockfile')
    except Exception as e:
        print('Error removing lockfile:', e)
else:
    print('No lockfile found')
