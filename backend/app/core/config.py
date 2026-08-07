from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    database_url_test: str = ""
    
    class Config:
        env_file = ".env"


settings = Settings()