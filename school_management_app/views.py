from email import message
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from school_management_app.EmailBackEnd import EmailBackEnd


# Create your views here.


def Logindon(request):
    return render(request, "login_page.html")
def Demopage(request):
    return render(request, "demo.html")

def doLogin(request):
    if request.method!="POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        user=EmailBackEnd.authenticate(request,username=request.POST.get("username"),password=request.POST.get("password"))
        if user!=None:
            login(request,user)
            if user.user_type=="1":
                return HttpResponseRedirect("admin_home")
            elif user.user_type=="2":
                return HttpResponseRedirect(reverse("staff_home"))
            else:
                return HttpResponseRedirect(reverse("student_home"))
        else:
            messages.error(request,"Invalid Login Details")
            return HttpResponseRedirect("/")

def GetUserDetails(request):
    if request.user!=None:
        return HttpResponse("User : "+request.user.email+" usertype : "+(request.user.user_type))
    else:
        return HttpResponse("Please Login First")

def StudentHome(request):
    return render(request, "student_template/base_template.html")

def logout_user(request):
    logout(request)
    return HttpResponseRedirect("/")


def showFirebaseJS(request):
    data='importScripts("https://www.gstatic.com/firebasejs/7.14.6/firebase-app.js");' \
         'importScripts("https://www.gstatic.com/firebasejs/7.14.6/firebase-messaging.js"); ' \
         'var firebaseConfig = {' \
         '        apiKey: "AIzaSyBcMOsGMY1ICaPu2XcPrzs2UzvMae1_REg",' \
         '        authDomain: "schoolmanagementsystem-ed016.firebaseapp.com",' \
         '        databaseURL: "https://schoolmanagementsystem-ed016-default-rtdb.firebaseio.com",' \
         '        projectId: "schoolmanagementsystem-ed016",' \
         '        storageBucket: "schoolmanagementsystem-ed016.appspot.com",' \
         '        messagingSenderId: "553673307471",' \
         '        appId: "1:553673307471:web:6522986dde31ccdad3813a",' \
         '        measurementId: "G-EHCB4PWFRK"' \
         ' };' \
         'firebase.initializeApp(firebaseConfig);' \
         'const messaging=firebase.messaging();' \
         'messaging.setBackgroundMessageHandler(function (payload) {' \
         '    console.log(payload);' \
         '    const notification=JSON.parse(payload);' \
         '    const notificationOption={' \
         '        body:notification.body,' \
         '        icon:notification.icon' \
         '    };' \
         '    return self.registration.showNotification(payload.notification.title,notificationOption);' \
         '});'

    return HttpResponse(data,content_type="text/javascript")



    