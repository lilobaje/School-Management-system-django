# from fileinput import filename # This import is not used
import json

from django.db.models import Q
from django import forms
from .filters import StaffsFilter # Assuming this filter is updated for new model fields
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404 # Import get_object_or_404 for safer lookups
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
# from mysqlx import Session # This import is not used
import requests
from school_management_app.filters import StaffsFilter # Duplicate import? Keep one.

from school_management_app.forms import AddStudentForm, EditStudentForm
from school_management_app.models import (Courses, CustomUser, FeedBackStaffs,
                                         FeedBackStudent, SessionYearModel,
                                         Staffs, Students, Subjects,
                                         LeaveReportStudent, LeaveReportStaff,
                                         AttendanceReport, Attendance,
                                         NotificationStaffs, NotificationStudent)

# --- Admin Home View ---
def AdminHome(request):
    # Counts are fine as they use model managers
    student_count = Students.objects.all().count()
    staff_count = Staffs.objects.all().count()
    subject_count = Subjects.objects.all().count()
    course_count = Courses.objects.all().count()

    course_all = Courses.objects.all()
    course_name_list = []
    subject_count_list = []
    student_count_list_in_course = []
    for course in course_all:
        # Use the new ForeignKey name 'course'
        subjects = Subjects.objects.filter(course=course).count()
        # Use the new ForeignKey name 'course'
        students = Students.objects.filter(course=course).count()
        course_name_list.append(course.course_name)
        subject_count_list.append(subjects)
        student_count_list_in_course.append(students)

    subjects_all = Subjects.objects.all()
    subject_list = []
    student_count_list_in_subject = []
    for subject in subjects_all:
        # Access related course using the new field name 'course'
        course = Courses.objects.get(id=subject.course.id) # Or simply subject.course
        # Use the new ForeignKey name 'course'
        student_count = Students.objects.filter(course=course).count()
        subject_list.append(subject.subject_name)
        student_count_list_in_subject.append(student_count) # Note: This counts students in the course, not students taking this specific subject

    staffs = Staffs.objects.all()
    attendance_present_list_staff = []
    attendance_absent_list_staff = [] # This seems to be counting leaves, not attendance absent
    staff_name_list = []
    for staff in staffs:
        # Link Subjects to Staffs using the new field name 'staff'
        subject_ids = Subjects.objects.filter(staff=staff)
        # Link Attendance to Subjects using the new field name 'subject'
        attendance = Attendance.objects.filter(subject__in=subject_ids).count()
        # Link LeaveReportStaff to Staffs using the new field name 'staff'
        # leave_status=1 corresponds to Approved in Staff Leave model
        leaves = LeaveReportStaff.objects.filter(staff=staff, leave_status=1).count()
        attendance_present_list_staff.append(attendance)
        attendance_absent_list_staff.append(leaves) # Check if this naming is appropriate
        # Access related CustomUser using the new field name 'user'
        staff_name_list.append(staff.user.username)

    students_all = Students.objects.all()
    attendance_present_list_student = []
    attendance_absent_list_student = [] # This seems to count leaves + attendance absent
    student_name_list = []
    for student in students_all:
        # Link AttendanceReport to Students using the new field name 'student'
        attendance = AttendanceReport.objects.filter(student=student, status=True).count()
        absent = AttendanceReport.objects.filter(student=student, status=False).count()
        # Link LeaveReportStudent to Students using the new field name 'student'
        # leave_status=1 corresponds to Approved in Student Leave model (Boolean True)
        leaves = LeaveReportStudent.objects.filter(student=student, leave_status=True).count()
        attendance_present_list_student.append(attendance)
        attendance_absent_list_student.append(leaves + absent) # Check if this calculation is correct
        # Access related CustomUser using the new field name 'user'
        student_name_list.append(student.user.username)

    return render(request, "admin_home/home_content.html", {
        "student_count": student_count,
        "staff_count": staff_count,
        "subject_count": subject_count,
        "course_count": course_count,
        "course_name_list": course_name_list,
        "subject_count_list": subject_count_list,
        "student_count_list_in_course": student_count_list_in_course,
        "student_count_list_in_subject": student_count_list_in_subject,
        "subject_list": subject_list,
        "staff_name_list": staff_name_list,
        "attendance_present_list_staff": attendance_present_list_staff,
        "attendance_absent_list_staff": attendance_absent_list_staff,
        "student_name_list": student_name_list,
        "attendance_present_list_student": attendance_present_list_student,
        "attendance_absent_list_student": attendance_absent_list_student
    })

def StaffHome(request):
    # Consider returning something more specific than base_template for a staff home view
    return render(request, "staff_template/base_template.html")

def Add_staff(request):
    return render(request,"admin_home/add_staff_temp.html")

# --- Delete Staff View ---
def deletestaff(request, staff_id):
    # Use get_object_or_404 for safer lookup
    # Link Staffs to CustomUser using the new field name 'user'
    staff = get_object_or_404(Staffs, user=staff_id)
    if request.method == 'POST':
        # When the Staff object is deleted, the related CustomUser will also be deleted due to on_delete=CASCADE
        staff.delete()
        messages.success(request, "Successfully Deleted Staff")
        return redirect('manage_staff')
    return render(request, 'admin_home/delete.html', {'obj': staff})

