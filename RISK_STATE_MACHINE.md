# RISK_STATE_MACHINE.md

States: `NORMAL`, `RESTRICTED`, `REDUCING_ONLY`, `HALTED`, `MANUAL_REVIEW_REQUIRED`.

Monotonic safety rule: uncertainty cannot increase permitted risk. Recovery uses hysteresis: cause cleared + minimum healthy interval + successful reconciliation + operator acknowledgement for SEV1/unknown external activity where required.
