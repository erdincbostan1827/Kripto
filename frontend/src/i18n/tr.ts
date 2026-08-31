export const tr = {
  'app.title':'Kripto Trading Platformu',
  'nav.dashboard':'Ana Ekran',
  'nav.scanner':'Piyasa / Scanner',
  'nav.analysis':'Analiz',
  'nav.orders':'Pozisyonlar & Emirler',
  'nav.alerts':'Alarmlar',
  'nav.research':'Backtest & Araştırma',
  'nav.performance':'Performans & Risk',
  'nav.settings':'Ayarlar / Sistem',
  'common.loading':'Yükleniyor',
} as const;
export type TranslationKey=keyof typeof tr;
export function t(key:TranslationKey):string{return tr[key]}
