#!/usr/bin/env python3
"""Test that .env file loads correctly."""

from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Get the API key
api_key = os.getenv("OPENAI_API_KEY")

if api_key:
    # Show first 20 and last 10 chars (masked for security)
    masked = api_key[:20] + "..." + api_key[-10:]
    print("✅ API Key loaded successfully!")
    print(f"   Key: {masked}")
    print()
    print("✅ Ready to use with OpenAI!")
else:
    print("❌ API Key not found in .env")
    print("   Make sure OPENAI_API_KEY is in your .env file")
