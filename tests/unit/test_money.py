from decimal import Decimal
import pytest
from app.core.money import decimal,quantize_step,normalize_price,normalize_quantity,bps_distance
@pytest.mark.parametrize('v', ['1','1.23',1,0,Decimal('2.5')])
def test_decimal_finite(v): assert decimal(v).is_finite()
@pytest.mark.parametrize('v',['NaN','Infinity','-Infinity'])
def test_decimal_rejects_nonfinite(v):
    with pytest.raises(ValueError): decimal(v)
@pytest.mark.parametrize('v,step,expected',[('1.234','0.01','1.23'),('0.019','0.001','0.019'),('12','5','10')])
def test_quantize_down(v,step,expected): assert quantize_step(Decimal(v),Decimal(step))==Decimal(expected)
def test_quantize_up(): assert quantize_step(Decimal('1.231'),Decimal('0.01'),direction='up')==Decimal('1.24')
def test_price_rounding_direction():
    assert normalize_price(Decimal('10.019'),Decimal('0.01'),'BUY')==Decimal('10.01')
    assert normalize_price(Decimal('10.011'),Decimal('0.01'),'SELL')==Decimal('10.02')
def test_quantity_rounds_down(): assert normalize_quantity(Decimal('1.23456'),Decimal('0.001'))==Decimal('1.234')
def test_bps(): assert bps_distance(Decimal('101'),Decimal('100'))==Decimal('100')
