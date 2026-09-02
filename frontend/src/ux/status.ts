export type SystemStatusCode='OK'|'DEGRADED'|'STALE'|'HALTED'|'REDUCE_ONLY'|'BLOCKED'|'RECONCILING';
export type HumanStatus={code:SystemStatusCode;title:string;whatHappened:string;impact:string;automaticAction:string;userAction:string;correlationId?:string};
export function humanStatus(code:SystemStatusCode,correlationId?:string):HumanStatus{
 const map:Record<SystemStatusCode,Omit<HumanStatus,'code'|'correlationId'>>={
  OK:{title:'Normal',whatHappened:'Sistem normal çalışıyor.',impact:'Risk artırıcı işlemler yalnız geçerli gate’lerle değerlendirilir.',automaticAction:'İzleme sürüyor.',userAction:'Aksiyon gerekmiyor.'},
  DEGRADED:{title:'Kısıtlı',whatHappened:'Bir veya daha fazla servis bozuldu.',impact:'Yeni risk sınırlandırılabilir.',automaticAction:'Fail-closed kontroller devrede.',userAction:'Sistem Sağlığı ayrıntılarını kontrol edin.'},
  STALE:{title:'Veri bayat',whatHappened:'Güncel veri doğrulanamadı.',impact:'Yeni işlem kararı güvenilir değildir.',automaticAction:'Yeni risk durdurulur ve resync istenir.',userAction:'Bağlantı düzelene kadar bekleyin.'},
  HALTED:{title:'Durduruldu',whatHappened:'Trading engine halt durumunda.',impact:'Yeni risk artırıcı emir üretilmez.',automaticAction:'Koruma/reconciliation sürer.',userAction:'Kritik uyarıları inceleyin.'},
  REDUCE_ONLY:{title:'Sadece azalt',whatHappened:'Risk azaltma modu etkin.',impact:'Yeni pozisyon açılamaz.',automaticAction:'Yalnız risk azaltıcı aksiyonlar kabul edilir.',userAction:'Nedeni çözmeden override etmeyin.'},
  BLOCKED:{title:'Engellendi',whatHappened:'Gerekli güvenlik kapısı geçmedi.',impact:'Yüksek riskli işlem engellendi.',automaticAction:'İşlem gönderilmedi.',userAction:'Eksik gate kanıtını tamamlayın.'},
  RECONCILING:{title:'Uzlaştırılıyor',whatHappened:'Exchange ve yerel state karşılaştırılıyor.',impact:'Yeni risk geçici olarak kapalı.',automaticAction:'Order/position/balance reconciliation çalışıyor.',userAction:'Tamamlanmasını bekleyin.'},
 };
 return correlationId?{code,...map[code],correlationId}:{code,...map[code]};
}
