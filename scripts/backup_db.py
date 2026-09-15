import os
import shutil
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
project_root = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=project_root / ".env")

def backup_databases():
    # Resolve paths from environment variables
    data_dir_env = os.getenv("DATA_DIR", "./data")
    
    # Handle variable expansion if DB_PATH uses ${DATA_DIR}
    db_path_env = os.path.expandvars(os.getenv("DB_PATH", f"{data_dir_env}/ops_pilot.db"))
    checkpoint_db_path_env = os.path.expandvars(os.getenv("CHECKPOINT_DB_PATH", f"{data_dir_env}/ops_pilot_agent_state.db"))
    
    # Create absolute paths
    db_path = Path(db_path_env)
    if not db_path.is_absolute():
        db_path = project_root / db_path
        
    checkpoint_db_path = Path(checkpoint_db_path_env)
    if not checkpoint_db_path.is_absolute():
        checkpoint_db_path = project_root / checkpoint_db_path
        
    # Create backups directory
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Backup ops_pilot.db
    if db_path.exists():
        backup_file = backup_dir / f"ops_pilot_{timestamp}.db"
        shutil.copy2(db_path, backup_file)
        print(f"Backed up {db_path.name} to {backup_file}")
        
        # Backup WAL and SHM if they exist
        wal_path = Path(f"{db_path}-wal")
        shm_path = Path(f"{db_path}-shm")
        if wal_path.exists():
            shutil.copy2(wal_path, backup_dir / f"ops_pilot_{timestamp}.db-wal")
        if shm_path.exists():
            shutil.copy2(shm_path, backup_dir / f"ops_pilot_{timestamp}.db-shm")
    else:
        print(f"Could not find {db_path.name} at {db_path}")
        
    # Backup ops_pilot_agent_state.db
    if checkpoint_db_path.exists():
        checkpoint_backup_file = backup_dir / f"ops_pilot_agent_state_{timestamp}.db"
        shutil.copy2(checkpoint_db_path, checkpoint_backup_file)
        print(f"Backed up {checkpoint_db_path.name} to {checkpoint_backup_file}")
        
        # Backup WAL and SHM if they exist
        wal_path = Path(f"{checkpoint_db_path}-wal")
        shm_path = Path(f"{checkpoint_db_path}-shm")
        if wal_path.exists():
            shutil.copy2(wal_path, backup_dir / f"ops_pilot_agent_state_{timestamp}.db-wal")
        if shm_path.exists():
            shutil.copy2(shm_path, backup_dir / f"ops_pilot_agent_state_{timestamp}.db-shm")
    else:
        print(f"Could not find {checkpoint_db_path.name} at {checkpoint_db_path}")

if __name__ == "__main__":
    print("Starting database backup...")
    backup_databases()
    print("Backup complete!")
