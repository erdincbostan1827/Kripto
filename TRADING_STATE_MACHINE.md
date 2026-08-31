# TRADING_STATE_MACHINE.md

States: `STOPPED`, `PREFLIGHT`, `PAPER_RUNNING`, `TESTNET_RUNNING`, `LIVE_LOCKED`, `LIVE_STAGE_0..3`, `REDUCING_ONLY`, `HALTED`, `MANUAL_REVIEW_REQUIRED`.

- First boot: `PREFLIGHT -> PAPER_RUNNING` only if mandatory local preflight passes.
- Any P0 safety ambiguity: running state -> `REDUCING_ONLY` or `HALTED`.
- `LIVE_LOCKED -> LIVE_STAGE_0` requires explicit human approval plus all backend gates.
- Stage increase is never automatic by default; stage decrease may be automatic on risk degradation.
- Restart always reconciles before risk-increasing actions.
