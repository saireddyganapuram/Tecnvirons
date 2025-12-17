"""
Database module for Supabase client initialization.

This module provides the Supabase client instance used throughout the application
for all database operations. It handles connection setup and configuration.
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Validate environment variables
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "Missing Supabase credentials. Please set SUPABASE_URL and SUPABASE_KEY "
        "in your .env file. See .env.example for reference."
    )

# Initialize Supabase client
# This client is thread-safe and can be reused across the application
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_supabase_client() -> Client:
    """
    Get the Supabase client instance.
    
    Returns:
        Client: The initialized Supabase client
    """
    return supabase
