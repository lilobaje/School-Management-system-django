# import filename # This import is not used
import json
from datetime import datetime
from uuid import uuid4
from django.contrib import messages
# from django.core import serializers # Not used in these views
# from django.forms import model_to_dict # Not used in these views
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404 # Import get_object_or_404
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from school_management_app.models import (Subjects,CustomUser,OnlineClassRoom,StudentResult,
                                         SessionYearModel,NotificationStaffs, Students, Attendance,
                                         AttendanceReport,LeaveReportStaff, Staffs,FeedBackStaffs, Courses)

# --- Staff Home View ---
def staff_home(request):
    # Get the logged-in staff's Staffs profile using the 'user' relationship
    # Use get_object_or_404 for safety
    staff_obj = get_object_or_404(Staffs, user=request.user)

    # Fetch Subjects taught by this staff using the new field name 'staff'
    subjects = Subjects.objects.filter(staff=staff_obj)
    subject_count = subjects.count() # Subject count is simply the count of this queryset

    course_id_list = []
    for subject in subjects:
        # Access related course using the new field name 'course'
        course = subject.course # Access the Course object directly
        course_id_list.append(course.id)

    final_course = []
    # removing Duplicate Course ID
    for course_id in course_id_list:
        if course_id not in final_course:
            final_course.append(course_id)

    # For Fetch All Student Under Staff's Courses
    # Filter students using the new field name 'course'
    students_in_courses = Students.objects.filter(course__id__in=final_course) # Filter by course ID
    students_count = students_in_courses.count()


    # Fetch All Attendance Count for subjects taught by this staff
    # Filter Attendance using the new field name 'subject'
    attendance_count = Attendance.objects.filter(subject__in=subjects).count()

    # Fetch All Approved Leave for this staff
    # Filter LeaveReportStaff using the new field name 'staff' and leave_status=1
    leave_count = LeaveReportStaff.objects.filter(staff=staff_obj, leave_status=1).count()


    # Fetch Attendance Data by Subject
    subject_list = []
    attendance_list = []
    for subject in subjects:
        # Filter Attendance using the new field name 'subject'
        attendance_count1 = Attendance.objects.filter(subject=subject).count()
        subject_list.append(subject.subject_name)
        attendance_list.append(attendance_count1)

    # Fetch Attendance Data for Students in Staff's Courses
    # This section counts attendance reports for *all* students in the courses, not just those taught by this staff
    # If you need attendance data only for students *in this staff's subjects*, the query logic needs adjustment.
    # Assuming the original logic of students in the courses is intended:
    student_list = []
    student_list_attendance_present = []
    student_list_attendance_absent = []
    for student in students_in_courses:
        # Filter AttendanceReport using the new field name 'student'
        attendance_present_count = AttendanceReport.objects.filter(status=True, student=student).count()
        attendance_absent_count = AttendanceReport.objects.filter(status=False, student=student).count()
        # Access related CustomUser using the new field name 'user'
        student_list.append(student.user.username)
        student_list_attendance_present.append(attendance_present_count)
        student_list_attendance_absent.append(attendance_absent_count)

    return render(request, "staff_template/staff_home_template.html", {
        "students_count": students_count,
        "attendance_count": attendance_count,
        "leave_count": leave_count,
        "subject_count": subject_count,
        "subject_list": subject_list,
        "attendance_list": attendance_list,
        "student_list": student_list,
        "present_list": student_list_attendance_present,
        "absent_list": student_list_attendance_absent
    })

# --- Staff FCM Token Save (AJAX) ---
@csrf_exempt
def staff_fcmtoken_save(request):
    if request.method != "POST":
        return HttpResponse("Method Not Allowed")

    token = request.POST.get("token")
    try:
        # Get the logged-in staff's Staffs profile using the 'user' relationship
        # Use get_object_or_404 for safety
        staff = get_object_or_404(Staffs, user=request.user)
        staff.fcm_token = token
        staff.save()
        return HttpResponse("True") # Indicate success
    except Exception as e: # Catch specific exceptions if possible
        print(f"Error saving staff FCM token: {e}") # Log error
        return HttpResponse("False") # Indicate failure

