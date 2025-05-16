import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

def get_database_url():
    # If DATABASE_URL is explicitly set, use it
    if os.getenv("DATABASE_URL"):
        return os.getenv("DATABASE_URL")
    
    # Otherwise, construct from individual components
    return "postgresql://{}:{}@{}:{}/{}".format(
        os.getenv("DB_USER", "user"),
        os.getenv("DB_PASSWORD", "password"),
        os.getenv("DB_HOST", "localhost"),
        os.getenv("DB_PORT", "5432"),
        os.getenv("DB_NAME", "database")
    )

def init_database():
    """Initialize the database with the schema"""
    load_dotenv()
    
    # Create engine
    engine = create_engine(get_database_url())
    
    # Read and execute migration files
    migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
    for filename in sorted(os.listdir(migrations_dir)):
        if filename.endswith('.sql'):
            with open(os.path.join(migrations_dir, filename)) as f:
                sql = f.read()
                with engine.connect() as conn:
                    conn.execute(text(sql))
                    conn.commit()
                print(f"Executed migration: {filename}")

if __name__ == "__main__":
    init_database()
