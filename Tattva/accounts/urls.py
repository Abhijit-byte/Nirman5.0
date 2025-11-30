# In your app's urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # --- PATIENT FLOW (Frontend) ---
    path('', views.landing, name='landing'),
    path('send_otp_page/', views.send_otp_page, name='send_otp_page'),
    path('verify_otp_page/', views.verify_otp_page, name='verify_otp_page'),
    path('dashboard/', views.dashboard, name='dashboard'), 
    path("hospital_loginpage/", views.hospital_owner_login_page, name="hospital_loginpage"),
    path('doctors_loginpage/', views.doctors_loginpage_view, name='doctors_loginpage'),
    path('doctor_booking/', views.doctor_booking_page, name='doctor_booking_page'),
    path('pharmacy_booking/', views.pharmacy_login, name='pharmacy_login'),
    # --- Patient/Doctor APIs ---
    path('check_patient_exists/', views.check_patient_exists, name='check_patient_exists'),
    path('send_otp/', views.send_otp, name='send_otp'),
    path('verify_otp/', views.verify_otp, name='verify_otp'),
    path('api/doctor/availability/', views.update_doctor_availability, name='update_doctor_availability'),
    
    # --- HOSPITAL OWNER FLOW (Admin) ---
    path('login/', views.render_hospital_login, name='hospital_login_page'), # 1. Render Login Page
    path('api/login/', views.hospital_owner_login_api, name='hospital_owner_login_api'), # 2. Login API
    
    # 3. Hospital Owner Dashboard View (The one that renders the HTML)
    # THIS IS THE VIEW THAT PASSES THE ID TO THE TEMPLATE
    path('accounts/dashboard/admin/<int:hospital_id>/', 
         views.hospital_owner_dashboard, 
         name='hospital_owner_dashboard'),
    
    # 4. Hospital Dashboard Data API Endpoint (The one the JavaScript calls)
    path('api/hospitaldashboard/<int:hospital_id>/', 
         views.get_dashboard_data, 
         name='get_filtered_dashboard_data'),
         
    # --- DOCTOR FLOW ---
    path('doctorsdashboard/<int:hospital_id>/', 
         views.doctor_dashboard_view, 
         name='doctors_dashboard'),
    
    path("doctor_login/", views.doctor_login, name="doctor_login"),
path("doctor/dashboard/", views.doctor_dashboard, name="doctor_dashboard"),
path("doctor/update-availability/", views.update_doctor_availability, name="update_doctor_availability"),
path("api/doctor/availability/", views.update_doctor_availability, name="update_doctor_availability"),
path("pharmacy/dashboard/", views.pharmacy_dashboard, name="pharmacy_dashboard"),
path("lab_login/", views.lab_login, name="lab_login"),
path("lab/dashboard/", views.lab_dashboard, name="lab_dashboard"),
path("medical_records/", views.medical_records, name="medical_records"),
path("labs/", views.labs, name="labs"),
path("records/", views.records, name="records"),
path("payment/", views.payment, name="payment"),
path("emi_payment/", views.emi_payment, name="emi_payment"),
path("ai_bill_analyzer/", views.ai_bill_analyzer, name="ai_bill_analyzer"),


]