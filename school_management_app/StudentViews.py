import datetime
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404 # Import get_object_or_404
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
# Assuming html_to_pdf is correctly implemented elsewhere
from school_management_app.process import html_to_pdf

from school_management_app.models import (Students, Courses, StudentResult, Subjects,
                                         CustomUser, OnlineClassRoom, Attendance,
                                         AttendanceReport, LeaveReportStudent,
                                         FeedBackStudent, NotificationStudent, SessionYearModel)

# --- Student Home View ---
def student_home(request):
    # Get the student's profile linked to the logged-in user
    # Use get_object_or_404 for safety, use the new field name 'user'
    student_obj = get_object_or_404(Students, user=request.user)

    # Filter using the new field name 'student'
    attendance_total = AttendanceReport.objects.filter(student=student_obj).count()
    attendance_present = AttendanceReport.objects.filter(student=student_obj, status=True).count()
    attendance_absent = AttendanceReport.objects.filter(student=student_obj, status=False).count()

    # Access related course using the new field name 'course'
    course = student_obj.course
    # Filter subjects using the new field name 'course'
    subjects = Subjects.objects.filter(course=course).count()
    # subjects_data = Subjects.objects.filter(course=course) # Redundant if not used directly

    # Access related session year using the new field name 'session_year'
    session_obj = student_obj.session_year

    subject_name = []
    data_present = []
    data_absent = []
    # Filter subjects using the new field name 'course'
    subject_data = Subjects.objects.filter(course=student_obj.course)
    for subject in subject_data:
        # Filter Attendance using the new field name 'subject'
        attendance = Attendance.objects.filter(subject=subject)
        # Filter AttendanceReport using new field names 'attendance' and 'student'
        attendance_present_count = AttendanceReport.objects.filter(
            attendance__in=attendance,
            status=True,
            student=student_obj
        ).count()
        attendance_absent_count = AttendanceReport.objects.filter(
            attendance__in=attendance,
            status=False,
            student=student_obj
        ).count()
        subject_name.append(subject.subject_name)
        data_present.append(attendance_present_count)
        data_absent.append(attendance_absent_count)

    return render(request, "student_template/student_home_template.html", {
        "total_attendance": attendance_total,
        "attendance_absent": attendance_absent,
        "attendance_present": attendance_present,
        "subjects": subjects, # This count might not be what the template expects vs. subjects_data
        "data_name": subject_name,
        "data1": data_present,
        "data2": data_absent
    })

# --- Student View Attendance ---
def student_view_attendance(request):
    # Get the student's profile
    student = get_object_or_404(Students, user=request.user)
    # Access related course using the new field name 'course'
    course = student.course
    # Filter subjects using the new field name 'course'
    subjects = Subjects.objects.filter(course=course)
    return render(request, "student_template/student_view_attendance.html", {"subjects": subjects})

# --- Student View Attendance Post (Filtering Attendance) ---
def student_view_attendance_post(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("student_view_attendance")) # Redirect if not POST

    subject_id = request.POST.get("subject")
    start_date = request.POST.get("start_date")
    end_date = request.POST.get("end_date")

    try:
        # Parse dates
        start_data_parse = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        end_data_parse = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        messages.error(request, "Invalid date format.")
        return HttpResponseRedirect(reverse("student_view_attendance"))

    # Get the student's profile
    stud_obj = get_object_or_404(Students, user=request.user)
    # Get the subject object
    subject_obj = get_object_or_404(Subjects, id=subject_id)

    # Filter Attendance using the new field name 'subject'
    attendance = Attendance.objects.filter(
        attendance_date__range=(start_data_parse, end_data_parse),
        subject=subject_obj
    )
    # Filter AttendanceReport using new field names 'attendance' and 'student'
    attendance_reports = AttendanceReport.objects.filter(
        attendance__in=attendance,
        student=stud_obj
    )

    return render(request, "student_template/student_attendance_data.html", {"attendance_reports": attendance_reports})

