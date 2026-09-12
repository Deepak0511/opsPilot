# config/settings.py
__author__ = "Deepak Kumar Chaudhary <deepak.techprofile@gmail.com>"

# Imports to avail OS-level utilities, cross platform easy path browsing, 
# parsing yaml files, and reading .env file.
import os
from pathlib import Path
import yaml
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# A lightweight container class to hold and supply configs and environment variables.
class Settings:
    """
    ops_pilot.config.settings
    -------------------------
    Thin loader for a YAML configuration file and for exposing selected
    environment variables (e.g. API keys) as a dictionary‑like object.
    Typical usage
    ~~~~~~~~~~~~~
    >>> from ops_pilot.config.settings import settings
    >>> settings["openai_api_key"]      # returns the value from .env or None
    >>> settings["some_yaml_key"]      # value read from config.yaml

    Attributes
    ----------
    config : dict
        Combined YAML and environment-based configuration.

    Author
    ------
    Deepak Kumar Chaudhary <deepak.techprofile@gmail.com>
    """
    def __init__(self):
        """
        Initialise the Settings instance.
        * Resolve the path to ``config.yaml`` next to this file.
        * Load the YAML content via :meth:`_load_yaml`.
        * Pull selected environment variables and store them in ``self.config``.
        """
        config_path = Path(__file__).parent / "config.yaml"
        self.config = self._load_yaml(config_path)
        
        # Merge with environment variables
        self.config["env_openai_api_key"] = os.getenv("OPENAI_API_KEY")
        self.config["env_gemini_api_key"] = os.getenv("GEMINI_API_KEY")
        self.config["env_huggingface_api_key"] = os.getenv("HUGGINGFACE_API_KEY")
        self.config["env_data_dir"] = os.getenv("DATA_DIR", "./data")
        #self.config["env_db_path"] = os.getenv("DB_PATH", f"{self.config['env_data_dir']}/ops_pilot.db")
        self.config["env_db_path"] = os.path.expandvars(os.environ["DB_PATH"])
        
        # Resolve log_dir relative to project root
        project_root = Path(__file__).parent.parent.parent.parent
        log_dir_relative = self.config.get("log_dir", "../tmp/ops_pilot/logs")
        self.config["env_log_dir"] = str((project_root / log_dir_relative).resolve())

    def _load_yaml(self, path):
        """
        Load a YAML file safely.
        Parameters
        ----------
        path : pathlib.Path or str
            Path to the YAML configuration file.
        Returns
        -------
        dict
            Parsed YAML content (or ``None`` if the file is empty).
        Raises
        ------
        FileNotFoundError
            If ``path`` does not point to an existing file.
        yaml.YAMLError
            If the file contains invalid YAML.
        """
        with open(path, 'r') as f:
            return yaml.safe_load(f)

    def __getitem__(self, key):
        """
        Dictionary‑style access to the underlying configuration.
        Parameters
        ----------
        key : str
            The configuration key you want to retrieve.
        Returns
        -------
        Any
            The value associated with ``key`` or ``None`` if the key is missing.
        """
        return self.config.get(key)

lookup_for_setting = Settings()
