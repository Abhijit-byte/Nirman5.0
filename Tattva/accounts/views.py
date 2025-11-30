from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum 
import random
import re
import json
import requests
from datetime import datetime

# CORE IMPORTS
from .models import Patient, HospitalOwner, Hospital, Doctor, Booking 

# In-memory storage for OTPs (Use database model for production)
otp_storage = {}

# ----------------------------------------------------------------------
# --- PATIENT FLOW VIEWS (OTP-based) ---
# ----------------------------------------------------------------------
def landing(request):
    return render(request, 'accounts/landing.html')
def send_otp_page(request):
    return render(request, 'accounts/send_otp.html')
def doctors_loginpage_view(request):
    return render(request, 'accounts/doctors_loginpage.html')
def verify_otp_page(request):
    return render(request, 'accounts/verify_otp.html')
def hospital_owner_login_page(request):
    return render(request, 'accounts/hospital_loginpage.html')
def doctor_booking_page(request):
    return render(request, 'accounts/doctor_booking.html')
def pharmacy_login(request):
    return render(request, 'accounts/pharmacy_loginpage.html')
def pharmacy_dashboard(request):
    return render(request, 'accounts/pharmacy_dashboard.html')
def lab_login(request):
    return render(request, 'accounts/lab_loginpage.html')
def lab_dashboard(request):
    return render(request, 'accounts/lab_dashboard.html')
def medical_records(request):
    return render(request, 'accounts/Medicine.html')
def labs(request):
    return render(request, 'accounts/Labs.html')
def records(request):
    return render(request, 'accounts/records.html')
def emi_payment(request):
    return render(request, 'accounts/emi.html')
def ai_bill_analyzer(request):
    return render(request, 'accounts/aibill.html')
def payment(request):
    return render(request, 'accounts/payment.html')
def doctor_dashboard(request):
    doctor_id = request.session.get("doctor_id")


    if not doctor_id:
        return redirect("doctor_login")  # protection if session empty

    doctor = Doctor.objects.get(id=doctor_id)

    return render(request, "accounts/doctors_dashboard.html", {
        "doctor_name": doctor.name,
    })


def send_otp_page(request):
    return render(request, 'accounts/send_otp.html')

def verify_otp_page(request):
    return render(request, 'accounts/verify_otp.html')

from django.shortcuts import render, redirect
from accounts.models import Patient # Adjust the import path for your Patient model

def dashboard(request):
    # Patient Dashboard - Requires phone session key
    
    # 1. Check if the user is logged in
    if 'phone' not in request.session:
        return redirect('/')
        
    phone_number = request.session.get('phone')
    
    # 2. Retrieve the Patient object from the database
    try:
        current_patient = Patient.objects.get(phone=phone_number)
    except Patient.DoesNotExist:
        # Handle case: User is logged in but patient record is missing (shouldn't happen)
        # We can log them out or redirect to an error page.
        # For security, we'll redirect back home.
        return redirect('/')

    # 3. Pass the Patient object to the template context
    return render(request, 'accounts/dashboard.html', {
        'patient': current_patient,
        # The phone number is now easily accessible via patient.phone
    })

@require_http_methods(["POST"])
@csrf_exempt
def check_patient_exists(request):
    """Checks if a patient with the given phone number exists in the database."""
    try:
        data = json.loads(request.body)
        phone = data.get("phone", "").strip()

        if not phone or not re.match(r"^\d{10}$", phone):
            return JsonResponse({'exists': False, 'message': 'Invalid phone number'}, status=400)

        patient_exists = Patient.objects.filter(phone=phone).exists()
        
        return JsonResponse({'exists': patient_exists})
    
    except Exception as e:
        return JsonResponse({'exists': False, 'message': f'Internal Server Error: {str(e)}'}, status=500)

