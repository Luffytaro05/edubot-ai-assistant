#!/usr/bin/env python3
"""
Railway deployment startup script
Creates necessary files and checks dependencies
"""

import os
import sys
import subprocess

def check_dependencies():
    """Check if all required packages are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'flask', 'pymongo', 'torch', 'nltk', 'deep-translator', 
        'langdetect', 'sentence-transformers', 'pinecone'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
        print("Installing missing packages...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
            print("✅ Packages installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install packages: {e}")
            return False
    
    return True

def create_fallback_model():
    """Create fallback model if data.pth doesn't exist"""
    if not os.path.exists("data.pth"):
        print("📦 Creating fallback model...")
        try:
            from create_fallback_model import create_fallback_model
            if create_fallback_model():
                print("✅ Fallback model created")
            else:
                print("❌ Failed to create fallback model")
        except Exception as e:
            print(f"❌ Error creating fallback model: {e}")

def check_environment():
    """Check Railway environment variables"""
    print("\n🔧 Checking environment variables...")
    
    # Check for Railway-specific variables
    port = os.getenv('PORT')
    if port:
        print(f"✅ PORT: {port}")
    else:
        print("⚠️ PORT not set (Railway should set this)")
    
    # Check for optional variables
    mongodb_uri = os.getenv('MONGODB_URI')
    if mongodb_uri:
        print("✅ MONGODB_URI: Set")
    else:
        print("⚠️ MONGODB_URI: Using default")
    
    pinecone_key = os.getenv('PINECONE_API_KEY')
    if pinecone_key:
        print("✅ PINECONE_API_KEY: Set")
    else:
        print("⚠️ PINECONE_API_KEY: Not set (vector search disabled)")

def main():
    """Main startup function"""
    print("🚀 Railway Deployment Startup")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Dependency check failed")
        sys.exit(1)
    
    # Create fallback model
    create_fallback_model()
    
    # Check environment
    check_environment()
    
    print("\n✅ Railway startup checks completed")
    print("🚀 Starting Flask application...")

if __name__ == "__main__":
    main()
