from skin_ai.store import ProductStore


def test_rgb_trends_exclude_noneligible_capture(tmp_path):
    store=ProductStore(tmp_path/'skin_ai.db')
    base={'rgb_engine_version':'1.1','redness_area_fraction':0.01,'pigmentation_area_fraction':0.02,'texture_index_proxy':0.01,'capture_quality':'good','longitudinal_eligible':True,'capture_quality_score':95.0}
    store.add_scan(scan_id='good',created_at='2026-09-21T01:00:00+00:00',modality='rgb',source_name='good.jpg',metrics=base,media_dir=None)
    bad={**base,'capture_quality':'usable','longitudinal_eligible':False,'capture_quality_score':72.0,'redness_area_fraction':0.25}
    store.add_scan(scan_id='usable',created_at='2026-09-21T02:00:00+00:00',modality='rgb',source_name='usable.jpg',metrics=bad,media_dir=None)
    rows=store.trends(modality='rgb')
    assert [r['scan_id'] for r in rows] == ['good']
    assert rows[0]['longitudinal_eligible'] is True
    assert rows[0]['capture_quality_score'] == 95.0
