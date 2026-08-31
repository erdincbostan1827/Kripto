from __future__ import annotations

from contextlib import nullcontext

from app.core.enums import OrderState,TradingMode
from app.exchange.base import AmbiguousExecution
from app.exchange.models import OrderRecord
from .pretrade import normalize_and_validate, validate_reduce_only, validate_spot_sell_balance
from .pretrade_guard import require_pretrade
from .isolation import AccountRiskLocks, SymbolRiskIsolation


class ExecutionService:
    def __init__(self,exchange,risk_machine,leader_registry=None,reservations=None,account_locks=None,symbol_isolation=None,persistent_intents=None,side_effect_fence=None):
        self.exchange=exchange
        self.risk=risk_machine
        self.leader=leader_registry
        self.reservations=reservations
        self.account_locks=account_locks or AccountRiskLocks()
        self.symbol_isolation=symbol_isolation
        self.persistent_intents=persistent_intents
        self.side_effect_fence=side_effect_fence
        self.records={}

    def submit(self,intent,reference_price,max_deviation_bps,mode=TradingMode.PAPER,instance_id=None,fencing_token=None,current_position_qty=None,current_available_base_qty=None,pretrade_limits=None,pretrade_context=None):
        with self.account_locks.hold(intent.account_id) if self.account_locks else nullcontext():
            if self.symbol_isolation and self.symbol_isolation.is_blocked(intent.account_id,intent.symbol) and not intent.reduce_only:
                raise PermissionError('symbol isolated due to unresolved execution state')
            if not self.risk.allow_new_risk() and not intent.reduce_only:
                raise PermissionError('risk state blocks new exposure')
            validate_reduce_only(intent, current_position_qty)
            if (pretrade_limits is None) != (pretrade_context is None):
                raise ValueError('pretrade_limits and pretrade_context must be supplied together')
            if pretrade_limits is not None:
                require_pretrade(intent, pretrade_limits, pretrade_context)
            if not intent.reduce_only:
                validate_spot_sell_balance(intent, current_available_base_qty) if intent.side.upper()=="SELL" else None
            if mode==TradingMode.LIVE:
                if not self.leader or not self.leader.validate(intent.account_id,instance_id,fencing_token):
                    raise PermissionError('invalid LIVE leader fencing token')
                if self.reservations and intent.intent_id not in self.reservations.items and not intent.reduce_only:
                    raise PermissionError('missing capital reservation')
                if self.reservations and not intent.reduce_only and hasattr(self.reservations,'validate_live_balance'):
                    try:
                        self.reservations.validate_live_balance(intent.intent_id,self.exchange.get_balance())
                    except PermissionError:
                        self.risk.restrict('SHARED_BALANCE_CHANGED_BEFORE_SUBMIT')
                        raise
            if intent.intent_id in self.records:
                return self.records[intent.intent_id]
            if self.persistent_intents is not None:
                existing=self.persistent_intents.reconcile_existing(self.exchange,intent.intent_id,intent)
                if existing is not None:
                    self.records[intent.intent_id]=existing
                    return existing
            filters=self.exchange.get_symbol_filters(intent.symbol)
            capabilities=self.exchange.get_capabilities(intent.symbol)
            normalized=normalize_and_validate(intent,filters,capabilities,reference_price,max_deviation_bps)
            current_filters=self.exchange.get_symbol_filters(intent.symbol)
            current_capabilities=self.exchange.get_capabilities(intent.symbol)
            if current_filters != filters or current_capabilities != capabilities:
                self.risk.manual_review('SYMBOL_METADATA_CHANGED_BEFORE_SUBMIT')
                raise PermissionError('symbol metadata changed before submit; revalidation required')
            rec=OrderRecord(normalized.intent_id,normalized.account_id,normalized.symbol,normalized.side,normalized.order_type,normalized.quantity,OrderState.SUBMITTED,normalized.price,normalized.stop_price,client_order_id=normalized.client_order_id)
            if self.persistent_intents is not None:
                durable,created=self.persistent_intents.reserve_before_side_effect(normalized)
                if not created:
                    resolved=self.persistent_intents.reconcile_existing(self.exchange,intent.intent_id,normalized)
                    self.records[intent.intent_id]=resolved
                    return resolved
                rec=durable
            self.records[intent.intent_id]=rec
            try:
                if mode==TradingMode.LIVE and self.side_effect_fence is not None:
                    self.side_effect_fence.require_current(intent.account_id,instance_id,fencing_token)
                actual=self.exchange.submit_order(normalized)
                self.records[intent.intent_id]=actual
                if self.persistent_intents is not None:
                    self.persistent_intents.mark(intent.intent_id,actual)
                return actual
            except (AmbiguousExecution,TimeoutError):
                rec.state=OrderState.UNKNOWN
                if self.persistent_intents is not None:
                    self.persistent_intents.mark(intent.intent_id,rec)
                if self.symbol_isolation is not None:
                    self.symbol_isolation.block(intent.account_id,intent.symbol,'UNKNOWN_ORDER')
                else:
                    self.risk.manual_review('UNKNOWN_ORDER')
                return rec
