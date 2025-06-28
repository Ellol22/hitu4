import logging
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, get_user_model
from accounts.serializers import CustomTokenObtainPairSerializer
from .models import DoctorRole, Student, Doctor
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated

# Set up logging
logger = logging.getLogger(__name__)

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
    logger.debug("Signup request data: %s", data)

    username = data.get('username')
    password = data.get('password')
    user_type = data.get('userType')
    national_id = data.get('nationalId')
    email = data.get('email')
    name = data.get('fullname')
    mobile = data.get('mobile', '')
    sec_num = data.get('sec_num', None)
    role = data.get('role', 'subject_doctor')

    if not all([username, password, user_type, national_id, email, name]):
        logger.error("Missing required fields")
        return Response({'error': 'All required fields (username, password, userType, nationalId, email, fullname) must be provided.'}, status=status.HTTP_400_BAD_REQUEST)

    if not validate_email_format(email):
        logger.error("Invalid email format: %s", email)
        return Response({'error': 'Invalid email format.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        validate_password(password)
    except ValidationError as e:
        logger.error("Password validation error: %s", e.messages)
        return Response({'error': e.messages}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        logger.error("Username already taken: %s", username)
        return Response({'error': 'Username is already taken.'}, status=status.HTTP_400_BAD_REQUEST)

    if user_type == 'Student':
        try:
            student = Student.objects.get(national_id=national_id)
            if student.user:
                logger.error("Student with national ID %s already linked to user", national_id)
                return Response({'error': 'This national ID is already registered with a Student account.'}, status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.create_user(username=username, password=password, email=email, first_name=name)
            user.is_active = False
            user.save()
            logger.info("Created user account for student %s", username)

            student.user = user
            if mobile:
                student.mobile = mobile
            if sec_num is not None:
                try:
                    student.sec_num = int(sec_num)
                except ValueError:
                    logger.error("sec_num is not an integer: %s", sec_num)
                    return Response({'error': 'sec_num must be an integer.'}, status=status.HTTP_400_BAD_REQUEST)

            student.save()
            logger.info("Linked user to student with national ID %s", national_id)

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            activation_link = f"{settings.FRONTEND_URL}/activate/{uid}/{token}/"
            logger.debug("Activation link: %s", activation_link)

            send_mail(
                subject="Activate your account ✉",
                message=(
                    f"Hello {user.username},\n\n"
                    f"Your account has been created successfully.\n"
                    f"Username: {username}\n"
                    f"Password: {password}\n\n"
                    f"⚠ You will not be able to log in until you activate your account.\n"
                    f"Please click the link below to activate:\n{activation_link}\n\n"
                    f"If you did not request this, please ignore this message."
                    f"Thank you,\n"
                    f"Faculty of Industrial and Energy Technology, \nHelwan International Technological University"
                ),
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user.email],
                fail_silently=False,
            )

            logger.info("Sent activation email to %s", user.email)

            return Response({'message': 'Student account created successfully. Please check your email to activate.'}, status=status.HTTP_201_CREATED)

        except Student.DoesNotExist:
            logger.error("Student with national ID %s not found", national_id)
            return Response({'error': 'National ID not found in the student database.'}, status=status.HTTP_404_NOT_FOUND)

    elif user_type == 'Staff':
        try:
            doctor = Doctor.objects.get(national_id=national_id)
            if doctor.user:
                logger.error("Doctor with national ID %s already linked to user", national_id)
                return Response({'error': 'This national ID is already registered with a Doctor account.'}, status=status.HTTP_400_BAD_REQUEST)

            if role not in dict(DoctorRole.choices):
                logger.warning("Invalid role '%s' received, defaulting to 'subject_doctor'", role)
                role = 'subject_doctor'

            if role == DoctorRole.ADMIN_DOCTOR and (not request.user.is_authenticated or not request.user.is_superuser):
                logger.error("Unauthorized attempt to create admin_doctor by user %s", request.user.username if request.user.is_authenticated else "anonymous")
                return Response({'error': 'Only admins can create admin doctor accounts.'}, status=status.HTTP_403_FORBIDDEN)

            user = User.objects.create_user(username=username, password=password, email=email, first_name=name)
            if role == DoctorRole.ADMIN_DOCTOR:
                user.is_staff = True
                user.is_superuser = True
                logger.info("Assigned admin privileges to ADMIN_DOCTOR for user %s", username)

            user.is_active = False
            user.save()
            logger.info("Created user account for doctor %s", username)

            doctor.user = user
            doctor.role = role
            if mobile:
                doctor.mobile = mobile
            doctor.save()
            logger.info("Linked user to doctor with national ID %s", national_id)

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            activation_link = f"{settings.FRONTEND_URL}/activate/{uid}/{token}/"
            logger.debug("Activation link: %s", activation_link)

            send_mail(
                subject="Activate your account ✉",
                message=(
                    f"Hello {user.username},\n\n"
                    f"Your account has been created successfully.\n"
                    f"Username: {username}\n"
                    f"Password: {password}\n\n"
                    f"⚠ You will not be able to log in until you activate your account.\n"
                    f"Please click the link below to activate:\n{activation_link}\n\n"
                    f"If you did not request this, please ignore this message."
                    f"Thank you,\n"
                    f"Faculty of Industrial and Energy Technology, \nHelwan International Technological University"
                ),
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user.email],
                fail_silently=False,
            )
            logger.info("Sent activation email to %s", user.email)

            return Response({'message': 'Doctor account created successfully. Please check your email to activate.'}, status=status.HTTP_201_CREATED)

        except Doctor.DoesNotExist:
            logger.error("Doctor with national ID %s not found", national_id)
            return Response({'error': 'National ID not found in the doctor database.'}, status=status.HTTP_404_NOT_FOUND)

    else:
        logger.error("Invalid userType received: %s", user_type)
        return Response({'error': 'Invalid userType. Must be "Student" or "Staff".'}, status=status.HTTP_400_BAD_REQUEST)





# login
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        data = serializer.validated_data
        refresh_token = data.get('refresh')

        # إعداد الـ response مع البيانات
        response = Response(data, status=status.HTTP_200_OK)

        # ✅ ضيف الكوكي هنا
        response.set_cookie(
            key='refresh',
            value=refresh_token,
            httponly=True,
            secure=True,  # يستخدم secure فقط في production
            samesite='None',
            path='/',
        )

        return response



@csrf_exempt
class CustomTokenRefreshView(TokenRefreshView):
    pass  # No customization needed unless you want to add extra logic

@api_view(['GET'])
def activate_user(request, uidb64, token):
    logger.debug("Activation attempt with uid: %s and token: %s", uidb64, token)
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError) as e:
        logger.error("Activation error: %s", str(e))
        return Response({'error': 'Invalid activation link.'}, status=status.HTTP_400_BAD_REQUEST)

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        logger.info("User %s activated successfully", user.username)
        return Response({'message': 'Account activated successfully.'}, status=status.HTTP_200_OK)
    else:
        logger.error("Invalid or expired activation link")
        return Response({'error': 'Invalid or expired activation link.'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def api_logout(request):
    logger.debug("Logout request received")
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
            logger.info("Refresh token blacklisted successfully")
        return Response({'message': 'Logged out successfully.'}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error("Error during logout: %s", str(e))
        return Response({'message': 'Logged out successfully.'}, status=status.HTTP_200_OK)

@api_view(['POST'])
def api_forgot_password(request):
    email = request.data.get('email')
    logger.debug("Password reset requested for email: %s", email)

    if not validate_email_format(email):
        logger.error("Invalid email format: %s", email)
        return Response({'error': 'Invalid email format.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_link = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"
        logger.debug("Password reset link: %s", reset_link)

        send_mail(
            subject="Reset your password",
            message=f"Hello {user.username},\nPlease use the following link to reset your password:\n{reset_link}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,
        )
        logger.info("Sent password reset email to %s", email)
        return Response({'message': 'Password reset link sent to your email.'}, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        logger.error("Email not found: %s", email)
        return Response({'error': 'Email not found.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def api_reset_password(request):
    uidb64 = request.data.get('uid')
    token = request.data.get('token')
    new_password = request.data.get('password')
    logger.debug("Password reset attempt with uid: %s and token: %s", uidb64, token)

    if not uidb64 or not token or not new_password:
        logger.error("Missing required fields for password reset")
        return Response({'error': 'UID, token, and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError) as e:
        logger.error("Reset password error: %s", str(e))
        return Response({'error': 'Invalid reset link.'}, status=status.HTTP_400_BAD_REQUEST)

    if not default_token_generator.check_token(user, token):
        logger.error("Invalid or expired reset token")
        return Response({'error': 'Invalid or expired reset token.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        validate_password(new_password)
    except ValidationError as e:
        logger.error("Password validation error: %s", e.messages)
        return Response({'error': e.messages}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save()
    logger.info("Password reset successfully for user %s", user.username)
    return Response({'message': 'Password reset successful.'}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_type(request):
    user = request.user
    logger.debug("Get user type for user: %s", user.username)

    if hasattr(user, 'student'):
        student = user.student
        structure = getattr(student, 'structure', None)
        return Response({
            'userType': 'Student',
            'fullName': student.name,
            'nationalId': student.national_id,
            'academicYear': structure.get_year_display() if structure else None,
            'department': structure.get_department_display() if structure else None,
        })

    elif hasattr(user, 'doctor'):
        doctor = user.doctor
        structures = doctor.structures.all()
        return Response({
            'userType': 'Staff',
            'fullName': doctor.name,
            'nationalId': doctor.national_id,
            'academicYear': [s.get_year_display() for s in structures],
            'department': [s.get_department_display() for s in structures],
        })

    else:
        logger.warning("User %s has no associated student or doctor", user.username)
        return Response({'userType': 'Other'}, status=status.HTTP_400_BAD_REQUEST)

