# # from django.conf import settings
# from collegeManagementSystem import settings
# from django.shortcuts import redirect ,render
# from django.http import HttpResponseForbidden

# class LoginRequiredMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         response = self.get_response(request)
#         if not request.user.is_authenticated and request.path not in settings.LOGIN_EXEMPT_URLS:
#             return redirect(settings.LOGIN_URL)
#         return response

# class TeacherRequiredMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response
#         self.teacher_urls = ['/teacher/', '/teacher/<int:pk>', '/staffleave/<int:pk>','/subattendance/','/takeattendance/','/admin/login/']


#     def __call__(self, request):
#         print("-*-------",request.path)
#         if request.user.is_authenticated and request.user.role == 'Teacher':
#             if request.user.role is not 'Teacher' and request.path not in self.teacher_urls:
#                 return render(request,'login.html')
#             else:
#                 response = self.get_response(request)
#         else:
#             response = self.get_response(request)
#         return response
