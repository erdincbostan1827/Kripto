# Hızlı Başlangıç

1. `.env.example` dosyasını örnek alın; gerçek secret'ları repoya yazmayın.
2. Varsayılan çalışma modu `PAPER` olarak bırakılmalıdır.
3. Linux/server kurulumunda `install.sh`, Windows geliştirme kurulumunda `INSTALL_WINDOWS.ps1` kullanılabilir.
4. Production adayında dependency lock dosyaları, migration, PostgreSQL/Redis readiness, backup ve external acceptance kanıtları doğrulanmadan LIVE açılmaz.
5. UI yalnız backend API/WebSocket state'ini gösterir; gerçek execution yetkisi backend risk/execution katmanındadır.
