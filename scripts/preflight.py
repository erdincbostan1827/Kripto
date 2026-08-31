from __future__ import annotations
import os,shutil,sys
checks={'python_3_12':sys.version_info[:2]>=(3,12),'disk_space':shutil.disk_usage('/').free>512*1024*1024,'mode_safe':os.getenv('MODE','PAPER')!='LIVE' or (os.getenv('ENVIRONMENT')=='PROD' and os.getenv('LIVE_TRADING_ENABLED')=='true')}
print(checks)
raise SystemExit(0 if all(checks.values()) else 2)
