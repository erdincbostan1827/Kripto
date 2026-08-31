import {Alert,Button,Dialog,DialogActions,DialogContent,DialogTitle,Stack,TextField,Typography} from '@mui/material';
export type HighRiskAction='ENABLE_AUTO_EXECUTION'|'INCREASE_RISK_LIMIT'|'INCREASE_MAX_POSITION'|'ENABLE_CROSS_MARGIN'|'CHANGE_API_CREDENTIAL'|'PANIC_CLOSE'|'MANUAL_LIVE_ORDER'|'OVERRIDE_EMERGENCY_STOP';
export type HighRiskSummary={action:HighRiskAction;mode:string;account:string;symbol:string;side:string;quantity:string;estimatedNotional:string;estimatedFees:string;estimatedSlippage:string;riskAmount:string;riskPercent:string;protectionState:string};
export function HighRiskConfirmation({open,summary,reason,onCancel,onReason,onConfirm}:{open:boolean;summary:HighRiskSummary;reason:string;onCancel:()=>void;onReason:(v:string)=>void;onConfirm:()=>void}){
 return <Dialog open={open} onClose={onCancel} aria-labelledby="high-risk-title"><DialogTitle id="high-risk-title">Yüksek riskli işlem — ikinci onay</DialogTitle><DialogContent><Stack spacing={1.5} sx={{pt:1}}>
  <Alert severity="error">Bu işlem gerçek sermaye riskini değiştirebilir. Mode, hesap, sembol, yön, miktar ve koruma durumunu doğrulayın.</Alert>
  {Object.entries(summary).map(([k,v])=><Typography key={k}><strong>{k}</strong>: {v}</Typography>)}
  <TextField required label="Audit reason" value={reason} onChange={e=>onReason(e.target.value)} error={!reason.trim()} helperText="Onay nedeni audit log’a bağlanır."/>
 </Stack></DialogContent><DialogActions><Button onClick={onCancel}>İptal</Button><Button color="error" variant="contained" disabled={!reason.trim()} onClick={onConfirm}>İkinci onayı ver</Button></DialogActions></Dialog>
}
