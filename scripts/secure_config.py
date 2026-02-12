#!/usr/bin/env python3
"""Secure configuration manager for goyoonjung-wiki.
Loads all sensitive data from environment variables instead of hardcoded values.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

class SecureConfig:
    """Secure configuration manager that loads from environment variables."""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.config = {}
        self.load_config()
    
    def load_config(self):
        """Load configuration from YAML file with environment variable substitution."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            # Load YAML with environment variable substitution
            raw_config = yaml.safe_load(f)
            
        # Substitute environment variables
        self.config = self._substitute_env_vars(raw_config)
    
    def _substitute_env_vars(self, obj: Any) -> Any:
        """Recursively substitute environment variables in configuration."""
        if isinstance(obj, dict):
            return {k: self._substitute_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._substitute_env_vars(item) for item in obj]
        elif isinstance(obj, str) and obj.startswith('${') and obj.endswith('}'):
            # Extract environment variable name
            env_var = obj[2:-1]
            return os.getenv(env_var, obj)  # Return original if not found
        else:
            return obj
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (dot notation supported)."""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def validate_required_vars(self) -> bool:
        """Validate that all required environment variables are set."""
        required_vars = [
            'DISCORD_WEBHOOK_URL',
            'RSS_URL',
            'MAA_URL'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True
    
    def get_discord_webhook_url(self) -> str:
        """Get Discord webhook URL from environment."""
        webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        if not webhook_url:
            raise ValueError("DISCORD_WEBHOOK_URL environment variable is required")
        return webhook_url
    
    def get_rss_url(self) -> str:
        """Get RSS URL from environment."""
        rss_url = os.getenv('RSS_URL')
        if not rss_url:
            raise ValueError("RSS_URL environment variable is required")
        return rss_url
    
    def get_maa_url(self) -> str:
        """Get MAA URL from environment."""
        maa_url = os.getenv('MAA_URL')
        if not maa_url:
            raise ValueError("MAA_URL environment variable is required")
        return maa_url
    
    def get_performance_settings(self) -> Dict[str, Any]:
        """Get performance-related settings."""
        return {
            'max_concurrent_requests': int(os.getenv('MAX_CONCURRENT_REQUESTS', '6')),
            'request_timeout': int(os.getenv('REQUEST_TIMEOUT', '25')),
            'cache_ttl': int(os.getenv('CACHE_TTL', '3600'))
        }
    
    def get_system_settings(self) -> Dict[str, Any]:
        """Get system-related settings."""
        return {
            'timezone': os.getenv('TIMEZONE', 'Asia/Seoul'),
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'backup_retention_days': int(os.getenv('BACKUP_RETENTION_DAYS', '30'))
        }

def create_secure_config() -> SecureConfig:
    """Create and return a secure configuration instance."""
    return SecureConfig()

def validate_environment() -> bool:
    """Validate that the environment is properly configured."""
    config = create_secure_config()
    return config.validate_required_vars()

if __name__ == "__main__":
    config = create_secure_config()
    config.validate_required_vars()
    print("✅ Environment validation passed")
    print(f"Discord webhook configured: {'Yes' if config.get_discord_webhook_url() else 'No'}")
    print(f"RSS URL configured: {'Yes' if config.get_rss_url() else 'No'}")
    print(f"Performance settings: {config.get_performance_settings()}")