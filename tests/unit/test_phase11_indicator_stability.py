from app.indicators.stability import recursive_stability

def rows(n,price=100.0):
    return [dict(open=price,high=price+1,low=price-1,close=price,volume=1000+i) for i in range(n)]

def test_recursive_indicator_stability_with_sufficient_warmup():
    # Constant price makes recursive price indicators converge exactly; volume
    # trend is deliberately constant too so a warmup extension must not move outputs.
    data=[dict(open=100,high=101,low=99,close=100,volume=1000) for _ in range(260)]
    r=recursive_stability(data,warmup_bars=200,extra_history=50,tolerance=1e-9)
    assert r.stable and r.max_relative_drift<=1e-9

def test_recursive_indicator_stability_rejects_insufficient_history():
    import pytest
    with pytest.raises(ValueError): recursive_stability(rows(100),200,50)
