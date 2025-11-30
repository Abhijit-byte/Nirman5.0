import requests
from django.conf import settings

def send_whatsapp_otp(phone, otp):
    """
    Send OTP via Ultramsg WhatsApp API
    
    Args:
        phone (str): Phone number with country code (e.g., '919876543210')
        otp (str): 6-digit OTP code
    
    Returns:
        dict: Response from Ultramsg API
    """
    
    # Ultramsg API endpoint
    instance_id = settings.ULTRAMSG_INSTANCE_ID
    token = settings.ULTRAMSG_TOKEN
    
    if not instance_id or not token:
        print("❌ Ultramsg credentials not configured!")
        return {"status": "error", "message": "API credentials missing"}
    
    url = f"https://api.ultramsg.com/{instance_id}/messages/chat"
    
    # Format phone number (add country code if not present)
    if not phone.startswith('91'):
        phone = '91' + phone
    
    # Message payload
    payload = {
        "token": token,
        "to": phone,
        "body": f"🔐 Your LifeCord OTP is: *{otp}*\n\nThis code is valid for 5 minutes.\n\nDo not share this code with anyone.\n\n- LifeCord Team"
    }
    
    try:
        response = requests.post(url, data=payload)
        result = response.json()
        
        if response.status_code == 200 and result.get('sent') == 'true':
            print(f"✅ OTP sent successfully to {phone}")
            return {"status": "success", "data": result}
        else:
            print(f"❌ Failed to send OTP: {result}")
            return {"status": "error", "message": result.get('error', 'Unknown error')}
    
    except Exception as e:
        print(f"❌ Exception sending OTP: {str(e)}")
        return {"status": "error", "message": str(e)}