# --- Delete Student View ---
def deletestudent(request, student_id):
    # Use get_object_or_404 for safer lookup
    # Link Students to CustomUser using the new field name 'user'
    student = get_object_or_404(Students, user=student_id)
    if request.method == 'POST':
        # When the Student object is deleted, the related CustomUser will also be deleted due to on_delete=CASCADE
        student.delete()
        messages.success(request, "Successfully Deleted Student")
        return redirect('manage_student')
    return render(request, 'admin_home/delete.html', {'obj': student})


def Add_student(request):
    courses = Courses.objects.all() # This is not used if using a ModelForm based on AddStudentForm
    form = AddStudentForm()
    return render(request, "admin_home/add_student_temp.html", {"form": form})

# --- Add Student Save View ---
def Add_student_save(request):
    if request.method != "POST":
        # Method Not Allowed response for non-POST requests
        return HttpResponse("Method Not Allowed", status=405)

    form = AddStudentForm(request.POST, request.FILES)

    if form.is_valid():
        # Get cleaned data from the form
        first_name = form.cleaned_data["first_name"]
        last_name = form.cleaned_data["last_name"]
        username = form.cleaned_data["username"]
        email = form.cleaned_data["email"] # Email is for CustomUser
        password = form.cleaned_data["password"]
        address = form.cleaned_data["address"]

        # Get the string IDs from the cleaned form data for related objects
        # These come from forms.ChoiceField, so they are strings
        session_year_id_str = form.cleaned_data["session_year"] # Correct field name 'session_year'
        course_id_str = form.cleaned_data["course"] # Correct field name 'course'

        sex = form.cleaned_data["sex"]
        age = form.cleaned_data['age'] # Integer or None from form

        # Handle profile picture upload
        profile_pic_path = None # Initialize variable to store the relative path
        if 'profile_pic' in request.FILES:
            profile_pic_file = request.FILES['profile_pic'] # Get the uploaded file
            fs = FileSystemStorage() # Get a storage instance
            # Save the file and get the path relative to MEDIA_ROOT
            profile_pic_path = fs.save(profile_pic_file.name, profile_pic_file)
            # DO NOT calculate the URL here or store the URL in the model field.
            # The FileField handles URL generation based on MEDIA_URL and the stored path.
            # profile_pic_url = fs.url(profile_pic_path) # Remove this line

        try:
            # Fetch the actual Course and SessionYearModel objects using the IDs from the form
            # Use get_object_or_404 for safer lookups
            course_obj = get_object_or_404(Courses, id=course_id_str)
            session_year_obj = get_object_or_404(SessionYearModel, id=session_year_id_str)

            # Create the CustomUser object first
            user = CustomUser.objects.create_user(
                username=username,
                password=password,
                email=email, # Set email on the CustomUser
                last_name=last_name,
                first_name=first_name,
                user_type=3 # Student user type
            )
            # The post_save signal 'create_user_profile' should automatically create the related Students object

            # Get the related Students object (it should exist after CustomUser creation by the signal)
            # Use the new field name 'user' to look up the Students object linked to this user
            student = get_object_or_404(Students, user=user)

            # Assign fields to the Students object
            student.address = address
            # Assign the fetched related objects (not the ID strings)
            student.course = course_obj
            student.session_year = session_year_obj
            # The email field was removed from Students, update it on the CustomUser instead if needed
            # student.email = email # Remove this line as email is on CustomUser
            student.gender = sex
            student.age = age # Assign the integer or None value from the form

            # Assign the relative file path to the FileField if a file was uploaded
            if profile_pic_path is not None: # Check if a new file was uploaded and saved
                student.profile_pic = profile_pic_path

            # Save the Students object to persist the assigned fields
            student.save()

            messages.success(request, "Successfully Added Student")
            return HttpResponseRedirect(reverse("add_student"))

        except Courses.DoesNotExist:
             messages.error(request, "Failed to Add Student: Course not found.")
             return HttpResponseRedirect(reverse("add_student"))
        except SessionYearModel.DoesNotExist:
             messages.error(request, "Failed to Add Student: Session Year not found.")
             return HttpResponseRedirect(reverse("add_student"))
        except Exception as e: # Catch other potential errors during user/student creation/save
             # Log the error for debugging
             print(f"Error adding student: {e}")
             messages.error(request, f"Failed to Add Student: An error occurred ({e})") # Show a more informative error message
             return HttpResponseRedirect(reverse("add_student"))
    else:
        # If form is not valid, re-render the form with errors
        # form=AddStudentForm(request.POST) # This line is redundant, the form is already instantiated with POST data
        messages.error(request, "Form validation failed. Please check the entered data.") # Indicate form errors
        # Need to pass courses and sessions to the template context IF the template manually populates selects
        # Since the form now populates choices in __init__, just passing the form is sufficient
        return render(request, "admin_home/add_student_temp.html", {"form": form}) # Pass the form instance with errors
