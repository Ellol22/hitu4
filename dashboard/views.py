from rest_framework.parsers import MultiPartParser
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Dash
from django.http import JsonResponse
from accounts.models import Student, Doctor  # استورد موديل Doctor
from .serializer import StudentSerializer, DoctorSerializer  # هنعمل DoctorSerializer بسيط
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from accounts.models import Student, Doctor
from dashboard.models import Dash
from dashboard.serializer import StudentSerializer, DoctorSerializer

@csrf_exempt
@api_view(['GET', 'POST', 'OPTIONS'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def personal_info(request):
    print("=" * 50)
    print(f"[Personal Info] Incoming {request.method} request")
    print(f"Path: {request.path}")
    print(f"User: {request.user.username} (ID: {request.user.id})")
    print(f"Body: {request.data}")
    print(f"Files: {request.FILES}")
    print("=" * 50)

    # لو OPTIONS → manual response مظبوط
    if request.method == 'OPTIONS':
        print("[Personal Info] Handling manual OPTIONS response")
        response = Response(status=204)  
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
        response["Access-Control-Max-Age"] = "86400"
        
        print(f"[Personal Info] Response (204): Manual OPTIONS Response sent.")
        return response

    # الباقي (GET أو POST)
    try:
        user = request.user
        profile_type = None
        profile_instance = None

        # نحاول نجيب الطالب
        try:
            student = Student.objects.get(user=user)
            profile_type = 'student'
            profile_instance = student
        except Student.DoesNotExist:
            pass

        # لو مش طالب نحاول نجيب الدكتور
        if profile_instance is None:
            try:
                doctor = Doctor.objects.get(user=user)
                profile_type = 'doctor'
                profile_instance = doctor
            except Doctor.DoesNotExist:
                pass

        # لو مفيش طالب ولا دكتور
        if profile_instance is None:
            response_data = {'error': 'Profile not found'}
            response_status = 404
        else:
            if request.method == 'GET':
                if profile_type == 'student':
                    serializer = StudentSerializer(profile_instance)
                    response_data = {
                        'photo': serializer.data.get('image'),
                        'name': serializer.data.get('name'),
                        'studentId': serializer.data.get('national_id'),
                        'department': student.structure.get_department_display() if student.structure else None,
                        'email': serializer.data.get('email'),
                        'phone': serializer.data.get('mobile'),
                    }
                else:  # doctor
                    serializer = DoctorSerializer(profile_instance)
                    response_data = {
                        'photo': serializer.data.get('image'),
                        'name': serializer.data.get('name'),
                        'studentId': serializer.data.get('national_id'),
                        'department': str(serializer.data.get('department')),
                        'email': serializer.data.get('email'),
                        'phone': serializer.data.get('mobile'),
                    }

                response_status = 200


            elif request.method == 'POST':
                # نفس لوجيك رفع الصورة دلوقتي للطالب والدكتور
                dash = None
                if profile_type == 'student':
                    dash, created = Dash.objects.get_or_create(student=profile_instance)
                else:
                    dash, created = Dash.objects.get_or_create(doctor=profile_instance)

                uploaded_image = request.FILES.get('photo') or request.FILES.get('image')

                if not uploaded_image:
                    response_data = {'error': 'No image provided'}
                    response_status = 400
                else:
                    # لو فيه صورة قديمة → نمسحها
                    if dash.image and dash.image.name:
                        dash.image.delete(save=False)

                    # نحط الصورة الجديدة
                    dash.image = uploaded_image
                    dash.save()

                    response_data = {'message': 'Image uploaded successfully'}
                    response_status = 200


    except Exception as e:
        print(f"[Personal Info] Exception: {str(e)}")
        response_data = {'error': 'An unexpected error occurred'}
        response_status = 500

    print("=" * 50)
    print(f"[Personal Info] Final Response ({response_status}): {response_data}")
    print("=" * 50)

    return Response(response_data, status=response_status)

#################################################################################

# dashboard/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Announcement
from .serializer import AnnouncementSerializer
from django.shortcuts import get_object_or_404
from accounts.models import DoctorRole

@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def announcement_api(request):
    # 1. الطالب أو أي يوزر يقدر يعمل GET
    if request.method == 'GET':
        announcements = Announcement.objects.all().order_by('-created_at')
        serializer = AnnouncementSerializer(announcements, many=True)
        return Response(serializer.data)

    # بعد كده كل العمليات (POST, PUT, DELETE) محتاجة صلاحية

    # هل اليوزر دكتور؟
    try:
        doctor = request.user.doctor
    except:
        return Response({"detail": "Only doctors can perform this action."}, status=403)

    # لو معيد → ماينفعش يعمل POST/PUT/DELETE
    if doctor.role == DoctorRole.TEACHING_ASSISTANT:
        return Response({"detail": "Teaching assistants can only view announcements."}, status=403)

    # 2. دكتور إداري أو دكتور مادة بيضيف إعلان جديد
    if request.method == 'POST':
        serializer = AnnouncementSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    # 3. دكتور إداري أو دكتور مادة بيعدل إعلان
    elif request.method == 'PUT':
        announcement_id = request.data.get('id')
        announcement = get_object_or_404(Announcement, id=announcement_id, created_by=request.user)
        serializer = AnnouncementSerializer(announcement, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    # 4. دكتور إداري أو دكتور مادة بيحذف إعلان
    elif request.method == 'DELETE':
        announcement_id = request.data.get('id')
        announcement = get_object_or_404(Announcement, id=announcement_id, created_by=request.user)
        announcement.delete()
        return Response({'message': 'Deleted successfully.'})
