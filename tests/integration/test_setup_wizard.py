from sqlalchemy.pool import StaticPool
from app.database.session import make_engine, init_db, session_factory
from app.services.setup_wizard import SetupWizardService


def service():
    e=make_engine('sqlite+pysqlite:///:memory:',connect_args={'check_same_thread':False},poolclass=StaticPool); init_db(e); return e,SetupWizardService(session_factory(e))

def test_wizard_resumes_and_never_persists_secrets():
    e,s=service(); x=s.start_or_resume('u'); s.complete_step(x.setup_id,1,{'server':'local','password':'must-not-persist'}); y=s.start_or_resume('u'); assert y.completed_steps==(1,) and 'password' not in y.non_secret_config['step_1']; e.dispose()

def test_wizard_requires_sequential_steps():
    e,s=service(); s.start_or_resume();
    try: s.complete_step('default',2,{}); ok=False
    except ValueError: ok=True
    assert ok; e.dispose()

def test_wizard_requires_final_preflight_and_forces_paper():
    e,s=service(); s.start_or_resume()
    for step in range(1,8): s.complete_step('default',step,{'requested_mode':'LIVE'} if step==4 else {})
    try: s.complete_step('default',8,{'preflight_ok':False}); ok=False
    except PermissionError: ok=True
    assert ok
    z=s.complete_step('default',8,{'preflight_ok':True}); assert z.completed and z.startup_mode=='PAPER'; e.dispose()
