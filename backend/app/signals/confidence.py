from __future__ import annotations
from dataclasses import dataclass
from app.signals.calibration import calibrate

@dataclass(frozen=True)
class ConfidenceEvidence:
    raw_probability: float
    calibrated_probability: float
    brier_score: float
    regime_alignment: float
    feature_completeness: float
    data_quality: float
    oos_validated: bool
    similar_signal_count: int
    bucket_observed_rate: float | None

class ConfidenceCalibrator:
    def __init__(self, probabilities, outcomes, *, oos_validated:bool, buckets:int=10):
        if not oos_validated: raise ValueError('confidence calibration requires out-of-sample validation')
        self.report=calibrate(probabilities,outcomes,buckets=buckets)
        self._pairs=tuple(zip(map(float,probabilities),map(bool,outcomes)))
    def evidence(self, raw_probability:float, *, regime_alignment:float, feature_completeness:float, data_quality:float) -> ConfidenceEvidence:
        p=max(0.0,min(1.0,float(raw_probability)))
        for name,v in {'regime_alignment':regime_alignment,'feature_completeness':feature_completeness,'data_quality':data_quality}.items():
            if not 0 <= float(v) <= 1: raise ValueError(f'{name} must be in [0,1]')
        bucket=None
        for b in self.report.buckets:
            if b['lower'] <= p <= b['upper'] + 1e-12:
                bucket=b; break
        observed=float(bucket['observed_rate']) if bucket else p
        support=int(bucket['count']) if bucket else 0
        quality=(float(regime_alignment)*float(feature_completeness)*float(data_quality)) ** (1/3)
        calibrated=max(0.0,min(1.0,observed*quality))
        return ConfidenceEvidence(p,calibrated,self.report.brier_score,float(regime_alignment),float(feature_completeness),float(data_quality),True,support,observed if bucket else None)
