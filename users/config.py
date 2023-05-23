"""Application configuration."""
from environ import config, var, group


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
    class TEST:
        """Test configurations."""

        is_testing = var(True, converter=bool)
        user_id = var("magicword")
        role = var("admin")

    db = group(DB)  # type: ignore
    auth = group(AUTH)  # type: ignore
    test = group(TEST)  # type: ignore