# --- Staff Take Attendance View ---
def staff_take_attendance(request):
    # Get the logged-in staff's Staffs profile
    staff_obj = get_object_or_404(Staffs, user=request.user)
    # Filter subjects taught by this staff using the new field name 'staff'
    subjects = Subjects.objects.filter(staff=staff_obj)
    session_years = SessionYearModel.objects.all()

    return render(request, "staff_template/staff_take_attendance.html", {"subjects": subjects, "session_years": session_years})

# --- Get Students for Attendance (AJAX) ---
@csrf_exempt
def get_students(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method Not Allowed"}, status=405)

    subject_id = request.POST.get("subject")
    session_year_id = request.POST.get("session_year") # Renamed variable for clarity

    try:
        # Use get_object_or_404 for safety
        subject = get_object_or_404(Subjects, id=subject_id)
        session_model = get_object_or_404(SessionYearModel, id=session_year_id)

        # Filter students by the subject's course and the selected session year
        # Use new field names 'course' and 'session_year'
        students = Students.objects.filter(course=subject.course, session_year=session_model)

        list_data = []
        for student in students:
            # Access related CustomUser using the new field name 'user'
            data_small = {"id": student.user.id, "name": f"{student.user.first_name} {student.user.last_name}"} # Use f-string
            list_data.append(data_small)

        return JsonResponse(json.dumps(list_data), content_type="application/json", safe=False)
    except Subjects.DoesNotExist:
         return JsonResponse({"error": "Subject not found."}, status=404)
    except SessionYearModel.DoesNotExist:
         return JsonResponse({"error": "Session year not found."}, status=404)
    except Exception as e:
        print(f"Error fetching students: {e}") # Log error
        return JsonResponse({"error": str(e)}, status=500) # Return error as JSON

# --- Save Attendance Data (AJAX) ---
@csrf_exempt
def save_attendance_data(request):
    if request.method != "POST":
         return HttpResponse("Method Not Allowed", status=405)

    student_ids_json = request.POST.get("student_ids") # Renamed variable for clarity
    subject_id = request.POST.get("subject_id")
    attendance_date_str = request.POST.get("attendance_date") # Renamed variable for clarity
    session_year_id = request.POST.get("session_year_id")

    try:
        # Use get_object_or_404 for safety
        subject_model = get_object_or_404(Subjects, id=subject_id)
        session_model = get_object_or_404(SessionYearModel, id=session_year_id)

        # Parse the attendance date string
        attendance_date = datetime.strptime(attendance_date_str, "%Y-%m-%d").date()


        json_sstudent = json.loads(student_ids_json)

        # Create the Attendance record using new field names 'subject' and 'session_year'
        attendance = Attendance(subject=subject_model, attendance_date=attendance_date, session_year=session_model)
        attendance.save() # Save Attendance first to get its ID

        # Create AttendanceReport records for each student
        for stud_data in json_sstudent: # Renamed variable for clarity
            student_id = stud_data['id']
            status = stud_data['status'] # Assuming status is boolean True/False or 1/0

            # Get the Students object using the CustomUser ID
            student = get_object_or_404(Students, user__id=student_id) # Link via CustomUser ID

            # Create AttendanceReport using new field names 'student' and 'attendance'
            attendance_report = AttendanceReport(student=student, attendance=attendance, status=status)
            attendance_report.save()

        return HttpResponse("OK") # Indicate success
    except Subjects.DoesNotExist:
         return HttpResponse("Error: Subject not found.", status=404)
    except SessionYearModel.DoesNotExist:
         return HttpResponse("Error: Session year not found.", status=404)
    except Students.DoesNotExist:
         return HttpResponse("Error: One or more students not found.", status=404)
    except json.JSONDecodeError:
         return HttpResponse("Error: Invalid student data format.", status=400)
    except Exception as e:
        print(f"Error saving attendance data: {e}") # Log error
        return HttpResponse(f"ERR: {str(e)}", status=500) # Return specific error message

# --- Staff Update Attendance View ---
def staff_update_attendance(request):
    # Get the logged-in staff's Staffs profile
    staff_obj = get_object_or_404(Staffs, user=request.user)
    # Filter subjects taught by this staff using the new field name 'staff'
    subjects = Subjects.objects.filter(staff=staff_obj)
    session_years = SessionYearModel.objects.all() # Renamed variable for clarity
    return render(request, "staff_template/staff_update_attendance.html", {"subjects": subjects, "session_years": session_years})

# --- Get Attendance Dates (AJAX) ---
@csrf_exempt
def get_attendance_dates(request):
    if request.method != "POST":
         return JsonResponse({"error": "Method Not Allowed"}, status=405)

    subject_id = request.POST.get("subject")
    session_year_id = request.POST.get("session_year_id")

    try:
        # Use get_object_or_404 for safety
        subject_obj = get_object_or_404(Subjects, id=subject_id)
        session_year_obj = get_object_or_404(SessionYearModel, id=session_year_id)

        # Filter Attendance using new field names 'subject' and 'session_year'
        attendance = Attendance.objects.filter(subject=subject_obj, session_year=session_year_obj)

        attendance_obj = []
        for attendance_single in attendance:
            data = {
                "id": attendance_single.id,
                "attendance_date": str(attendance_single.attendance_date),
                # Use new field name 'session_year' but keep original key name for template compatibility
                "session_year_id": attendance_single.session_year.id
            }
            attendance_obj.append(data)

        # Return JSON response
        return JsonResponse(json.dumps(attendance_obj), safe=False, content_type="application/json") # Explicit content_type
    except Subjects.DoesNotExist:
         return JsonResponse({"error": "Subject not found."}, status=404)
    except SessionYearModel.DoesNotExist:
         return JsonResponse({"error": "Session year not found."}, status=404)
    except Exception as e:
        print(f"Error fetching attendance dates: {e}") # Log error
        return JsonResponse({"error": str(e)}, status=500) # Return error as JSON

# --- Get Attendance Students for Update (AJAX) ---
@csrf_exempt
def get_attendance_student(request):
    if request.method != "POST":
         return JsonResponse({"error": "Method Not Allowed"}, status=405)

    attendance_id = request.POST.get("attendance_date") # Renamed variable for clarity

    try:
        # Use get_object_or_404 for safety
        attendance = get_object_or_404(Attendance, id=attendance_id)

        # Filter AttendanceReport using the new field name 'attendance'
        attendance_data = AttendanceReport.objects.filter(attendance=attendance)

        list_data = []
        for student_report in attendance_data: # Renamed variable for clarity
            data_small = {
                # Access related CustomUser using the new field name 'user'
                "id": student_report.student.user.id, # CustomUser ID
                "name": f"{student_report.student.user.first_name} {student_report.student.user.last_name}", # Use f-string
                "status": student_report.status
            }
            list_data.append(data_small)

        # Return JSON response
        return JsonResponse(json.dumps(list_data), content_type="application/json", safe=False)
    except Attendance.DoesNotExist:
         return JsonResponse({"error": "Attendance record not found."}, status=404)
    except Exception as e:
        print(f"Error fetching attendance students: {e}") # Log error
        return JsonResponse({"error": str(e)}, status=500) # Return error as JSON

# --- Save Updated Attendance Data (AJAX) ---
@csrf_exempt
def save_updateattendance_data(request):
    if request.method != "POST":
         return HttpResponse("Method Not Allowed", status=405)

    student_ids_json = request.POST.get("student_ids") # Renamed variable for clarity
    attendance_id = request.POST.get("attendance_date") # Renamed variable for clarity

    try:
        # Use get_object_or_404 for safety
        attendance = get_object_or_404(Attendance, id=attendance_id)

        json_sstudent = json.loads(student_ids_json)

        for stud_data in json_sstudent: # Renamed variable for clarity
            student_user_id = stud_data['id'] # This is the CustomUser ID
            status = stud_data['status'] # Assuming status is boolean True/False or 1/0

            # Get the Students object using the CustomUser ID
            student = get_object_or_404(Students, user__id=student_user_id) # Link via CustomUser ID

            # Get the specific AttendanceReport for this student and attendance record
            # Use new field names 'student' and 'attendance'
            attendance_report = get_object_or_404(AttendanceReport, student=student, attendance=attendance)

            # Update the status and save
            attendance_report.status = status
            attendance_report.save()

        return HttpResponse("OK") # Indicate success
    except Attendance.DoesNotExist:
         return HttpResponse("Error: Attendance record not found.", status=404)
    except Students.DoesNotExist:
         return HttpResponse("Error: One or more students not found.", status=404)
    except AttendanceReport.DoesNotExist:
         return HttpResponse("Error: Attendance report for a student not found.", status=404)
    except json.JSONDecodeError:
         return HttpResponse("Error: Invalid student data format.", status=400)
    except Exception as e:
        print(f"Error saving updated attendance data: {e}") # Log error
        return HttpResponse(f"ERR: {str(e)}", status=500) # Return specific error message


# --- Staff Apply Leave View ---
def staff_apply_leave(request):
    # Get the logged-in staff's Staffs profile
    staff_obj = get_object_or_404(Staffs, user=request.user)
    # Filter leave reports using the new field name 'staff'
    leave_data = LeaveReportStaff.objects.filter(staff=staff_obj)
    return render(request, "staff_template/staff_apply_leave.html", {"leave_data": leave_data})

# --- Staff Apply Leave Save ---
def staff_apply_leave_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("staff_apply_leave"))
    else:
        leave_date_str = request.POST.get("leave_date") # Renamed variable
        leave_msg = request.POST.get("leave_msg")

        # Get the logged-in staff's Staffs profile
        staff_obj = get_object_or_404(Staffs, user=request.user)

        try:
            # Create LeaveReportStaff using new field name 'staff'
            # leave_status=0 is correct for the IntegerField choices (Pending)
            leave_report = LeaveReportStaff(
                staff=staff_obj,
                leave_date=leave_date_str, # Assuming date string is valid for DateField
                leave_message=leave_msg,
                leave_status=0 # Pending
            )
            leave_report.save()
            messages.success(request, "Successfully Applied for Leave")
            return HttpResponseRedirect(reverse("staff_apply_leave"))
        except Exception as e: # Catch specific exceptions if possible
            messages.error(request, f"Failed To Apply for Leave: {e}") # Show error message
            return HttpResponseRedirect(reverse("staff_apply_leave"))

