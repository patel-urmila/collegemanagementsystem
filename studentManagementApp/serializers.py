from rest_framework import serializers
from .models import *
from django.contrib.auth import authenticate

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['first_name','last_name','email','password','confirm_password','role']
        
    def create(self, validated_data):
        password = validated_data.pop('password')
        confirm_password = validated_data.pop('confirm_password')
        roles = validated_data['role']
        if password != confirm_password:
            raise serializers.ValidationError("Passwords do not match")
        
        user = User.objects.create(first_name=validated_data['first_name'],last_name=validated_data['last_name'],email=validated_data['email'],role=validated_data['role'],is_staff=True,is_superuser = True)

        user.set_password(password)
        user.save()
        return user
        
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        user = authenticate(
            username=attrs['username'], password=attrs['password']
        )
        if not user:
            raise serializers.ValidationError('Invalid username or password')

        attrs['user'] = user
        return attrs
    
class SessionSerializer(serializers.Serializer):
    startYear = serializers.DateField(format="%Y-%m-%d")
    endYear = serializers.DateField(format="%Y-%m-%d")
    
    class Meta:
        model = SessionYear
        # fields = ['startYear','endYear']
        fields = '__all__'

class NewCourseSerializer(serializers.ModelSerializer):
    sessionYear = SessionSerializer()
    class Meta:
        model = Courses
        fields = '__all__'

class TeacherSerializer(serializers.ModelSerializer):    
    class Meta:
        model = User
        fields = ['first_name','last_name','email']     
        
class AddSubjectSerializer(serializers.ModelSerializer):
    course = NewCourseSerializer()
    # teacher = TeacherSerializer()
    class Meta:
        model = Subjects
        fields = '__all__'
        # fields = ['subName','course','teacher']       

class StudentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name','last_name','email','password']
        
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.role = "Student"
        user.set_password(password)
        user.save()
        return user
      
class StudentSerializer(serializers.ModelSerializer):
    user = StudentUserSerializer()
    class Meta:
        model = Students
        fields = ['user','course','sessionYear']
        
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = StudentUserSerializer.create(StudentUserSerializer(), validated_data=user_data)
        student = Students.objects.create(user=user, **validated_data)
        return student
    

class StaffLeaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffLeave
        exclude = ['user','status']
        
class StudentLeaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentLeave
        exclude = ['user','status']