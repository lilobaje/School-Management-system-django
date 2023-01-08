from fileinput import filename
import json

from django.db.models import Q
from django import forms
from .filters import StaffsFilter
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from mysqlx import Session
import requests
from school_management_app.filters import StaffsFilter

from school_management_app.forms import AddStudentForm, EditStudentForm
from school_management_app.models import (Courses, CustomUser, FeedBackStaffs,
                                          FeedBackStudent, SessionYearModel,
                                          Staffs, Students, Subjects,LeaveReportStudent,LeaveReportStaff,AttendanceReport,Attendance
                                          ,NotificationStaffs,NotificationStudent)


def AdminHome(request):
    student_count1=Students.objects.all().count()
    staff_count=Staffs.objects.all().count()
    subject_count=Subjects.objects.all().count()
    course_count=Courses.objects.all().count()

    course_all=Courses.objects.all()
    course_name_list=[]
    subject_count_list=[]
    student_count_list_in_course=[]
    for course in course_all:
        subjects=Subjects.objects.filter(course_id=course.id).count()
        students=Students.objects.filter(course_id=course.id).count()
        course_name_list.append(course.course_name)
        subject_count_list.append(subjects)
        student_count_list_in_course.append(students)

    subjects_all=Subjects.objects.all()
    subject_list=[]
    student_count_list_in_subject=[]
    for subject in subjects_all:
        course=Courses.objects.get(id=subject.course_id.id)
        student_count=Students.objects.filter(course_id=course.id).count()
        subject_list.append(subject.subject_name)
        student_count_list_in_subject.append(student_count)

    staffs=Staffs.objects.all()
    attendance_present_list_staff=[]
    attendance_absent_list_staff=[]
    staff_name_list=[]
    for staff in staffs:
        subject_ids=Subjects.objects.filter(staff_id=staff.admin.id)
        attendance=Attendance.objects.filter(subject_id__in=subject_ids).count()
        leaves=LeaveReportStaff.objects.filter(staff_id=staff.id,leave_status=1).count()
        attendance_present_list_staff.append(attendance)
        attendance_absent_list_staff.append(leaves)
        staff_name_list.append(staff.admin.username)

    students_all=Students.objects.all()
    attendance_present_list_student=[]
    attendance_absent_list_student=[]
    student_name_list=[]
    for student in students_all:
        attendance=AttendanceReport.objects.filter(student_id=student.id,status=True).count()
        absent=AttendanceReport.objects.filter(student_id=student.id,status=False).count()
        leaves=LeaveReportStudent.objects.filter(student_id=student.id,leave_status=1).count()
        attendance_present_list_student.append(attendance)
        attendance_absent_list_student.append(leaves+absent)
        student_name_list.append(student.admin.username)


    return render(request,"admin_home/home_content.html",{"student_count":student_count1,"staff_count":staff_count,"subject_count":subject_count,"course_count":course_count,"course_name_list":course_name_list,"subject_count_list":subject_count_list,"student_count_list_in_course":student_count_list_in_course,"student_count_list_in_subject":student_count_list_in_subject,"subject_list":subject_list,"staff_name_list":staff_name_list,"attendance_present_list_staff":attendance_present_list_staff,"attendance_absent_list_staff":attendance_absent_list_staff,"student_name_list":student_name_list,"attendance_present_list_student":attendance_present_list_student,"attendance_absent_list_student":attendance_absent_list_student})




def StaffHome(request):
    return render(request, "staff_template/base_template.html")

def Add_staff(request):
    return render(request,"admin_home/add_staff_temp.html")

def deletestaff(request,staff_id):
    staff= Staffs.objects.get(admin=staff_id)
    if request.method == 'POST':
        staff.delete()
        return redirect('manage_staff')
    return render(request,'admin_home/delete.html', {'obj':staff})

def deletestudent(request,student_id):
    student= Students.objects.get(admin=student_id)
    if request.method == 'POST':
        student.delete()
        return redirect('manage_student')
    return render(request,'admin_home/delete.html', {'obj':student})