# --- Staff Feedback View ---
def staff_feedback(request):
    # Get the logged-in staff's Staffs profile
    # Renamed variable from staff_id to staff_obj for clarity
    staff_obj = get_object_or_404(Staffs, user=request.user)
    # Filter feedback using the new field name 'staff'
    feedback_data = FeedBackStaffs.objects.filter(staff=staff_obj)
    return render(request, "staff_template/staff_feedback.html", {"feedback_data": feedback_data})

# --- Staff Feedback Save ---
def staff_feedback_save(request):
    if request.method != "POST":
        # Redirect to the correct view name
        return HttpResponseRedirect(reverse("staff_feedback"))
    else:
        feedback_msg = request.POST.get("feedback_msg")

        # Get the logged-in staff's Staffs profile
        staff_obj = get_object_or_404(Staffs, user=request.user)

        try:
            # Create FeedBackStaffs using new field name 'staff'
            # feedback_reply is nullable and blank
            feedback = FeedBackStaffs(
                staff=staff_obj,
                feedback=feedback_msg,
                feedback_reply=None # Use None for nullable field if no reply yet
            )
            feedback.save()
            messages.success(request, "Successfully Sent Feedback")
            return HttpResponseRedirect(reverse("staff_feedback"))
        except Exception as e: # Catch specific exceptions if possible
            messages.error(request, f"Failed To Send Feedback: {e}") # Show error message
            return HttpResponseRedirect(reverse("staff_feedback"))

