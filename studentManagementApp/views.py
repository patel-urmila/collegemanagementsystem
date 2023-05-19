from django.shortcuts import render,redirect
from rest_framework.generics import *
from django.views.generic.base import *
from rest_framework.response import Response
from  .serializers import * 
from rest_framework.views import *
from django.contrib.auth import authenticate, login,logout
from django.db.models import Q
from datetime import datetime, timezone
from rest_framework_simplejwt.tokens import RefreshToken
import jwt
from rest_framework_simplejwt.tokens import AccessToken
from datetime import datetime


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
        print("here---------------",request.POST['subjectselect'])
        print("here---------------",request.POST['sessionselect'])
        subject = Subjects.objects.get(subName=request.POST['subjectselect'])
        subjectData = Subjects.objects.get(subName=request.POST['subjectselect']).course
        # studentsData = Students.objects.filter(course = subjectData)
        # demo = Courses.objects.filter(course = subjectData)
        # print("-------demo",demo.sessionYear)
        studentsData = Students.objects.filter(Q(course = subjectData) & Q(sessionYear = request.POST['sessionselect']))
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
             Attendance.objects.create(student=student,subject=subject,sessionYear=session,status=status)
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

def logoutview(request):
    logout(request)
    return redirect("login")

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
                auth_token = get_tokens_for_user(user)
                accesstoken = str(auth_token['access'])
                request.session['accessToken'] = accesstoken
                # request.session.set_expiry(settings.SESSION_COOKIE_AGE)
                return render(request,'HodDashBoard.html',{"user":user})
            elif user.role == "Student":
                login(request, user)
                auth_token = get_tokens_for_user(user)
                accesstoken = str(auth_token['access'])
                request.session['accessToken'] = accesstoken
                return render(request,'studentDashBoard.html',{"user":user})
            else:
                auth_token = get_tokens_for_user(user)
                accesstoken = str(auth_token['access'])
                request.session['accessToken'] = accesstoken
                login(request, user)
                return render(request,'teacherDashBoard.html',{"user":user})
                
        else:
            return render(request,'login.html',{'alert': 'Invalid login credentials'})
    

class CourseView(APIView):
    def get(self,request,pk = None ,format = None):
        if request.session.has_key('accessToken'):
            try:
                AccessToken(request.session['accessToken'])
                d_token = decode_token(request.session['accessToken'])
                user_id = d_token['user_id']
                hod = User.objects.get(id=user_id).role == "HOD"
                # cookie = request.COOKIES['user']
                if hod is True:
                    if pk is not None:
                        stu = Courses.objects.get(id=pk)
                        serializer = NewCourseSerializer(stu)
                        return Response(serializer.data)
                    stu = Courses.objects.all()
                    serializer = NewCourseSerializer(stu,many = True)
                    return Response(serializer.data)
                else:
                    return Response({"msg":"permission denied"})
            except Exception as e:
                return Response({'msg': 'Unauthorized'},status=status.HTTP_401_UNAUTHORIZED) 
    
    def post(self,request,format = None):
        d_token = decode_token(request.session['accessToken'])
        user_id = d_token['user_id']
        hod = User.objects.get(id=user_id).role == "HOD"
        if hod is True:
            serializer = CourseSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({'msg' : 'Data Created'})
            return Response(serializer.errors)
        else:
            return Response({"msg":"permission denied"})
    
    def patch(self,request,pk = None,format = None):
        d_token = decode_token(request.session['accessToken'])
        user_id = d_token['user_id']
        hod = User.objects.get(id=user_id).role == "HOD"    
        if hod is True:
            subject = Courses.objects.get(pk=pk)   
            serializer = CourseSerializer(subject, data=request.data, partial = True)
            if serializer.is_valid():
                updated_course = serializer.save()
                CourseSerializer(updated_course).data
                return Response({'msg' : serializer.data})
            return Response(serializer.errors)
        else:
            return Response({"msg":"permission denied"})

    def delete(self,request,pk = None ,format = None):
        d_token = decode_token(request.session['accessToken'])
        user_id = d_token['user_id']
        hod = User.objects.get(id=user_id).role == "HOD"
        if hod is True:
            sub = Courses.objects.get(pk=pk)
            sub.delete()
            return Response({'msg': 'DATA Deleted'})
        else:
            return Response({"msg":"permission denied"})

