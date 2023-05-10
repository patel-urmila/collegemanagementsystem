from django.contrib import admin
from django.urls import path
from studentManagementApp.views import * 

urlpatterns = [
    path('', LoginView.as_view(), name='login'),
    # path('tokenlogin/', TokenLogin.as_view(), name='tokenlogin'),
    path('login/', LoginView.as_view(), name='login'),
    path('register/',StaffHodRegisterView.as_view(),name="createstudent"),
    path('course/', CourseView.as_view(), name='newcourse'),
    path('course/<int:pk>', CourseView.as_view(), name='newcourse'),
    path('session/', SessionYearView.as_view(), name='newsession'),
    path('session/<int:pk>', SessionYearView.as_view(), name='editsession'),
    path('subject/', SubjectView.as_view(), name='addsubject'),
    path('subject/<int:pk>', SubjectView.as_view(), name='editsubject'),
    path('teacher/', TeachersView.as_view(), name='teacher'),
    path('teacher/<int:pk>', TeachersView.as_view(), name='editteacher'),
    path('student/', StudentView.as_view(), name='student'),
    path('student/<int:pk>', StudentView.as_view(), name='editstudent'),
    path('staffleave/', StaffLeaveView.as_view(), name='studentleave'),
    path('staffleave/<int:pk>', StaffLeaveView.as_view(), name='editstudentleave'),
    path('studentleave/', StudentLeaveView.as_view(), name='staffleave'),
    path('studentleave/<int:pk>', StudentLeaveView.as_view(), name='editstaffleave'),
    path('teachers/', TeachersDashBoard, name='teachers'),
    path('takeattendancestudent/', takeattendance, name='takeattendancestudent'),
    path('subattendance/', Subattendance.as_view(), name='subattendance'),
    path('takeattendance/', TakeAttendance.as_view(), name='takeattendance'),
    path('studentnotification/', StudentNotifications.as_view(), name='studentnotification'),
]   