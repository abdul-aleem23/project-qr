import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_workflow():
    """Test the complete QR tracking workflow"""
    
    print("🚀 Testing QR Tracking Workflow")
    print("=" * 50)
    
    # Step 1: Create a campaign
    print("\n1. Creating a campaign for Joe's Pizza...")
    campaign_data = {
        "business_name": "Joe's Pizza",
        "target_url": "https://joespizza.com/august-promo",
        "description": "August promotion flyer campaign"
    }
    
    response = requests.post(f"{BASE_URL}/create_campaign", json=campaign_data)
    if response.status_code == 200:
        campaign_result = response.json()
        campaign_id = campaign_result['campaign_id']
        tracking_url = campaign_result['tracking_url']
        
        print(f"✅ Campaign created successfully!")
        print(f"   Campaign ID: {campaign_id}")
        print(f"   Tracking URL: {tracking_url}")
    else:
        print(f"❌ Failed to create campaign: {response.text}")
        return
    
    # Step 2: Show QR code generation
    print(f"\n2. QR Code can be viewed at: {BASE_URL}/generate_qr/{campaign_id}")
    
    # Step 3: Simulate QR scans
    print(f"\n3. Simulating QR code scans...")
    
    # Simulate multiple scans
    for i in range(3):
        print(f"   Scan {i+1}...")
        try:
            # This will redirect, so we'll get a redirect response
            response = requests.get(tracking_url, allow_redirects=False)
            if response.status_code in [301, 302]:
                print(f"   ✅ Scan {i+1} logged successfully (redirected to {response.headers.get('Location')})")
            else:
                print(f"   ⚠️  Unexpected response: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error during scan: {e}")
        
        time.sleep(1)  # Small delay between scans
    
    # Step 4: Check campaign statistics
    print(f"\n4. Checking campaign statistics...")
    response = requests.get(f"{BASE_URL}/campaign/{campaign_id}/stats")
    if response.status_code == 200:
        stats = response.json()
        print(f"✅ Campaign Stats:")
        print(f"   Total scans: {stats['total_scans']}")
        for i, scan in enumerate(stats['scans'], 1):
            print(f"   Scan {i}: {scan['timestamp']} from {scan['ip_address']}")
    else:
        print(f"❌ Failed to get stats: {response.text}")
    
    # Step 5: List all campaigns
    print(f"\n5. Listing all campaigns...")
    response = requests.get(f"{BASE_URL}/campaigns")
    if response.status_code == 200:
        campaigns = response.json()
        print(f"✅ Total campaigns: {len(campaigns)}")
        for camp_id, camp_data in campaigns.items():
            print(f"   {camp_id}: {camp_data['business_name']}")
    else:
        print(f"❌ Failed to list campaigns: {response.text}")
    
    print(f"\n🎉 Workflow test completed!")
    print(f"📊 View QR code at: {BASE_URL}/generate_qr/{campaign_id}")

if __name__ == "__main__":
    print("Make sure Flask server is running (python app.py)")
    print("Press Enter to continue with the test...")
    input()
    test_workflow()