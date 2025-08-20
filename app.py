from flask import Flask, request, redirect, jsonify, render_template_string
import json
import os
from datetime import datetime
import qrcode
import io
import base64
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key')

# Data storage paths
CAMPAIGNS_FILE = 'data/campaigns.json'
SCANS_FILE = 'data/scans.json'

# Ensure data directory exists
os.makedirs('data', exist_ok=True)

def load_json_file(filepath):
    """Load data from JSON file, return empty dict if file doesn't exist"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_json_file(filepath, data):
    """Save data to JSON file"""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)

@app.route('/')
def home():
    """Simple home page to test server"""
    return """
    <h1>QR Tracking Server</h1>
    <p>Server is running! 🚀</p>
    <p>Ready to track QR code scans.</p>
    """

@app.route('/scan/<campaign_id>')
def scan_qr(campaign_id):
    """Handle QR code scans - log data and redirect to target URL"""
    
    # Load campaigns to find target URL
    campaigns = load_json_file(CAMPAIGNS_FILE)
    
    if campaign_id not in campaigns:
        return f"Campaign {campaign_id} not found", 404
    
    # Get campaign details
    campaign = campaigns[campaign_id]
    target_url = campaign['target_url']
    
    # Collect scan data
    scan_data = {
        'campaign_id': campaign_id,
        'timestamp': datetime.now().isoformat(),
        'ip_address': request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr),
        'user_agent': request.headers.get('User-Agent', ''),
        'referrer': request.headers.get('Referer', ''),
        'method': request.method
    }
    
    # Log the scan
    scans = load_json_file(SCANS_FILE)
    if 'scans' not in scans:
        scans['scans'] = []
    
    scans['scans'].append(scan_data)
    save_json_file(SCANS_FILE, scans)
    
    # Redirect to target URL
    return redirect(target_url)

@app.route('/create_campaign', methods=['POST'])
def create_campaign():
    """Create a new tracking campaign"""
    data = request.get_json()
    
    if not data or 'business_name' not in data or 'target_url' not in data:
        return jsonify({'error': 'Missing required fields: business_name, target_url'}), 400
    
    # Generate campaign ID (simple approach for MVP)
    campaigns = load_json_file(CAMPAIGNS_FILE)
    campaign_count = len(campaigns)
    campaign_id = f"camp_{campaign_count + 1:04d}"
    
    # Create campaign
    campaign = {
        'campaign_id': campaign_id,
        'business_name': data['business_name'],
        'target_url': data['target_url'],
        'description': data.get('description', ''),
        'created_date': datetime.now().isoformat(),
        'status': 'active'
    }
    
    campaigns[campaign_id] = campaign
    save_json_file(CAMPAIGNS_FILE, campaigns)
    
    # Generate tracking URL
    base_url = os.getenv('BASE_URL', 'http://localhost:5000')
    tracking_url = f"{base_url}/scan/{campaign_id}"
    
    return jsonify({
        'success': True,
        'campaign_id': campaign_id,
        'tracking_url': tracking_url,
        'campaign': campaign
    })

@app.route('/campaigns')
def list_campaigns():
    """List all campaigns"""
    campaigns = load_json_file(CAMPAIGNS_FILE)
    return jsonify(campaigns)

@app.route('/campaign/<campaign_id>/stats')
def campaign_stats(campaign_id):
    """Get statistics for a specific campaign"""
    scans = load_json_file(SCANS_FILE)
    campaign_scans = [scan for scan in scans.get('scans', []) if scan['campaign_id'] == campaign_id]
    
    stats = {
        'campaign_id': campaign_id,
        'total_scans': len(campaign_scans),
        'scans': campaign_scans
    }
    
    return jsonify(stats)

@app.route('/generate_qr/<campaign_id>')
def generate_qr(campaign_id):
    """Generate QR code for a campaign"""
    campaigns = load_json_file(CAMPAIGNS_FILE)
    
    if campaign_id not in campaigns:
        return f"Campaign {campaign_id} not found", 404
    
    base_url = os.getenv('BASE_URL', 'http://localhost:5000')
    tracking_url = f"{base_url}/scan/{campaign_id}"
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(tracking_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for display
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_str = base64.b64encode(img_buffer.getvalue()).decode()
    
    return f"""
    <h2>QR Code for Campaign: {campaign_id}</h2>
    <p>Business: {campaigns[campaign_id]['business_name']}</p>
    <p>Tracking URL: {tracking_url}</p>
    <p>Target URL: {campaigns[campaign_id]['target_url']}</p>
    <img src="data:image/png;base64,{img_str}" alt="QR Code">
    """

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)