import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import json
import hashlib

class Database:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/qr_tracker')
        self.conn = None
    
    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False
    
    def create_tables(self):
        """Create database tables"""
        queries = [
            """
            CREATE TABLE IF NOT EXISTS campaigns (
                id SERIAL PRIMARY KEY,
                campaign_id VARCHAR(50) UNIQUE NOT NULL,
                business_name VARCHAR(255) NOT NULL,
                target_url TEXT NOT NULL,
                description TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20) DEFAULT 'active'
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS scans (
                id SERIAL PRIMARY KEY,
                campaign_id VARCHAR(50) REFERENCES campaigns(campaign_id),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address INET,
                user_agent TEXT,
                referrer TEXT,
                visitor_hash VARCHAR(64),
                country VARCHAR(50),
                city VARCHAR(100)
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_scans_campaign_id ON scans(campaign_id);
            CREATE INDEX IF NOT EXISTS idx_scans_timestamp ON scans(timestamp);
            CREATE INDEX IF NOT EXISTS idx_scans_visitor_hash ON scans(visitor_hash);
            """
        ]
        
        cursor = self.conn.cursor()
        for query in queries:
            cursor.execute(query)
        self.conn.commit()
        cursor.close()
    
    def create_campaign(self, campaign_id, business_name, target_url, description=""):
        """Create new campaign"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO campaigns (campaign_id, business_name, target_url, description) VALUES (%s, %s, %s, %s)",
            (campaign_id, business_name, target_url, description)
        )
        self.conn.commit()
        cursor.close()
    
    def get_campaign(self, campaign_id):
        """Get campaign by ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM campaigns WHERE campaign_id = %s", (campaign_id,))
        result = cursor.fetchone()
        cursor.close()
        return dict(result) if result else None
    
    def log_scan(self, campaign_id, ip_address, user_agent, referrer=""):
        """Log QR scan with unique visitor tracking"""
        visitor_hash = hashlib.sha256(f"{ip_address}:{user_agent}".encode()).hexdigest()
        
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO scans (campaign_id, ip_address, user_agent, referrer, visitor_hash) 
               VALUES (%s, %s, %s, %s, %s)""",
            (campaign_id, ip_address, user_agent, referrer, visitor_hash)
        )
        self.conn.commit()
        cursor.close()
    
    def get_campaign_stats(self, campaign_id):
        """Get campaign statistics"""
        cursor = self.conn.cursor()
        
        # Total scans
        cursor.execute("SELECT COUNT(*) as total_scans FROM scans WHERE campaign_id = %s", (campaign_id,))
        total_scans = cursor.fetchone()['total_scans']
        
        # Unique visitors
        cursor.execute("SELECT COUNT(DISTINCT visitor_hash) as unique_visitors FROM scans WHERE campaign_id = %s", (campaign_id,))
        unique_visitors = cursor.fetchone()['unique_visitors']
        
        # Recent scans
        cursor.execute("""
            SELECT timestamp, ip_address, user_agent 
            FROM scans WHERE campaign_id = %s 
            ORDER BY timestamp DESC LIMIT 10
        """, (campaign_id,))
        recent_scans = [dict(row) for row in cursor.fetchall()]
        
        cursor.close()
        return {
            'campaign_id': campaign_id,
            'total_scans': total_scans,
            'unique_visitors': unique_visitors,
            'recent_scans': recent_scans
        }
    
    def migrate_json_data(self):
        """Migrate existing JSON data to PostgreSQL"""
        # Load campaigns
        try:
            with open('data/campaigns.json', 'r') as f:
                campaigns = json.load(f)
            
            for campaign_id, campaign_data in campaigns.items():
                try:
                    self.create_campaign(
                        campaign_id,
                        campaign_data['business_name'],
                        campaign_data['target_url'],
                        campaign_data.get('description', '')
                    )
                except psycopg2.IntegrityError:
                    pass  # Campaign already exists
        except FileNotFoundError:
            print("No campaigns.json found to migrate")
        
        # Load scans
        try:
            with open('data/scans.json', 'r') as f:
                scans_data = json.load(f)
            
            for scan in scans_data.get('scans', []):
                self.log_scan(
                    scan['campaign_id'],
                    scan['ip_address'],
                    scan['user_agent'],
                    scan.get('referrer', '')
                )
        except FileNotFoundError:
            print("No scans.json found to migrate")
        
        self.conn.commit()
        print("JSON data migration completed")
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()