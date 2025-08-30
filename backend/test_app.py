#!/usr/bin/env python3
"""
Test script to check if the app can be imported and run.
"""

import sys
import os

print("Testing imports...")

try:
    print("1. Testing Flask import...")
    import flask
    print("   ✅ Flask imported successfully")
    
    print("2. Testing app import...")
    from app import create_app
    print("   ✅ App imported successfully")
    
    print("3. Creating app instance...")
    app = create_app('development')
    print("   ✅ App created successfully")
    
    print("4. Testing app configuration...")
    print(f"   Host: {app.config.get('HOST', 'localhost')}")
    print(f"   Port: {app.config.get('PORT', 5000)}")
    print(f"   Debug: {app.config.get('DEBUG', False)}")
    
    print("\n🎉 All tests passed! App should be ready to run.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
