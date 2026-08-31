from __future__ import annotations
import hashlib
import os
import hmac
from pathlib import Path
from fastapi import FastAPI,HTTPException,WebSocket,Request,Response as FastAPIResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import generate_latest,CONTENT_TYPE_LATEST
from starlette.responses import Response
from app import __version__
from app.api.schemas import AnalyzeRequest,MultiTimeframeAnalyzeRequest,BacktestRequest,TradingAction,LoginRequest,BootstrapAdminRequest,HighRiskConfirmationRequest,LiveModeRequest,MfaEnrollmentRequest,MfaEnrollmentConfirmRequest,MfaResetRequest,SetupStepRequest
from app.services.pipeline import analyze
from app.signals.multi_timeframe import analyze_multi_timeframe
from app.backtest.engine import run
from app.monitoring.health import HealthService
from app.monitoring.dashboard import build_dashboard_snapshot
from app.core.http_security import SecurityHeadersMiddleware
from app.core.logging import configure_json_logging
from app.core.enums import TradingMode,RiskState,Environment
from app.core.security import ConfirmationStore
from app.core.live_gate import LiveGateEvidence, require_live_gate
from app.services.runtime import RuntimeFacade
from app.database.session import make_engine,session_factory
from app.auth.db_service import DatabaseAuthService
from app.services.setup_wizard import SetupWizardService
from app.core.security import SecretBox

SESSION_COOKIE="ctp_session"
logger=configure_json_logging(os.getenv("LOG_LEVEL","INFO"))

