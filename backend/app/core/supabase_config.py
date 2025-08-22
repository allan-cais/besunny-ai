"""
Supabase configuration module for BeSunny.ai Python backend.
Handles Supabase client initialization, authentication, and database operations.
"""

import os
from typing import Optional, Dict, Any, List
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
import logging

logger = logging.getLogger(__name__)


class SupabaseConfig:
    """Supabase configuration and client management."""
    
    def __init__(self):
        self.supabase_url: Optional[str] = None
        self.supabase_anon_key: Optional[str] = None
        self.supabase_service_role_key: Optional[str] = None
        self.client: Optional[Client] = None
        self._initialized = False
        
        # Load configuration from environment
        self._load_config()
    
    def _load_config(self):
        """Load Supabase configuration from environment variables."""
        self.supabase_url = os.getenv('SUPABASE_URL') or os.getenv('VITE_SUPABASE_URL')
        self.supabase_anon_key = os.getenv('SUPABASE_ANON_KEY') or os.getenv('VITE_SUPABASE_ANON_KEY')
        self.supabase_service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('VITE_SUPABASE_SERVICE_ROLE_KEY')
        
        if not self.supabase_url:
            logger.warning("SUPABASE_URL not found in environment variables")
        if not self.supabase_anon_key:
            logger.warning("SUPABASE_ANON_KEY not found in environment variables")
        if not self.supabase_service_role_key:
            logger.warning("SUPABASE_SERVICE_ROLE_KEY not found in environment variables")
    
    def initialize(self) -> bool:
        """Initialize Supabase client."""
        if self._initialized:
            return True
        
        try:
            if not self.supabase_url or not self.supabase_anon_key:
                logger.error("Cannot initialize Supabase: missing URL or anon key")
                return False
            
            # Create client options
            options = ClientOptions(
                schema='public',
                headers={
                    'X-Client-Info': 'besunny-ai-python-backend'
                }
            )
            
            # Create Supabase client
            self.client = create_client(
                self.supabase_url,
                self.supabase_anon_key,
                options=options
            )
            
            # Test connection
            self._test_connection()
            
            self._initialized = True
            logger.info("Supabase client initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            return False
    
    def get_service_role_client(self) -> Optional[Client]:
        """Get Supabase client with service role key (bypasses RLS)."""
        try:
            if not self.supabase_url or not self.supabase_service_role_key:
                logger.error("Cannot create service role client: missing URL or service role key")
                return None
            
            # Create client options
            options = ClientOptions(
                schema='public',
                headers={
                    'X-Client-Info': 'besunny-ai-python-backend-service-role'
                }
            )
            
            # Create Supabase client with service role key
            service_client = create_client(
                self.supabase_url,
                self.supabase_service_role_key,
                options=options
            )
            
            logger.info("Service role Supabase client created successfully")
            return service_client
            
        except Exception as e:
            logger.error(f"Failed to create service role client: {e}")
            return None
    
    def _test_connection(self):
        """Test Supabase connection."""
        try:
            # Simple query to test connection
            response = self.client.table('users').select('id').limit(1).execute()
            logger.info("Supabase connection test successful")
        except Exception as e:
            logger.warning(f"Supabase connection test failed: {e}")
            # Don't fail initialization for connection test issues
    
    def get_client(self) -> Optional[Client]:
        """Get initialized Supabase client."""
        if not self._initialized:
            if not self.initialize():
                return None
        return self.client
    
    def is_initialized(self) -> bool:
        """Check if Supabase client is initialized."""
        return self._initialized
    
    def get_config_info(self) -> Dict[str, Any]:
        """Get configuration information."""
        return {
            "supabase_url": self.supabase_url,
            "has_anon_key": bool(self.supabase_anon_key),
            "has_service_role_key": bool(self.supabase_service_role_key),
            "initialized": self._initialized,
            "client_available": bool(self.client)
        }


# Global Supabase configuration instance
_supabase_config: Optional[SupabaseConfig] = None


def get_supabase_config() -> SupabaseConfig:
    """Get global Supabase configuration instance."""
    global _supabase_config
    if _supabase_config is None:
        _supabase_config = SupabaseConfig()
    return _supabase_config


def get_supabase_client() -> Optional[Client]:
    """Get initialized Supabase client."""
    config = get_supabase_config()
    return config.get_client()


def get_supabase_service_client() -> Optional[Client]:
    """Get Supabase client with service role key (bypasses RLS)."""
    config = get_supabase_config()
    return config.get_service_role_client()


def is_supabase_available() -> bool:
    """Check if Supabase is available and configured."""
    config = get_supabase_config()
    return config.is_initialized()


def get_supabase_url() -> Optional[str]:
    """Get Supabase URL."""
    config = get_supabase_config()
    return config.supabase_url


def get_supabase_anon_key() -> Optional[str]:
    """Get Supabase anonymous key."""
    config = get_supabase_config()
    return config.supabase_anon_key


def get_supabase_service_role_key() -> Optional[str]:
    """Get Supabase service role key."""
    config = get_supabase_config()
    return config.supabase_service_role_key


def get_supabase() -> Optional[Client]:
    """Get initialized Supabase client (alias for get_supabase_client)."""
    return get_supabase_client()