# --- Staff Profile View ---
def staff_profile(request):
    # request.user is already the CustomUser object
    user = request.user
    # Get the logged-in staff's Staffs profile using the 'user' relationship
    staff = get_object_or_404(Staffs, user=user)
    return render(request, "staff_template/staff_profile.html", {"user": user, "staff": staff})

# --- Staff Profile Save ---
def staff_profile_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("staff_profile"))
    else:
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        address = request.POST.get("address")
        password = request.POST.get("password") # Handle password change
        # Get other editable staff fields from the form if they exist (gender, state, city)

        try:
            # request.user is already the CustomUser object
            customuser = request.user
            customuser.first_name = first_name
            customuser.last_name = last_name

            # Handle password change ONLY if a new password is provided
            if password: # Check if password is not None and not an empty string
                customuser.set_password(password)

            customuser.save() # Save the CustomUser changes

            # Get the logged-in staff's Staffs profile using the 'user' relationship
            staff = get_object_or_404(Staffs, user=customuser) # Use new field name 'user'
            staff.address = address
             # Update other fields if collected in the form
            # staff.gender = request.POST.get("gender") # Example
            # staff.state = request.POST.get("state")
            # staff.city = request.POST.get("city")
            staff.save() # Save the Staffs changes

            messages.success(request, "Successfully Updated Profile")
            return HttpResponseRedirect(reverse("staff_profile"))
        except Exception as e: # Catch specific exceptions if possible
            messages.error(request, f"Failed to Update Profile: {e}") # Show error message
            return HttpResponseRedirect(reverse("staff_profile"))

