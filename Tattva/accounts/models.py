from django.db import models
from django.utils import timezone
from datetime import timedelta

# --- Utility Model ---

class OTP(models.Model):
    phone = models.CharField(max_length=20)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        # Checks if the OTP is older than 5 minutes
        return timezone.now() > self.created_at + timedelta(minutes=5)

    def __str__(self):
        return f"{self.phone} - {self.code}"

# --- Core Models ---

# Model for 'Patient' table
class Patient(models.Model):
    # 'id' is automatically created by Django as the primary key
    abha_id = models.BigIntegerField(unique=True, help_text="Unique ABHA ID for the patient.")
    name = models.TextField()
    blood_grp = models.TextField()
    age = models.BigIntegerField()
    phone = models.CharField(
        max_length=15, 
        null=True, 
        blank=True, 
        help_text="Patient's contact phone number."
    )
    # Storing large files/BLOBs in the database is generally discouraged. 
    # FileField/ImageField or cloud storage is better, but BinaryField used to match bytea.
    lab_report_file = models.BinaryField(
        blank=True,
        null=True,
        help_text="The actual lab report file (bytea/BLOB data)."
    )

    class Meta:
        verbose_name = "Patient"
        verbose_name_plural = "Patients"

    def __str__(self):
        return self.name

# Model for 'Doctor' table
class Doctor(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField()
    specification = models.TextField()
    # Foreign Key relations are usually better handled on the Booking/Hospital side.
    available = models.BooleanField(default=True) 
    pin = models.BigIntegerField(unique=True, help_text="Unique PIN associated with prescriptions.")
    
    # Store a default file format/template, if needed.
    prescription_file = models.BinaryField(
        blank=True,
        null=True,
        help_text="The default prescription format/file (bytea/BLOB data)."
    )

    class Meta:
        verbose_name = "Doctor"
        verbose_name_plural = "Doctors"

    def __str__(self):
        return f"Dr. {self.name} ({self.specification})"


# Model for 'Hospitals' table (Renamed to singular: Hospital)
class Hospital(models.Model):
    name = models.TextField(unique=True)
    revenue = models.BigIntegerField()
    # Appointments count, not a FK to a booking slot
    appointments = models.BigIntegerField(
        help_text="Total number of appointments."
    )
    availability = models.TextField(
        help_text="Availability status (e.g., 'Fully Staffed', 'Limited Beds')."
    )
    # BinaryField for a template/example file.
    lab_report_file = models.BinaryField(
        blank=True,
        null=True,
        help_text="General lab report file template/example."
    )
    
    # Many-to-Many field for a proper doctor/hospital relationship
    doctors = models.ManyToManyField(
        Doctor, 
        related_name="hospitals"
    )

    class Meta:
        verbose_name = "Hospital"
        verbose_name_plural = "Hospitals"

    def __str__(self):
        return self.name

# Model for 'Lab' table (Lab Report Entry)
class Lab(models.Model):
    # FIX 1: Lab must link to Patient. Using OneToOneField here because 
    # the original SQL had a UNIQUE constraint on lab.abha_id, implying
    # one lab entry per ABHA ID (or patient), which is a strange design. 
    # If a patient can have MANY lab reports, change this to ForeignKey.
    patient = models.OneToOneField( 
        Patient, 
        on_delete=models.CASCADE, 
        to_field='abha_id', # Link to the unique abha_id field in Patient
        primary_key=True # Using the patient's link as the primary key
    )
    
    lab_report_file = models.BinaryField(
        help_text="The actual lab report file (bytea/BLOB data)."
    )
    
    category = models.TextField()
    time = models.DateTimeField() 
    completed = models.BooleanField()
    
    # FIX 2: Add a proper Foreign Key to Hospital, as the Lab is done at a hospital/facility.
    hospital = models.ForeignKey(
        Hospital,
        on_delete=models.PROTECT,
        related_name="lab_results",
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "Lab Report"
        verbose_name_plural = "Lab Reports"
        # Removed unique_together since patient is now OneToOne/PK

    def __str__(self):
        return f"Lab Report for {self.patient.name} ({self.category})"


# Model for 'prescription' table (Renamed to singular: Prescription)
class Prescription(models.Model):
    # FIX 3: Removed pin as primary_key and reverted to auto-ID. 
    # pin is now a unique foreign key link to the Doctor.
    # The PIN should uniquely identify the doctor, not the prescription itself.
    
    patient = models.ForeignKey(
        Patient, 
        on_delete=models.CASCADE, 
        related_name="prescriptions"
    ) 
    doctor = models.ForeignKey(
        Doctor, 
        on_delete=models.PROTECT, 
        related_name="prescriptions"
    ) 
    
    category = models.TextField()
    prescription_file = models.BinaryField(
        help_text="The actual prescription file (bytea/BLOB data)."
    )
    
    # Store the doctor's unique PIN here for lookup, if necessary
    doctor_pin_lookup = models.BigIntegerField(
        help_text="The Doctor's unique PIN at the time of prescription."
    )

    class Meta:
        verbose_name = "Prescription"
        verbose_name_plural = "Prescriptions"

    def __str__(self):
        return f"Prescription for {self.patient.name} by Dr. {self.doctor.name}"


# Model for 'Booking' table
class Booking(models.Model):
    # Establishes relationship to Patient (The patient is doing the booking)
    patient = models.ForeignKey(
        Patient, 
        on_delete=models.CASCADE, 
        related_name="bookings"
    ) 
    # Establishes relationship to Doctor (The booking is with this doctor)
    doctor = models.ForeignKey(
        Doctor, 
        on_delete=models.PROTECT, 
        related_name="bookings"
    ) 
    # FIX 4: Add Foreign Key to Hospital (The hospital where the appointment takes place)
    hospital = models.ForeignKey(
        Hospital,
        on_delete=models.PROTECT,
        related_name="bookings",
        null=True,
        blank=True
    )
    
    disease = models.TextField()
    category = models.TextField()
    booked_slot = models.BigIntegerField() 
    availability = models.BooleanField()
    time = models.TimeField() 

    class Meta:
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"
        # Unique constraint for a real-world system: one doctor, one time slot, one day (implicitly by ID)
        unique_together = ('doctor', 'time', 'booked_slot') 

    def __str__(self):
        return f"Booking for {self.patient.name} with Dr. {self.doctor.name} at {self.time}"
    
    
    
    
    


from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import User
# Model for 'HospitalOwner' table

class HospitalOwner(models.Model):
    hospital = models.OneToOneField(
        Hospital,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='owner'
    )
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=50)  # PLAIN TEXT

    def __str__(self):
        return f"{self.username} ({self.hospital.name})"