@require_http_methods(["POST"])
@csrf_exempt
def send_otp(request):
    try:
        data = json.loads(request.body)
        phone = data.get("phone", "").strip()
        
        if not phone or not re.match(r"^\d{10}$", phone):
            return JsonResponse({"status": "error", "message": "Invalid phone number"})
        
        if not Patient.objects.filter(phone=phone).exists():
             return JsonResponse({
                "status": "error", 
                "message": "Patient not found. Registration required."
            }, status=403) 
        
        # Generate OTP
        otp = str(random.randint(100000, 999999))
        otp_storage[phone] = otp
        
        # 🌟 RESTORED CONSOLE PRINT FOR TESTING 🌟
        print(f"\n{'='*50}")
        print(f"📱 OTP for {phone}: {otp}")
        print(f"{'='*50}\n")
        # 🌟 ------------------------------------- 🌟
        
        # (Ultramsg sending logic remains the same)
        instance_id = getattr(settings, 'ULTRAMSG_INSTANCE_ID', None)
        token = getattr(settings, 'ULTRAMSG_TOKEN', None)
        
        if instance_id and token:
            try:
                url = f"https://api.ultramsg.com/{instance_id}/messages/chat"
                payload = {
                    "token": token,
                    "to": f"91{phone}",
                    "body": f"🔐 Your LifeCord OTP is: *{otp}*\n\nThis code is valid for 5 minutes.\n\nDo not share this code with anyone.\n\n- LifeCord Team"
                }
                requests.post(url, data=payload, timeout=10)
            except Exception:
                pass

        return JsonResponse({"status": "success", "message": "OTP sent successfully"})
    
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})

@require_http_methods(["POST"])
@csrf_exempt
def verify_otp(request):
    try:
        data = json.loads(request.body)
        phone = data.get("phone", "").strip()
        otp = data.get("otp", "").strip()
        
        if phone in otp_storage and otp_storage[phone] == otp:
            del otp_storage[phone]
            request.session["phone"] = phone
            return JsonResponse({"status": "success", "message": "OTP verified"})
        else:
            return JsonResponse({"status": "error", "message": "Invalid or expired OTP"})
    
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})

# ----------------------------------------------------------------------
# --- HOSPITAL OWNER FLOW VIEWS (Password-based, Filtered by ID) ---
# ----------------------------------------------------------------------

#@login_required 
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login 
from .models import HospitalOwner, Hospital # Assuming these models exist

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login 
 # Ensure HospitalAccess model is used

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login 
# Import both your CustomUser model (for staff) and Hospital model

# We will use the Hospital model itself to store the facility-level password for simplicity, 
# or you can use a dedicated HospitalAccess model if preferred.

# In LIFE-CORD/accounts/views.py

import json
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login 
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

# In LIFE-CORD/mobile_otp_login/accounts/views.py

import json
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login 
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
# Import the specific models needed
from .models import HospitalOwner, Hospital 
# NOTE: If you are not using Django's main auth system, you will need a 
# Custom Authentication Backend or use session management manually. 
# For simplicity, we assume you have a generic User model (e.g., CustomUser) 
# to link to the session for @login_required to work, but we will focus on 
# the HospitalOwner check only.

# In LIFE-CORD/mobile_otp_login/accounts/views.py

import json
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login 
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
# Import the specific models needed from your existing models.py
from .models import HospitalOwner, Hospital, HospitalOwner


# --- RENDER VIEW (To open the login page) ---
# In LIFE-CORD/mobile_otp_login/accounts/views.py

import json
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
# --- FIXED IMPORT ---
from django.contrib.auth.models import User
from .models import HospitalOwner, Hospital 
# --------------------


# --- RENDER VIEW (No change) ---
def render_hospital_login(request):
    """Renders the main hospital login page."""
    return render(request, 'accounts/hospital_loginpage.html')