# --- Staff All Notifications ---
def staff_all_notification(request):
    # Get the logged-in staff's Staffs profile
    staff_obj = get_object_or_404(Staffs, user=request.user)
    # Filter notifications using the new field name 'staff'
    notifications = NotificationStaffs.objects.filter(staff=staff_obj)
    return render(request, "staff_template/all_notification.html", {"notifications": notifications})

# --- Start Live Classroom View ---
def start_live_classroom(request):
    # Get the logged-in staff's Staffs profile
    staff_obj = get_object_or_404(Staffs, user=request.user)
    # Filter subjects taught by this staff using the new field name 'staff'
    subjects = Subjects.objects.filter(staff=staff_obj)
    session_years = SessionYearModel.objects.all()
    return render(request, "staff_template/start_live_classroom.html", {"subjects": subjects, "session_years": session_years})

# --- Start Live Classroom Process ---
def start_live_classroom_process(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("start_live_classroom"))

    session_year_id = request.POST.get("session_year") # Renamed variable
    subject_id = request.POST.get("subject") # Renamed variable

    try:
        # Use get_object_or_404 for safety
        subject_obj = get_object_or_404(Subjects, id=subject_id)
        session_obj = get_object_or_404(SessionYearModel, id=session_year_id)
        # Get the logged-in staff's Staffs profile
        staff_obj = get_object_or_404(Staffs, user=request.user)

        # Check for active online class using new field names 'subject' and 'session_years'
        onlineclass_queryset = OnlineClassRoom.objects.filter(
            subject=subject_obj,
            session_years=session_obj, # Note: Field name is session_years in model
            is_active=True
        )

        if onlineclass_queryset.exists():
            # If active class exists, get its details
            data = onlineclass_queryset.first() # Use first() to get the instance
            room_pwd = data.room_pwd # Note: Displaying passwords directly is insecure
            roomname = data.room_name
            messages.info(request, "An active classroom already exists for this subject and session.")
        else:
            # If no active class, create a new one
            room_pwd = datetime.now().strftime('%Y%m%d%H%M%S') + '-' + str(uuid4()) # Use hyphens or underscores consistently
            roomname = datetime.now().strftime('%Y%m%d%H%M%S') + '-' + str(uuid4())
            # Create OnlineClassRoom using new field names and objects
            onlineClass = OnlineClassRoom(
                room_name=roomname,
                room_pwd=room_pwd,
                subject=subject_obj,
                session_years=session_obj, # Note: Field name is session_years
                started_by=staff_obj, # started_by links to Staffs
                is_active=True
            )
            onlineClass.save()
            messages.success(request, "New online classroom started successfully.")

        return render(request, "staff_template/live_class_room_start.html", {
            "username": request.user.username,
            "password": room_pwd, # Note: Displaying passwords directly is insecure
            "roomid": roomname,
            "subject": subject_obj.subject_name,
            "session_year": session_obj.session_start_year # Use session_start_year for display
        })

    except Subjects.DoesNotExist:
        messages.error(request, "Subject not found.")
        return HttpResponseRedirect(reverse("start_live_classroom"))
    except SessionYearModel.DoesNotExist:
        messages.error(request, "Session year not found.")
        return HttpResponseRedirect(reverse("start_live_classroom"))
    except Exception as e: # Catch other potential errors during creation/lookup
        messages.error(request, f"Failed to start online classroom: {e}")
        return HttpResponseRedirect(reverse("start_live_classroom"))


# --- Staff Add Result View ---
def staff_add_result(request):
    # Get the logged-in staff's Staffs profile
    staff_obj = get_object_or_404(Staffs, user=request.user)
    # Filter subjects taught by this staff using the new field name 'staff'
    subjects = Subjects.objects.filter(staff=staff_obj)
    session_years = SessionYearModel.objects.all()
    # You might want to filter students available based on subject and session here for the template
    return render(request, "staff_template/staff_add_result.html", {"subjects": subjects, "session_years": session_years})

