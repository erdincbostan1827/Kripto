import {useEffect,useState} from 'react';
import {Alert,Button,Card,CardContent,Divider,Stack,TextField,Typography} from '@mui/material';
import {beginMfa,completeSetupStep,confirmMfa,getSetup,SetupSnapshot} from '../api/client';

const labels=['Sistem / Server','Exchange','Bildirim','Trading Modu','Risk Profili','Coin Universe','Yerelleştirme','Final Preflight'];

export default function Settings(){
  const [setup,setSetup]=useState<SetupSnapshot>();
  const [error,setError]=useState('');
  const [mfaPassword,setMfaPassword]=useState('');
  const [mfaSecret,setMfaSecret]=useState('');
  const [mfaCode,setMfaCode]=useState('');
  const [recovery,setRecovery]=useState<string[]>([]);

  useEffect(()=>{
    getSetup().then(setSetup).catch(()=>setError('First-run state alınamadı. Admin oturumu ve database readiness kontrol edilmeli.'));
  },[]);

  const complete=async(step:number)=>{
    setError('');
    try{
      const data:Record<string,unknown>=step===4?{requested_mode:'PAPER'}:step===8?{preflight_ok:true}:{confirmed:true};
      setSetup(await completeSetupStep(step,data));
    }catch{
      setError('Adım güvenli biçimde tamamlanamadı. Önce önceki adımları ve preflight durumunu kontrol edin.');
    }
  };

  const startMfa=async()=>{
    try{
      const result=await beginMfa(mfaPassword);
      setMfaSecret(result.secret);
      setRecovery([]);
    }catch{
      setError('MFA enrollment başlatılamadı.');
    }
  };

  const finishMfa=async()=>{
    try{
      const result=await confirmMfa(mfaCode);
      setRecovery(result.recovery_codes);
      setMfaSecret('');
      setMfaPassword('');
    }catch{
      setError('MFA doğrulaması başarısız.');
    }
  };

  return <Stack spacing={2}>
    <Typography variant="h4">Ayarlar / Sistem</Typography>
    <Alert severity="error">LIVE enable yalnız toggle ile açılamaz. Backend evidence + reconciliation + security + human approval gate’leri zorunludur.</Alert>
    {error&&<Alert severity="warning">{error}</Alert>}
    <Card variant="outlined"><CardContent><Stack spacing={1.5}>
      <Typography variant="h6">First-Run Wizard</Typography>
      <Typography variant="body2">Secret değerleri wizard state’ine yazılmaz. Exchange credential girişi ayrı encrypted credential-vault akışının sorumluluğundadır.</Typography>
      {setup ? labels.map((label,i)=>{
        const step=i+1;
        const done=setup.completed_steps.includes(step);
        return <Stack key={step} direction={{xs:'column',sm:'row'}} spacing={1} sx={{alignItems:{sm:'center'}}}>
          <Typography sx={{flex:1}}>{step}. {label} — {done?'Tamamlandı':step===setup.current_step?'Sırada':'Bekliyor'}</Typography>
          <Button disabled={done||step!==setup.current_step} onClick={()=>complete(step)}>{step===8?'Preflight onayla':'Adımı tamamla'}</Button>
        </Stack>;
      }) : <Typography>Wizard yükleniyor…</Typography>}
      {setup?.completed&&<Alert severity="success">Kurulum tamamlandı. Başlangıç modu: {setup.startup_mode}</Alert>}
    </Stack></CardContent></Card>
    <Card variant="outlined"><CardContent><Stack spacing={1.5}>
      <Typography variant="h6">Yönetim Alanları</Typography>
      <Typography variant="body2" color="text.secondary">Temel ayarlar sade tutulur; uzman seçenekleri yalnız ilgili alanda kademeli olarak açılır.</Typography>
      <Stack direction={{xs:'column',sm:'row'}} spacing={1} useFlexGap sx={{flexWrap:'wrap'}}>
        {['Exchange','Telegram/Bildirim','Risk','Coin Universe','Strategy','Kullanıcı & Güvenlik','Sistem Sağlığı','Yedekleme'].map(x=><Button key={x} variant="outlined" size="small">{x}</Button>)}
      </Stack>
      <details><summary>Gelişmiş ayrıntılar</summary><Typography variant="body2" sx={{mt:1}}>Risk artırıcı ayarlar varsayılan olarak seçili değildir. Değişiklikler backend doğrulamasına ve gerektiğinde ikinci onaya tabidir.</Typography></details>
    </Stack></CardContent></Card>
    <Card variant="outlined"><CardContent><Stack spacing={2}>
      <Typography variant="h6">MFA / TOTP</Typography>
      <Typography variant="body2">Admin/trader için önerilir. Secret yalnız enrollment sırasında, recovery code’lar yalnız confirmation sonrasında bir kez gösterilir.</Typography>
      <TextField label="Mevcut parola ile yeniden doğrula" type="password" value={mfaPassword} onChange={e=>setMfaPassword(e.target.value)} autoComplete="current-password"/>
      <Button variant="outlined" onClick={startMfa}>MFA enrollment başlat</Button>
      {mfaSecret&&<Alert severity="warning">TOTP secret: <code>{mfaSecret}</code> — authenticator’a ekledikten sonra aşağıdaki kodla doğrulayın.</Alert>}
      <TextField label="TOTP kodu" value={mfaCode} onChange={e=>setMfaCode(e.target.value)} slotProps={{htmlInput:{inputMode:'numeric'}}}/>
      <Button disabled={!mfaSecret} onClick={finishMfa}>MFA’yı doğrula</Button>
      {recovery.length>0&&<><Divider/><Alert severity="warning">Recovery code’ları şimdi güvenli yerde saklayın; tekrar gösterilmez.</Alert><Typography component="pre" sx={{whiteSpace:'pre-wrap'}}>{recovery.join('\n')}</Typography></>}
    </Stack></CardContent></Card>
  </Stack>;
}
