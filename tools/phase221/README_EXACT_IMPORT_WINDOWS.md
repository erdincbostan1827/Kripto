# Phase 221 — Exact Git History Import (Windows)

Bu araç **commit yeniden üretmez**. Phase 220 exact Git bundle içindeki native Git object/ref'leri taşır.

## Gerekli dosyalar
Aynı klasörde şu dosyalar bulunmalıdır:
- `IMPORT_PHASE221_EXACT_HISTORY.ps1`
- `RUN_PHASE221_EXACT_IMPORT.bat`
- `crypto_trading_platform_v5_1_phase220_git.bundle`
- `PHASE221_EXACT_REFERENCE.json`

Bundle ve reference dosyaları Phase 221 teslimat paketinden alınmalıdır.

## Ön koşullar
1. Git for Windows kurulu olmalı.
2. `erdincbostan1827/Kripto` repository'sine push yetkiniz olmalı.
3. Git Credential Manager ile GitHub oturumu açılabilmeli.
4. Token/şifre hiçbir dosyaya yazılmamalıdır.

## Çalıştırma
`RUN_PHASE221_EXACT_IMPORT.bat` dosyasına çift tıklayın.

Araç fail-closed çalışır:
- bundle SHA-256 ve boyutunu doğrular;
- `git bundle verify` çalıştırır;
- 25 commit'in SHA/parent/tree değerlerini doğrular;
- 19 annotated tag'in tag-object/target SHA'larını doğrular;
- remote tag conflict varsa hiçbir mutation yapmadan durur;
- mevcut `main` SHA'yı force-with-lease koşulu olarak kullanır;
- mevcut bootstrap `main`i timestamp'li backup branch'e korur;
- main + 19 tag'i **tek `git push --atomic` transaction** ile native olarak taşır;
- işlem sonrası GitHub'dan fresh fetch yapıp bütün graph'i yeniden doğrular.

Sadece GitHub `main` tam olarak
`8f369aaf135ae86d31872353b7c68f2555c18089`
olup bütün graph/tag doğrulamaları geçerse `PHASE221_EXACT_HISTORY_CLOSURE=PASS` üretir.

Makine-okunur sonuç `PHASE221_NATIVE_IMPORT_RESULT.json` dosyasına yazılır.
