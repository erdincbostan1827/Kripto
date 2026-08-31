# Strategy Assumptions and Failure Modes

Deterministic signal engine trend, momentum, volume, volatility, market structure, regime and multi-timeframe evidence'i birleştirir. Tek RSI/oversold koşulu BUY üretemez. Higher-timeframe bearish/falling-knife koşulları düşük-timeframe BUY'ı bloke edebilir. Bearish signal SPOT profilinde otomatik short emri anlamına gelmez; exit/avoidance yönüdür.

Entry/risk planı ATR tabanlı protective levels ve risk-budget sizing kullanır. Fee, spread, entry/stop slippage ve uygun market type'ta funding/borrow maliyeti risk hesabına eklenebilir. Backtest/PAPER sonuçları gerçek kârlılık garantisi değildir.

Başlıca başarısızlık modları: rejim değişimi, likidite/spread bozulması, veri gecikmesi/gap, correlated exposure, execution divergence, exchange API/private-stream problemi ve research overfitting. Strategy degradation canlı parametreleri kendi kendine değiştirmez; risk azaltma/research review önerir.

## Matematiksel mantık

Skorlar ve risk bütçeleri deterministik, sonlu ve açıklanabilir girdilerden üretilir; maliyet-sonrası net edge ve belirsizlik hesaba katılır.

## Giriş şartları

Giriş yalnız veri kalitesi, rejim, çoklu-zaman dilimi, likidite, net-edge ve portföy-risk kapıları izin verdiğinde değerlendirilebilir.

## Çıkış şartları

Stop-loss, take-profit, trailing/koruyucu emir, invalidation, risk azaltma ve circuit-breaker koşulları çıkış/azaltma davranışını tetikleyebilir.

## Risk şartları

Pozisyon büyüklüğü, stop mesafesi, fee/slippage/funding, korelasyon-konsantrasyon, drawdown ve hesap-seviyesi limitlerle sınırlandırılır.

## Başarısızlık durumları

Stale/gap veri, execution divergence, reconciliation sorunu, exchange/private-stream hatası, likidite kaybı ve model/strateji degradation fail-closed veya reduce-only davranışına yol açar.
