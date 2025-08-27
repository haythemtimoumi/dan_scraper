import firebase_admin
from firebase_admin import credentials, messaging
import os
from datetime import datetime

class FirebaseNotifier:
    _initialized = False
    
    @classmethod
    def initialize(cls):
        if not cls._initialized:
            try:
                cred = credentials.Certificate("firebase-service-account.json")
                firebase_admin.initialize_app(cred)
                cls._initialized = True
            except Exception as e:
                print(f"Firebase initialization failed: {e}")
    
    @classmethod
    def send_notification(cls, title, body, data=None):
        try:
            cls.initialize()
            if not cls._initialized:
                return
            
            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                topic='scraper_updates',
                data=data or {}
            )
            response = messaging.send(message)
            print(f'Firebase notification sent: {response}')
        except Exception as e:
            print(f'Firebase notification failed: {e}')