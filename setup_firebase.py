#!/usr/bin/env python
"""
Firebase setup script for scraper notifications
"""

import os
import json

def create_firebase_service_account_template():
    """Create a template for Firebase service account JSON"""
    template = {
        "type": "service_account",
        "project_id": "your-project-id",
        "private_key_id": "your-private-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY_HERE\n-----END PRIVATE KEY-----\n",
        "client_email": "your-service-account@your-project-id.iam.gserviceaccount.com",
        "client_id": "your-client-id",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project-id.iam.gserviceaccount.com"
    }
    
    if not os.path.exists("firebase-service-account.json"):
        with open("firebase-service-account.json", "w") as f:
            json.dump(template, f, indent=2)
        print("✅ Created firebase-service-account.json template")
        print("📝 Please update it with your actual Firebase credentials")
    else:
        print("⚠️ firebase-service-account.json already exists")

def test_firebase_connection():
    """Test Firebase connection"""
    try:
        from firebase_notifier import FirebaseNotifier
        FirebaseNotifier.send_notification(
            title="Test Notification",
            body="Firebase setup test successful!",
            data={"test": "true"}
        )
        print("✅ Firebase test notification sent successfully!")
        return True
    except Exception as e:
        print(f"❌ Firebase test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔥 Setting up Firebase for scraper notifications...")
    
    # Create service account template
    create_firebase_service_account_template()
    
    # Test connection
    print("\n🧪 Testing Firebase connection...")
    if test_firebase_connection():
        print("\n🎉 Firebase setup complete!")
    else:
        print("\n⚠️ Firebase setup incomplete - please check your credentials")