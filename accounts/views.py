# from django.core.exceptions import ValidationError
# from django.core.validators import validate_email
# from rest_framework.decorators import api_view
# from rest_framework.response import Response
# from rest_framework import status
# from django.contrib.auth.models import User
# from django.contrib.auth import authenticate , get_user_model
# from .models import Student, Doctor
# from django.views.decorators.csrf import csrf_exempt 
# from django.contrib.auth.tokens import default_token_generator
# from django.utils.http import urlsafe_base64_encode ,  urlsafe_base64_decode
# from django.utils.encoding import force_bytes
# from django.conf import settings
# from django.core.mail import send_mail
# from django.http import JsonResponse
# from django.contrib.auth.password_validation import validate_password
# from django.shortcuts import redirect , render



# # دالة للتحقق من صحة الإيميل
# def validate_email_format(email):
#     # اي حاجة @ اي حاجة .com
#     try:
#         validate_email(email)
#         return True
#     except ValidationError:
#         return False

# def login_page(request):
#     return render(request, 'login.html')

# @csrf_exempt
# @api_view(['POST'])
# def api_sign_up(request):
#     data = request.data
#     username = data.get('username')
#     password = data.get('password')
#     user_type = data.get('user_type')
#     national_id = data.get('national_id')
#     email = data.get('email')
#     mobile = data.get('mobile')
#     name = data.get('name') 

#     # التحقق من صحة الإيميل
#     if not validate_email_format(email):
#         return Response({'error': 'Invalid email format.'}, status=status.HTTP_400_BAD_REQUEST)
    
#     # ✅ خطوة التحقق من الباسورد
#     try:
#         validate_password(password)  # هيشوف لو الباسورد ضعيف ويرجع خطأ
#     except ValidationError as e:
#         return Response({'error': e.messages}, status=status.HTTP_400_BAD_REQUEST)

#     # التحقق من تكرار اسم المستخدم
#     if User.objects.filter(username=username).exists():
#         return Response({'error': 'Username is already taken.'}, status=status.HTTP_400_BAD_REQUEST)

#     # التحقق من النوع وتسجيل الطالب أو الطبيب
#     if user_type == 'Student':  # Student
#         try:
#             student = Student.objects.get(national_id=national_id)
#             if student.user:
#                 return Response({'error': 'This national ID is already registered with a Student account.'}, status=status.HTTP_400_BAD_REQUEST)


#             user = User.objects.create_user(username=username, password=password, email=email, first_name=name)
#             user.is_active = False  # بنقوله انت مش مفعل لسة
#             user.save()
#             student.user = user
#             student.mobile = mobile
#             student.save()

#             uid = urlsafe_base64_encode(force_bytes(user.pk))
#             token = default_token_generator.make_token(user)
#             activation_link = f"{settings.SITE_DOMAIN}/api/activate/{uid}/{token}/"
#             # إرسال الإيميل
#             send_mail(
#                 subject="activate your account ✉",
#                 message=f"hello {user.username}!\n please, press the link to activate your account :\n{activation_link}",
#                 from_email=settings.EMAIL_HOST_USER,
#                 recipient_list=[user.email],
#                 fail_silently=False,
#             )


#             return Response({'message': 'Student account created successfully.'}, status=status.HTTP_201_CREATED)

#         except Student.DoesNotExist:
#             return Response({'error': 'National ID not found in the student database.'}, status=status.HTTP_404_NOT_FOUND)

#     elif user_type == 'Doctor':  # Doctor
#         try:
#             doctor = Doctor.objects.get(national_id=national_id)
#             if doctor.user:
#                 return Response({'error': 'This national ID is already registered with a Doctor account.'}, status=status.HTTP_400_BAD_REQUEST)

#             user = User.objects.create_user(username=username, password=password, email=email, first_name=name)
#             user.is_active = False  # بنقوله انت مش مفعل لسة
#             user.save()
#             doctor.user = user
#             doctor.mobile = mobile
#             doctor.save()

#             uid = urlsafe_base64_encode(force_bytes(user.pk))
#             token = default_token_generator.make_token(user)
#             activation_link = f"{settings.SITE_DOMAIN}/api/activate/{uid}/{token}/"
#             # إرسال الإيميل
#             send_mail(
#                 subject="activate your account ✉",
#                 message=f"hello {user.username}!\n please, press the link to activate your account :\n{activation_link}",
#                 from_email=settings.EMAIL_HOST_USER,
#                 recipient_list=[user.email],
#                 fail_silently=False,
#             )

