from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
# Removed unused import: from sqlalchemy import UniqueConstraint


class SessionYearModel(models.Model):
    id = models.AutoField(primary_key=True)
    session_start_year = models.DateField()
    session_end_year = models.DateField()
    # objects = models.Manager() # This is the default, can be omitted

    def __str__(self):
        return f"{self.session_start_year.year} - {self.session_end_year.year}"


class CustomUser(AbstractUser):
    user_type_data = ((1, "HOD"), (2, "Staff"), (3, "Student"))
    user_type = models.CharField(default=1, choices=user_type_data, max_length=10)

    def __str__(self):
        return self.username


class AdminHOD(models.Model):
    id = models.AutoField(primary_key=True)
    # Renamed 'admin' to 'user' for clarity that it links to CustomUser
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    # Changed to DateTimeField for consistency
    updated_at = models.DateTimeField(auto_now=True) # Use auto_now=True for update time
    # objects = models.Manager() # Default

    def __str__(self):
        return self.user.username


class Staffs(models.Model):
    id = models.AutoField(primary_key=True)
    # Removed redundant email field - use CustomUser's email
    # Renamed 'admin' to 'user' for clarity
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    address = models.TextField()
    gender = models.CharField(max_length=255) # Consider using choices for gender
    state = models.CharField(max_length=50, help_text="state of origin")
    city = models.CharField(max_length=50, help_text="city of origin")
    fcm_token = models.TextField(default="", blank=True) # Added blank=True
    created_at = models.DateTimeField(auto_now_add=True)
    # Changed to DateTimeField for consistency
    updated_at = models.DateTimeField(auto_now=True)
    # objects = models.Manager() # Default

    def __str__(self):
        # Using full name from CustomUser is often better
        return f"{self.user.first_name} {self.user.last_name}"


class Courses(models.Model):
    id = models.AutoField(primary_key=True)
    course_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # objects = models.Manager() # Default

    def __str__(self):
        return self.course_name


class Subjects(models.Model):
    id = models.AutoField(primary_key=True)
    # Renamed course_id to course
    course = models.ForeignKey(Courses, on_delete=models.CASCADE, default=1) # on_delete=CASCADE is reasonable here
    # Changed staff_id to link to Staffs model for better structure
    staff = models.ForeignKey(Staffs, on_delete=models.DO_NOTHING) # Consider CASCADE or SET_NULL if staff are removed
    subject_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    # Changed to DateTimeField for consistency
    updated_at = models.DateTimeField(auto_now=True)
    # objects = models.Manager() # Default

    def __str__(self):
        return self.subject_name


class Students(models.Model):
    id = models.AutoField(primary_key=True)
    # Renamed admin to user for clarity
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    # Removed redundant email field - use CustomUser's email
    profile_pic = models.FileField(blank=True) # Added blank=True
    gender = models.CharField(max_length=255) # Consider using choices for gender
    address = models.TextField()
    # Changed age to IntegerField for better data type
    age = models.IntegerField(null=True, blank=True) # Added null/blank as age might not be required immediately
    # Renamed course_id to course and session_year_id to session_year
    # Changed on_delete for course - CASCADE is often more suitable here
    course = models.ForeignKey(Courses, on_delete=models.CASCADE)
    session_year = models.ForeignKey(SessionYearModel, on_delete=models.CASCADE)
    fcm_token = models.TextField(default="", blank=True) # Added blank=True
    created_at = models.DateTimeField(auto_now_add=True)
    # Changed to DateTimeField for consistency
    updated_at = models.DateTimeField(auto_now=True)
    # objects = models.Manager() # Default

    def __str__(self):
        # Using full name from CustomUser is often better
        return f"{self.user.first_name} {self.user.last_name}"


class Attendance(models.Model):
    id = models.AutoField(primary_key=True)
    # Renamed subject_id to subject
    # Consider CASCADE for on_delete here, as attendance without a subject is less meaningful
    subject = models.ForeignKey(Subjects, on_delete=models.CASCADE)
    attendance_date = models.DateField(auto_now_add=True) # auto_now_add is fine here
    # Renamed session_year_id to session_year
    session_year = models.ForeignKey(SessionYearModel, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # objects = models.Manager() # Default

    def __str__(self):
        return f"Attendance for {self.subject.subject_name} on {self.attendance_date}"


class AttendanceReport(models.Model):
    id = models.AutoField(primary_key=True)
    # Renamed student_id to student and attendance_id to attendance
    # Consider CASCADE for on_delete for student
    student = models.ForeignKey(Students, on_delete=models.CASCADE)
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE)
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # objects = models.Manager() # Default

    def __str__(self):
        status = "Present" if self.status else "Absent"
        return f"{self.student} - {self.attendance.subject.subject_name} ({status})"


class LeaveReportStudent(models.Model):
    id = models.AutoField(primary_key=True)
    # Renamed student_id to student
    student = models.ForeignKey(Students, on_delete=models.CASCADE)
    # Changed leave_date to DateField
    leave_date = models.DateField()
    leave_message = models.TextField()
    leave_status = models.BooleanField(default=False) # True for Approved, False for Pending/Rejected
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # objects = models.Manager() # Default

    def __str__(self):
        status = "Approved" if self.leave_status else "Pending/Rejected"
        return f"Leave for {self.student} on {self.leave_date} ({status})"


