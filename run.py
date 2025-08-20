#!/usr/bin/env python3
"""
Quick start script for the QR tracking server
"""
import os
import sys

def main():
    print("🚀 Starting QR Tracking Server...")
    print("=" * 40)
    
    # Check if data directory exists
    if not os.path.exists('data'):
        print("📁 Creating data directory...")
        os.makedirs('data')
    
    print("🌐 Server will be available at: http://localhost:5000")
    print("📊 Available endpoints:")
    print("   GET  /                        - Home page")
    print("   GET  /scan/<campaign_id>      - Track QR scan")
    print("   POST /create_campaign         - Create new campaign")
    print("   GET  /campaigns               - List all campaigns")
    print("   GET  /campaign/<id>/stats     - Get campaign stats")
    print("   GET  /generate_qr/<id>        - Generate QR code")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 40)
    
    # Import and run the Flask app
    from app import app
    app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == "__main__":
    main()