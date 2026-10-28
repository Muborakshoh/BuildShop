from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from sqlalchemy import make_url

from app.core.config import settings
from app.db.session import Base


# Fix SSL for Render PostgreSQL
def get_database_url():
    url = make_url(settings.database_url)
    if "render.com" in str(url) and "sslmode" not in url.query:
        url = url.update_query_dict({"sslmode": "require"})
    return str(url)

# Import models so SQLAlchemy metadata is complete.
from app.auth import models as _auth_models  # noqa: F401
from app.auth import repository as _auth_repository  # noqa: F401
from app.cashier import models as _cashier_models  # noqa: F401
from app.cms import models as _cms_models  # noqa: F401
from app.inventory import models as _inventory_models  # noqa: F401
from app.orders import models as _orders_models  # noqa: F401
from app.products import models as _products_models  # noqa: F401
from app.users import models as _users_models  # noqa: F401
from app.reviews import models as _reviews_models  # noqa: F401
from app.promos import models as _promos_models  # noqa: F401
from app.delivery import models as _delivery_models  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", get_database_url())

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    from sqlalchemy import create_engine
    connectable = create_engine(get_database_url(), poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
