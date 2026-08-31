from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from decimal import Decimal
@dataclass(frozen=True)
class SymbolEligibility:
    symbol:str; listing_age_days:int; quote_volume_24h:Decimal; spread_bps:Decimal; depth_notional:Decimal; history_bars:int; data_fresh:bool; active:bool=True; suspended:bool=False

def eligibility(x:SymbolEligibility,min_age=30,min_volume=Decimal('5000000'),max_spread=Decimal('20'),min_depth=Decimal('100000'),min_history=250):
    reasons=[]
    if not x.active or x.suspended: reasons.append('NOT_TRADABLE')
    if x.listing_age_days<min_age: reasons.append('NEW_LISTING_QUARANTINE')
    if x.quote_volume_24h<min_volume: reasons.append('LOW_VOLUME')
    if x.spread_bps>max_spread: reasons.append('WIDE_SPREAD')
    if x.depth_notional<min_depth: reasons.append('THIN_BOOK')
    if x.history_bars<min_history: reasons.append('INSUFFICIENT_HISTORY')
    if not x.data_fresh: reasons.append('STALE_DATA')
    return (not reasons,reasons)
@dataclass(frozen=True)
class UniverseSnapshot:
    snapshot_id:str; timestamp:datetime; members:tuple[str,...]; excluded:dict[str,tuple[str,...]]

@dataclass(frozen=True)
class UniverseMembership:
    symbol: str
    listed_at: datetime
    delisted_at: datetime | None = None
    suspended_from: datetime | None = None
    suspended_until: datetime | None = None

    def active_at(self, as_of: datetime) -> bool:
        as_of = as_of if as_of.tzinfo else as_of.replace(tzinfo=timezone.utc)
        listed = self.listed_at if self.listed_at.tzinfo else self.listed_at.replace(tzinfo=timezone.utc)
        if as_of < listed:
            return False
        if self.delisted_at is not None:
            de = self.delisted_at if self.delisted_at.tzinfo else self.delisted_at.replace(tzinfo=timezone.utc)
            if as_of >= de:
                return False
        if self.suspended_from is not None:
            sf = self.suspended_from if self.suspended_from.tzinfo else self.suspended_from.replace(tzinfo=timezone.utc)
            su = self.suspended_until
            if su is None and as_of >= sf:
                return False
            if su is not None:
                su = su if su.tzinfo else su.replace(tzinfo=timezone.utc)
                if sf <= as_of < su:
                    return False
        return True


class PointInTimeUniverse:
    def __init__(self, memberships: list[UniverseMembership]):
        self.memberships = tuple(memberships)

    def members(self, as_of: datetime) -> tuple[str, ...]:
        return tuple(sorted(m.symbol for m in self.memberships if m.active_at(as_of)))

    def contains(self, symbol: str, as_of: datetime) -> bool:
        return any(m.symbol == symbol and m.active_at(as_of) for m in self.memberships)

@dataclass(frozen=True)
class SymbolMetadataVersion:
    symbol: str
    effective_at: datetime
    version: str
    metadata_source: str
    price_precision: int | None
    quantity_precision: int | None
    filters: tuple[tuple[str, str], ...]


class SymbolMetadataHistory:
    """Point-in-time symbol/filter metadata history.

    Metadata versions are content-addressed so a changed exchange filter or
    precision produces a different immutable version. Callers must query with
    an as-of timestamp; future metadata is never returned for historical use.
    """

    def __init__(self):
        self._versions: dict[str, list[SymbolMetadataVersion]] = {}

    @staticmethod
    def _canonical_filters(filters: dict[str, object] | list[dict[str, object]] | tuple) -> tuple[tuple[str, str], ...]:
        items: list[tuple[str, str]] = []
        if isinstance(filters, dict):
            for key, value in filters.items():
                items.append((str(key), str(value)))
        else:
            for item in filters or ():
                if isinstance(item, dict):
                    prefix = str(item.get('filterType', 'FILTER'))
                    for key, value in sorted(item.items()):
                        items.append((f'{prefix}.{key}', str(value)))
                else:
                    items.append(('value', str(item)))
        return tuple(sorted(items))

    @staticmethod
    def _aware(value: datetime) -> datetime:
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)

    def record(
        self,
        symbol: str,
        *,
        effective_at: datetime,
        metadata_source: str,
        filters: dict[str, object] | list[dict[str, object]] | tuple,
        price_precision: int | None = None,
        quantity_precision: int | None = None,
    ) -> SymbolMetadataVersion:
        import hashlib
        import json

        effective = self._aware(effective_at)
        canonical = self._canonical_filters(filters)
        payload = {
            'symbol': symbol.upper(),
            'metadata_source': metadata_source,
            'price_precision': price_precision,
            'quantity_precision': quantity_precision,
            'filters': canonical,
        }
        version = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()[:16]
        entry = SymbolMetadataVersion(
            symbol.upper(), effective, version, metadata_source,
            price_precision, quantity_precision, canonical,
        )
        bucket = self._versions.setdefault(symbol.upper(), [])
        if any(existing.effective_at == effective and existing.version != version for existing in bucket):
            raise ValueError('conflicting metadata for same effective timestamp')
        if not any(existing.effective_at == effective and existing.version == version for existing in bucket):
            bucket.append(entry)
            bucket.sort(key=lambda item: item.effective_at)
        return entry

    def version_at(self, symbol: str, as_of: datetime) -> SymbolMetadataVersion:
        current = self._aware(as_of)
        eligible = [item for item in self._versions.get(symbol.upper(), ()) if item.effective_at <= current]
        if not eligible:
            raise LookupError(f'no metadata version available as_of for {symbol.upper()}')
        return eligible[-1]

    def changed_between(self, symbol: str, earlier: datetime, later: datetime) -> bool:
        return self.version_at(symbol, earlier).version != self.version_at(symbol, later).version