# --- DEDICATED API VIEW (Hospital Owner Only) ---
@csrf_exempt
def hospital_owner_login_api(request):
    if request.method != 'POST':
        return JsonResponse({'message': 'Only POST requests are allowed.'}, status=405)

    try:
        data = json.loads(request.body)
        owner_username = data.get('nin') # Using 'nin' from frontend as the username/login_id
        password = data.get('password')
    except json.JSONDecodeError:
        return JsonResponse({'message': 'Invalid JSON format'}, status=400)

    # --- AUTHENTICATION: HOSPITAL OWNER LOGIN ---
    try:
        # 1. Look up the HospitalOwner record by username
        owner_instance = HospitalOwner.objects.get(username=owner_username)

        # 🚨 WARNING: INSECURE PASSWORD CHECK! (Kept as per constraint)
        if owner_instance.password == password:

            # Hospital Owner Login SUCCESS
            hospital_id = owner_instance.hospital.id

            # 2. Log in the associated specific User account for session tracking
            # ASSUMPTION: The HospitalOwner has a corresponding Django User (User model) 
            # with the same username for session tracking.
            try:
                # Use the imported Django 'User' model
                system_user = User.objects.get(username=owner_username)
                login(request, system_user) # Establish Django session
            except User.DoesNotExist:
                return JsonResponse({'message': 'Owner account found, but session user is missing (User model).'}, status=500)

            # 3. Redirect the owner to the specialized admin dashboard
            redirect_url = f'/accounts/dashboard/admin/{hospital_id}/'

            return JsonResponse({
                'message': f'Facility Access Granted: {owner_instance.hospital.name}',
                'redirectUrl': redirect_url
            }, status=200)

        else:
             # Password mismatch
             raise HospitalOwner.DoesNotExist # Fails the check, jumps to final failure block

    except HospitalOwner.DoesNotExist:
        # No HospitalOwner found or password mismatch
        pass

    # --- FINAL FAILURE ---
    return JsonResponse({'message': 'Invalid ID or Password.'}, status=401)


# --- DASHBOARD VIEW (Authorization Enforced) ---
@login_required
def hospital_owner_dashboard(request, hospital_id):
    """Checks for both authentication (@login_required) and authorization (ID/Role)."""

    # 1. Get the Hospital instance
    hospital = get_object_or_404(Hospital, id=hospital_id)

    # 2. Authorization Check: Ensure the logged-in user is the actual owner of this hospital
    try:
        # Retrieve the HospitalOwner instance associated with the requested Hospital
        owner_instance = HospitalOwner.objects.get(hospital=hospital)

        # Check if the logged-in User's username matches the HospitalOwner's username
        if request.user.username != owner_instance.username:
            # User is logged in, but not as the owner of this specific hospital
            return HttpResponseForbidden("Access Denied: Not the authorized Hospital Owner.")

    except HospitalOwner.DoesNotExist:
        # Hospital has no linked owner record
        return HttpResponseForbidden("Configuration Error: Hospital Owner not defined.")


    # Authorization Passed
    return render(request, 'accounts/hospitaldashboard.html', {
        'hospital_id': hospital_id,          # <--- ADD THIS LINE
        'hospital_name': hospital.name,      # <--- ADDED hospital_name for the HTML title/topbar
        'owner_username': request.user.username
    })
    # ----------------------------------------------------------------------
# --- DASHBOARD API VIEW (WITH FILTERING) ---
# ----------------------------------------------------------------------