class SessionYearView(APIView): 
    queryset = SessionYear.objects.all()
    serializer_class = SessionSerializer
    
    def get(self,request,pk = None ,format = None):
        if request.session.has_key('accessToken'):
            try:
                token = AccessToken(request.session['accessToken'])
                d_token = decode_token(request.session['accessToken'])
                user_id = d_token['user_id']
                hod = User.objects.get(id=user_id).role == "HOD"
                if hod is True:
                    id = pk
                    if id is not None:
                        stu = SessionYear.objects.get(id=id)
                        serializer = SessionSerializer(stu)
                        return Response(serializer.data)
                    stu = SessionYear.objects.all()
                    data = []
                    for i in stu:
                        data.append({
                                    "id":i.id,
                                    'startYear': i.startYear,
                                    'endYear': i.endYear,  
                                })
                    return Response(data)
                else:
                    return Response({"msg":"permission denied"})
            except Exception as e:
                return Response({'msg': 'Unauthorized'},status=status.HTTP_401_UNAUTHORIZED) 

    def post(self,request,format = None):
        d_token = decode_token(request.session['accessToken'])
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
            
    def patch(self,request,pk = None,format = None):
        d_token = decode_token(request.session['accessToken'])
        user_id = d_token['user_id']
        hod = User.objects.get(id=user_id).role == "HOD"
        if hod is True:
            session = SessionYear.objects.get(pk=pk)   
            serializer = SessionSerializer(session, data=request.data, partial = True)
            if serializer.is_valid():
                serializer.save()
                return Response({'msg' : serializer.data})
            return Response(serializer.errors)
        else:
            return Response({"msg":"permission denied"})
    
    def delete(self,request,pk = None ,format = None):
        d_token = decode_token(request.session['accessToken'])
        user_id = d_token['user_id']
        hod = User.objects.get(id=user_id).role == "HOD"
        if hod is True:
            sub = SessionYear.objects.get(pk=pk)
            sub.delete()
            return Response({'msg': 'DATA Deleted'})
        else:
            return Response({"msg":"permission denied"})

class SubjectView(APIView):  
    queryset = Subjects.objects.all()
    serializer_class = AddSubjectSerializer
    
    def get(self,request,pk = None ,format = None):
        if request.session.has_key('accessToken'):
            try:
                AccessToken(request.session['accessToken'])
                d_token = decode_token(request.session['accessToken'])
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
            except Exception:
                return Response({'msg': 'Unauthorized'},status=status.HTTP_401_UNAUTHORIZED)
    
    def post(self,request,format = None):
        d_token = decode_token(request.session['accessToken'])
        user_id = d_token['user_id']
        hod = User.objects.get(id=user_id).role == "HOD"
        if hod is True:
            serializer = AddSubjectSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({'msg' : serializer.data})
            return Response(serializer.errors)
        else:
            print("denied")
            return Response({"msg":"permission denied"})

    def patch(self,request,pk = None,format = None):
        d_token = decode_token(request.session['accessToken'])
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
    
    def delete(self,request,pk = None ,format = None):
        d_token = decode_token(request.session['accessToken'])
        user_id = d_token['user_id']
        hod = User.objects.get(id=user_id).role == "HOD"
        if hod is True:
            sub = Subjects.objects.get(pk=pk)
            sub.delete()
            return Response({'msg': 'DATA Deleted'})
        else:
            return Response({"msg":"permission denied"})

