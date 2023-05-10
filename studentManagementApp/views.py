from django.shortcuts import render,HttpResponse
from rest_framework.generics import *
from django.views.generic.base import *
from rest_framework.response import Response
from  .serializers import * 
from rest_framework.views import *
from django.contrib.auth import authenticate, login
from django.db.models import Q
from collegeManagementSystem import settings
from django.contrib.auth.decorators import login_required
from rest_framework.permissions import IsAuthenticated
from django.utils.decorators import method_decorator
from datetime import datetime, timezone
from rest_framework_simplejwt.tokens import RefreshToken
import jwt
from django.views.decorators.csrf import csrf_exempt

def home(request):
    return HttpResponse("helloo")

def TeachersDashBoard(request):
    return render(request,"teacherDashBoard.html")


def takeattendance(request):
    if request.user.role == "Teacher":
        user = User.objects.get(email=request.user)
        teacher = Teachers.objects.get(user = user)
        sub = Subjects.objects.filter(teacher=teacher)
        session = SessionYear.objects.all()
        return render(request,"takeattendance.html",{'sub':sub,'session':session})

class Subattendance(APIView):   
    def post(self,request):
        subject = Subjects.objects.get(subName=request.POST['subjectselect'])
        subjectData = Subjects.objects.get(subName=request.POST['subjectselect']).course
        studentsData = Students.objects.filter(course = subjectData)
        now = datetime.now(timezone.utc)
        today = now.date()
        mainData = []
        data = []
        for i in studentsData:
            data.append({
                "fnm":i.user.first_name,
                'lnm': i.user.last_name,
                'email': i.user.email,
                'user_id': i.id     
            })
        attendances = Attendance.objects.filter(created_at__date=today, subject=subject)
        common_student_ids = [(i.student.id,i.status) for i in attendances if i.student.id in studentsData.values_list('id',flat=True)]
        mainData.append(data)
        mainData.append(common_student_ids)
        return Response(mainData)

class TakeAttendance(APIView):
    def post(self,request):
        student_id = request.POST['studentId']
        subject_id = request.POST['subjectId']      
        session_year= request.POST['year']
        status = request.POST['status']
        now = datetime.now(timezone.utc)
        today = now.date()
        student = Students.objects.get(id = student_id)
        subject = Subjects.objects.get(subName= subject_id)
        session = SessionYear.objects.get(id = session_year)
        demo = Attendance.objects.filter(Q(student=student) & Q(subject=subject) & Q(sessionYear=session) & Q(created_at__date = today ))
        if demo:
            for i in demo:
                stu = Attendance.objects.get(id= i.id)
                stu.status = status
                stu.save()
        else:
            takeAtt = Attendance.objects.create(student=student,subject=subject,sessionYear=session,status=status)
        return Response({'msg' : 'Data Created'})

class StaffHodRegisterView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    } 

def decode_token(token):
    decode_token = jwt.decode(token,None,None)
    return decode_token

# class TokenLogin(APIView):
#     def post(self,request,format = None):
#         email = request.data.get('email') 
#         password = request.data.get('password')
#         # user = User.objects.get(email=email)
#         user = authenticate(request, email=email, password=password)
#         if user:
#             auth_token = get_tokens_for_user(user)
#             print("-----------------auth data",auth_token)
#             response = Response({"success":True ,'refreshtoken': str(auth_token['refresh']), 'accesstoken': str(auth_token['access'])})
#             response.set_cookie("user",user, max_age = 60)
#             return response
#         return Response({"msg":"Invalid Login credentials"})
       
class LoginView(TemplateView):
    template_name = 'login.html'
    def post(self, request, format=None):
        email = request.POST['email']
        password = request.POST['password'] 
        user = authenticate(request, email=email, password=password)
        if user is not None:
            if user.role == "HOD":
                login(request, user)
                request.session.set_expiry(settings.SESSION_COOKIE_AGE)
                return render(request,'HodDashBoard.html',{"user":user})
            elif user.role == "Student":
                login(request, user)
                return render(request,'studentDashBoard.html',{"user":user})
            else:
                login(request, user)
                return render(request,'teacherDashBoard.html',{"user":user})
                
        else:
            return render(request,'login.html',{'alert': 'Invalid login credentials'})
    

