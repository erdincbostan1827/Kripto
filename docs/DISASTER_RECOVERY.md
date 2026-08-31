# Disaster Recovery

Recovery hedefleri tasarım hedefleridir; ölçülmüş SLA değildir. Detaylar `BACKUP_RESTORE_DRILL.md` içindedir.

Recovery sırası: risk artırmayı durdur → DB/exchange truth'u oku → account/balance/position/open-order reconciliation → protective-order coverage doğrula → audit/event bütünlüğünü doğrula → yalnız tanımlı recovery hysteresis ve human approval sonrası risk artırmayı tekrar değerlendir.

Backup dosyasının oluşması başarı sayılmaz. Encrypted backup/PITR izole ortamda restore edilmeli; migration/schema, ledger/order/fill referential integrity, checksums/audit ve read-only application smoke test geçmelidir. Bu local release'te gerçek PostgreSQL PITR restore drill `NOT_TESTED` durumundadır.