class TeachersView(APIView):  
    queryset = Teachers.objects.all()
    serializer_class = TeacherSerializer
    
    def get(self,request,pk = None ,format = None):
        if request.session.has_key('accessToken'):
            try:
                AccessToken(request.session['accessToken'])
                d_token = decode_token(request.session['accessToken'])
                user_id = d_token['user_id']
                id = pk
                loggedIn_user = User.objects.get(id = user_id)
                if loggedIn_user.role == "HOD":
                    if id is not None:
                        teacher = Teachers.objects.get(id=id)
                        serializer = TeacherSerializer(teacher)
                        teacher={
                            'user':loggedIn_user.first_name,
                            'id': teacher.id,
                            'user_id':teacher.user.id,
                            'email': teacher.user.email,
                            'first_name': teacher.user.first_name,
                            'last_name': teacher.user.last_name
                        }
                        return Response(teacher, status=status.HTTP_200_OK)
                    teachers = Teachers.objects.all()
                    teacher_info = []
                    for i in teachers:
                        teacher_info.append({
                            'user':loggedIn_user.first_name,
                            'id': i.id,
                            'user_id':i.user.id,
                            'email': i.user.email,
                            'first_name': i.user.first_name,
                            'last_name': i.user.last_name
                        })
                    return Response(teacher_info,status=status.HTTP_200_OK)
                return Response({'msg': 'Permission Denied'},status=status.HTTP_403_FORBIDDEN)
            except Exception as e:
                return Response({'msg': e },status=status.HTTP_401_UNAUTHORIZED) 
    
    def post(self,request,format = None):
        print("post ----here")
        d_token = decode_token(request.session['accessToken'])
        user_id = d_token['user_id']
        if User.objects.get(id = user_id).role == "HOD":
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
        
    
    # def patch(self,request,pk = None,format = None):
    def patch(self,request,pk= None, *args, **kwargs):
        d_token = decode_token(request.session['accessToken'])
        user_id = d_token['user_id']
        user = User.objects.get(id = user_id)
        if User.objects.get(id = user_id).role == "HOD" or Teachers.objects.filter(user=user).filter(pk=pk).exists():
            teacher = Teachers.objects.get(pk=pk)   
            id = teacher.user
            serializer = TeacherSerializer(id, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({'msg' : serializer.data})
            return Response(serializer.errors)
        return Response({'msg': 'Permission Denied'})
    
    def delete(self,request,pk = None ,format = None):
        d_token = decode_token(request.session['accessToken'])
        user_id = d_token['user_id']
        user = User.objects.get(id = user_id)
        if User.objects.get(id = user_id).role == "HOD" or (Teachers.objects.filter(user=user).filter(pk=pk).exists()):
            sub = Teachers.objects.get(pk=pk)
            sub.delete()
            return Response({'msg': 'DATA Deleted'})
        return Response({'msg': 'Permission Denied'})

class StudentView(APIView):      
    queryset = Students.objects.all()
    serializer_class = StudentSerializer
    
    def get(self,request,pk = None ,format = None):
        if request.session.has_key('accessToken'):
            try:
                token = AccessToken(request.session['accessToken'])
                d_token = decode_token(request.session['accessToken'])
                user_id = d_token['user_id']
                courses = Courses.objects.all()
                sessions = SessionYear.objects.all()
                if pk is not None:
                    student = Students.objects.get(id=pk)
                    serializer = StudentSerializer(student)
                    teacher={
                        'courses':courses,
                        'sessions':sessions,
                        'id': student.id,
                        'user_id':student.user.id,
                        'email': student.user.email,
                        'first_name': student.user.first_name,
                        'last_name': student.user.last_name,
                        'course': student.course.courseName,
                        'sessionYear': student.sessionYear

                    }
                    return Response(teacher)
                student = Students.objects.all()
                student_info = []
                student_info1 = []
                for i in student:
                    student_info.append({
                        'courses':courses,
                        'sessions':sessions,
                        'id': i.id,
                        'user_id':i.user.id,
                        'email': i.user.email,
                        'first_name': i.user.first_name,
                        'last_name': i.user.last_name,
                        'course': i.course.courseName,
                        'sessionYear': i.sessionYear
                    })
                return Response(student_info)
            except Exception as e:
                return Response({'msg': 'Unauthorized'},status=status.HTTP_401_UNAUTHORIZED) 
    
    def post(self,request,format = None):
        d_token = decode_token(request.session['accessToken'])
        user_id = d_token['user_id']
        if (User.objects.get(id = user_id).role == "HOD"):
            serializer = StudentSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({'Student' : serializer.data})
            return Response(serializer.errors)
        return Response({'msg': 'Permission Denied'})
    
    def patch(self,request,pk = None,format = None):
        d_token = decode_token(request.session['accessToken'])
        user_id = d_token['user_id']
        user = User.objects.get(id = user_id)
        if User.objects.get(id = user_id).role == "HOD" or Students.objects.filter(user=user).filter(pk=pk).exists():
            teacher = Students.objects.get(pk=pk)   
            id = teacher.user
            serializer = TeacherSerializer(id, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({'msg' : serializer.data})
            return Response(serializer.errors)
        return Response({'msg': 'Permission Denied'})
    
    def delete(self,request,pk = None ,format = None):
        d_token = decode_token(request.session['accessToken'])
        user_id = d_token['user_id']
        if User.objects.get(id = user_id).role == "HOD" :
            student = Students.objects.get(id=pk)
            student.delete()
            return Response({'msg': 'DATA Deleted'})
        return Response({'msg': 'Permission Denied'})
    
class StaffLeaveView(APIView):
    def get(self,request,pk = None ,format = None):
        if request.session.has_key('accessToken'):
            try:
                AccessToken(request.session['accessToken'])
                d_token = decode_token(request.session['accessToken'])
                user_id = d_token['user_id']
                if pk is not None:
                    if User.objects.get(id = user_id).role == "HOD":
                        leave = StaffLeave.objects.get(id=pk)
                        leaves={
                                'id': leave.id,
                                'Teacher': leave.teacher.user.first_name,
                                'leave_date': leave.leaveDate,
                                'leave_msg': leave.reason,
                                'applied_on': leave.created_at,
                                'status': leave.status

                            }
                        return Response(leaves)
                    elif User.objects.get(id = user_id).role == "Teacher":
                        teacher = Teachers.objects.get(user = user_id)
                        leave = StaffLeave.objects.filter((Q(pk=pk) & Q(teacher=teacher)))
                        if leave.exists():
                            teacher_info = []
                            for i in leave:
                                teacher_info.append({
                                    'id': i.id,
                                    'Teacher': i.teacher.user.first_name,
                                    'leave_date': i.leaveDate,
                                    'leave_msg': i.reason,
                                    'applied_on': i.created_at,
                                    'status': i.status
                                })
                            return Response(teacher_info)
                        return Response({'msg': 'Permission Denied'})
                    else:
                        return Response({'msg' : "Not a Hod "})
                else:
                    if User.objects.get(id = user_id).role == "HOD":
                        teachers = StaffLeave.objects.filter(status="Requested")
                        teacher_info = []
                        for i in teachers:
                            teacher_info.append({
                                'id': i.id,
                                'Teacher': i.teacher.user.first_name,
                                'leave_date': i.leaveDate,
                                'leave_msg': i.reason,
                                'applied_on': i.created_at,
                                'status': i.status
                            })
                        return Response(teacher_info)
                    elif User.objects.get(id = user_id).role == "Teacher":
                        teacher = Teachers.objects.get(user = user_id)
                        leave = StaffLeave.objects.filter(teacher=teacher)
                        if leave:
                            teacher_info = []
                            for i in leave:
                                teacher_info.append({
                                    'id': i.id,
                                    'Teacher': i.teacher.user.first_name,
                                    'leave_date': i.leaveDate,
                                    'leave_msg': i.reason,
                                    'applied_on': i.created_at,
                                    'status': i.status
                                })
                            return Response(teacher_info)
                        return Response({'msg': 'No Data Found'})
                    else:
                        return Response({'msg' : "Permission Denied"})
            except Exception:
                return Response({'msg': 'Unauthorized'},status=status.HTTP_401_UNAUTHORIZED) 

    def post(self,request,format = None):
        d_token = decode_token(request.session['accessToken'])
        user_id = d_token['user_id']
        if (User.objects.get(id = user_id).role == "HOD"):
            serializer = StaffLeaveSerializer(data=request.data)
            if serializer.is_valid():
                demo = serializer.validated_data['teacher']
                teacher_user = User.objects.get(first_name= demo)
                staff_id = Teachers.objects.get(user=teacher_user)
                serializer.save(teacher=staff_id,status="Requested")
                return Response({'leave' : serializer.data})
            return Response(serializer.errors)
        elif (User.objects.get(id = user_id).role == "Teacher"):
            serializer = StaffLeaveSerializer(data=request.data)
            if serializer.is_valid():
                staff_id = Teachers.objects.get(user=user_id)
                serializer.save(teacher=staff_id,status="Requested")
                return Response({'leave' : serializer.data})
            return Response(serializer.errors)
        else:
            return Response({'msg' : "Unauthorized"})
    
    def patch(self,request,pk = None,format = None):
        d_token = decode_token(request.session['accessToken'])
        user_id = d_token['user_id']
        # leave_id = StaffLeave.objects.get((Q(pk=pk)&Q(user=Teachers.objects.get(user=user_id))) | Q(user=User.objects.get(id=user_id).role=="HOD")) 
        leave_id = StaffLeave.objects.get(pk=pk)  
        serializer = StaffLeaveSerializer(leave_id, data=request.data,partial = True)
        if serializer.is_valid():
            serializer.save()
            return Response({'msg' : serializer.data})
        return Response(serializer.errors)
    
    def delete(self,request,pk = None ,format = None):
        d_token = decode_token(request.session['accessToken'])
        user_id = d_token['user_id']
        teacher = Teachers.objects.get(user = user_id)
        leave = StaffLeave.objects.filter((Q(pk=pk) & Q(user=teacher)))
        if leave.exists():
            leave.delete()
            return Response({'msg': 'DATA Deleted'})
        return Response({'msg': 'Permission Denied'})
    

class StudentLeaveView(APIView):
    queryset = StudentLeave.objects.all()
    serializer_class = StudentLeaveSerializer
    
    def get(self,request,pk = None ,format = None):
        if request.session.has_key('accessToken'):
            try:
                AccessToken(request.session['accessToken'])
                d_token = decode_token(request.session['accessToken'])
                user_id = d_token['user_id']
                if pk is not None:
                    if User.objects.get(id = user_id).role == "HOD":
                        leave = StudentLeave.objects.get(id=pk)
                        leave={
                                'id': leave.id,
                                'email': leave.student.user.first_name,
                                'leave_date': leave.leaveDate,
                                'leave_msg': leave.reason,
                                'applied on': leave.created_at,
                                'status': leave.status

                            }
                        return Response(leave)
                    elif User.objects.get(id = user_id).role == "Student":
                        student = Students.objects.get(user = user_id)
                        leave = StudentLeave.objects.filter((Q(pk=pk) & Q(student=student)))
                        if leave.exists():
                            student_info = []
                            for i in leave:
                                student_info.append({
                                    'id': i.id,
                                    'email': i.student.user.first_name,
                                    'leave_date': i.leaveDate,
                                    'leave_msg': i.reason,
                                    'applied on': i.created_at,
                                    'status': i.status
                                })
                            return Response(student_info)
                        return Response({'msg': 'Permission Denied'})
                    else:
                        return Response({'msg' : "Not a Hod "})
                if User.objects.get(id = user_id).role == "HOD":
                    student = StudentLeave.objects.all()
                    student_info = []
                    for i in student:
                        student_info.append({
                            'id': i.id,
                            'email': i.student.user.first_name,
                            'leave_date': i.leaveDate,
                            'leave_msg': i.reason,
                            'applied on': i.created_at,
                            'status': i.status
                        })
                    return Response(student_info)
                elif User.objects.get(id = user_id).role == "Student":
                    student = Students.objects.get(user = user_id)
                    leave = StudentLeave.objects.filter(student=student)
                    if leave:
                        student_info = []
                        for i in leave:
                            student_info.append({
                                'id': i.id,
                                'email': i.student.user.first_name,
                                'leave_date': i.leaveDate,
                                'leave_msg': i.reason,
                                'applied on': i.created_at,
                                'status': i.status
                            })
                        return Response(student_info)
                    return Response({'msg': 'No Data Found'})
                else:
                    return Response({'msg' : "Permission Denied"})
            except Exception:
                return Response({'msg': 'Unauthorized'},status=status.HTTP_401_UNAUTHORIZED) 
    def post(self,request,format = None):
        d_token = decode_token(request.session['accessToken'])
        user_id = d_token['user_id']
        if User.objects.get(id = user_id).role == "Student":
            serializer = StudentLeaveSerializer(data=request.data)
            if serializer.is_valid():
                student_id = Students.objects.get(user=user_id)
                serializer.save(student=student_id,status="Requested")
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
       
class TeacherListView(TemplateView):
    template_name = 'manageTeacher.html'
    
    def get_context_data(self, **kwargs):
        response = TeachersView.as_view()(self.request)
        if response.status_code == status.HTTP_200_OK:
            flag=1
            context = {
                'teacher': response.data,
                'flag' : 1
            }
            return context
        
        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            context = {
                'flag':2
            }
            return context
        
class StudentListView(TemplateView):
    template_name = 'managestudent.html'

    def get_context_data(self, **kwargs):
        response = StudentView.as_view()(self.request)
        if response.status_code == status.HTTP_200_OK:
            context = {
                'student':response.data
            }
            return context
        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            context = {
                'flag':2
            }
            return context
    
class CourseListView(TemplateView):
    template_name = 'manageCourse.html'

    def get_context_data(self, **kwargs):
        response = CourseView.as_view()(self.request)
        if response.status_code == status.HTTP_200_OK:
            context = {
                'course':response.data
            }
            return context
        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            context = {
                'flag':2
            }
            return context
    
class SubjectListView(TemplateView):
    template_name = 'manageSubject.html'

    def get_context_data(self, **kwargs):
        response = SubjectView.as_view()(self.request)
        if response.status_code == status.HTTP_200_OK:
            context = {
                'subject':response.data
            }
            return context
        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            context = {
                'flag':2
            }
            return context
    
class SessionListView(TemplateView):
    template_name = 'manageSession.html'

    def get_context_data(self, **kwargs):
        response = SessionYearView.as_view()(self.request)
        if response.status_code == status.HTTP_200_OK:
            context = {
                'session':response.data
            }
            return context
        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            context = {
                'flag':2
            }
            return context
#HOD side 
class StaffLeaveListView(TemplateView):
    template_name = 'manageStaffLeaves.html'

    def get_context_data(self, **kwargs):
        response = StaffLeaveView.as_view()(self.request)
        if response.status_code == status.HTTP_200_OK:
            context = {
                'leaves':response.data
            }
            return context
        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            context = {
                'flag':2
            }
            return context
        
# Staff side       
class StaffApplyLeaveView(TemplateView):
    template_name = 'staffapplyleave.html'

    def get_context_data(self, **kwargs):
        response = StaffLeaveView.as_view()(self.request)
        if response.status_code == status.HTTP_200_OK:
            context = {
                'leaves':response.data
            }
            return context
        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            context = {
                'flag':2
            }
            return context
        
#Student side    
class StudentApplyLeaveView(TemplateView):
    template_name = 'studentapplyLeave.html'

    def get_context_data(self, **kwargs):
        response = StudentLeaveView.as_view()(self.request)
        print(response.data,"ppppp")
        if response.status_code == status.HTTP_200_OK:
            context = {
                'leaves':response.data
            }
            return context
        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            context = {
                'flag':2
            }
            return context    
        
class ViewAttendanceView(TemplateView):
    template_name = 'viewAttendance.html'

    def get_context_data(self, **kwargs):
        response = MyattendanceView.as_view()(self.request)
        if response.status_code == status.HTTP_200_OK:
            context = {
                'subject':response.data
            }
            return context
        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            context = {
                'flag':2
            }
            return context  
        

class StudentProfileView(TemplateView):
    template_name = 'studentProfile.html'
    
    def get_context_data(self, **kwargs):
        response = MyProfileView.as_view()(self.request)
        if response.status_code == status.HTTP_200_OK:
            context = {
                'user':response.data
            }
            return context
        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            context = {
                'flag':2
            }
            return context  

class StaffProfileView(TemplateView):
    template_name = 'staffProfile.html'
    
    def get_context_data(self, **kwargs):
        response = MyProfileView.as_view()(self.request)
        if response.status_code == status.HTTP_200_OK:
            context = {
                'user':response.data
            }
            return context
        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            context = {
                'flag':2
            }
            return context  
        
class HodProfileView(TemplateView):
    template_name = 'hodProfile.html'
    
    def get_context_data(self, **kwargs):
        response = MyProfileView.as_view()(self.request)
        if response.status_code == status.HTTP_200_OK:
            context = {
                'user':response.data
            }
            return context
        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            context = {
                'flag':2
            }
            return context  
    
    
class MyProfileView(APIView):
    def get(self,request):
        if request.session.has_key('accessToken'):
            try:
                AccessToken(request.session['accessToken'])
                d_token = decode_token(request.session['accessToken'])
                user_id = d_token['user_id']
                user = User.objects.get(id = user_id)
                data = {
                    "user_id":user.pk,
                    "fnm":user.first_name,
                    "lnm":user.last_name,
                    "email":user.email,
                    "password":user.password,
                    "role": user.role  
                }
                return Response(data)
            except Exception:
                return Response({'msg': 'Unauthorized'},status=status.HTTP_401_UNAUTHORIZED) 
    def post(self,request):
        if request.session.has_key('accessToken'):
            try:
                AccessToken(request.session['accessToken'])
                d_token = decode_token(request.session['accessToken'])
                user_id = d_token['user_id']
                user = User.objects.get(id = user_id)
                user.first_name = request.data['fnm']
                user.last_name = request.data['lnm']
                user.email = request.data['email']
                user.save()
                print(request.data)
                data = {
                    "user_id":user.pk,
                    "fnm":user.first_name,
                    "lnm":user.last_name,
                    "email":user.email  
                }
                return Response(data)
            except Exception:
                return Response({'msg': 'Unauthorized'},status=status.HTTP_401_UNAUTHORIZED)
        
class MyattendanceView(APIView):
    serializer_class = MyAttendanceSerializer
       
    def get(self, request):
        if request.session.has_key('accessToken'):
            try:
                AccessToken(request.session['accessToken'])
                subject = Subjects.objects.all()
                mainData = []
                for i in subject:
                    mainData.append({
                        'subId':i.pk,
                        'subnm':i.subName
                    })
                return Response(mainData)
            except Exception:
                return Response({'msg': 'Unauthorized'},status=status.HTTP_401_UNAUTHORIZED)
    
    def post(self, request):
        d_token = decode_token(request.session['accessToken'])
        user_id = d_token['user_id']
        serializer = MyAttendanceSerializer(data=request.data)
        if serializer.is_valid():
            start_date = serializer.validated_data['start_date']
            end_date = serializer.validated_data['end_date']
            subject = serializer.validated_data['subjects']
            student = Students.objects.get(user = user_id)
            attendance = Attendance.objects.filter(student = student).filter(subject = subject).filter(created_at__date__range = (start_date,end_date))
            attendance_arr = []
            for i in attendance:
                attendance_arr.append({
                    "subject":i.subject.subName,
                    "status":i.status,
                    "date":i.created_at
                })
            return Response(attendance_arr)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


      
    
        
           