class CourseView(APIView):
    def get(self,request,pk = None ,format = None):
        try:
            id = pk
            token = request.data['token']
            d_token = decode_token(token)
            user_id = d_token['user_id']
            hod = User.objects.get(id=user_id).role == "HOD"
            cookie = request.COOKIES['user']
            print("-----cookie",cookie) 
            if hod is True:
                if id is not None:
                    stu = Courses.objects.get(id=id)
                    serializer = NewCourseSerializer(stu)
                    return Response(serializer.data)
                stu = Courses.objects.all()
                serializer = NewCourseSerializer(stu,many = True)
                return Response(serializer.data)
            else:
                return Response({"msg":"permission denied"})
        except Exception as e:
                return Response(str(e)) 
    
    def post(self,request,format = None):
        try:
            request.session.set_expiry(settings.SESSION_COOKIE_AGE)
            token = request.data['token']
            d_token = decode_token(token)
            user_id = d_token['user_id']
            hod = User.objects.get(id=user_id).role == "HOD"
            if hod is True:
                serializer = NewCourseSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({'msg' : 'Data Created'})
                return Response(serializer.errors)
            else:
                return Response({"msg":"permission denied"})
        except Exception as e:
                return Response(str(e)) 
    
    def put(self,request,pk = None,format = None):
        try:
            token = request.data['token']
            d_token = decode_token(token)
            user_id = d_token['user_id']
            hod = User.objects.get(id=user_id).role == "HOD"
            if hod is True:
                subject = Courses.objects.get(pk=pk)   
                serializer = NewCourseSerializer(subject, data=request.data, partial = True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({'msg' : serializer.data})
                return Response(serializer.errors)
            else:
                return Response({"msg":"permission denied"})
        except Exception as e:
                return Response(str(e)) 
    
    def delete(self,request,pk = None ,format = None):
        try:
            token = request.data['token']
            d_token = decode_token(token)
            user_id = d_token['user_id']
            hod = User.objects.get(id=user_id).role == "HOD"
            if hod is True:
                sub = Courses.objects.get(pk=pk)
                sub.delete()
                return Response({'msg': 'DATA Deleted'})
            else:
                return Response({"msg":"permission denied"})
        except Exception as e:
                return Response(str(e)) 

class SessionYearView(APIView): 
    queryset = SessionYear.objects.all()
    serializer_class = SessionSerializer
    
    def get(self,request,pk = None ,format = None):
        try:
            token = request.data['token']
            d_token = decode_token(token)
            user_id = d_token['user_id']
            hod = User.objects.get(id=user_id).role == "HOD"
            if hod is True:
                id = pk
                if id is not None:
                    stu = SessionYear.objects.get(id=id)
                    serializer = SessionSerializer(stu)
                    return Response(serializer.data)
                stu = SessionYear.objects.all()
                serializer = SessionSerializer(stu,many = True)
                return Response(serializer.data)
            else:
                return Response({"msg":"permission denied"})
        except Exception as e:
                return Response(str(e)) 
    
    def post(self,request,format = None):
        try:
            token = request.data['token']
            d_token = decode_token(token)
            user_id = d_token['user_id']
            hod = User.objects.get(id=user_id).role == "HOD"
            if hod is True:
                serializer = SessionSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({'msg' : serializer.data})
                return Response(serializer.errors)
            else:
                return Response({"msg":"permission denied"})
        except Exception as e:
                return Response(str(e)) 
            
    def put(self,request,pk = None,format = None):
        try:
            token = request.data['token']
            d_token = decode_token(token)
            user_id = d_token['user_id']
            hod = User.objects.get(id=user_id).role == "HOD"
            if hod is True:
                subject = SessionYear.objects.get(pk=pk)   
                serializer = SessionSerializer(subject, data=request.data, partial = True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({'msg' : serializer.data})
                return Response(serializer.errors)
            else:
                return Response({"msg":"permission denied"})
        except Exception as e:
                return Response(str(e)) 
    
    def delete(self,request,pk = None ,format = None):
        try:
            token = request.data['token']
            d_token = decode_token(token)
            user_id = d_token['user_id']
            hod = User.objects.get(id=user_id).role == "HOD"
            if hod is True:
                sub = SessionYear.objects.get(pk=pk)
                sub.delete()
                return Response({'msg': 'DATA Deleted'})
            else:
                return Response({"msg":"permission denied"})
        except Exception as e:
                return Response(str(e)) 


class SubjectView(APIView):  
    queryset = Subjects.objects.all()
    serializer_class = AddSubjectSerializer
    
    def get(self,request,pk = None ,format = None):
        try:
            token = request.data['token']
            d_token = decode_token(token)
            user_id = d_token['user_id']
            hod = User.objects.get(id=user_id).role == "HOD"
            if hod is True:
                id = pk
                if id is not None:
                    stu = Subjects.objects.get(id=id)
                    serializer = AddSubjectSerializer(stu)
                    return Response(serializer.data)
                stu = Subjects.objects.all()
                serializer = AddSubjectSerializer(stu,many = True)
                return Response(serializer.data)
            else:
                return Response({"msg":"permission denied"})
        except Exception as e:
                return Response(str(e)) 
    
    def post(self,request,format = None):
        try:
            token = request.data['token']
            d_token = decode_token(token)
            user_id = d_token['user_id']
            hod = User.objects.get(id=user_id).role == "HOD"
            if hod is True:
                serializer = AddSubjectSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({'msg' : serializer.data})
                return Response(serializer.errors)
            else:
                return Response({"msg":"permission denied"})
        except Exception as e:
                return Response(str(e)) 
    
    def put(self,request,pk = None,format = None):
        try:
            token = request.data['token']
            d_token = decode_token(token)
            user_id = d_token['user_id']
            hod = User.objects.get(id=user_id).role == "HOD"
            if hod is True:
                subject = Subjects.objects.get(pk=pk)   
                serializer = AddSubjectSerializer(subject, data=request.data, partial = True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({'msg' : serializer.data})
                return Response(serializer.errors)
            else:
                return Response({"msg":"permission denied"})
        except Exception as e:
                return Response(str(e)) 
    
    def delete(self,request,pk = None ,format = None):
        try:
            token = request.data['token']
            d_token = decode_token(token)
            user_id = d_token['user_id']
            hod = User.objects.get(id=user_id).role == "HOD"
            if hod is True:
                sub = Subjects.objects.get(pk=pk)
                sub.delete()
                return Response({'msg': 'DATA Deleted'})
            else:
                return Response({"msg":"permission denied"})
        except Exception as e:
                return Response(str(e)) 

class TeachersView(APIView):  
    queryset = Teachers.objects.all()
    serializer_class = TeacherSerializer
    
    def get(self,request,pk = None ,format = None):
        id = pk
        if id is not None:
            teacher = Teachers.objects.get(id=id)
            serializer = TeacherSerializer(teacher)
            teacher={
                'id': teacher.id,
                'user_id':teacher.user.id,
                'email': teacher.user.email,
                'first_name': teacher.user.first_name,
                'last_name': teacher.user.last_name
            }
            return Response(teacher)
        teachers = Teachers.objects.all()
        teacher_info = []
        for i in teachers:
            teacher_info.append({
                'id': i.id,
                'user_id':i.user.id,
                'email': i.user.email,
                'first_name': i.user.first_name,
                'last_name': i.user.last_name
            })
        return Response(teacher_info)
    
    def post(self,request,format = None):
        if User.objects.get(email = request.user).role == "HOD":
            password = request.data['password']
            serializer = TeacherSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                user.set_password(password)
                user.role = "Teacher"
                user.save()
                Teachers.objects.create(user = user)
                return Response({'msg' : serializer.data})
            return Response(serializer.errors)
        return Response({'msg': 'Permission Denied'})
        
    
    def patch(self,request,pk = None,format = None):
        user = User.objects.get(email = request.user)
        if User.objects.get(email = request.user).role == "HOD" or Teachers.objects.filter(user=user).filter(pk=pk).exists():
            teacher = Teachers.objects.get(pk=pk)   
            id = teacher.user
            serializer = TeacherSerializer(id, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({'msg' : serializer.data})
            return Response(serializer.errors)
        return Response({'msg': 'Permission Denied'})
    
    def delete(self,request,pk = None ,format = None):
        user = User.objects.get(email = request.user)
        if User.objects.get(email = request.user).role == "HOD" or Teachers.objects.filter(user=user).filter(pk=pk).exists():
            sub = Teachers.objects.get(pk=pk)
            sub.delete()
            return Response({'msg': 'DATA Deleted'})
        return Response({'msg': 'Permission Denied'})

class StudentView(APIView):      
    queryset = Students.objects.all()
    serializer_class = StudentSerializer
    
    def get(self,request,pk = None ,format = None):
        if pk is not None:
            student = Students.objects.get(id=pk)
            serializer = StudentSerializer(student)
            teacher={
                'id': student.id,
                'user_id':student.user.id,
                'email': student.user.email,
                'first_name': student.user.first_name,
                'last_name': student.user.last_name,
                'course': student.course.courseName,
                'sessionYear': student.sessionYear.startYear
                
            }
            return Response(teacher)
        student = Students.objects.all()
        student_info = []
        for i in student:
            student_info.append({
                'id': i.id,
                'user_id':i.user.id,
                'email': i.user.email,
                'first_name': i.user.first_name,
                'last_name': i.user.last_name,
                'course': i.course.courseName,
                'sessionYear': i.sessionYear.startYear
            })
        return Response(student_info)
    
    def post(self,request,format = None):
        if User.objects.get(email = request.user).role == "HOD":
            serializer = StudentSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({'Student' : serializer.data})
            return Response(serializer.errors)
        return Response({'msg': 'Permission Denied'})
    
    def patch(self,request,pk = None,format = None):
        user = User.objects.get(email = request.user)
        if User.objects.get(email = request.user).role == "HOD" or Students.objects.filter(user=user).filter(pk=pk).exists():
            teacher = Students.objects.get(pk=pk)   
            id = teacher.user
            serializer = TeacherSerializer(id, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({'msg' : serializer.data})
            return Response(serializer.errors)
        return Response({'msg': 'Permission Denied'})
    
    def delete(self,request,pk = None ,format = None):
        user = User.objects.get(email = request.user)
        if User.objects.get(email = request.user).role == "HOD" :
            student = Students.objects.get(id=pk)
            student.delete()
            return Response({'msg': 'DATA Deleted'})
        return Response({'msg': 'Permission Denied'})
    
@method_decorator(login_required, name='dispatch')
class StaffLeaveView(APIView):
    permission_classes = [IsAuthenticated]   
    queryset = StaffLeave.objects.all()
    serializer_class = StaffLeaveSerializer
    
    def get(self,request,pk = None ,format = None):
        if pk is not None:
            if User.objects.get(email = request.user).role == "HOD":
                leave = StaffLeave.objects.get(id=pk)
                leave={
                        'id': leave.id,
                        'email': leave.user.user.first_name,
                        'leave_date': leave.leaveDate,
                        'leave msg': leave.reason,
                        'applied on': leave.created_at,
                        'status': leave.status

                    }
                return Response(leave)
            elif User.objects.get(email = request.user).role == "Teacher":
                teacher = Teachers.objects.get(user = request.user)
                leave = StaffLeave.objects.filter((Q(pk=pk) & Q(user=teacher)))
                if leave.exists():
                    teacher_info = []
                    for i in leave:
                        teacher_info.append({
                            'id': i.id,
                            'email': i.user.user.first_name,
                            'leave_date': i.leaveDate,
                            'leave msg': i.reason,
                            'applied on': i.created_at,
                            'status': i.status
                        })
                    return Response(teacher_info)
                return Response({'msg': 'Permission Denied'})
            else:
                return Response({'msg' : "Not a Hod "})
        if User.objects.get(email = request.user).role == "HOD":
            teachers = StaffLeave.objects.all()
            teacher_info = []
            for i in teachers:
                teacher_info.append({
                    'id': i.id,
                    'email': i.user.user.first_name,
                    'leave_date': i.leaveDate,
                    'leave msg': i.reason,
                    'applied on': i.created_at,
                    'status': i.status
                })
            return Response(teacher_info)
        elif User.objects.get(email = request.user).role == "Teacher":
            teacher = Teachers.objects.get(user = request.user)
            leave = StaffLeave.objects.filter(user=teacher)
            if leave:
                teacher_info = []
                for i in leave:
                    teacher_info.append({
                        'id': i.id,
                        'email': i.user.user.first_name,
                        'leave_date': i.leaveDate,
                        'leave msg': i.reason,
                        'applied on': i.created_at,
                        'status': i.status
                    })
                return Response(teacher_info)
            return Response({'msg': 'No Data Found'})
        else:
            return Response({'msg' : "Permission Denied"})
    def post(self,request,format = None):
        if User.objects.get(email = request.user).role == "Teacher":
            serializer = StaffLeaveSerializer(data=request.data)
            if serializer.is_valid():
                staff_id = Teachers.objects.get(user=request.user)
                user = serializer.save(user=staff_id,status="Requested")
                return Response({'leave' : serializer.data})
            return Response(serializer.errors)
        else:
            return Response({'msg' : "Not a Teacher"})
    
    def patch(self,request,pk = None,format = None):
        leave_id = StaffLeave.objects.get((Q(pk=pk)&Q(user=Teachers.objects.get(user=request.user))))   
        serializer = StaffLeaveSerializer(leave_id, data=request.data,partial = True)
        if serializer.is_valid():
            serializer.save()
            return Response({'msg' : serializer.data})
        return Response(serializer.errors)
    
    def delete(self,request,pk = None ,format = None):
        teacher = Teachers.objects.get(user = request.user)
        leave = StaffLeave.objects.filter((Q(pk=pk) & Q(user=teacher)))
        if leave.exists():
            leave.delete()
            return Response({'msg': 'DATA Deleted'})
        return Response({'msg': 'Permission Denied'})
    
@method_decorator(login_required, name='dispatch')
class StudentLeaveView(APIView):
    permission_classes = [IsAuthenticated]   
    queryset = StudentLeave.objects.all()
    serializer_class = StudentLeaveSerializer
    
    def get(self,request,pk = None ,format = None):
        if pk is not None:
            if User.objects.get(email = request.user).role == "HOD":
                leave = StudentLeave.objects.get(id=pk)
                leave={
                        'id': leave.id,
                        'email': leave.user.user.first_name,
                        'leave_date': leave.leaveDate,
                        'leave msg': leave.reason,
                        'applied on': leave.created_at,
                        'status': leave.status

                    }
                return Response(leave)
            elif User.objects.get(email = request.user).role == "Student":
                student = Students.objects.get(user = request.user)
                leave = StudentLeave.objects.filter((Q(pk=pk) & Q(user=student)))
                if leave.exists():
                    student_info = []
                    for i in leave:
                        student_info.append({
                            'id': i.id,
                            'email': i.user.user.first_name,
                            'leave_date': i.leaveDate,
                            'leave msg': i.reason,
                            'applied on': i.created_at,
                            'status': i.status
                        })
                    return Response(student_info)
                return Response({'msg': 'Permission Denied'})
            else:
                return Response({'msg' : "Not a Hod "})
        if User.objects.get(email = request.user).role == "HOD":
            student = StudentLeave.objects.all()
            student_info = []
            for i in student:
                student_info.append({
                    'id': i.id,
                    'email': i.user.user.first_name,
                    'leave_date': i.leaveDate,
                    'leave msg': i.reason,
                    'applied on': i.created_at,
                    'status': i.status
                })
            return Response(student_info)
        elif User.objects.get(email = request.user).role == "Student":
            student = Students.objects.get(user = request.user)
            leave = StudentLeave.objects.filter(user=student)
            if leave:
                student_info = []
                for i in leave:
                    student_info.append({
                        'id': i.id,
                        'email': i.user.user.first_name,
                        'leave_date': i.leaveDate,
                        'leave msg': i.reason,
                        'applied on': i.created_at,
                        'status': i.status
                    })
                return Response(student_info)
            return Response({'msg': 'No Data Found'})
        else:
            return Response({'msg' : "Permission Denied"})
    def post(self,request,format = None):
        if User.objects.get(email = request.user).role == "Student":
            serializer = StudentLeaveSerializer(data=request.data)
            if serializer.is_valid():
                student_id = Students.objects.get(user=request.user)
                user = serializer.save(user=student_id,status="Requested")
                return Response({'leave' : serializer.data})
            return Response(serializer.errors)
        else:
            return Response({'msg' : "Not a Student"})
    
    def patch(self,request,pk = None,format = None):
        leave_id = StudentLeave.objects.get((Q(pk=pk)&Q(user=Students.objects.get(user=request.user))))   
        serializer = StudentLeaveSerializer(leave_id, data=request.data,partial = True)
        if serializer.is_valid():
            serializer.save()
            return Response({'msg' : serializer.data})
        else:
            return Response(serializer.errors)
    
    def delete(self,request,pk = None ,format = None):
        student = Students.objects.get(user = request.user)
        leave = StudentLeave.objects.filter((Q(pk=pk) & Q(user=student)))
        if leave.exists():
            leave.delete()
            return Response({'msg': 'DATA Deleted'})
        else:
            return Response({'msg': 'Permission Denied'})
        
        
class StudentNotifications(APIView):
    def get(self,request):
        if request.user.role == "Student":
            student  = Students.objects.get(user = request.user)
            attendance = Attendance.objects.filter(student=student)
            data = []
            if attendance is not None:
                for i in attendance:
                    notification = AttendanceNotification.objects.get(attendance=i)
                    date = str(notification.attendance.created_at)
                    notification_date = date.split()
                    data.append({
                        'date': notification_date[0],
                        'attendance': notification.attendance.status,
                        'subject':notification.attendance.subject.subName
                    })
            return Response(data)
        else:
            return Response({'msg': 'Permission Denied'})