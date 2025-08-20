from flask import Flask, request, redirect, jsonify
import os
from datetime import datetime
import qrcode
import io
import base64
from dotenv import load_dotenv
from database import Database

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key')

# Initialize database
db = Database()

@app.before_first_request
def setup_database():
    """Setup database on first request"""
    if db.connect():
        db.create_tables()
        print("✅ Database connected and tables created")
    else:
        print("❌ Database connection failed - falling back to JSON")

@app.route('/')
def home():
    return """
    <h1>QR Tracking Server (PostgreSQL)</h1>
    <p>Server is running with database! 🚀</p>
    <p><a href="/migrate">Migrate JSON data</a></p>
    """

@app.route('/migrate')
def migrate_data():
    """Migrate existing JSON data to PostgreSQL"""
    try:
        db.migrate_json_data()
        return "✅ Data migration completed successfully!"
    except Exception as e:
        return f"❌ Migration failed: {e}", 500

@app.route('/scan/<campaign_id>')
def scan_qr(campaign_id):
    campaign = db.get_campaign(campaign_id)
    
    if not campaign:
        return f"Campaign {campaign_id} not found", 404
    
    # Log the scan
    ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    user_agent = request.headers.get('User-Agent', '')
    referrer = request.headers.get('Referer', '')
    
    db.log_scan(campaign_id, ip_address, user_agent, referrer)
    
    return redirect(campaign['target_url'])

@app.route('/create_campaign', methods=['POST'])
def create_campaign():
    data = request.get_json()
    
    if not data or 'business_name' not in data or 'target_url' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Generate campaign ID
    import time
    campaign_id = f"camp_{int(time.time())}"
    
    try:
        db.create_campaign(
            campaign_id,
            data['business_name'],
            data['target_url'],
            data.get('description', '')
        )
        
        base_url = os.getenv('BASE_URL', 'http://localhost:5000')
        tracking_url = f"{base_url}/scan/{campaign_id}"
        
        return jsonify({
            'success': True,
            'campaign_id': campaign_id,
            'tracking_url': tracking_url
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/campaign/<campaign_id>/stats')
def campaign_stats(campaign_id):
    try:
        stats = db.get_campaign_stats(campaign_id)
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate_qr/<campaign_id>')
def generate_qr(campaign_id):
    campaign = db.get_campaign(campaign_id)
    
    if not campaign:
        return f"Campaign {campaign_id} not found", 404
    
    base_url = os.getenv('BASE_URL', 'http://localhost:5000')
    tracking_url = f"{base_url}/scan/{campaign_id}"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(tracking_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_str = base64.b64encode(img_buffer.getvalue()).decode()
    
    stats = db.get_campaign_stats(campaign_id)
    
    return f"""
    <h2>QR Code: {campaign['business_name']}</h2>
    <p>Campaign ID: {campaign_id}</p>
    <p>Target: {campaign['target_url']}</p>
    <p>Total Scans: {stats['total_scans']} | Unique Visitors: {stats['unique_visitors']}</p>
    <img src="data:image/png;base64,{img_str}" alt="QR Code">
    """

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)