#             return Response({'message': 'Doctor account created successfully.'}, status=status.HTTP_201_CREATED)

#         except Doctor.DoesNotExist:
#             return Response({'error': 'National ID not found in the doctor database.'}, status=status.HTTP_404_NOT_FOUND)

#     return Response({'error': 'Invalid user_type. Must be "Doctor" for Doctor or "Student" for Student.'}, status=status.HTTP_400_BAD_REQUEST)


# @api_view(['POST'])
# def api_log_in(request):
#     data = request.data
#     username = data.get('username')
#     password = data.get('password')

#     user = authenticate(username=username, password=password)

#     if user is not None:
#         # return Response({'message': 'Login successful.'}, status=status.HTTP_200_OK)
#         from django.contrib.auth import login
#         login(request, user)  # دي اللي بتخلي Django يعرف اليوزر في كل الصفحات بعد كده
#         return redirect('personal-info-page')  # نوديه على صفحة البيانات
#     else:
#         return Response({'error': 'Invalid username or password.'}, status=status.HTTP_401_UNAUTHORIZED)
    




# User = get_user_model()
# def activate_user(request, uidb64, token):
#     try:
#         uid = urlsafe_base64_decode(uidb64).decode()
#         user = User.objects.get(pk=uid)
#     except (User.DoesNotExist, ValueError, TypeError, OverflowError):
#         user = None

#     if user and default_token_generator.check_token(user, token):
#         user.is_active = True
#         user.save()
#         return JsonResponse({'message': 'تم تفعيل الحساب بنجاح ✅'})
#     else:
#         return JsonResponse({'message': 'رابط التفعيل غير صالح ❌'}, status=400)

##############################################################################################
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, get_user_model
from .models import DoctorRole, Student, Doctor
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer

# إضافة imports لـ JWT tokens (تأكد أنك مثبت مكتبة simplejwt)
from rest_framework_simplejwt.tokens import RefreshToken

def validate_email_format(email):
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False

User = get_user_model()