# --- Edit Student View ---
def Edit_student_save(request):
    if request.method != "POST":
        # Method Not Allowed response for non-POST requests
        return HttpResponse("Method Not Allowed", status=405)

    # Retrieve CustomUser ID from session (or preferably from URL kwargs)
    student_user_id = request.session.get("student_id")
    if student_user_id is None:
        messages.error(request, "Student ID not found in session.")
        return HttpResponseRedirect(reverse("manage_student")) # Redirect to manage page if ID is missing

    # Use get_object_or_404 for safer lookup of the CustomUser and Students objects
    user = get_object_or_404(CustomUser, id=student_user_id)
    # Get the related Students object using the new field name 'user'
    student = get_object_or_404(Students, user=user)

    form = EditStudentForm(request.POST, request.FILES)

    if form.is_valid():
        # Get cleaned data from the form
        first_name = form.cleaned_data["first_name"]
        last_name = form.cleaned_data["last_name"]
        username = form.cleaned_data["username"]
        email = form.cleaned_data["email"] # Email is for CustomUser
        address = form.cleaned_data["address"]

        # Get the string IDs from the cleaned form data for related objects
        # These come from forms.ChoiceField, so they are strings
        session_year_id_str = form.cleaned_data["session_year"] # Correct field name 'session_year'
        course_id_str = form.cleaned_data["course"] # Correct field name 'course'

        sex = form.cleaned_data["sex"]
        age = form.cleaned_data['age'] # Integer or None from form

        # Handle profile picture upload (only if a new file is uploaded)
        profile_pic_path = None # Initialize variable to store the relative path
        if 'profile_pic' in request.FILES:
             profile_pic_file = request.FILES['profile_pic'] # Get the uploaded file
             fs = FileSystemStorage() # Get a storage instance
             # Save the file and get the path relative to MEDIA_ROOT
             profile_pic_path = fs.save(profile_pic_file.name, profile_pic_file)
             # DO NOT calculate the URL here or store the URL in the model field.
             # profile_pic_url = fs.url(profile_pic_path) # Remove this line
        # If no new file is uploaded, student.profile_pic will retain its existing value

        try:
            # Fetch the actual Course and SessionYearModel objects using the IDs from the form
            # Use get_object_or_404 for safer lookups
            course_obj = get_object_or_404(Courses, id=course_id_str)
            session_year_obj = get_object_or_404(SessionYearModel, id=session_year_id_str)

            # Update CustomUser fields
            user.first_name = first_name
            user.last_name = last_name
            user.username = username
            user.email = email # Update email on the CustomUser
            # Password change is handled in a separate profile save view usually
            user.save() # Save the CustomUser changes

            # Update Students fields
            student.address = address
            # Assign the fetched related objects (not the ID strings)
            student.session_year = session_year_obj
            student.gender = sex
            student.age = age # Assign the integer or None value from the form
            # Assign the fetched related course object (not the ID string)
            student.course = course_obj

            # Assign the relative file path to the FileField if a new file was uploaded
            if profile_pic_path is not None: # Check if a new file was uploaded and saved
                student.profile_pic = profile_pic_path
            # else: If no new file, the existing student.profile_pic remains

            # Save the Students object to persist the updated fields
            student.save()

            # Consider if you still need to remove the ID from the session if using URL kwargs
            # del request.session['student_id'] # Remove this if passing ID in URL kwargs

            messages.success(request,"Successfully Edited Student")
            # Redirect back to the edit page for this student using their CustomUser ID
            return HttpResponseRedirect(reverse("edit_student", kwargs={"student_id": user.id}))

        except Courses.DoesNotExist:
             messages.error(request, "Failed to Edit Student: Course not found.")
             return HttpResponseRedirect(reverse("edit_student", kwargs={"student_id": user.id}))
        except SessionYearModel.DoesNotExist:
             messages.error(request, "Failed to Edit Student: Session Year not found.")
             return HttpResponseRedirect(reverse("edit_student", kwargs={"student_id": user.id}))
        except Exception as e: # Catch other potential errors during save
             # Log the error for debugging
             print(f"Error editing student: {e}")
             messages.error(request, f"Failed to Edit Student: An error occurred ({e})") # Show a more informative error message
             # Redirect back to the edit page for this student
             return HttpResponseRedirect(reverse("edit_student", kwargs={"student_id": user.id}))
    else:
        # If form is not valid, re-render the form with errors
        # form=EditStudentForm(request.POST) # This line is redundant
        messages.error(request, "Form validation failed. Please check the entered data.") # Indicate form errors
        # Need to pass student, user, and form to the template context for rendering the edit page
        # student and user objects were already retrieved at the beginning of the view
        return render(request, "admin_home/edit_student_temp.html", {"form": form, "id": user.id, "username": user.username})

