# from django.db import models
# from django.utils import timezone
# from accounts.models import Student
# from courses.models import Course

# # جلسة المحاضرة اللي الدكتور بيسجلها
# class LectureSession(models.Model):
#     course = models.ForeignKey(Course, on_delete=models.CASCADE)
#     title = models.CharField(max_length=255)  # اسم المحاضرة
#     date = models.DateField(default=timezone.now)  # تاريخ المحاضرة
#     is_open_for_attendance = models.BooleanField(default=False)
#     qr_session_started_at = models.DateTimeField(null=True, blank=True)  # ممكن نغير الاسم لـ code_session_started_at

#     def __str__(self):
#         return f"{self.course.name} - {self.title} ({self.date})"

# # سجل الحضور لكل طالب في كل محاضرة
# class Attendance(models.Model):
#     student = models.ForeignKey(Student, on_delete=models.CASCADE)
#     lecture = models.ForeignKey(LectureSession, on_delete=models.CASCADE, null=True, blank=True)
#     status_choices = [
#         ('present', 'Present'),
#         ('absent', 'Absent'),
#     ]
#     status = models.CharField(max_length=10, choices=status_choices, default='absent')
#     failed_face_attempts = models.PositiveIntegerField(default=0)
#     face_updated = models.BooleanField(default=False)
    
#     def __str__(self):
#         return f"{self.student.name} - {self.lecture} - {self.get_status_display()}"

# # جلسة الكود العشوائي الخاصة بمحاضرة معينة
# class CodeSession(models.Model):
#     lecture = models.ForeignKey(LectureSession, on_delete=models.CASCADE, null=True, blank=True)
#     code = models.CharField(max_length=6)  # كود 6 أرقام
#     created_at = models.DateTimeField(default=timezone.now)
#     is_active = models.BooleanField(default=True)

#     def is_expired(self):
#         # الكود منتهي بعد دقيقة واحدة
#         return (timezone.now() - self.created_at).total_seconds() > 60

#     def __str__(self):
#         return f"{self.lecture} | Code: {self.code} | Time: {self.created_at.strftime('%H:%M:%S')}"
    

#################################################################################################


from django.db import models
from django.utils import timezone
from accounts.models import Student
from courses.models import Course

# جلسة المحاضرة اللي الدكتور بيسجلها
class LectureSession(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)  # اسم المحاضرة
    date = models.DateField(default=timezone.now)  # تاريخ المحاضرة
    is_open_for_attendance = models.BooleanField(default=False)
    qr_session_started_at = models.DateTimeField(null=True, blank=True)  # وقت بدء جلسة الـ QR

    def __str__(self):
        return f"{self.course.name} - {self.title} ({self.date})"

# سجل الحضور لكل طالب في كل محاضرة
class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    lecture = models.ForeignKey(LectureSession, on_delete=models.CASCADE, null=True, blank=True)
    status_choices = [
        ('present', 'Present'),
        ('absent', 'Absent'),
    ]
    status = models.CharField(max_length=10, choices=status_choices, default='absent')
    failed_face_attempts = models.PositiveIntegerField(default=0)
    face_updated = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.student.name} - {self.lecture} - {self.get_status_display()}"

# جلسة الـ QR Code الخاصة بمحاضرة معينة
class CodeSession(models.Model):
    lecture = models.ForeignKey(LectureSession, on_delete=models.CASCADE, null=True, blank=True)
    qr_code_data = models.TextField(blank=True,null=True)  # نخزن الـ QR Code كـ base64 string
    created_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    def is_expired(self):
        # الـ QR Code منتهي بعد دقيقة واحدة
        return (timezone.now() - self.created_at).total_seconds() > 60

    def __str__(self):
        return f"{self.lecture} | QR Code | Time: {self.created_at.strftime('%H:%M:%S')}"