def Add_student(request):
    courses=Courses.objects.all()
    form=AddStudentForm()
    return render(request,"admin_home/add_student_temp.html",{"form":form})

def Add_student_save(request):
    if request.method!="POST":
        return HttpResponse("Method Not Allowed")
    else:
        form=AddStudentForm(request.POST,request.FILES)
        if form.is_valid():
                    first_name=form.cleaned_data["first_name"]
                    last_name=form.cleaned_data["last_name"]
                    username=form.cleaned_data["username"]
                    email=form.cleaned_data["email"]
                    password=form.cleaned_data["password"]
                    address=form.cleaned_data["address"]
                    session_year_id=form.cleaned_data["session_year_id"]
                    course_id=form.cleaned_data["course"]
                    sex=form.cleaned_data["sex"]
                    age=form.cleaned_data['age']
                    
                    profile_pic=request.FILES['profile_pic']
                    fs=FileSystemStorage()
                    filename=fs.save(profile_pic.name,profile_pic)
                    profile_pic_url=fs.url(filename)
                   
                    try:
                        user=CustomUser.objects.create_user(username=username,password=password,last_name=last_name,first_name=first_name,user_type=3)
                        user.students.address=address
                        course_obj=Courses.objects.get(id=course_id)
                        user.students.course_id=course_obj
                        session_year=SessionYearModel.objects.get(id=session_year_id)
                        user.students.session_year_id=session_year
                        user.students.email=email
                        user.students.gender=sex
                        user.students.age=age
                        user.students.profile_pic=profile_pic_url
                        user.save()           
                        messages.success(request,"Successfully Added Student")
                        return HttpResponseRedirect(reverse("add_student"))
                    except:
                        messages.error(request,"Failed to Add Student")
                        return HttpResponseRedirect(reverse("add_student"))
        else:
                form=AddStudentForm(request.POST)
                return render(request, "admin_home/add_student_temp.html", {"form": form})

def Edit_student(request, student_id):
    courses=Courses.objects.all()
    student=Students.objects.get(admin=student_id)
    request.session['student_id']=student_id
    student=Students.objects.get(admin=student_id)
    form=EditStudentForm()
    form.fields['email'].initial=student.admin.email
    form.fields['first_name'].initial=student.admin.first_name
    form.fields['last_name'].initial=student.admin.last_name
    form.fields['username'].initial=student.admin.username
    form.fields['address'].initial=student.address
    form.fields['course'].initial=student.course_id.id
    form.fields['sex'].initial=student.gender
    form.fields['age'].initial=student.age
    form.fields['session_year_id'].initial=student.session_year_id.id
   
    return render(request,"admin_home/edit_student_temp.html",{"form":form,"id":student_id,"username":student.admin.username})
  

def Edit_student_save(request):
    if request.method!="POST":
        return HttpResponse("Method Not Allowed")
    else:
        student_id=request.session.get("student_id")
        if student_id==None:
            return HttpResponseRedirect(reverse("manage_student"))

        form=EditStudentForm(request.POST,request.FILES)
        if form.is_valid():
            first_name = form.cleaned_data["first_name"]
            last_name = form.cleaned_data["last_name"]
            username = form.cleaned_data["username"]
            email = form.cleaned_data["email"]
            address = form.cleaned_data["address"]
            session_year_id=form.cleaned_data["session_year_id"]
            course_id = form.cleaned_data["course"]
            sex = form.cleaned_data["sex"]
            age = form.cleaned_data['age']

            if request.FILES.get('profile_pic',False):
                profile_pic=request.FILES['profile_pic']
                fs=FileSystemStorage()
                filename=fs.save(profile_pic.name,profile_pic)
                profile_pic_url=fs.url(filename)
            else:
                profile_pic_url=None

            try:
                user=CustomUser.objects.get(id=student_id)
                user.first_name=first_name
                user.last_name=last_name
                user.username=username
                user.email=email
                user.save()
                student=Students.objects.get(admin=student_id)
                student.address=address
                session_year = SessionYearModel.objects.get(id=session_year_id)
                student.session_year_id = session_year
                student.gender=sex
                student.age=age
                course=Courses.objects.get(id=course_id)
                student.course_id=course
                if profile_pic_url!=None:
                    student.profile_pic=profile_pic_url
                student.save()
                del request.session['student_id']
                messages.success(request,"Successfully Edited Student")
                return HttpResponseRedirect(reverse("edit_student",kwargs={"student_id":student_id}))
            except:  
                messages.error(request,"Failed to Edit Student")
                return HttpResponseRedirect(reverse("edit_student",kwargs={"student_id":student_id}))
        else:
            form=EditStudentForm(request.POST)
            student=Students.objects.get(admin=student_id)
            return render(request,"admin_home/edit_student_temp.html",{"form":form,"id":student_id,"username":student.admin.username})