def Edit_student(request, student_id):
    # Use get_object_or_404 for safer lookup of the student's profile object
    # Link Students to CustomUser using the new field name 'user'
    student = get_object_or_404(Students, user__id=student_id) # Use user__id to filter by the CustomUser ID

    # You can store the CustomUser ID in the session if needed for the save view,
    # but passing it in the URL kwargs for the save view (as corrected in urls.py) is often cleaner.
    # If using session, ensure you clear it after saving.
    # request.session['student_id'] = student.user.id # Store the CustomUser ID

    # Instantiate the EditStudentForm
    form = EditStudentForm()

    # Populate initial form data from both CustomUser and Students objects
    # Access fields via the related 'user' and directly on the 'student' object
    form.fields['email'].initial = student.user.email
    form.fields['first_name'].initial = student.user.first_name
    form.fields['last_name'].initial = student.user.last_name
    form.fields['username'].initial = student.user.username
    form.fields['address'].initial = student.address
    form.fields['sex'].initial = student.gender
    form.fields['age'].initial = student.age

    # For ForeignKey fields (course and session_year), set the initial value to the ID of the related object
    # Access related objects using the new field names 'course' and 'session_year'
    form.fields['course'].initial = student.course.id
    form.fields['session_year'].initial = student.session_year.id


    # Render the edit student template, passing the form, student's CustomUser ID, and username
    return render(request, "admin_home/edit_student_temp.html", {
        "form": form,
        "id": student.user.id, # Pass the CustomUser ID for the form action/URL
        "username": student.user.username
    })


# --- Edit Student Save View (Ensure this function exists and is correct) ---
# This function should be the target of the form POST submission, and does NOT expect st

def Add_subject(request):
    courses = Courses.objects.all()
    # Changed to query Staffs model directly
    staffs = Staffs.objects.all() # Get all Staff profiles
    return render(request,"admin_home/add_subject_temp.html",{"staffs":staffs,"courses":courses})

# --- Add Subject Save View ---
def Add_subject_save(request):
    if request.method != "POST":
        return HttpResponse("<h2>Method not Allowed</h2>")
    else:
        subject_name = request.POST.get("subject_name")
        # staff_id will now be the ID of the Staffs object, not CustomUser
        staff_id = request.POST.get("staff")
        course_id = request.POST.get("course")

        try:
            # Get Staffs object
            staff = Staffs.objects.get(id=staff_id)
            # Get Courses object
            course = Courses.objects.get(id=course_id)

            # Create Subject object using new field names
            subject = Subjects(subject_name=subject_name, course=course, staff=staff)
            subject.save()

            messages.success(request, "Successfully Added Subject")
            return HttpResponseRedirect(reverse("add_subject"))
        except Exception as e: # Catch specific exceptions if possible
            messages.error(request, f"Failed to Add Subject: {e}") # Show error message
            return HttpResponseRedirect(reverse("add_subject"))


def Add_course(request):
    return render(request,"admin_home/add_course_temp.html")

def Add_course_save(request):
    if request.method != "POST":
        return HttpResponseRedirect("Method Not Allowed!")
    else:
        course_name = request.POST.get("course")
        try:
            course_model = Courses(course_name=course_name)
            course_model.save()
            messages.success(request, "Successfully Added course")
            return HttpResponseRedirect(reverse("add_course"))
        except Exception as e: # Catch specific exceptions if possible
            messages.error(request, f"Failed to Add course: {e}") # Show error message
            return HttpResponseRedirect(reverse("add_course"))

# --- Add Staff Save View ---
def add_staff_save(request):
    if request.method != "POST":
        return HttpResponse("Method Not Allowed")
    else:
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        username = request.POST.get("username")
        # Get email from form, save on CustomUser
        email = request.POST.get("email")
        password = request.POST.get("password")
        address = request.POST.get("address")

        try:
            # Create CustomUser first
            user = CustomUser.objects.create_user(
                username=username,
                password=password,
                email=email, # Set email on CustomUser
                first_name=first_name,
                last_name=last_name,
                user_type=2 # Staff user type
            )

            # The signal 'create_user_profile' should have created the related Staffs object
            # Get the related staff object
            staff = Staffs.objects.get(user=user) # Use the new field name 'user'

            # Assign fields to the Staffs object
            staff.address = address
            # email is on CustomUser, so don't assign it here
            # staff.gender, state, city etc. are also on Staffs, add them here if collected in form
            # staff.gender = request.POST.get("gender") # Example if added to form

            # Save the Staffs object
            staff.save()

            messages.success(request, "Successfully Added Staff")
            return HttpResponseRedirect(reverse("add_staff"))
        except Exception as e: # Catch specific exceptions if possible
            messages.error(request, f"Failed to Add Staff: {e}") # Show error message
            return HttpResponseRedirect(reverse("add_staff"))


def Manage_staff(request):
    staffs = Staffs.objects.all()
    # Assuming StaffsFilter is updated to filter on fields like user__email, user__username etc.
    Staffs_Filter = StaffsFilter(request.GET, queryset=staffs)
    # Pass the filtered queryset to the template
    context = {'Staffs_Filter': Staffs_Filter, 'staffs': Staffs_Filter.qs}
    return render(request, "admin_home/manage_staff_temp.html", context)