def create_app(environment:Environment|str=Environment.DEV,auth_service=None,bootstrap_token_hash:str|None=None,live_evidence:LiveGateEvidence|None=None,runtime=None,setup_service=None,health_service:HealthService|None=None)->FastAPI:
    env=Environment(str(environment))
    api=FastAPI(title='Crypto Trading Platform',version=__version__,docs_url=None if env==Environment.PROD else '/docs',redoc_url=None if env==Environment.PROD else '/redoc',openapi_url=None if env==Environment.PROD else '/openapi.json')
    origins=[x.strip() for x in os.getenv('CORS_ORIGINS','http://localhost:5173,http://localhost:8080').split(',') if x.strip()]
    api.add_middleware(CORSMiddleware,allow_origins=origins,allow_credentials=True,allow_methods=['GET','POST'],allow_headers=['Content-Type','X-CSRF-Token','X-Correlation-ID'])
    hosts=[x.strip() for x in os.getenv('TRUSTED_HOSTS','localhost,127.0.0.1,testserver' if env!=Environment.PROD else 'localhost,127.0.0.1').split(',') if x.strip()]
    api.add_middleware(TrustedHostMiddleware,allowed_hosts=hosts)
    api.add_middleware(SecurityHeadersMiddleware,production=env==Environment.PROD)
    api.state.auth_service=auth_service
    api.state.environment=env
    api.state.bootstrap_token_hash=bootstrap_token_hash or os.getenv('ADMIN_BOOTSTRAP_TOKEN_HASH')
    api.state.confirmations=ConfirmationStore()
    api.state.live_evidence=live_evidence
    api.state.runtime=runtime or RuntimeFacade()
    api.state.setup_service=setup_service
    trading_state={'mode':TradingMode.PAPER,'risk':RiskState.NORMAL,'running':False}
    health=health_service or (HealthService.production() if env==Environment.PROD else HealthService.mock_development())

    @api.exception_handler(HTTPException)
    async def http_exception(request:Request,exc:HTTPException):
        correlation_id=getattr(request.state,'correlation_id','unavailable')
        logger.warning('http_error',extra={'correlation_id':correlation_id,'path':request.url.path,'status_code':exc.status_code,'details':{'detail':str(exc.detail)}})
        return JSONResponse(status_code=exc.status_code,content={'detail':exc.detail,'correlation_id':correlation_id,'recommended_action':'İşlemi ve sistem durumunu kontrol edin.'})

    @api.exception_handler(RequestValidationError)
    async def validation_exception(request:Request,exc:RequestValidationError):
        correlation_id=getattr(request.state,'correlation_id','unavailable')
        fields=[{'loc':[str(x) for x in e.get('loc',())],'type':e.get('type','validation_error')} for e in exc.errors()]
        logger.warning('request_validation_error',extra={'correlation_id':correlation_id,'path':request.url.path,'status_code':422,'details':{'fields':fields}})
        return JSONResponse(status_code=422,content={'detail':'Request validation failed','fields':fields,'correlation_id':correlation_id,'recommended_action':'Gönderilen alanları kontrol edin.'})

    @api.exception_handler(Exception)
    async def unhandled_exception(request:Request,exc:Exception):
        correlation_id=getattr(request.state,'correlation_id','unavailable')
        logger.exception('unhandled_exception',extra={'correlation_id':correlation_id,'path':request.url.path,'status_code':500})
        return JSONResponse(status_code=500,content={'detail':'Beklenmeyen sistem hatası. İşlem güvenli şekilde durduruldu.','correlation_id':correlation_id,'recommended_action':'Yeni risk açmayın; sistem sağlığını kontrol edin.'})

    def require(request:Request,role:str='viewer',csrf:bool=False):
        if env!=Environment.PROD:
            return {'user_id':'local-dev','role':'admin'}
        svc=api.state.auth_service
        if svc is None: raise HTTPException(503,'authentication service unavailable')
        token=request.cookies.get(SESSION_COOKIE)
        if not token: raise HTTPException(401,'authentication required')
        try: ctx=svc.authenticate(token,role)
        except PermissionError as exc: raise HTTPException(403,str(exc)) from exc
        if csrf:
            presented=request.headers.get('X-CSRF-Token','')
            if not presented or not svc.verify_csrf(token,presented): raise HTTPException(403,'CSRF validation failed')
        return ctx

    @api.get('/api/v1/compatibility')
    def compatibility(): return {'api_version':'v1','server_version':__version__,'min_client':'0.3.0','max_client':'0.3.x'}
    @api.get('/health')
    @api.get('/api/v1/health')
    def get_health(): return health.snapshot()
    @api.get('/ready')
    @api.get('/api/v1/ready')
    def ready():
        x=health.snapshot(); return Response(status_code=200 if x['ready_for_new_risk'] else 503,content='ready' if x['ready_for_new_risk'] else 'not ready')
    @api.get('/metrics')
    def metrics(): return Response(generate_latest(),media_type=CONTENT_TYPE_LATEST)

    @api.post('/api/v1/auth/bootstrap-admin')
    def bootstrap_admin(req:BootstrapAdminRequest):
        svc=api.state.auth_service
        expected=api.state.bootstrap_token_hash
        if svc is None or not expected: raise HTTPException(403,'admin bootstrap disabled')
        supplied=hashlib.sha256(req.bootstrap_token.encode()).hexdigest()
        if not hmac.compare_digest(supplied,expected): raise HTTPException(403,'invalid bootstrap token')
        try: user_id=svc.bootstrap_admin(req.username,req.password)
        except (ValueError,PermissionError) as exc: raise HTTPException(409,str(exc)) from exc
        api.state.bootstrap_token_hash=None
        return {'user_id':user_id,'created':True}

    @api.post('/api/v1/auth/login')
    def login(req:LoginRequest,response:FastAPIResponse):
        svc=api.state.auth_service
        if svc is None: raise HTTPException(503,'authentication service unavailable')
        try: result=svc.login(req.username,req.password,req.mfa_code,req.recovery_code)
        except PermissionError as exc: raise HTTPException(401,str(exc)) from exc
        response.set_cookie(SESSION_COOKIE,result.session_token,httponly=True,secure=env==Environment.PROD,samesite='strict',max_age=getattr(svc,'ttl',3600),path='/')
        return {'csrf_token':result.csrf_token,'user_id':result.user_id,'role':result.role}

    @api.post('/api/v1/auth/logout')
    def logout(request:Request,response:FastAPIResponse):
        require(request,'viewer',True); token=request.cookies.get(SESSION_COOKIE,''); api.state.auth_service.revoke(token); response.delete_cookie(SESSION_COOKIE,path='/'); return {'ok':True}

    @api.get('/api/v1/auth/me')
    def me(request:Request):
        ctx=require(request,'viewer',False)
        if env==Environment.PROD:
            token=request.cookies.get(SESSION_COOKIE,'')
            ctx={**ctx,'csrf_token':api.state.auth_service.rotate_csrf(token)}
        else:
            ctx={**ctx,'csrf_token':'DEV_CSRF_BYPASS'}
        return ctx

    @api.post('/api/v1/auth/mfa/enroll')
    def mfa_enroll(req:MfaEnrollmentRequest,request:Request):
        ctx=require(request,'viewer',True)
        svc=api.state.auth_service
        try:
            secret=svc.begin_mfa_enrollment(ctx['user_id'],req.password)
        except PermissionError as exc:
            raise HTTPException(403,str(exc)) from exc
        label=f"CryptoTradingPlatform:{ctx.get('username','user')}"
        issuer='CryptoTradingPlatform'
        uri=f"otpauth://totp/{label}?secret={secret}&issuer={issuer}"
        return {'secret':secret,'otpauth_uri':uri,'message':'Secret yalnız bu enrollment aşamasında gösterilir.'}

    @api.post('/api/v1/auth/mfa/confirm')
    def mfa_confirm(req:MfaEnrollmentConfirmRequest,request:Request):
        ctx=require(request,'viewer',True)
        try:
            codes=api.state.auth_service.confirm_mfa_enrollment(ctx['user_id'],req.code)
        except PermissionError as exc:
            raise HTTPException(403,str(exc)) from exc
        return {'enabled':True,'recovery_codes':codes,"message":"Recovery code’ları şimdi güvenli biçimde saklayın; tekrar gösterilmez."}

    @api.post('/api/v1/auth/mfa/reset')
    def mfa_reset(req:MfaResetRequest,request:Request):
        ctx=require(request,'admin',True)
        if not api.state.confirmations.consume(req.confirmation_nonce,'RESET_MFA'):
            raise HTTPException(403,'invalid or expired RESET_MFA confirmation')
        try:
            api.state.auth_service.reset_mfa(req.target_user_id,ctx['user_id'],req.password)
        except (PermissionError,ValueError) as exc:
            raise HTTPException(403,str(exc)) from exc
        return {'reset':True,'target_user_id':req.target_user_id}

    def wizard_payload(snapshot):
        return {'setup_id':snapshot.setup_id,'current_step':snapshot.current_step,'completed_steps':list(snapshot.completed_steps),'non_secret_config':snapshot.non_secret_config,'completed':snapshot.completed,'startup_mode':snapshot.startup_mode}

    @api.get('/api/v1/setup')
    def setup_state(request:Request,setup_id:str='default'):
        ctx=require(request,'admin',False)
        svc=api.state.setup_service
        if svc is None: raise HTTPException(503,'setup service unavailable')
        return wizard_payload(svc.start_or_resume(ctx['user_id'],setup_id))

    @api.post('/api/v1/setup/step')
    def setup_step(req:SetupStepRequest,request:Request):
        require(request,'admin',True)
        svc=api.state.setup_service
        if svc is None: raise HTTPException(503,'setup service unavailable')
        try:
            return wizard_payload(svc.complete_step(req.setup_id,req.step,req.data))
        except LookupError as exc:
            raise HTTPException(404,str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(423,str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(422,str(exc)) from exc

    @api.post('/api/v1/auth/confirm-high-risk')
    def confirm_high_risk(req:HighRiskConfirmationRequest,request:Request):
        ctx=require(request,'admin',True)
        if req.action not in {'ENABLE_LIVE','PANIC_CLOSE','CHANGE_RISK_LIMITS','CHANGE_CREDENTIALS','RESET_MFA'}: raise HTTPException(422,'unsupported high-risk action')
        try: api.state.auth_service.reauthenticate(ctx['user_id'],req.password)
        except PermissionError as exc: raise HTTPException(403,str(exc)) from exc
        nonce=api.state.confirmations.issue(req.action,120)
        return {'confirmation_nonce':nonce,'expires_in_seconds':120,'action':req.action}

    @api.get('/api/v1/status')
    def status(request:Request): require(request); return {**trading_state,'mode':str(trading_state['mode']),'risk':str(trading_state['risk'])}
    @api.get('/api/v1/dashboard')
    def dashboard(request:Request):
        require(request)
        scanner_snapshot=api.state.runtime.scanner()
        recent_signals=api.state.runtime.signals()
        selected_market=None
        if recent_signals:
            try: selected_market=api.state.runtime.market(recent_signals[0]['symbol'])
            except KeyError: selected_market=None
        snap=build_dashboard_snapshot(mode=str(trading_state['mode']),health=health.snapshot(),scanner=scanner_snapshot,portfolio=api.state.runtime.portfolio(),risk_state=str(trading_state['risk']),selected_market=selected_market,recent_signals=recent_signals)
        return snap.to_dict()
    @api.get('/api/v1/market/{symbol}')
    def market(symbol:str,request:Request):
        require(request); 
        try: return api.state.runtime.market(symbol.upper())
        except KeyError as exc: raise HTTPException(404,'unknown symbol') from exc
    @api.get('/api/v1/signals')
    def signals(request:Request): require(request); return {'items':api.state.runtime.signals()}
    @api.get('/api/v1/signals/{symbol}')
    def signal(symbol:str,request:Request): require(request); return api.state.runtime.signal(symbol.upper())
    @api.get('/api/v1/positions')
    def positions(request:Request): require(request); return api.state.runtime.positions()
    @api.get('/api/v1/orders')
    def orders(request:Request): require(request); return api.state.runtime.orders()
    @api.get('/api/v1/portfolio')
    def portfolio(request:Request): require(request); return api.state.runtime.portfolio()
    @api.get('/api/v1/performance')
    def performance(request:Request): require(request); return {'status':'NO_DATA','message':'No persisted realized performance sample is available in this runtime.'}
    @api.get('/api/v1/risk')
    def risk(request:Request): require(request); return {'state':str(trading_state['risk']),'new_risk_allowed':trading_state['risk']==RiskState.NORMAL,'mode':str(trading_state['mode'])}
    @api.get('/api/v1/strategies')
    def strategies(request:Request): require(request); return {'items':[{'id':'deterministic-composite-v1','status':'RESEARCH_PAPER','live_approved':False}]}
    @api.get('/api/v1/universe')
    def universe(request:Request): require(request); return api.state.runtime.universe()
    @api.get('/api/v1/universe/{symbol}')
    def universe_symbol(symbol:str,request:Request): require(request); return next((x for x in api.state.runtime.universe()['items'] if x['symbol']==symbol.upper()),{'symbol':symbol.upper(),'eligible':False,'reasons':['UNKNOWN_SYMBOL']})
    @api.post('/api/v1/universe/refresh')
    def universe_refresh(req:TradingAction,request:Request): require(request,'trader',True); return api.state.runtime.universe()
    @api.get('/api/v1/scanner')
    def scanner(request:Request): require(request); return api.state.runtime.scanner()
    @api.post('/api/v1/scanner/run')
    def scanner_run(req:TradingAction,request:Request): require(request,'trader',True); return api.state.runtime.scanner()
    @api.get('/api/v1/assets/{asset}')
    def asset(asset:str,request:Request): require(request); return {'asset':asset.upper(),'source':api.state.runtime.source,'status':'KNOWN' if any(asset.upper() in x for x in api.state.runtime.exchange.list_markets()) else 'UNKNOWN'}
    @api.get('/api/v1/symbols/{symbol}/metadata')
    def symbol_metadata(symbol:str,request:Request): require(request); return api.state.runtime.symbol_metadata(symbol.upper())
    @api.get('/api/v1/portfolio/correlation')
    def correlation(request:Request): require(request); return {'status':'NO_DATA','matrix':{},'sample_count':0}
    @api.get('/api/v1/portfolio/concentration')
    def concentration(request:Request): require(request); return {'status':'NO_OPEN_POSITIONS' if not api.state.runtime.exchange.get_positions() else 'AVAILABLE','items':[]}
    @api.get('/api/v1/market-breadth')
    def breadth(request:Request): require(request); return api.state.runtime.scanner()['breadth']
    @api.post('/api/v1/analyze')
    def analyze_api(req:AnalyzeRequest,request:Request):
        require(request,'viewer',True)
        try: return analyze(req.candles,req.timeframe)
        except Exception as exc: raise HTTPException(422,str(exc)) from exc
    @api.post('/api/v1/analyze/multi-timeframe')
    def analyze_multi_timeframe_api(req:MultiTimeframeAnalyzeRequest,request:Request):
        require(request,'viewer',True)
        try:
            return analyze_multi_timeframe(req.candles_by_timeframe,req.weights)
        except Exception as exc:
            raise HTTPException(422,str(exc)) from exc

    @api.post('/api/v1/backtest')
    def backtest_api(req:BacktestRequest,request:Request):
        require(request,'trader',True)
        def sig(hist):
            if len(hist)<20:return 'HOLD'
            closes=[float(x['close']) for x in hist[-20:]]; return 'BUY' if closes[-1]>sum(closes)/len(closes) else 'SELL'
        return run(req.candles,sig,req.initial_equity,req.risk_fraction)
    @api.post('/api/v1/trading/start')
    def start(req:TradingAction,request:Request): require(request,'trader',True); trading_state['running']=True; return {'ok':True,'mode':trading_state['mode']}
    @api.post('/api/v1/trading/stop')
    def stop(req:TradingAction,request:Request): require(request,'trader',True); trading_state['running']=False; return {'ok':True}
    @api.post('/api/v1/trading/paper')
    def paper(req:TradingAction,request:Request): require(request,'trader',True); trading_state['mode']=TradingMode.PAPER; trading_state['running']=True; return {'ok':True,'mode':'PAPER'}
    @api.post('/api/v1/trading/testnet')
    def testnet(req:TradingAction,request:Request): require(request,'trader',True); trading_state['mode']=TradingMode.TESTNET; trading_state['running']=True; return {'ok':True,'mode':'TESTNET'}
    @api.post('/api/v1/trading/live')
    def live(req:LiveModeRequest,request:Request):
        require(request,'admin',True)
        if env!=Environment.PROD: raise HTTPException(403,'LIVE is only permitted in PROD')
        confirmed=api.state.confirmations.consume(req.confirmation_nonce,'ENABLE_LIVE')
        try: require_live_gate(TradingMode.LIVE,api.state.live_evidence,confirmed)
        except PermissionError as exc: raise HTTPException(423,str(exc)) from exc
        trading_state['mode']=TradingMode.LIVE; trading_state['running']=True
        return {'ok':True,'mode':'LIVE','label':'GERÇEK PARA'}
    @api.websocket('/api/v1/ws')
    async def ws(websocket:WebSocket):
        if env==Environment.PROD:
            svc=api.state.auth_service; token=websocket.cookies.get(SESSION_COOKIE)
            if svc is None or not token:
                await websocket.close(code=4401); return
            try: svc.authenticate(token,'viewer')
            except PermissionError:
                await websocket.close(code=4403); return
        await websocket.accept(); await websocket.send_json({'schema_version':1,'message_type':'status','sequence':1,'payload':{'mode':'PAPER','risk':'NORMAL'}}); await websocket.close()
    return api

def _read_secret(name:str)->str|None:
    file_name=os.getenv(f"{name}_FILE")
    if file_name:
        try: return Path(file_name).read_text(encoding="utf-8").strip()
        except OSError: return None
    value=os.getenv(name)
    return value.strip() if value else None

def build_app_from_env()->FastAPI:
    env=Environment(os.getenv("ENVIRONMENT","DEV").upper())
    if env!=Environment.PROD:
        return create_app(env)
    database_url=os.getenv("DATABASE_URL")
    engine=make_engine(database_url,pool_pre_ping=True) if database_url else None
    key=_read_secret("APP_ENCRYPTION_KEY")
    auth=None
    setup=None
    if engine is not None:
        sf=session_factory(engine)
        setup=SetupWizardService(sf)
        if key:
            try:
                auth=DatabaseAuthService(sf,SecretBox(key.encode()),int(os.getenv("SESSION_TTL_SECONDS","3600")),int(os.getenv("SESSION_INACTIVITY_SECONDS","900")))
            except Exception:
                auth=None
    health=HealthService.production(engine,os.getenv("REDIS_URL"),os.getenv("BINANCE_BASE_URL","https://api.binance.com"),float(os.getenv("MAX_CLOCK_DRIFT_SECONDS","2")))
    return create_app(env,auth_service=auth,bootstrap_token_hash=os.getenv("ADMIN_BOOTSTRAP_TOKEN_HASH"),setup_service=setup,health_service=health)

app=build_app_from_env()