def Add_subject(request):
    courses=Courses.objects.all()
    staffs=CustomUser.objects.filter(user_type=2)
    return render(request,"admin_home/add_subject_temp.html",{"staffs":staffs,"courses":courses})

def Add_subject_save(request):
    if request.method!="POST":
        return HttpResponse("<h2>Method not Allowed</h2>")
    else:

        subject_name=request.POST.get("subject_name")
        staff_id=request.POST.get("staff")
        course_id=request.POST.get("course")
        staff=CustomUser.objects.get(id=staff_id)
        course=Courses.objects.get(id=course_id)

        try:
            subject=Subjects(subject_name=subject_name,course_id=course,staff_id=staff)
            subject.save()
            messages.success(request,"Successfully Added Subject")
            return HttpResponseRedirect(reverse("add_subject"))
        except:
            messages.error(request,"Failed to Add Subject")
            return HttpResponseRedirect(reverse("add_subject"))




def Add_course(request):
    return render(request,"admin_home/add_course_temp.html")

def Add_course_save(request):
    if request.method!="POST":
        return HttpResponseRedirect("Method Not Allowed!")
    else:
        course=request.POST.get("course")
        try:
            course_model=Courses(course_name=course)
            course_model.save()
        
            messages.success(request,"Successfully Added course")
            return HttpResponseRedirect(reverse("add_course"))
        except:
            messages.error(request,"Failed to Add course")
            return HttpResponseRedirect(reverse("add_course"))
        





def add_staff_save(request):
    if request.method!="POST":
        return HttpResponse("Method Not Allowed")
    else:
        first_name=request.POST.get("first_name")
        last_name=request.POST.get("last_name")
        username=request.POST.get("username")
        email=request.POST.get("email")
        password=request.POST.get("password")
        address=request.POST.get("address")        
        try:
            user=CustomUser.objects.create_user(username=username,password=password,last_name=last_name,first_name=first_name,user_type=2)
            user.staffs.address=address
            user.staffs.email=email
            user.save()
            messages.success(request,"Successfully Added Staff")
            return HttpResponseRedirect(reverse("add_staff"))
        except:
            messages.error(request,"Failed to Add Staff")
            return HttpResponseRedirect(reverse("add_staff"))


def Manage_staff(request):
    staffs=Staffs.objects.all()
    Staffs_Filter=StaffsFilter(request.GET, queryset=staffs)
    context = {'Staffs_Filter':Staffs_Filter, 'staffs':staffs}
    return render(request,"admin_home/manage_staff_temp.html",context)

def edit_staff(request,staff_id):
    staff=Staffs.objects.get(admin=staff_id)
    return render(request,"admin_home/edit_staff_temp.html",{"staff":staff,"id":staff_id})