# --- Edit Staff View ---
def edit_staff(request, staff_id):
    # Use get_object_or_404 for safer lookup
    # Link Staffs to CustomUser using the new field name 'user'
    staff = get_object_or_404(Staffs, user=staff_id)
    return render(request, "admin_home/edit_staff_temp.html", {"staff": staff, "id": staff.user.id}) # Use staff.user.id

# --- Edit Staff Save View ---
def Edit_staff_save(request):
    if request.method != "POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        # staff_id here is the CustomUser ID from the URL/form
        staff_user_id = request.POST.get("staff_id")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email") # Email is on CustomUser
        username = request.POST.get("username")
        address = request.POST.get("address")
        # Get other fields from the form if they exist (gender, state, city)

        try:
            # Use get_object_or_404 for safer lookup of the CustomUser
            user = get_object_or_404(CustomUser, id=staff_user_id)
            # Get the related Staffs object
            staff_model = get_object_or_404(Staffs, user=user) # Use new field name 'user'

            # Update CustomUser fields
            user.first_name = first_name
            user.last_name = last_name
            user.email = email # Update email on CustomUser
            user.username = username
            user.save()

            # Update Staffs fields
            staff_model.address = address
            # Update other fields if collected in the form
            # staff_model.gender = request.POST.get("gender") # Example

            # Save the Staffs object
            staff_model.save()

            messages.success(request, "Successfully Edited Staff")
            # Redirect back to the edit page for this staff member
            return HttpResponseRedirect(reverse("edit_staff", kwargs={"staff_id": user.id})) # Use user.id
        except Exception as e: # Catch specific exceptions if possible
            messages.error(request, f"Failed to Edit Staff: {e}") # Show error message
            # Redirect back to the edit page for this staff member
            return HttpResponseRedirect(reverse("edit_staff", kwargs={"staff_id": user.id})) # Use user.id


def Manage_student(request):
    students = Students.objects.all()
    context = {'students': students}
    return render(request,"admin_home/manage_student_temp.html",context)

# --- Search Student View (Already corrected) ---
def Search_student(request):
    q = request.GET.get('q') if request.GET.get('q') is not None else ''

    students = Students.objects.filter(
        Q(user__email__icontains=q)
        | Q(user__first_name__icontains=q) # Added search by first name
        | Q(user__last_name__icontains=q) # Added search by last name
        | Q(address__icontains=q) # Added search by address
        # Add other fields here if you want to search across multiple fields
        # e.g., | Q(gender__icontains=q) if applicable
    )

    context = {'students': students}
    # This view seems intended for an AJAX call or partial update?
    # It returns a template fragment, not a full page.
    # If it's a full page search result, the template name might need adjusting.
    return render(request, "admin_home/search_student_temp.html", context)

def modal(request):
    return render(request,"admin_home/modals.html")


def Manage_course(request):
    courses = Courses.objects.all()
    return render(request,"admin_home/manage_course_temp.html",{"courses":courses})

def Edit_course(request, course_id):
    # Use get_object_or_404 for safer lookup
    course = get_object_or_404(Courses, id=course_id)
    return render(request,"admin_home/edit_course_temp.html",{"course":course,"id":course_id})

def Edit_course_save(request):
    if request.method != "POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        course_id = request.POST.get("course_id")
        course_name = request.POST.get("course")

        try:
            # Use get_object_or_404 for safer lookup
            course = get_object_or_404(Courses, id=course_id)
            course.course_name = course_name
            course.save()
            messages.success(request, "Successfully Edited Course")
            return HttpResponseRedirect(reverse("edit_course", kwargs={"course_id": course_id}))
        except Exception as e: # Catch specific exceptions if possible
            messages.error(request, f"Failed to Edit Course: {e}") # Show error message
            return HttpResponseRedirect(reverse("edit_course", kwargs={"course_id": course_id}))


def Manage_subject(request):
    subjects = Subjects.objects.all()
    return render(request,"admin_home/manage_subject_temp.html",{"subjects":subjects})

# --- Edit Subject View ---
def Edit_subject(request, subject_id):
    # Use get_object_or_404 for safer lookup
    subject = get_object_or_404(Subjects, id=subject_id)
    courses = Courses.objects.all()
    # Changed to query Staffs model directly
    staffs = Staffs.objects.all() # Get all Staff profiles
    return render(request, "admin_home/edit_subject_temp.html", {"subject": subject, "staffs": staffs, "courses": courses, "id": subject_id})

# --- Edit Subject Save View ---
def Edit_subject_save(request):
    if request.method != "POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        subject_id = request.POST.get("subject_id")
        subject_name = request.POST.get("subject_name")
        # staff_id will be the ID of the Staffs object from the form
        staff_id = request.POST.get("staff")
        course_id = request.POST.get("course")

        try:
            # Use get_object_or_404 for safer lookups
            subject = get_object_or_404(Subjects, id=subject_id)
            staff = get_object_or_404(Staffs, id=staff_id) # Get the Staffs object
            course = get_object_or_404(Courses, id=course_id) # Get the Courses object

            # Update subject fields using new field names
            subject.subject_name = subject_name
            subject.staff = staff # Assign Staffs object
            subject.course = course # Assign Courses object
            subject.save()

            messages.success(request, "Successfully Edited Subject")
            return HttpResponseRedirect(reverse("edit_subject", kwargs={"subject_id": subject_id}))
        except Exception as e: # Catch specific exceptions if possible
            messages.error(request, f"Failed to Edit Subject: {e}") # Show error message
            return HttpResponseRedirect(reverse("edit_subject", kwargs={"subject_id": subject_id}))


