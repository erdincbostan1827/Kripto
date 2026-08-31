from __future__ import annotations
from pathlib import Path
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex,CreateTable
from app.database.models import Base

def main():
    dialect=postgresql.dialect()
    statements=[]
    for table in Base.metadata.sorted_tables:
        statements.append(str(CreateTable(table).compile(dialect=dialect)).strip())
        for index in sorted(table.indexes,key=lambda x:x.name or ''):
            statements.append(str(CreateIndex(index).compile(dialect=dialect)).strip())
    Path('database/schema.sql').write_text(';\n\n'.join(statements)+';\n',encoding='utf-8')
    print(f'wrote {len(Base.metadata.tables)} tables')
if __name__=='__main__': main()