@csrf_exempt
@api_view(['POST'])
def api_sign_up(request):
    data = request.data
    print("Signup request data:", data)  # لوج كامل للداتا القادمة

    username = data.get('username')
    password = data.get('password')
    user_type = data.get('userType')
    national_id = data.get('nationalId')
    email = data.get('email')
    name = data.get('fullname')

    # اختياري
    mobile = data.get('mobile', '')
    sec_num = data.get('sec_num', None)
    role = data.get('role', 'subject_doctor')

    # التحقق من الحقول الأساسية فقط
    if not all([username, password, user_type, national_id, email, name]):
        print("Missing required fields!")
        return Response({'error': 'All required fields (username, password, userType, nationalId, email, fullname) must be provided.'}, status=status.HTTP_400_BAD_REQUEST)

    if not validate_email_format(email):
        print(f"Invalid email format: {email}")
        return Response({'error': 'Invalid email format.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        validate_password(password)
    except ValidationError as e:
        print(f"Password validation error: {e.messages}")
        return Response({'error': e.messages}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        print(f"Username already taken: {username}")
        return Response({'error': 'Username is already taken.'}, status=status.HTTP_400_BAD_REQUEST)

    if user_type == 'Student':
        try:
            student = Student.objects.get(national_id=national_id)
            if student.user:
                print(f"Student with national ID {national_id} already linked to user")
                return Response({'error': 'This national ID is already registered with a Student account.'}, status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.create_user(username=username, password=password, email=email, first_name=name)
            user.is_active = False
            user.save()
            print(f"Created user account for student {username}")

            student.user = user

            if mobile:
                student.mobile = mobile

            if sec_num is not None:
                try:
                    student.sec_num = int(sec_num)
                except ValueError:
                    print("sec_num is not an integer")
                    return Response({'error': 'sec_num must be an integer.'}, status=status.HTTP_400_BAD_REQUEST)

            student.save()
            print(f"Linked user to student with national ID {national_id}")

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            activation_link = f"{settings.SITE_DOMAIN}/accounts/activate/{uid}/{token}/"
            print(f"Activation link: {activation_link}")

            send_mail(
                subject="Activate your account ✉",
                message=f"Hello {user.username}!\nPlease, press the link to activate your account:\n{activation_link}",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user.email],
                fail_silently=False,
            )
            print(f"Sent activation email to {user.email}")

            return Response({'message': 'Student account created successfully.'}, status=status.HTTP_201_CREATED)

        except Student.DoesNotExist:
            print(f"Student with national ID {national_id} not found")
            return Response({'error': 'National ID not found in the student database.'}, status=status.HTTP_404_NOT_FOUND)

    elif user_type == 'Staff':
        try:
            doctor = Doctor.objects.get(national_id=national_id)
            if doctor.user:
                print(f"Doctor with national ID {national_id} already linked to user")
                return Response({'error': 'This national ID is already registered with a Doctor account.'}, status=status.HTTP_400_BAD_REQUEST)

            if role not in dict(DoctorRole.choices):
                print(f"Invalid role '{role}' received, defaulting to 'subject_doctor'")
                role = 'subject_doctor'  # اجعل القيمة الافتراضية

            user = User.objects.create_user(username=username, password=password, email=email, first_name=name)
            user.is_active = False
            user.save()
            print(f"Created user account for doctor {username}")

            doctor.user = user
            doctor.role = role

            if mobile:
                doctor.mobile = mobile

            doctor.save()
            print(f"Linked user to doctor with national ID {national_id}")

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            activation_link = f"{settings.SITE_DOMAIN}/accounts/activate/{uid}/{token}/"
            print(f"Activation link: {activation_link}")

            send_mail(
                subject="Activate your account ✉",
                message=f"Hello {user.username}!\nPlease, press the link to activate your account:\n{activation_link}",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user.email],
                fail_silently=False,
            )
            print(f"Sent activation email to {user.email}")

            return Response({'message': 'Doctor account created successfully.'}, status=status.HTTP_201_CREATED)

        except Doctor.DoesNotExist:
            print(f"Doctor with national ID {national_id} not found")
            return Response({'error': 'National ID not found in the doctor database.'}, status=status.HTTP_404_NOT_FOUND)

    else:
        print(f"Invalid userType received: {user_type}")
        return Response({'error': 'Invalid userType. Must be "Student" or "Staff".'}, status=status.HTTP_400_BAD_REQUEST)


from rest_framework_simplejwt.views import TokenObtainPairView

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        print("Login request data:", request.data)  # طباعة بيانات الريكويست (الـ body)
        response = super().post(request, *args, **kwargs)
        print("Login response data:", response.data)  # طباعة بيانات الرد
        return response






@api_view(['GET'])
def activate_user(request, uidb64, token):
    print(f"Activation attempt with uid: {uidb64} and token: {token}")
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError) as e:
        print(f"Activation error: {str(e)}")
        return Response(
            {'error': 'Invalid activation link.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        print(f"User {user.username} activated successfully")
        return Response(
            {'message': 'Account activated successfully.'},
            status=status.HTTP_200_OK
        )
    else:
        print("Invalid or expired activation link")
        return Response(
            {'error': 'Invalid or expired activation link.'},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['POST'])
def api_logout(request):
    print("Logout request received - no server-side token handling")

    # Simply return success; client should delete tokens locally
    return Response({'message': 'Logged out successfully.'}, status=status.HTTP_200_OK)

@api_view(['POST'])
def api_forgot_password(request):
    email = request.data.get('email')
    print(f"Password reset requested for email: {email}")

    if not validate_email_format(email):
        print("Invalid email format")
        return Response(
            {'error': 'Invalid email format.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.get(email=email)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_link = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}"# Send email with reset_link
        print(f"Password reset link: {reset_link}")

        send_mail(
            subject="Reset your password",
            message=f"Hello {user.username},\nPlease use the following link to reset your password:\n{reset_link}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,
        )
        print(f"Sent password reset email to {email}")
        return Response({'message': 'Password reset link sent to your email.'}, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        print(f"Email not found: {email}")
        return Response({'error': 'Email not found.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def api_reset_password(request):
    # نجيب البيانات كلها من request.data بدلاً من URL
    uidb64 = request.data.get('uid')
    token = request.data.get('token')
    new_password = request.data.get('password')

    print(f"Password reset attempt with uid: {uidb64} and token: {token}")

    if not uidb64 or not token or not new_password:
        return Response({'error': 'UID, token, and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError) as e:
        print(f"Reset password error: {str(e)}")
        return Response({'error': 'Invalid reset link.'}, status=status.HTTP_400_BAD_REQUEST)

    if not default_token_generator.check_token(user, token):
        print("Invalid or expired reset token")
        return Response({'error': 'Invalid or expired reset token.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        validate_password(new_password)
    except ValidationError as e:
        print(f"Password validation error: {e.messages}")
        return Response({'error': e.messages}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save()
    print(f"Password reset successfully for user {user.username}")

    return Response({'message': 'Password reset successful.'}, status=status.HTTP_200_OK)