class LeaveReportStaff(models.Model):
    id = models.AutoField(primary_key=True)
    # Renamed staff_id to staff
    staff = models.ForeignKey(Staffs, on_delete=models.CASCADE)
    # Changed leave_date to DateField
    leave_date = models.DateField()
    leave_message = models.TextField()
    # Using choices for clarity
    LEAVE_STATUS_CHOICES = (
        (0, 'Pending'),
        (1, 'Approved'),
        (2, 'Rejected'),
    )
    leave_status = models.IntegerField(default=0, choices=LEAVE_STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # objects = models.Manager() # Default

    def __str__(self):
        status = dict(self.LEAVE_STATUS_CHOICES).get(self.leave_status, 'Unknown')
        return f"Leave for {self.staff} on {self.leave_date} ({status})"


class FeedBackStudent(models.Model):
    id = models.AutoField(primary_key=True)
    # Renamed student_id to student
    student = models.ForeignKey(Students, on_delete=models.CASCADE)
    feedback = models.TextField()
    # Made feedback_reply nullable and blank
    feedback_reply = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # objects = models.Manager() # Default

    def __str__(self):
        return f"Feedback from {self.student}"


class FeedBackStaffs(models.Model):
    id = models.AutoField(primary_key=True)
    # Renamed staff_id to staff
    staff = models.ForeignKey(Staffs, on_delete=models.CASCADE)
    feedback = models.TextField()
    # Made feedback_reply nullable and blank
    feedback_reply = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # objects = models.Manager() # Default

    def __str__(self):
        return f"Feedback from {self.staff}"


class NotificationStudent(models.Model):
    id = models.AutoField(primary_key=True)
    # Renamed student_id to student
    student = models.ForeignKey(Students, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # objects = models.Manager() # Default

    def __str__(self):
        return f"Notification for {self.student}"


class NotificationStaffs(models.Model):
    id = models.AutoField(primary_key=True)
    # Renamed staff_id to staff
    staff = models.ForeignKey(Staffs, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # objects = models.Manager() # Default

    def __str__(self):
        return f"Notification for {self.staff}"


class StudentResult(models.Model):
    id = models.AutoField(primary_key=True)
    # Renamed student_id to student and subject_id to subject
    student = models.ForeignKey(Students, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subjects, on_delete=models.CASCADE)
    fca_marks = models.FloatField(default=0)
    sca_marks = models.FloatField(default=0)
    # Note: Consider if grade_marks should be calculated or entered directly.
    # Using choices or a separate Grade model might be beneficial for complex grading.
    grade_marks = models.CharField(max_length=2, blank=True, null=True) # Increased max_length, added blank/null
    subject_assignment_marks = models.FloatField(default=0)
    subject_exam_marks = models.FloatField(default=0)
    overall_marks = models.FloatField(default=0) # Consider if this should be calculated automatically
    # Changed to DateTimeField for consistency
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # objects = models.Manager() # Default

    def __str__(self):
        return f"Result for {self.student} in {self.subject}"


class OnlineClassRoom(models.Model):
    id = models.AutoField(primary_key=True)
    room_name = models.CharField(max_length=255)
    # Note: Storing passwords directly is insecure. Consider alternative methods.
    room_pwd = models.CharField(max_length=255, help_text="Consider using a secure method for storing passwords.")
    # Renamed foreign keys
    subject = models.ForeignKey(Subjects, on_delete=models.CASCADE)
    session_year = models.ForeignKey(SessionYearModel, on_delete=models.CASCADE)
    # Link to Staffs model
    started_by = models.ForeignKey(Staffs, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    # objects = models.Manager() # Default

    def __str__(self):
        return f"Online Room: {self.room_name} ({self.subject.subject_name})"


# Signal Handlers: Updated to use new field names and be more robust

@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.user_type == 1:
            AdminHOD.objects.create(user=instance)
        elif instance.user_type == 2:
            # Provide default values for required fields
            Staffs.objects.create(user=instance, address="", gender="", state="", city="")
        elif instance.user_type == 3:
            # Handle potential absence of default Course or SessionYearModel
            try:
                default_course = Courses.objects.first() # Get the first course or handle appropriately
                default_session_year = SessionYearModel.objects.first() # Get the first session year or handle appropriately

                if default_course and default_session_year:
                    Students.objects.create(
                        user=instance,
                        course=default_course,
                        session_year=default_session_year,
                        address="",
                        profile_pic="",
                        gender=""
                    )
                else:
                    # Log a warning or raise an error if default objects are missing
                    print("WARNING: Default Course or SessionYearModel not found. Student profile not fully created.")
                    # Or create the student with null fields if they are nullable
                    # Students.objects.create(user=instance, address="", profile_pic="", gender="")

            except Exception as e:
                 print(f"Error creating student profile: {e}")
                 # Handle the errorappropriately (e.g., log it)


@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    try:
        if instance.user_type == 1:
            # Use the related_name if defined, otherwise the lowercase model name
            # Assuming default related_name: adminhod
            instance.adminhod.save()
        elif instance.user_type == 2:
             # Assuming default related_name: staffs
            instance.staffs.save()
        elif instance.user_type == 3:
             # Assuming default related_name: students
            instance.students.save()
    except AdminHOD.DoesNotExist:
        print(f"AdminHOD profile not found for user {instance.username}")
    except Staffs.DoesNotExist:
         print(f"Staffs profile not found for user {instance.username}")
    except Students.DoesNotExist:
         print(f"Students profile not found for user {instance.username}")
    except Exception as e:
         print(f"Error saving user profile for {instance.username}: {e}")