def manage_session(request):
    # You might want to retrieve and display existing sessions here
    sessions = SessionYearModel.objects.all()
    return render(request, "admin_home/manage_session_temp.html", {"sessions": sessions})

def add_session_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("manage_session")) # Redirect to the correct view name
    else:
        session_start_year = request.POST.get("session_start")
        session_end_year = request.POST.get("session_end")

        try:
            sessionyear = SessionYearModel(session_start_year=session_start_year, session_end_year=session_end_year)
            sessionyear.save()
            messages.success(request, "Successfully Added Session")
            return HttpResponseRedirect(reverse("manage_session"))
        except Exception as e: # Catch specific exceptions if possible
            messages.error(request, f"Failed to Add Session: {e}") # Show error message
            return HttpResponseRedirect(reverse("manage_session"))


# --- Existing check_email_exist and check_username_exist are fine ---
@csrf_exempt
def check_email_exist(request):
    email = request.POST.get("email")
    # This checks CustomUser, which is correct
    user_obj = CustomUser.objects.filter(email=email).exists()
    if user_obj:
        return HttpResponse(True)
    else:
        return HttpResponse(False)

@csrf_exempt
def check_username_exist(request):
    username = request.POST.get("username")
    # This checks CustomUser, which is correct
    user_obj = CustomUser.objects.filter(username=username).exists()
    if user_obj:
        return HttpResponse(True)
    else:
        return HttpResponse(False)

def staff_feedback_message(request):
    feedbacks = FeedBackStaffs.objects.all()
    return render(request,"admin_home/staff_feedback_template.html",{"feedbacks":feedbacks})

def student_feedback_message(request):
    feedbacks = FeedBackStudent.objects.all()
    return render(request,"admin_home/student_feedback_template.html",{"feedbacks":feedbacks})

# --- Student Feedback Reply ---
@csrf_exempt
def student_feedback_message_replied(request):
    feedback_id = request.POST.get("id")
    feedback_message = request.POST.get("message")

    try:
        # Use get_object_or_404 for safer lookup
        feedback = get_object_or_404(FeedBackStudent, id=feedback_id)
        feedback.feedback_reply = feedback_message
        feedback.save()
        return HttpResponse("True")
    except Exception as e: # Catch specific exceptions if possible
        print(f"Error replying to student feedback: {e}") # Log the error
        return HttpResponse("False")

# --- Staff Feedback Reply ---
@csrf_exempt
def staff_feedback_message_replied(request):
    feedback_id = request.POST.get("id")
    feedback_message = request.POST.get("message")

    try:
        # Use get_object_or_404 for safer lookup
        feedback = get_object_or_404(FeedBackStaffs, id=feedback_id)
        feedback.feedback_reply = feedback_message
        feedback.save()
        return HttpResponse("True")
    except Exception as e: # Catch specific exceptions if possible
        print(f"Error replying to staff feedback: {e}") # Log the error
        return HttpResponse("False")


def staff_leave_view(request):
    leaves = LeaveReportStaff.objects.all()
    return render(request,"admin_home/staff_leave_view.html",{"leaves":leaves})

def student_leave_view(request):
    leaves = LeaveReportStudent.objects.all()
    return render(request,"admin_home/student_leave_view.html",{"leaves":leaves})

# --- Student Approve Leave ---
def student_approve_leave(request, leave_id):
    # Use get_object_or_404 for safer lookup
    leave = get_object_or_404(LeaveReportStudent, id=leave_id)
    # Model uses BooleanField, True for approved
    leave.leave_status = True
    leave.save()
    messages.success(request, "Student leave approved.")
    return HttpResponseRedirect(reverse("student_leave_view"))

# --- Student Disapprove Leave ---
def student_disapprove_leave(request, leave_id):
    # Use get_object_or_404 for safer lookup
    leave = get_object_or_404(LeaveReportStudent, id=leave_id)
    # Model uses BooleanField, False for disapproved/pending
    leave.leave_status = False # Setting to False
    leave.save()
    messages.info(request, "Student leave disapproved.") # Use info or warning for disapproval
    return HttpResponseRedirect(reverse("student_leave_view"))


# --- Staff Approve Leave ---
def staff_approve_leave(request, leave_id):
    # Use get_object_or_404 for safer lookup
    leave = get_object_or_404(LeaveReportStaff, id=leave_id)
    # Model uses IntegerField with choices, 1 for Approved
    leave.leave_status = 1
    leave.save()
    messages.success(request, "Staff leave approved.")
    return HttpResponseRedirect(reverse("staff_leave_view"))

