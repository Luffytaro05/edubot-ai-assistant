#!/usr/bin/env python3
"""
Setup script for TCC Assistant with Vector Search
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def install_requirements():
    """Install required packages"""
    print("\n📦 Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Packages installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install packages: {e}")
        return False

def check_environment_variables():
    """Check if required environment variables are set"""
    print("\n🔧 Checking environment variables...")
    
    required_vars = {
        'PINECONE_API_KEY': 'Pinecone API key for vector database',
        'MONGODB_URI': 'MongoDB connection string (optional - default provided)'
    }
    
    missing_vars = []
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if var == 'PINECONE_API_KEY' and not value:
            missing_vars.append((var, description))
            print(f"⚠️  {var}: Not set - {description}")
        elif value:
            print(f"✅ {var}: Set")
    
    if missing_vars:
        print("\n⚠️  Warning: Some environment variables are missing.")
        print("To set them, run:")
        for var, description in missing_vars:
            if var == 'PINECONE_API_KEY':
                print(f"export {var}='your-pinecone-api-key-here'")
        print("\nThe chatbot will work without Pinecone, but vector search will be disabled.")
    
    return len(missing_vars) == 0

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = [
        'static/images',
        'templates',
        'logs'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def download_nltk_data():
    """Download required NLTK data"""
    print("\n📚 Downloading NLTK data...")
    try:
        import nltk
        nltk.download('punkt', quiet=True)
        print("✅ NLTK data downloaded")
        return True
    except Exception as e:
        print(f"❌ Failed to download NLTK data: {e}")
        return False

def test_imports():
    """Test if all required packages can be imported"""
    print("\n🧪 Testing imports...")
    
    test_packages = [
        ('torch', 'PyTorch'),
        ('sentence_transformers', 'Sentence Transformers'),
        ('pinecone', 'Pinecone'),
        ('flask', 'Flask'),
        ('nltk', 'NLTK'),
        ('pymongo', 'PyMongo')
    ]
    
    failed_imports = []
    
    for package, name in test_packages:
        try:
            __import__(package)
            print(f"✅ {name}")
        except ImportError:
            print(f"❌ {name}")
            failed_imports.append(name)
    
    if failed_imports:
        print(f"\n❌ Failed to import: {', '.join(failed_imports)}")
        print("Run 'pip install -r requirements.txt' to install missing packages")
        return False
    
    return True

def create_env_template():
    """Create .env template file"""
    print("\n📄 Creating .env template...")
    
    env_template = """# TCC Assistant Environment Variables
# Copy this file to .env and fill in your actual values

# Pinecone Configuration
PINECONE_API_KEY=pcsk_3LGtPm_F7RyLr4yFTu4C7bbEonvRcCxysxCztU9ADjyRefakqjq7wxqjJXVwt5JD5TeM62
PINECONE_ENVIRONMENT=us-east-1-aws

# MongoDB Configuration (optional - default provided in code)
MONGODB_URI=mongodb+srv://dxtrzpc26:w1frwdiwmW9VRItO@cluster0.gskdq3p.mongodb.net/

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
"""
    
    env_file = Path('.env.template')
    if not env_file.exists():
        env_file.write_text(env_template)
        print("✅ Created .env.template file")
    else:
        print("✅ .env.template already exists")

def print_next_steps():
    """Print next steps for the user"""
    print("\n" + "="*50)
    print("🎉 Setup completed! Next steps:")
    print("="*50)
    
    print("\n1. Set up your Pinecone account:")
    print("   - Go to https://www.pinecone.io/")
    print("   - Create an account and get your API key")
    print("   - Set the environment variable:")
    print("     export PINECONE_API_KEY=pcsk_3LGtPm_F7RyLr4yFTu4C7bbEonvRcCxysxCztU9ADjyRefakqjq7wxqjJXVwt5JD5TeM62")
    
    print("\n2. Train the model:")
    print("   python train.py")
    
    print("\n3. Run the application:")
    print("   python app.py")
    
    print("\n4. Open your browser and visit:")
    print("   http://localhost:5000")
    
    print("\n📝 Notes:")
    print("   - The chatbot will work without Pinecone, but vector search will be disabled")
    print("   - Check the logs for any issues")
    print("   - Modify intents.json to customize responses")
    
    print("\n🔗 Useful links:")
    print("   - Pinecone Documentation: https://docs.pinecone.io/")
    print("   - Sentence Transformers: https://www.sbert.net/")

def main():
    """Main setup function"""
    print("🚀 TCC Assistant Setup")
    print("="*30)
    
    success = True
    
    # Check Python version
    success &= check_python_version()
    
    # Install requirements
    success &= install_requirements()
    
    # Test imports
    success &= test_imports()
    
    # Download NLTK data
    success &= download_nltk_data()
    
    # Create directories
    create_directories()
    
    # Create environment template
    create_env_template()
    
    # Check environment variables
    env_vars_ok = check_environment_variables()
    
    if success:
        print("\n✅ Setup completed successfully!")
        if not env_vars_ok:
            print("⚠️  Note: Some environment variables need to be configured.")
        print_next_steps()
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()