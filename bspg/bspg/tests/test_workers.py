from bspg.gui.workers import DemucsWorker, RepairWorker, SlicerWorker


def test_workers_run():
    d = DemucsWorker()
    r = RepairWorker()
    s = SlicerWorker()

    res_d = d.run()
    res_r = r.run()
    res_s = s.run()

    assert res_d['status'] == 'ok' and res_d['stage'] == 'demucs'
    assert res_r['status'] == 'ok' and res_r['stage'] == 'repair'
    assert res_s['status'] == 'ok' and res_s['stage'] == 'slicer'
