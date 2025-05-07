"""School_management_system URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls.static import static

# Removed: from django import views # Use specific imports instead
from django.contrib import admin
from django.urls import path, include

from School_management_system import settings # Project settings

# Import views from your app
from school_management_app import adminviews, StaffViews, StudentViews, views as school_views # Renamed app's views import to avoid conflict
# Removed: from school_management_app import forms, EditResultVIewClass # forms not used here, EditResultVIewClass imported below if needed
from school_management_app.EditResultVIewClass import EditResultViewClass # Import the class directly


urlpatterns = [
    path('admin/', admin.site.urls),
    # Changed views.Demopage to school_views.Demopage
    path('demopage/', school_views.Demopage, name="Demopage"), # Added trailing slash
    path('accounts/', include('django.contrib.auth.urls')),

    # Changed views.Logindon to school_views.Logindon, etc.
    path('', school_views.Logindon, name="Logindon"),
    path('dologin/', school_views.doLogin, name="do_login"), # Added trailing slash
    path('get_user_details/', school_views.GetUserDetails), # Added trailing slash
    path('logout_user/', school_views.logout_user, name="logout"), # Added trailing slash

    # Admin Views URLs (Updated Student Edit/Save URLs)
    path('admin_home/', adminviews.AdminHome, name="admin_home"), # Added trailing slash
    path('add_staff/', adminviews.Add_staff, name="add_staff"), # Added trailing slash
    path('add_staff_save/', adminviews.add_staff_save, name="add_staff_save"), # Added trailing slash
    path('add_student/', adminviews.Add_student, name="add_student"), # Added trailing slash
    path('add_student_save/', adminviews.Add_student_save, name="add_student_save"), # Added trailing slash
    path('add_subject/', adminviews.Add_subject, name="add_subject"), # Added trailing slash
    path('add_subject_save/', adminviews.Add_subject_save, name="add_subject_save"), # Added trailing slash
    path('edit_subject/<str:subject_id>/', adminviews.Edit_subject, name="edit_subject"), # Added trailing slash
    path('edit_subject_save/', adminviews.Edit_subject_save, name="edit_subject_save"), # Added trailing slash
    path('add_course/', adminviews.Add_course, name="add_course"), # Added trailing slash
    path('add_course_save/', adminviews.Add_course_save, name="add_course_save"), # Added trailing slash
    path('edit_course/<str:course_id>/', adminviews.Edit_course, name="edit_course"), # Added trailing slash
    path('edit_course_save/', adminviews.Edit_course_save, name="edit_course_save"), # Added trailing slash
    path('manage_staff/', adminviews.Manage_staff, name="manage_staff"), # Added trailing slash
    path('manage_student/', adminviews.Manage_student, name="manage_student"), # Added trailing slash
    path('manage_course/', adminviews.Manage_course, name="manage_course"), # Added trailing slash
    path('manage_subject/', adminviews.Manage_subject, name="manage_subject"), # Added trailing slash
    path('edit_staff/<str:staff_id>/', adminviews.edit_staff, name="edit_staff"), # Added trailing slash
    path('edit_staff_save/', adminviews.Edit_staff_save, name="edit_staff_save"), # Added trailing slash
    path('modal/', adminviews.modal, name="modal"), # Added trailing slash

    # CORRECTED STUDENT EDIT/SAVE URLS
    # This URL displays the edit form and passes student_id to Edit_student view
    path('edit_student/<str:student_id>/', adminviews.Edit_student, name="edit_student"), # Note: Duplicate name 'edit_student' will cause issues if defined elsewhere. This replaces the incorrect one below.

    # This URL processes the form submission and does NOT capture student_id from the URL
    # Ensure your form action points to this URL name 'edit_student_save'
    path('edit_student_save/', adminviews.Edit_student_save, name="edit_student_save"), # Added trailing slash


    # Removed the incorrect duplicate line:
    # path('edit_student/<str:student_id>', adminviews.Edit_student_save,name="Edit_student_save"), # REMOVE THIS LINE

    # Staff Views URLs
    path('staff_home/', StaffViews.staff_home, name="staff_home"), # Added trailing slash
    path('staff_take_attendance/', StaffViews.staff_take_attendance, name="staff_take_attendance"), # Added trailing slash
    # Corrected: student_home appears twice, keep only one unique name
    # path('student_home', StudentViews.student_home, name="student_home"), # REMOVE DUPLICATE

    # Admin Views URLs (continued)
    path('manage_session/', adminviews.manage_session, name="manage_session"), # Added trailing slash
    path('add_session_save/', adminviews.add_session_save, name="add_session_save"), # Added trailing slash
    path('get_students/', StaffViews.get_students, name="get_students"), # Added trailing slash
    path('save_attendance_data/', StaffViews.save_attendance_data, name="save_attendance_data"), # Added trailing slash
    path('staff_update_attendance/', StaffViews.staff_update_attendance, name="staff_update_attendance"), # Added trailing slash
    path('get_attendance_dates/', StaffViews.get_attendance_dates, name="get_attendance_dates"), # Added trailing slash
    path('get_attendance_student/', StaffViews.get_attendance_student, name="get_attendance_student"), # Added trailing slash
    path('save_updateattendance_data/', StaffViews.save_updateattendance_data, name="save_updateattendance_data"), # Added trailing slash
    path('staff_apply_leave/', StaffViews.staff_apply_leave, name="staff_apply_leave"), # Added trailing slash
    path('staff_apply_leave_save/', StaffViews.staff_apply_leave_save, name="staff_apply_leave_save"), # Added trailing slash
    path('staff_feedback/', StaffViews.staff_feedback, name="staff_feedback"), # Added trailing slash
    path('staff_feedback_save/', StaffViews.staff_feedback_save, name="staff_feedback_save"), # Added trailing slash

    # Student Views URLs (continued)
    path('student_view_attendance/', StudentViews.student_view_attendance, name="student_view_attendance"), # Added trailing slash
    path('student_view_attendance_post/', StudentViews.student_view_attendance_post, name="student_view_attendance_post"), # Added trailing slash
    path('student_apply_leave/', StudentViews.student_apply_leave, name="student_apply_leave"), # Added trailing slash
    path('student_apply_leave_save/', StudentViews.student_apply_leave_save, name="student_apply_leave_save"), # Added trailing slash
    path('student_feedback/', StudentViews.student_feedback, name="student_feedback"), # Added trailing slash
    path('student_feedback_save/', StudentViews.student_feedback_save, name="student_feedback_save"), # Added trailing slash

    # Admin Views URLs (continued)
    path('check_email_exist/', adminviews.check_email_exist, name="check_email_exist"), # Added trailing slash
    path('check_username_exist/', adminviews.check_username_exist, name="check_username_exist"), # Added trailing slash
    path('student_feedback_message/', adminviews.student_feedback_message, name="student_feedback_message"), # Added trailing slash
    path('student_feedback_message_replied/', adminviews.student_feedback_message_replied, name="student_feedback_message_replied"), # Added trailing slash
    path('staff_feedback_message/', adminviews.staff_feedback_message, name="staff_feedback_message"), # Added trailing slash
    path('staff_feedback_message_replied/', adminviews.staff_feedback_message_replied, name="staff_feedback_message_replied"), # Added trailing slash
    path('student_leave_view/', adminviews.student_leave_view, name="student_leave_view"), # Added trailing slash
    path('staff_leave_view/', adminviews.staff_leave_view, name="staff_leave_view"), # Added trailing slash
    path('student_approve_leave/<str:leave_id>/', adminviews.student_approve_leave, name="student_approve_leave"), # Added trailing slash
    path('student_disapprove_leave/<str:leave_id>/', adminviews.student_disapprove_leave, name="student_disapprove_leave"), # Added trailing slash
    path('staff_disapprove_leave/<str:leave_id>/', adminviews.staff_disapprove_leave, name="staff_disapprove_leave"), # Added trailing slash
    path('staff_approve_leave/<str:leave_id>/', adminviews.staff_approve_leave, name="staff_approve_leave"), # Added trailing slash
    path('admin_view_attendance/', adminviews.admin_view_attendance, name="admin_view_attendance"), # Added trailing slash
    path('admin_get_attendance_dates/', adminviews.admin_get_attendance_dates, name="admin_get_attendance_dates"), # Added trailing slash
    path('admin_get_attendance_student/', adminviews.admin_get_attendance_student, name="admin_get_attendance_student"), # Added trailing slash
    path('admin_profile/', adminviews.admin_profile, name="admin_profile"), # Added trailing slash
    path('admin_profile_save/', adminviews.admin_profile_save, name="admin_profile_save"), # Added trailing slash
    path('admin_send_notification_staff/', adminviews.admin_send_notification_staff, name="admin_send_notification_staff"), # Added trailing slash
    path('admin_send_notification_student/', adminviews.admin_send_notification_student, name="admin_send_notification_student"), # Added trailing slash
    path('send_student_notification/', adminviews.send_student_notification, name="send_student_notification"), # Added trailing slash
    path('send_staff_notification/', adminviews.send_staff_notification, name="send_staff_notification"), # Added trailing slash

    # Staff Views URLs (continued)
    path('staff_profile/', StaffViews.staff_profile, name="staff_profile"), # Added trailing slash
    path('staff_profile_save/', StaffViews.staff_profile_save, name="staff_profile_save"), # Added trailing slash
    path('student_profile/', StudentViews.student_profile, name="student_profile"), # Added trailing slash
    path('student_profile_save/', StudentViews.student_profile_save, name="student_profile_save"), # Added trailing slash

    # Student Views URLs (continued)
    path('student_home/', StudentViews.student_home, name="student_home"), # Kept one student_home
    path('student_fcmtoken_save/', StudentViews.student_fcmtoken_save, name="student_fcmtoken_save"), # Added trailing slash

    # Staff Views URLs (continued)
    path('staff_fcmtoken_save/', StaffViews.staff_fcmtoken_save, name="staff_fcmtoken_save"), # Added trailing slash
    path('staff_all_notification/', StaffViews.staff_all_notification, name="staff_all_notification"), # Added trailing slash

    # Student Views URLs (continued)
    path('student_all_notification/', StudentViews.student_all_notification, name="student_all_notification"), # Added trailing slash

    # Other Views URLs
    path('firebase-messaging-sw.js/', school_views.showFirebaseJS, name="show_firebase_js"), # Added trailing slash

    # Student Views URLs (continued)
    path('join_class_room/<int:subject_id>/<int:session_year_id>/', StudentViews.join_class_room, name="join_class_room"), # Added trailing slash, confirmed int types

    # Staff Views URLs (continued)
    path('start_live_classroom/', StaffViews.start_live_classroom, name="start_live_classroom"), # Added trailing slash
    path('start_live_classroom_process/', StaffViews.start_live_classroom_process, name="start_live_classroom_process"), # Added trailing slash
    path('staff_add_result/', StaffViews.staff_add_result, name="staff_add_result"), # Added trailing slash
    path('save_student_result/', StaffViews.save_student_result, name="save_student_result"), # Added trailing slash

    # Staff/Admin Views URLs (Result Editing)
    # Ensure this class-based view correctly uses URL args if needed, or is configured for POST submission
    path('edit_student_result/', EditResultViewClass.as_view(), name="edit_student_result"), # Added trailing slash
    path('fetch_result_student/', StaffViews.fetch_result_student, name="fetch_result_student"), # Added trailing slash

    # Student Views URLs (continued)
    path('student_view_result/', StudentViews.student_view_result, name="student_view_result"), # Added trailing slash

    # Delete URLs
    path('deletestaff/<str:staff_id>/', adminviews.deletestaff, name='deletestaff'), # Added trailing slash
    path('deletestudent/<str:student_id>/', adminviews.deletestudent, name='deletestudent'), # Added trailing slash

    # Search URL
    path('Search_student/', adminviews.Search_student, name='Search_student'), # Added trailing slash

    # PDF URL
    path('pdf/', StudentViews.GeneratePdf.as_view(), name="pdf"), # Added trailing slash


]

# Serve media and static files during development
# This should only be active in DEBUG mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Note: You had static files serving twice, combined here
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)