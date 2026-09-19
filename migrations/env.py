from alembic import context
from prediction_terminal.config import Settings
from prediction_terminal.persistence.database import database
from prediction_terminal.persistence.tables import metadata

if context.is_offline_mode():
    context.configure(url=Settings().database_url, target_metadata=metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = database(Settings().database_url)
    with engine.connect() as connection:
        context.configure(
            connection=connection, target_metadata=metadata, render_as_batch=engine.dialect.name == "sqlite"
        )
        with context.begin_transaction():
            context.run_migrations()
