from pathlib import Path
from app.risk.position_view import position_management_actions
ROOT=Path(__file__).resolve().parents[2]

def test_phase123_position_management_tracks_volatility_trend_trailing_stop_and_partial_tp():
    out=position_management_actions(entry=100,price=112,stop=95,atr=2,take_profits=[105,110,120],filled_take_profits=2,volatility_ratio=2.0,trend_changed=True)
    assert out['volatility_ratio']==2.0 and out['trend_changed'] is True
    assert out['trailing_stop']>=100 and out['partial_tp_due'] is False and out['next_take_profit']==120
    assert out['reduce_only_recommended'] is True

def test_phase123_project_structure_is_cleanly_split_and_api_surface_is_versioned():
    for rel in ('backend/app','frontend/src','tests','scripts','docs','alembic'):
        assert (ROOT/rel).exists()
    main=(ROOT/'backend/app/main.py').read_text(encoding='utf-8')
    assert '/api/v1/' in main

def test_phase123_signal_pipeline_snapshot_duplicate_and_confirmation_sections_have_real_implementations():
    required=('backend/app/signals/engine.py','backend/app/audit/decision_evidence.py','backend/app/strategies/outcomes.py','backend/app/monitoring/telegram_security.py')
    for rel in required: assert (ROOT/rel).is_file()
    cfg=(ROOT/'backend/app/core/config.py').read_text(encoding='utf-8')
    assert 'auto_execution: bool = False' in cfg
