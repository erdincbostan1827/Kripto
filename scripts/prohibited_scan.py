from pathlib import Path
import ast,re,sys
bad=[]
for p in [*Path('backend').rglob('*.py'),*Path('frontend').rglob('*.ts'),*Path('frontend').rglob('*.tsx')]:
    text=p.read_text(encoding='utf-8')
    if re.search(r'\b(TODO|FIXME|NotImplementedError)\b',text): bad.append(str(p))
    if p.suffix=='.py':
        tree=ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node,ast.Pass): bad.append(f'{p}:pass@{node.lineno}')
print('PASS' if not bad else '\n'.join(bad)); raise SystemExit(1 if bad else 0)