# --- Save Student Result ---
def save_student_result(request):
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('staff_add_result')) # Use reverse

    student_admin_id = request.POST.get('student_list') # This is the CustomUser ID
    assignment_marks = request.POST.get('assignment_marks')
    exam_marks = request.POST.get('exam_marks')
    subject_id = request.POST.get('subject')
    fcamark = request.POST.get('fca_marks')
    scamark = request.POST.get('sca_marks')
    overall = request.POST.get('overall_marks') # Consider calculating this in the view or model

    try:
        # Use get_object_or_404 for safety
        # Get the Students object using the CustomUser ID
        student_obj = get_object_or_404(Students, user__id=student_admin_id) # Link via CustomUser ID
        # Get the Subject object
        subject_obj = get_object_or_404(Subjects, id=subject_id)

        # Check if a result already exists for this student and subject
        # Filter using new field names 'subject' and 'student'
        result_queryset = StudentResult.objects.filter(subject=subject_obj, student=student_obj)

        if result_queryset.exists():
            # If result exists, update it
            result = result_queryset.first() # Get the existing instance
            result.subject_assignment_marks = assignment_marks
            result.subject_exam_marks = exam_marks
            result.fca_marks = fcamark
            result.sca_marks = scamark
            result.overall_marks = overall
            # Update grade_marks if you have logic for that here
            result.save()
            messages.success(request, "Successfully Updated Result")
        else:
            # If result does not exist, create a new one
            # Create StudentResult using new field names 'student' and 'subject'
            result = StudentResult(
                student=student_obj,
                subject=subject_obj,
                subject_exam_marks=exam_marks,
                subject_assignment_marks=assignment_marks,
                fca_marks=fcamark,
                sca_marks=scamark,
                overall_marks=overall
                # Add grade_marks here if calculated/provided
            )
            result.save()
            messages.success(request, "Successfully Added Result")

        return HttpResponseRedirect(reverse("staff_add_result"))

    except Students.DoesNotExist:
         messages.error(request, "Error: Student not found.")
         return HttpResponseRedirect(reverse("staff_add_result"))
    except Subjects.DoesNotExist:
         messages.error(request, "Error: Subject not found.")
         return HttpResponseRedirect(reverse("staff_add_result"))
    except Exception as e: # Catch other potential errors during save
        messages.error(request, f"Failed to Add/Update Result: {e}") # Show error message
        return HttpResponseRedirect(reverse("staff_add_result"))

# --- Fetch Student Result (AJAX) ---
@csrf_exempt
def fetch_result_student(request):
    if request.method != "POST":
         return HttpResponse("Method Not Allowed", status=405)

    subject_id = request.POST.get('subject_id')
    student_id = request.POST.get('student_id') # This is the CustomUser ID

    try:
        # Use get_object_or_404 for safety
        # Get the Students object using the CustomUser ID
        student_obj = get_object_or_404(Students, user__id=student_id) # Link via CustomUser ID

        # Filter StudentResult using new field names 'student' and 'subject'
        result_queryset = StudentResult.objects.filter(student=student_obj, subject__id=subject_id)

        if result_queryset.exists():
            # Get the existing result instance
            result = result_queryset.first()
            # Prepare data for JSON response
            result_data = {
                "exam_marks": result.subject_exam_marks,
                "assign_marks": result.subject_assignment_marks,
                "fca_marks": result.fca_marks,
                "sca_marks": result.sca_marks,
                "overall_marks": result.overall_marks,
                "grade_marks": result.grade_marks # Include grade_marks if available
            }
            return JsonResponse(json.dumps(result_data), safe=False, content_type="application/json") # Return as JSON
        else:
            # If result does not exist
            return HttpResponse("False") # Indicate not found to AJAX

    except Students.DoesNotExist:
         return HttpResponse("Error: Student not found.", status=404) # Indicate error to AJAX
    except Subjects.DoesNotExist:
         return HttpResponse("Error: Subject not found.", status=404) # Should not happen if subject_id is valid
    except Exception as e:
        print(f"Error fetching student result: {e}") # Log error
        return HttpResponse(f"ERR: {str(e)}", status=500) # Indicate generic error

# --- Example Widget View ---
def returnHtmlWidget(request):
    return render(request,"widget.html")