# --- Student Apply Leave ---
def student_apply_leave(request):
    # Get the student's profile
    # Renamed variable from staff_obj to student_obj for clarity
    student_obj = get_object_or_404(Students, user=request.user)
    # Filter leave reports using the new field name 'student'
    leave_data = LeaveReportStudent.objects.filter(student=student_obj)
    return render(request, "student_template/student_apply_leave.html", {"leave_data": leave_data})

# --- Student Apply Leave Save ---
def student_apply_leave_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("student_apply_leave"))
    else:
        leave_date = request.POST.get("leave_date")
        leave_msg = request.POST.get("leave_msg")

        # Get the student's profile
        student_obj = get_object_or_404(Students, user=request.user)

        try:
            # Create LeaveReportStudent using new field name 'student'
            # Leave_status is Boolean, False is default (Pending/Rejected)
            leave_report = LeaveReportStudent(
                student=student_obj,
                leave_date=leave_date, # Assuming leave_date is in a format Django DateField accepts
                leave_message=leave_msg,
                leave_status=False # Use False for pending/new leave
            )
            leave_report.save()
            messages.success(request, "Successfully Applied for Leave")
            return HttpResponseRedirect(reverse("student_apply_leave"))
        except Exception as e: # Catch specific exceptions if possible
            messages.error(request, f"Failed To Apply for Leave: {e}") # Show error message
            return HttpResponseRedirect(reverse("student_apply_leave"))

# --- Student Feedback ---
def student_feedback(request):
    # Get the student's profile
    # Renamed variable from staff_id to student_obj for clarity
    student_obj = get_object_or_404(Students, user=request.user)
    # Filter feedback using the new field name 'student'
    feedback_data = FeedBackStudent.objects.filter(student=student_obj)
    return render(request, "student_template/student_feedback.html", {"feedback_data": feedback_data})

# --- Student Feedback Save ---
def student_feedback_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("student_feedback"))
    else:
        feedback_msg = request.POST.get("feedback_msg")

        # Get the student's profile
        student_obj = get_object_or_404(Students, user=request.user)

        try:
            # Create FeedBackStudent using new field name 'student'
            # feedback_reply is nullable and blank
            feedback = FeedBackStudent(
                student=student_obj,
                feedback=feedback_msg,
                feedback_reply=None # Use None for nullable field if no reply yet
            )
            feedback.save()
            messages.success(request, "Successfully Sent Feedback")
            return HttpResponseRedirect(reverse("student_feedback"))
        except Exception as e: # Catch specific exceptions if possible
            messages.error(request, f"Failed To Send Feedback: {e}") # Show error message
            return HttpResponseRedirect(reverse("student_feedback"))

# --- Student Profile ---
def student_profile(request):
    # request.user is already the CustomUser object
    user = request.user
    # Get the student's profile using the new field name 'user'
    student = get_object_or_404(Students, user=user)
    return render(request, "student_template/student_profile.html", {"user": user, "student": student})

# --- Student Profile Save ---
def student_profile_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("student_profile"))
    else:
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        password = request.POST.get("password") # Handle password change
        address = request.POST.get("address") # Assuming address is editable here

        try:
            # request.user is already the CustomUser object
            customuser = request.user
            customuser.first_name = first_name
            customuser.last_name = last_name

            # Handle password change ONLY if a new password is provided
            if password: # Check if password is not None and not an empty string
                customuser.set_password(password)

            customuser.save()

            # Get the student's profile using the new field name 'user'
            student = get_object_or_404(Students, user=customuser)
            student.address = address
            # Add other editable student fields here if they are in the form
            # student.gender = request.POST.get("gender")
            # student.age = request.POST.get("age")
            student.save()

            messages.success(request, "Successfully Updated Profile")
            return HttpResponseRedirect(reverse("student_profile"))
        except Exception as e: # Catch specific exceptions if possible
            messages.error(request, f"Failed to Update Profile: {e}") # Show error message
            return HttpResponseRedirect(reverse("student_profile"))

