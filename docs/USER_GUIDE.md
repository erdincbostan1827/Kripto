# Kullanıcı Kılavuzu

## İlk kullanım
1. Uygulamayı kurun ve yalnız `PAPER` modunda başlatın.
2. GUI First-Run Wizard adımlarını tamamlayın: sistem, exchange, bildirim, trading modu, risk profili, coin evreni, yerelleştirme ve final preflight.
3. Exchange secret değerleri wizard state'e kaydedilmez; credential vault ayrı source-of-truth'tur.
4. Withdrawal izni olan API anahtarı trading için reddedilir.

## Günlük kullanım
Ana ekranda önce Mode, Exchange/Market Data health, Risk state ve açık pozisyon/risk durumunu kontrol edin. Scanner sonucu `NO_TRADE` olması normal bir karardır. Sinyal detayında score/confidence yanında gerekçeler, riskler, veri zamanı, entry/SL/TP ve R/R bilgilerini birlikte değerlendirin.

## PAPER / TESTNET / LIVE
`PAPER` gerçek piyasa/örnek akışı üzerinde sanal execution içindir. `TESTNET` exchange test ortamında credentialed acceptance ister. `LIVE` varsayılan kapalıdır ve yalnız backend evidence gate + re-authentication + kısa ömürlü tek kullanımlık confirmation + human approval sonrası düşünülebilir. Bu release'te PROD LIVE **BLOCKED** durumundadır.

## Acil durum
Emergency Stop yeni risk artırıcı emirleri engeller ve koruyucu emirleri mümkün olduğunca korur. Panic Close ayrı ve açık insan onayı isteyen bir işlemdir. UNKNOWN order, external account activity veya unprotected position durumunda yeni risk açmayın ve Incident Runbooks prosedürünü izleyin.