# --- Staff Disapprove Leave ---
def staff_disapprove_leave(request, leave_id):
    # Use get_object_or_404 for safer lookup
    leave = get_object_or_404(LeaveReportStaff, id=leave_id)
    # Model uses IntegerField with choices, 2 for Rejected
    leave.leave_status = 2
    leave.save()
    messages.info(request, "Staff leave disapproved.") # Use info or warning
    return HttpResponseRedirect(reverse("staff_leave_view"))


def admin_view_attendance(request):
    subjects = Subjects.objects.all()
    session_years = SessionYearModel.objects.all() # Renamed variable for clarity
    return render(request, "admin_home/admin_view_attendance.html", {"subjects": subjects, "session_years": session_years})

# --- Admin Get Attendance Dates (AJAX) ---
@csrf_exempt
def admin_get_attendance_dates(request):
    # subject_id and session_year_id are coming from the AJAX request
    subject_id = request.POST.get("subject")
    session_year_id = request.POST.get("session_year_id")

    try:
        # Use get_object_or_404 for safer lookups
        subject_obj = get_object_or_404(Subjects, id=subject_id)
        session_year_obj = get_object_or_404(SessionYearModel, id=session_year_id)

        # Filter Attendance using new field names 'subject' and 'session_year'
        attendance = Attendance.objects.filter(subject=subject_obj, session_year=session_year_obj)

        attendance_obj = []
        for attendance_single in attendance:
            data = {
                "id": attendance_single.id,
                "attendance_date": str(attendance_single.attendance_date),
                # Use new field name 'session_year' in JSON response
                "session_year_id": attendance_single.session_year.id # Kept original key name for template compatibility
            }
            attendance_obj.append(data)

        # Return JSON response
        return JsonResponse(json.dumps(attendance_obj), safe=False, content_type="application/json") # Explicit content_type
    except Exception as e:
        print(f"Error fetching attendance dates: {e}") # Log error
        return JsonResponse({"error": str(e)}, status=500) # Return error as JSON


# --- Admin Get Attendance Students (AJAX) ---
@csrf_exempt
def admin_get_attendance_student(request):
    # attendance_date is actually the Attendance ID
    attendance_id = request.POST.get("attendance_date") # Renamed variable for clarity

    try:
        # Use get_object_or_404 for safer lookup
        attendance = get_object_or_404(Attendance, id=attendance_id)

        # Filter AttendanceReport using new field name 'attendance'
        attendance_data = AttendanceReport.objects.filter(attendance=attendance)

        list_data = []
        for student_report in attendance_data: # Renamed variable for clarity
            data_small = {
                # Access CustomUser ID and name via the related student object using new field names
                "id": student_report.student.user.id,
                "name": f"{student_report.student.user.first_name} {student_report.student.user.last_name}",
                "status": student_report.status
            }
            list_data.append(data_small)

        # Return JSON response
        return JsonResponse(json.dumps(list_data), content_type="application/json", safe=False)
    except Exception as e:
        print(f"Error fetching attendance students: {e}") # Log error
        return JsonResponse({"error": str(e)}, status=500) # Return error as JSON


def admin_profile(request):
    # Use get_object_or_404 for safer lookup
    user = get_object_or_404(CustomUser, id=request.user.id)
    return render(request, "admin_home/admin_profile.html", {"user": user})

def admin_profile_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("admin_profile"))
    else:
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        password = request.POST.get("password") # Handle password change carefully

        try:
            # Use get_object_or_404 for safer lookup
            customuser = get_object_or_404(CustomUser, id=request.user.id)
            customuser.first_name = first_name
            customuser.last_name = last_name

            # Handle password change ONLY if a new password is provided
            if password: # Check if password is not None and not an empty string
                customuser.set_password(password)

            customuser.save()
            messages.success(request, "Successfully Updated Profile")
            return HttpResponseRedirect(reverse("admin_profile"))
        except Exception as e: # Catch specific exceptions if possible
            messages.error(request, f"Failed to Update Profile: {e}") # Show error message
            return HttpResponseRedirect(reverse("admin_profile"))

def admin_send_notification_student(request):
    students = Students.objects.all()
    return render(request,"admin_home/student_notification.html",{"students":students})

def admin_send_notification_staff(request):
    staffs = Staffs.objects.all()
    return render(request,"admin_home/staff_notification.html",{"staffs":staffs})