# --- Student FCM Token Save (AJAX) ---
@csrf_exempt
def student_fcmtoken_save(request):
    if request.method != "POST":
        return HttpResponse("Method Not Allowed")

    token = request.POST.get("token")
    try:
        # Get the student's profile using the new field name 'user'
        student = get_object_or_404(Students, user=request.user)
        student.fcm_token = token
        student.save()
        return HttpResponse("True") # Indicate success
    except Exception as e: # Catch specific exceptions if possible
        print(f"Error saving student FCM token: {e}") # Log error
        return HttpResponse("False") # Indicate failure


# --- Student All Notifications ---
def student_all_notification(request):
    # Get the student's profile using the new field name 'user'
    student = get_object_or_404(Students, user=request.user)
    # Filter notifications using the new field name 'student'
    notifications = NotificationStudent.objects.filter(student=student)
    return render(request, "student_template/all_notification.html", {"notifications": notifications})

# --- Join Class Room ---
def join_class_room(request, subject_id, session_year_id):
    # Use get_object_or_404 for safer lookups
    session_year_obj = get_object_or_404(SessionYearModel, id=session_year_id)
    subject_obj = get_object_or_404(Subjects, id=subject_id)

    # Get the student's profile
    student_obj = get_object_or_404(Students, user=request.user)

    # Access related course using new field name 'course'
    course = subject_obj.course

    # Check if the student is enrolled in this course and session year
    # Filter Students using new field names 'user', 'course', and 'session_year'
    check_enrollment = Students.objects.filter(
        user=request.user,
        course=course,
        session_year=session_year_obj
    ).exists()

    if check_enrollment:
        try:
            # Use new field names 'session_years' and 'subject' for OnlineClassRoom lookup
            onlineclass = OnlineClassRoom.objects.get(session_years=session_year_obj, subject=subject_obj)
            return render(request, "student_template/join_class_room_start.html", {
                "username": request.user.username,
                "password": onlineclass.room_pwd, # Note: Displaying passwords directly is insecure
                "roomid": onlineclass.room_name
            })
        except OnlineClassRoom.DoesNotExist:
            messages.warning(request, "No online class scheduled for this subject and session yet.")
            # Redirect back to a suitable page, e.g., student home or subjects list
            return HttpResponseRedirect(reverse("student_home")) # Or another relevant view
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
            # Redirect back to a suitable page
            return HttpResponseRedirect(reverse("student_home")) # Or another relevant view
    else:
        # Student is not enrolled in this subject's course/session
        messages.warning(request, "This subject is not part of your enrolled course or session.")
        # Redirect back to a suitable page
        return HttpResponseRedirect(reverse("student_home")) # Or another relevant view


# --- Student View Result ---
def student_view_result(request):
    # request.user is already the CustomUser object
    user = request.user
    # Get the student's profile using the new field name 'user'
    student = get_object_or_404(Students, user=user)
    # Filter student results using the new field name 'student'
    studentresult = StudentResult.objects.filter(student=student)

    return render(request, "student_template/student_result.html", {"studentresult": studentresult, "student": student})

# --- Generate PDF (Class-Based View) ---
class GeneratePdf(View):
    def get(self, request, *args, **kwargs):
        # request.user is already the CustomUser object
        user = request.user
        # Get the student's profile using the new field name 'user'
        student = get_object_or_404(Students, user=user)
        # Filter student results using the new field name 'student'
        studentresult = StudentResult.objects.filter(student=student)

        # Make sure the template context matches what the template expects
        context = {"studentresult": studentresult, "student": student, 'user': user}

        # Render the template to HTML and then convert to PDF
        # Ensure 'student_template/student_result.html' is the correct template path for the PDF
        pdf = html_to_pdf('student_template/student_result.html', context)

        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            # Optionally add a filename for download
            filename = f"Student_Result_{student.user.username}.pdf"
            content = f"attachment; filename={filename}"
            response['Content-Disposition'] = content
            return response
        else:
            # Handle error if PDF generation failed
            messages.error(request, "Failed to generate PDF.")
            # Redirect back to the result view or show an error page
            return HttpResponse("Error Generating PDF", status=400)