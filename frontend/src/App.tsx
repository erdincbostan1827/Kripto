import {lazy,Suspense,useState} from 'react';
import {NavLink,Route,Routes} from 'react-router-dom';
import MenuIcon from '@mui/icons-material/Menu';
import {AppBar,Box,CircularProgress,Container,Drawer,IconButton,List,ListItemButton,ListItemText,Toolbar,Typography,useMediaQuery,useTheme} from '@mui/material';
import {ErrorBoundary} from './components/ErrorBoundary'; import {StatusStrip} from './components/StatusStrip'; import {t} from './i18n/tr';
const Dashboard=lazy(()=>import('./pages/Dashboard')); const Scanner=lazy(()=>import('./pages/Scanner')); const Analysis=lazy(()=>import('./pages/Analysis')); const Orders=lazy(()=>import('./pages/Orders')); const Alerts=lazy(()=>import('./pages/Alerts')); const Research=lazy(()=>import('./pages/Research')); const Performance=lazy(()=>import('./pages/Performance')); const Settings=lazy(()=>import('./pages/Settings'));
const nav=[['/',t('nav.dashboard')],['/scanner',t('nav.scanner')],['/analysis',t('nav.analysis')],['/orders',t('nav.orders')],['/alerts',t('nav.alerts')],['/research',t('nav.research')],['/performance',t('nav.performance')],['/settings',t('nav.settings')]];
function Page({children}:{children:React.ReactNode}){return <ErrorBoundary><Suspense fallback={<Box p={4}><CircularProgress aria-label="Yükleniyor"/></Box>}>{children}</Suspense></ErrorBoundary>}
export default function App(){
 const theme=useTheme(); const desktop=useMediaQuery(theme.breakpoints.up('md')); const [mobileOpen,setMobileOpen]=useState(false);
 const drawer=<List aria-label="Ana navigasyon">{nav.map(([to,label])=><ListItemButton key={to} component={NavLink} to={to} onClick={()=>setMobileOpen(false)}><ListItemText primary={label}/></ListItemButton>)}</List>;
 return <Box sx={{display:'flex',minHeight:'100vh'}}>
  <AppBar position="fixed" sx={{zIndex:1300}}><Toolbar><IconButton aria-label="Menüyü aç" onClick={()=>setMobileOpen(true)} sx={{display:{md:'none'},mr:1}}><MenuIcon/></IconButton><Typography variant="h6">{t('app.title')}</Typography></Toolbar></AppBar>
  {desktop?<Drawer variant="permanent" sx={{width:250,'& .MuiDrawer-paper':{width:250,pt:8}}}>{drawer}</Drawer>:<Drawer open={mobileOpen} onClose={()=>setMobileOpen(false)} ModalProps={{keepMounted:true}} sx={{'& .MuiDrawer-paper':{width:280,pt:2}}}>{drawer}</Drawer>}
  <Box component="main" sx={{flex:1,ml:{xs:0,md:'250px'},pt:8,minWidth:0}}><StatusStrip/><Container maxWidth="xl" sx={{py:{xs:2,md:3},px:{xs:1.5,sm:2,md:3}}}><Routes><Route path="/" element={<Page><Dashboard/></Page>}/><Route path="/scanner" element={<Page><Scanner/></Page>}/><Route path="/analysis" element={<Page><Analysis/></Page>}/><Route path="/orders" element={<Page><Orders/></Page>}/><Route path="/alerts" element={<Page><Alerts/></Page>}/><Route path="/research" element={<Page><Research/></Page>}/><Route path="/performance" element={<Page><Performance/></Page>}/><Route path="/settings" element={<Page><Settings/></Page>}/></Routes></Container></Box>
 </Box>
}