def Edit_staff_save(request):
    if request.method!="POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        staff_id=request.POST.get("staff_id")
        first_name=request.POST.get("first_name")
        last_name=request.POST.get("last_name")
        email=request.POST.get("email")
        username=request.POST.get("username")
        address=request.POST.get("address")

        try:
            user=CustomUser.objects.get(id=staff_id)
            user.first_name=first_name
            user.last_name=last_name
            user.email=email
            user.username=username
            user.save()

            staff_model=Staffs.objects.get(admin=staff_id)
            staff_model.address=address
            staff_model.save()
            messages.success(request,"Successfully Edited Staff")
            return HttpResponseRedirect(reverse("edit_staff",kwargs={"staff_id":staff_id}))
        except:
            messages.error(request,"Failed to Edit Staff")
            return HttpResponseRedirect(reverse("edit_staff",kwargs={"staff_id":staff_id}))





def Manage_student(request):
   
    students=Students.objects.all()
    context = {'students':students }
    return render(request,"admin_home/manage_student_temp.html",context)

def Search_student(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    students=Students.objects.filter(
        Q(email__icontains=q) 
        
        
    
    )
    context = {'students':students }
    return render(request,"admin_home/search_student_temp.html",context)



def modal(request):
    
    return render(request,"admin_home/modals.html")



def Manage_course(request):
    courses=Courses.objects.all()
    return render(request,"admin_home/manage_course_temp.html",{"courses":courses})

def Edit_course(request,course_id):
    course=Courses.objects.get(id=course_id)
    return render(request,"admin_home/edit_course_temp.html",{"course":course,"id":course_id})

def Edit_course_save(request):
    if request.method!="POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        course_id=request.POST.get("course_id")
        course_name=request.POST.get("course")

        try:
            course=Courses.objects.get(id=course_id)
            course.course_name=course_name
            course.save()
            messages.success(request,"Successfully Edited Course")
            return HttpResponseRedirect(reverse("edit_course",kwargs={"course_id":course_id}))
        except:
            messages.error(request,"Failed to Edit Course")
            return HttpResponseRedirect(reverse("edit_course",kwargs={"course_id":course_id}))






def Manage_subject(request):
    subjects=Subjects.objects.all()
    return render(request,"admin_home/manage_subject_temp.html",{"subjects":subjects})

def Edit_subject(request,subject_id):
    subject=Subjects.objects.get(id=subject_id)
    courses=Courses.objects.all()
    staffs=CustomUser.objects.filter(user_type=2)
    return render(request,"admin_home/edit_subject_temp.html",{"subject":subject,"staffs":staffs,"courses":courses,"id":subject_id})

def Edit_subject_save(request):
    if request.method!="POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        subject_id=request.POST.get("subject_id")
        subject_name=request.POST.get("subject_name")
        staff_id=request.POST.get("staff")
        course_id=request.POST.get("course")

        try:
            subject=Subjects.objects.get(id=subject_id)
            subject.subject_name=subject_name
            staff=CustomUser.objects.get(id=staff_id)
            subject.staff_id=staff
            course=Courses.objects.get(id=course_id)
            subject.course_id=course
            subject.save()

            messages.success(request,"Successfully Edited Subject")
            return HttpResponseRedirect(reverse("edit_subject",kwargs={"subject_id":subject_id}))
        except:
            messages.error(request,"Failed to Edit Subject")
            return HttpResponseRedirect(reverse("edit_subject",kwargs={"subject_id":subject_id}))


def manage_session(request):
    return render(request, "admin_home/manage_session_temp.html")

def add_session_save(request):
    if request.method!="POST":
        return HttpResponseRedirect(reverse(manage_session))
    else:
        session_start_year=request.POST.get("session_start")
        session_end_year=request.POST.get("session_end")

        try:
            sessionyear=SessionYearModel(session_start_year=session_start_year,session_end_year=session_end_year)
            sessionyear.save()
            messages.success(request,"Successfully Added Session")
            return HttpResponseRedirect(reverse("manage_session"))
        except:
            messages.error(request,"Failed to Add Session")
            return HttpResponseRedirect(reverse("manage_session"))


@csrf_exempt
def check_email_exist(request):
    email=request.POST.get("email")
    user_obj=CustomUser.objects.filter(email=email).exists()
    if user_obj:
        return HttpResponse(True)
    else:
        return HttpResponse(False)

@csrf_exempt
def check_username_exist(request):
    username=request.POST.get("username")
    user_obj=CustomUser.objects.filter(username=username).exists()
    if user_obj:
        return HttpResponse(True)
    else:
        return HttpResponse(False)

def staff_feedback_message(request):
    feedbacks=FeedBackStaffs.objects.all()
    return render(request,"admin_home/staff_feedback_template.html",{"feedbacks":feedbacks})

def student_feedback_message(request):
    feedbacks=FeedBackStudent.objects.all()
    return render(request,"admin_home/student_feedback_template.html",{"feedbacks":feedbacks})

@csrf_exempt
def student_feedback_message_replied(request):
    feedback_id=request.POST.get("id")
    feedback_message=request.POST.get("message")

    try:
        feedback=FeedBackStudent.objects.get(id=feedback_id)
        feedback.feedback_reply=feedback_message
        feedback.save()
        return HttpResponse("True")
    except:
        return HttpResponse("False")

@csrf_exempt
def staff_feedback_message_replied(request):
    feedback_id=request.POST.get("id")
    feedback_message=request.POST.get("message")

    try:
        feedback=FeedBackStaffs.objects.get(id=feedback_id)
        feedback.feedback_reply=feedback_message
        feedback.save()
        return HttpResponse("True")
    except:
        return HttpResponse("False")

    
def staff_leave_view(request):
    leaves=LeaveReportStaff.objects.all()
    return render(request,"admin_home/staff_leave_view.html",{"leaves":leaves})

def student_leave_view(request):
    leaves=LeaveReportStudent.objects.all()
    return render(request,"admin_home/student_leave_view.html",{"leaves":leaves})

def student_approve_leave(request,leave_id):
    leave=LeaveReportStudent.objects.get(id=leave_id)
    leave.leave_status=1
    leave.save()
    return HttpResponseRedirect(reverse("student_leave_view"))

def student_disapprove_leave(request,leave_id):
    leave=LeaveReportStudent.objects.get(id=leave_id)
    leave.leave_status=2
    leave.save()
    return HttpResponseRedirect(reverse("student_leave_view"))



def staff_approve_leave(request,leave_id):
    leave=LeaveReportStaff.objects.get(id=leave_id)
    leave.leave_status=1
    leave.save()
    return HttpResponseRedirect(reverse("staff_leave_view"))

def staff_disapprove_leave(request,leave_id):
    leave=LeaveReportStaff.objects.get(id=leave_id)
    leave.leave_status=2
    leave.save()
    return HttpResponseRedirect(reverse("staff_leave_view"))


def admin_view_attendance(request):
    subjects=Subjects.objects.all()
    session_year_id=SessionYearModel.objects.all()
    return render(request,"admin_home/admin_view_attendance.html",{"subjects":subjects,"session_year_id":session_year_id})

@csrf_exempt
def admin_get_attendance_dates(request):
    subject=request.POST.get("subject")
    session_year_id=request.POST.get("session_year_id")
    subject_obj=Subjects.objects.get(id=subject)
    session_year_obj=SessionYearModel.objects.get(id=session_year_id)
    attendance=Attendance.objects.filter(subject_id=subject_obj,session_year_id=session_year_obj)
    attendance_obj=[]
    for attendance_single in attendance:
        data={"id":attendance_single.id,"attendance_date":str(attendance_single.attendance_date),"session_year_id":attendance_single.session_year_id.id}
        attendance_obj.append(data)

    return JsonResponse(json.dumps(attendance_obj),safe=False)


@csrf_exempt
def admin_get_attendance_student(request):
    attendance_date=request.POST.get("attendance_date")
    attendance=Attendance.objects.get(id=attendance_date)

    attendance_data=AttendanceReport.objects.filter(attendance_id=attendance)
    list_data=[]

    for student in attendance_data:
        data_small={"id":student.student_id.admin.id,"name":student.student_id.admin.first_name+" "+student.student_id.admin.last_name,"status":student.status}
        list_data.append(data_small)
    return JsonResponse(json.dumps(list_data),content_type="application/json",safe=False)


def admin_profile(request):
    user=CustomUser.objects.get(id=request.user.id)
    return render(request,"admin_home/admin_profile.html",{"user":user})

def admin_profile_save(request):
    if request.method!="POST":
        return HttpResponseRedirect(reverse("admin_profile"))
    else:
        first_name=request.POST.get("first_name")
        last_name=request.POST.get("last_name")
        password=request.POST.get("password")
        try:
            customuser=CustomUser.objects.get(id=request.user.id)
            customuser.first_name=first_name
            customuser.last_name=last_name
            # if password!=None and password!="":
            #     customuser.set_password(password)
            customuser.save()
            messages.success(request, "Successfully Updated Profile")
            return HttpResponseRedirect(reverse("admin_profile"))
        except:
            messages.error(request, "Failed to Update Profile")
            return HttpResponseRedirect(reverse("admin_profile"))

def admin_send_notification_student(request):
    students=Students.objects.all()
    return render(request,"admin_home/student_notification.html",{"students":students})

def admin_send_notification_staff(request):
    staffs=Staffs.objects.all()
    return render(request,"admin_home/staff_notification.html",{"staffs":staffs})

@csrf_exempt
def send_student_notification(request):
    id=request.POST.get("id")
    message=request.POST.get("message")
    student=Students.objects.get(admin=id)
    token=student.fcm_token
    url="https://fcm.googleapis.com/v1/projects/myproject-b5ae1/messages:send"
    body={
        "notification":{
            "title":"School Management System",
            "body":message,
            "click_action": "127.0.0.1/student_all_notification",
            "icon": "http://studentmanagementsystem22.herokuapp.com/static/dist/img/user2-160x160.jpg"
        },
        "to":token
    }
    headers={"Content-Type":"application/json","Authorization":"key=AAAAgOmANU8:APA91bEtqGZ2ywNyTxaJWqTxcgKoKzQjOIA2O98hpgOenMnrfqJYWzFHhiuB7Pegpys-m4UiOd7SluGkMF1d26kcajiWr22iuYNyJzlEJDfB_GxNJ3eagx7d32On9x-DaGH2MPCBMVGX"}
    data=requests.post(url,data=json.dumps(body),headers=headers)
    notification=NotificationStudent(student_id=student,message=message)
    notification.save()
    print(data.text)
    return HttpResponse("True")

@csrf_exempt
def send_staff_notification(request):
    id=request.POST.get("id")
    message=request.POST.get("message")
    staff=Staffs.objects.get(admin=id)
    token=staff.fcm_token
    url="https://fcm.googleapis.com/v1/projects/myproject-b5ae1/messages:send"
    body={
        "notification":{
            "title":"School Management System",
            "body":message,
            "click_action":"127.0.0.1:8000/staff_all_notification",
            "icon":"http://studentmanagementsystem22.herokuapp.com/static/dist/img/user2-160x160.jpg"
        },
        "to":token
    }
    headers={"Content-Type":"application/json","Authorization":"key=AAAAgOmANU8:APA91bEtqGZ2ywNyTxaJWqTxcgKoKzQjOIA2O98hpgOenMnrfqJYWzFHhiuB7Pegpys-m4UiOd7SluGkMF1d26kcajiWr22iuYNyJzlEJDfB_GxNJ3eagx7d32On9x-DaGH2MPCBMVGX"}
    data=requests.post(url,data=json.dumps(body),headers=headers)
    notification=NotificationStaffs(staff_id=staff,message=message)
    notification.save()
    print(data.text)
    return HttpResponse("True")

