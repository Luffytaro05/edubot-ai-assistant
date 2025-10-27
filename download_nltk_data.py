#!/usr/bin/env python3
"""
NLTK Data Download Script for Deployment
Downloads required NLTK data files for the chatbot
"""

import nltk
import os
import sys

def download_nltk_data():
    """Download required NLTK data files"""
    print("📦 Downloading NLTK data files...")
    
    # List of required NLTK data
    required_data = [
        'punkt',
        'punkt_tab',  # Newer NLTK versions
        'wordnet',
        'averaged_perceptron_tagger',
        'stopwords',
        'omw-1.4'  # Open Multilingual Wordnet
    ]
    
    success_count = 0
    total_count = len(required_data)
    
    for data_name in required_data:
        try:
            print(f"📥 Downloading {data_name}...")
            nltk.download(data_name, quiet=True)
            print(f"✅ {data_name} downloaded successfully")
            success_count += 1
        except Exception as e:
            print(f"⚠️ Failed to download {data_name}: {e}")
            # Continue with other downloads
    
    print(f"\n📊 Download Summary: {success_count}/{total_count} packages downloaded")
    
    if success_count == total_count:
        print("🎉 All NLTK data downloaded successfully!")
        return True
    else:
        print("⚠️ Some NLTK data failed to download, but fallback methods will be used")
        return False

def verify_nltk_data():
    """Verify that NLTK data is available"""
    print("\n🔍 Verifying NLTK data...")
    
    try:
        # Test tokenization
        from nltk.tokenize import word_tokenize
        test_text = "Hello world! This is a test."
        tokens = word_tokenize(test_text)
        print(f"✅ Tokenization test passed: {tokens}")
        
        # Test stemming
        from nltk.stem import PorterStemmer
        stemmer = PorterStemmer()
        stemmed = stemmer.stem("running")
        print(f"✅ Stemming test passed: running -> {stemmed}")
        
        return True
        
    except Exception as e:
        print(f"❌ NLTK verification failed: {e}")
        return False

def main():
    """Main function"""
    print("🚀 NLTK Data Download Script")
    print("=" * 40)
    
    # Download data
    download_success = download_nltk_data()
    
    # Verify data
    verify_success = verify_nltk_data()
    
    if download_success and verify_success:
        print("\n🎉 NLTK setup completed successfully!")
        sys.exit(0)
    else:
        print("\n⚠️ NLTK setup completed with warnings")
        print("The application will use fallback methods for missing functionality")
        sys.exit(0)  # Still exit successfully as fallbacks are available

if __name__ == "__main__":
    main()