# --- Send Student Notification (AJAX) ---
@csrf_exempt
def send_student_notification(request):
    # id here is the CustomUser ID of the student
    student_user_id = request.POST.get("id")
    message = request.POST.get("message")

    try:
        # Get the Students object using the CustomUser ID
        # Use get_object_or_404 for safer lookup
        student = get_object_or_404(Students, user=student_user_id) # Use new field name 'user'

        token = student.fcm_token
        # Check if token exists before sending
        if not token:
            print(f"No FCM token found for student user ID: {student_user_id}")
            # You might want to return an error response here
            return HttpResponse("No FCM token")


        # --- FCM Sending Logic (Review URL and Auth Key) ---
        # NOTE: The URL format 'v1/projects/myproject-b5ae1/messages:send' is for Firebase Cloud Messaging HTTP v1 API.
        # This requires a service account key and a different authorization header ('Bearer <token>').
        # The 'key=AAAA...' format is for the legacy HTTP protocol, which uses a different endpoint URL:
        # https://fcm.googleapis.com/fcm/send
        # You need to use the correct URL and authorization header for the API you are using.
        # The provided key looks like a legacy server key. If so, the URL should be https://fcm.googleapis.com/fcm/send
        # If using the v1 API, you need to handle authentication differently.

        # Assuming you intend to use the LEGACY HTTP protocol with the provided key:
        fcm_send_url = "https://fcm.googleapis.com/fcm/send"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "key=AAAAgOmANU8:APA91bEtqGZ2ywNyTxaJWqTxcgKoKzQjOIA2O98hpgOenMnrfqJYWzFHhiuB7Pegpys-m4UiOd7SluGkMF1d26kcajiWr22iuYNyJzlEJDfB_GxNJ3eagx7d32On9x-DaGH2MPCBMVGX" # Your Server Key
        }
        body = {
            "notification": {
                "title": "School Management System",
                "body": message,
                # Consider making click_action a proper URL or handling in the app
                "click_action": "127.0.0.1/student_all_notification", # This is likely not a valid action for a mobile app
                "icon": "http://studentmanagementsystem22.herokuapp.com/static/dist/img/user2-160x160.jpg" # Ensure this URL is publicly accessible
            },
            "to": token # Device token
        }
        # --- End FCM Sending Logic ---

        data = requests.post(fcm_send_url, data=json.dumps(body), headers=headers)
        print("FCM Response:", data.text) # Print the response for debugging

        # Create the NotificationStudent object using the new field name 'student'
        notification = NotificationStudent(student=student, message=message)
        notification.save()

        return HttpResponse("True") # Indicate success to the AJAX call

    except Students.DoesNotExist:
        print(f"Student with user ID {student_user_id} not found.")
        return HttpResponse("Student not found") # Indicate error to AJAX call
    except requests.exceptions.RequestException as e:
        print(f"Error sending FCM notification: {e}")
        return HttpResponse("FCM send failed") # Indicate error to AJAX call
    except Exception as e: # Catch other potential errors
        print(f"An unexpected error occurred: {e}")
        return HttpResponse("False") # Indicate generic error


# --- Send Staff Notification (AJAX) ---
@csrf_exempt
def send_staff_notification(request):
    # id here is the CustomUser ID of the staff
    staff_user_id = request.POST.get("id")
    message = request.POST.get("message")

    try:
        # Get the Staffs object using the CustomUser ID
        # Use get_object_or_404 for safer lookup
        staff = get_object_or_404(Staffs, user=staff_user_id) # Use new field name 'user'

        token = staff.fcm_token
         # Check if token exists before sending
        if not token:
            print(f"No FCM token found for staff user ID: {staff_user_id}")
            return HttpResponse("No FCM token")

        # --- FCM Sending Logic (Review URL and Auth Key) ---
        # Assuming you intend to use the LEGACY HTTP protocol with the provided key:
        fcm_send_url = "https://fcm.googleapis.com/fcm/send"
        headers = {
            "Content-Type": "application/json",
             "Authorization": "key=AAAAgOmANU8:APA91bEtqGZ2ywNyTxaJWqTxcgKoKzQjOIA2O98hpgOenMnrfqJYWzFHhiuB7Pegpys-m4UiOd7SluGkMF1d26kcajiWr22iuYNyJzlEJDfB_GxNJ3eagx7d32On9x-DaGH2MPCBMVGX" # Your Server Key
        }
        body = {
            "notification": {
                "title": "School Management System",
                "body": message,
                 # Consider making click_action a proper URL or handling in the app
                "click_action": "127.0.0.1:8000/staff_all_notification", # This is likely not a valid action for a mobile app
                "icon": "http://studentmanagementsystem22.herokuapp.com/static/dist/img/user2-160x160.jpg" # Ensure this URL is publicly accessible
            },
            "to": token # Device token
        }
         # --- End FCM Sending Logic ---

        data = requests.post(fcm_send_url, data=json.dumps(body), headers=headers)
        print("FCM Response:", data.text) # Print the response for debugging


        # Create the NotificationStaffs object using the new field name 'staff'
        notification = NotificationStaffs(staff=staff, message=message)
        notification.save()

        return HttpResponse("True") # Indicate success to the AJAX call

    except Staffs.DoesNotExist:
        print(f"Staff with user ID {staff_user_id} not found.")
        return HttpResponse("Staff not found") # Indicate error to AJAX call
    except requests.exceptions.RequestException as e:
        print(f"Error sending FCM notification: {e}")
        return HttpResponse("FCM send failed") # Indicate error to AJAX call
    except Exception as e: # Catch other potential errors
        print(f"An unexpected error occurred: {e}")
        return HttpResponse("False") # Indicate generic error