from skin_ai.session_summary import build_session_summary, find_previous_comparable


def scan(scan_id, created_at, region='left_cheek', spots=2, area=0.01, session_id=None, comparable=True):
    metrics={
        'tracking_series_key': f'subject:{region}',
        'tracking_region_label': region.replace('_',' ').title(),
        'uv_longitudinal_eligible': comparable,
        'uv_comparison_key': f'uv:{region}' if comparable else None,
        'porphyrin_component_count_proxy': spots,
        'porphyrin_area_fraction_valid': area,
        'porphyrin_red_intensity_proxy': 0.4,
        'artifact_area_fraction': 0.05,
        'uv_input_validation_score': 95,
    }
    if session_id:
        metrics['scan_session_id']=session_id
    return {'id':scan_id,'created_at':created_at,'modality':'uv','metrics':metrics}


def test_previous_comparable_requires_same_series_and_earlier_scan():
    current=scan('current','2026-09-21T10:00:00+00:00',spots=3,session_id='s2')
    good=scan('good','2026-09-20T10:00:00+00:00',spots=2,session_id='s1')
    wrong_region=scan('wrong','2026-09-20T11:00:00+00:00',region='right_cheek',spots=9,session_id='s1')
    same_session=scan('same','2026-09-21T09:00:00+00:00',spots=8,session_id='s2')
    assert find_previous_comparable(current,[current,good,wrong_region,same_session])['id']=='good'


def test_summary_marks_first_region_as_baseline():
    current=scan('current','2026-09-21T10:00:00+00:00',spots=2,session_id='s1')
    session={'id':'s1','status':'complete','session_version':'1.0','modality':'uv','created_at':'2026-09-21T09:00:00+00:00','completed_at':'2026-09-21T10:00:00+00:00','items':[{'scan_id':'current','region_code':'left_cheek'}]}
    summary=build_session_summary(session,[current],{'id':'p1','display_name':'Test'})
    assert summary['regions'][0]['status']=='baseline'
    assert summary['comparable_region_count']==0
    assert summary['diagnostic_use'] is False


def test_summary_marks_small_uv_change_as_stable():
    previous=scan('previous','2026-09-20T10:00:00+00:00',spots=2,area=0.010,session_id='s0')
    current=scan('current','2026-09-21T10:00:00+00:00',spots=3,area=0.014,session_id='s1')
    session={'id':'s1','status':'complete','session_version':'1.0','modality':'uv','created_at':'2026-09-21T09:00:00+00:00','completed_at':'2026-09-21T10:00:00+00:00','items':[{'scan_id':'current','region_code':'left_cheek'}]}
    summary=build_session_summary(session,[previous,current])
    assert summary['regions'][0]['status']=='stable'
    assert summary['regions'][0]['comparison']['spot_delta']==1


def test_summary_marks_consistent_increase_as_higher_signal():
    previous=scan('previous','2026-09-20T10:00:00+00:00',spots=2,area=0.010,session_id='s0')
    current=scan('current','2026-09-21T10:00:00+00:00',spots=5,area=0.020,session_id='s1')
    session={'id':'s1','status':'complete','session_version':'1.0','modality':'uv','created_at':'2026-09-21T09:00:00+00:00','completed_at':'2026-09-21T10:00:00+00:00','items':[{'scan_id':'current','region_code':'left_cheek'}]}
    summary=build_session_summary(session,[previous,current])
    assert summary['regions'][0]['status']=='higher'
    assert 'higher' in summary['headline']
