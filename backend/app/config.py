import os


def get_database_config() -> dict[str, object]:
    return {
        "host": os.getenv("DB_HOST", "127.0.0.1"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "database": os.getenv("DB_NAME", "business_dashboard"),
        "user": os.getenv("DB_USER", "dashboard_user"),
        "password": os.getenv("DB_PASSWORD", "dashboard_password"),
        "connection_timeout": 5,
    }


def get_cors_origins() -> list[str]:
    value = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    return [origin.strip() for origin in value.split(",") if origin.strip()]
