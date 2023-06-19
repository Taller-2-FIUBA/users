"""Application configuration."""
from environ import bool_var, config, var, group


@config(prefix="USERS")
class AppConfig:
    """Application configuration values from environment."""

    log_level = var("WARNING")
    prometheus_port = var(9001, converter=int)

    @config
    class DB:
        """Database configuration."""

        driver = var("postgresql")
        password = var("postgres")
        user = var("postgres")
        host = var("user_db")
        port = var(5432, converter=int)
        database = var("postgres")

    @config(prefix="MONGO")
    class Mongo:
        """MongoDB configuration."""

        driver = var("mongodb")
        user = var("fiufit")
        password = var("fiufit")
        host = var("cluster.mongodb.net")
        database = var("fiufit")

    @config
    class AUTH:
        """Authentication service configuration."""

        host = var("auth-svc")

    @config
    class PAYMENTS:
        """Payment service configuration."""

        host = var("localhost:8020")

    @config(prefix="SENTRY")
    class Sentry:
        """Sentry configuration."""

        enabled = bool_var(False)
        dsn = var("https://token@sentry.ingest.localhost")

    db = group(DB)  # type: ignore
    mongo = group(Mongo)
    payments = group(PAYMENTS)  # type: ignore
    auth = group(AUTH)  # type: ignore
    sentry = group(Sentry)
