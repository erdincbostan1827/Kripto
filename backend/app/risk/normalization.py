from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class AssetLiquidityClass(str,Enum):
    CORE_HIGH_LIQUIDITY="CORE_HIGH_LIQUIDITY"; LARGE_CAP="LARGE_CAP"; MID_LIQUIDITY="MID_LIQUIDITY"; NEW_LISTING="NEW_LISTING"; HIGH_VOLATILITY="HIGH_VOLATILITY"; RESTRICTED_NO_TRADE="RESTRICTED/NO_TRADE"

@dataclass(frozen=True)
class NormalizedMarketFeatures:
    atr_percent:float; spread_bps:float; quote_volume_notional:float; depth_notional:float; standardized_return:float; standardized_volatility:float
    def __post_init__(self):
        if min(self.atr_percent,self.spread_bps,self.quote_volume_notional,self.depth_notional) < 0: raise ValueError("normalized liquidity features cannot be negative")

@dataclass(frozen=True)
class SafetyLimits:
    max_position_fraction:float; max_order_notional:float; max_spread_bps:float; min_quote_volume_notional:float; min_depth_notional:float
    def __post_init__(self):
        if not 0 < self.max_position_fraction <= 1 or self.max_order_notional <= 0 or self.max_spread_bps < 0 or self.min_quote_volume_notional < 0 or self.min_depth_notional < 0: raise ValueError("invalid safety limits")

@dataclass(frozen=True)
class ResolvedAssetPolicy:
    asset_class:AssetLiquidityClass; limits:SafetyLimits; calibrated_parameters:dict[str,float]; trade_allowed:bool

class AssetParameterPolicy:
    def __init__(self,global_limits:SafetyLimits,class_limits:dict[AssetLiquidityClass,SafetyLimits],strategy_asset_parameters:dict[tuple[str,str],dict[str,float]]|None=None):
        self.global_limits=global_limits; self.class_limits=dict(class_limits); self.strategy_asset_parameters=strategy_asset_parameters or {}
    def resolve(self,*,strategy_id:str,symbol:str,asset_class:AssetLiquidityClass,features:NormalizedMarketFeatures)->ResolvedAssetPolicy:
        if asset_class==AssetLiquidityClass.RESTRICTED_NO_TRADE:
            return ResolvedAssetPolicy(asset_class,self.global_limits,dict(self.strategy_asset_parameters.get((strategy_id,symbol),{})),False)
        if asset_class not in self.class_limits: raise ValueError("missing asset/liquidity-class limits")
        c=self.class_limits[asset_class]; g=self.global_limits
        limits=SafetyLimits(min(g.max_position_fraction,c.max_position_fraction),min(g.max_order_notional,c.max_order_notional),min(g.max_spread_bps,c.max_spread_bps),max(g.min_quote_volume_notional,c.min_quote_volume_notional),max(g.min_depth_notional,c.min_depth_notional))
        allowed=features.spread_bps<=limits.max_spread_bps and features.quote_volume_notional>=limits.min_quote_volume_notional and features.depth_notional>=limits.min_depth_notional
        return ResolvedAssetPolicy(asset_class,limits,dict(self.strategy_asset_parameters.get((strategy_id,symbol),{})),allowed)