@require_http_methods(["GET"])
def get_dashboard_data(request, hospital_id): 
    """Fetches dashboard data filtered by the provided hospital_id."""
    try:
        # 1. Get the target Hospital (Used as the filtering criteria)
        hospital = Hospital.objects.get(id=hospital_id)
        
        # --- Filtering all queries based on the Hospital instance ---
        
        # 2. Appointments Count 
        # Assumes Booking is linked to Hospital via doctor__hospitals M2M link
        appointments_count = Booking.objects.filter(doctor__hospitals=hospital).count() 
        
        # 3. Doctors Data (Filtered)
        doctors_data = []
        # Note: If this line crashes, you need to populate data in your database
        doctors_qs = hospital.doctors.all()[:4] 

        for doc in doctors_qs:
            next_slot_time = "—"
            status_text = "Off"
            status_class = "off"
            
            if doc.available:
                status_class = "online"
                status_text = "Online"
                
                # Filter bookings for the future
                next_booking = doc.bookings.filter(time__gt=datetime.now().time()).order_by('time').first() 
                if next_booking:
                    next_slot_time = f"Today, {next_booking.time.strftime('%I:%M %p')}"
                    status_class = "busy"
                    status_text = "Busy"
            
            doctors_data.append({
                'name': doc.name,
                'spec': doc.specification,
                'slot': next_slot_time,
                'status': status_class,
                'status_text': status_text,
            })

        # 4. Upcoming Appointments (Filtered by Hospital)
        upcoming_bookings = Booking.objects.select_related('patient', 'doctor') \
            .filter(doctor__hospitals=hospital, availability=True, time__gt=datetime.now().time()) \
            .order_by('time')[:2]
        
        upcoming_data = []
        for booking in upcoming_bookings:
            upcoming_data.append({
                'patient': booking.patient.name,
                'doc': booking.doctor.name,
                'time': booking.time.strftime('%A, %I:%M %p'),
                'status': 'Confirmed', 
            })

        # --- Combine all data ---
        dashboard_data = {
            'kpis': {
                # This requires 'revenue' field on the Hospital model
                'revenue_today': f"₹ {hospital.revenue:,.0f}", 
                'appointments_count': appointments_count,
            },
            'doctors': doctors_data,
            'upcoming': upcoming_data,
            'charts': {
                'appointments_7d': { 
                    'labels': ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'], 
                    'booked': [34,28,36,30,40,22,20],
                    'walkin': [12,8,10,6,14,8,4]
                },
            }
        }

        return JsonResponse(dashboard_data)

    except Hospital.DoesNotExist:
        return JsonResponse({'error': 'Hospital not found'}, status=404)
    except Exception as e:
        # If a model attribute is missing (e.g., Hospital.revenue), it will hit here
        return JsonResponse({'error': f'Internal Server Error: {str(e)}'}, status=500)
    
# views.py (Add this function)

@require_http_methods(["POST"])
@csrf_exempt
def update_doctor_availability(request):
    """Updates the 'available' status of the logged-in doctor."""
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Not authenticated'}, status=401)
    
    try:
        # 1. Get the current Doctor profile linked to the user
        # NOTE: You need a one-to-one relationship from User to Doctor for this to work.
        doctor = get_object_or_404(Doctor, user=request.user)
    except Doctor.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Doctor profile not found'}, status=404)

    try:
        data = json.loads(request.body)
        new_status = data.get("is_available") # True or False
        
        # 2. Update the status
        doctor.available = new_status
        doctor.save()
        
        return JsonResponse({'status': 'success', 'is_available': doctor.available})
        
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON format'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
# views.py (Rename the old function to doctor_dashboard_view)

def doctor_dashboard_view(request, hospital_id): # <-- NEW NAME HERE
    """Renders the unsecured Doctor's Command Center (for testing)."""
    try:
        hospital = get_object_or_404(Hospital, id=hospital_id)
    except Hospital.DoesNotExist:
        return JsonResponse({'error': f'Hospital with ID {hospital_id} not found'}, status=404) 

    # Renders the doctor's specific template
    return render(request, 'accounts/doctors_dashboard.html', {
        'hospital_id': hospital_id,
        'hospital_name': hospital.name
    })

# NOTE: The API view `get_dashboard_data` is fine as it is.


from django.http import JsonResponse
from django.contrib import messages
import json

def doctor_login(request):
    if request.method == "POST":
        data = json.loads(request.body)
        doc_id = data.get("doc_id")
        pin = data.get("pin")

        doctor = Doctor.objects.filter(id=doc_id, pin=pin).first()

        if doctor:
            request.session["doctor_id"] = doctor.id
            request.session["doctor_name"] = doctor.name  # store name in session

            return JsonResponse({
                "status": "success",
                "doctor_name": doctor.name,                 # pass to JS
                "redirect_url": "/doctor/dashboard/"        # your path
            })

        return JsonResponse({"status": "error", "message": "Invalid ID or PIN"})
    
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

@csrf_exempt
@require_http_methods(["POST"])
def update_doctor_availability(request):
    try:
        doctor_id = request.session.get("doctor_id")
        if not doctor_id:
            return JsonResponse({"status": "error", "message": "Not logged in"}, status=401)

        data = json.loads(request.body)
        status = data.get("is_available")

        doctor = Doctor.objects.get(id=doctor_id)
        doctor.available = status
        doctor.save()

        return JsonResponse({"status": "success", "is_available": doctor.available})

    except Doctor.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Doctor not found"}, status=404)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


