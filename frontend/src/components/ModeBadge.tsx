import { Chip } from '@mui/material';
export function ModeBadge({mode}:{mode:string}){const live=mode==='LIVE';return <Chip label={live?'LIVE — GERÇEK PARA':mode} color={live?'error':mode==='TESTNET'?'warning':'info'} variant={live?'filled':'outlined'} />}
