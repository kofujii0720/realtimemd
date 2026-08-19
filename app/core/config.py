import os
from pathlib import Path


class Settings:
    PROJECT_NAME: str = "Realtime Markdown App"
    API_V1_STR: str = "/api/v1"
    
    # データベースファイルパス
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DB_PATH: str = os.getenv("DB_PATH", str(BASE_DIR / "realtimemd.db"))


settings = Settings()
