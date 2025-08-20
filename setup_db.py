#!/usr/bin/env python3
"""
Database setup script for QR Tracker
"""
import os
from database import Database
from dotenv import load_dotenv

def main():
    load_dotenv()
    
    print("🗄️  Setting up PostgreSQL database...")
    print("=" * 40)
    
    # Check if PostgreSQL URL is configured
    db_url = os.getenv('DATABASE_URL')
    if 'username:password' in db_url:
        print("⚠️  Please update DATABASE_URL in .env file with actual credentials")
        print("   Format: postgresql://username:password@localhost:5432/qr_tracker")
        return
    
    db = Database()
    
    if db.connect():
        print("✅ Connected to PostgreSQL")
        
        # Create tables
        db.create_tables()
        print("✅ Database tables created")
        
        # Migrate existing JSON data if it exists
        if os.path.exists('data/campaigns.json') or os.path.exists('data/scans.json'):
            print("📦 Migrating existing JSON data...")
            db.migrate_json_data()
            print("✅ Data migration completed")
        
        db.close()
        print("🎉 Database setup complete!")
        print("\nNext steps:")
        print("1. Run: python app_db.py")
        print("2. Test: python test_workflow.py")
        
    else:
        print("❌ Failed to connect to PostgreSQL")
        print("\nTroubleshooting:")
        print("1. Install PostgreSQL")
        print("2. Create database: createdb qr_tracker")
        print("3. Update DATABASE_URL in .env")

if __name__ == "__main__":
    main()