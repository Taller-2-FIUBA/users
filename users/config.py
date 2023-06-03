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
        host = "localhost"
        port = var(5432, converter=int)
        database = var("postgres")

    @config
    class AUTH:
        """Authentication service configuration."""

        host = "localhost:8002"

    @config
    class PAYMENTS:
        """Payment service configuration."""

        host = "localhost:8020"

    @config(prefix="SENTRY")
    class Sentry:
        """Sentry configuration."""

        enabled = bool_var(False)
        dsn = var("https://token@sentry.ingest.localhost")

    db = group(DB)  # type: ignore
    payments = group(PAYMENTS)  # type: ignore
    auth = group(AUTH)  # type: ignore
    sentry = group(Sentry)
