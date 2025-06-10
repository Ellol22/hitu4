from django.db import models
from django.utils import timezone
from accounts.models import Student
from courses.models import Course

# جلسة المحاضرة اللي الدكتور بيسجلها
class LectureSession(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)  # اسم المحاضرة
    date = models.DateField(default=timezone.now)  # تاريخ المحاضرة
    is_open_for_attendance = models.BooleanField(default=False)  # اختياري لو حابة صراحة اكتر


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



# جلسة QR Code خاصة بمحاضرة محددة
class QRCodeSession(models.Model):
    lecture = models.ForeignKey(LectureSession, on_delete=models.CASCADE,null=True, blank=True)  # ربط الـ QR بمحاضرة معينة
    code = models.CharField(max_length=10)  # الكود العشوائي
    created_at = models.DateTimeField(default=timezone.now)  # وقت الإنشاء
    image = models.ImageField(upload_to='qr_codes/', null=True, blank=True)  # صورة الـ QR
    is_active = models.BooleanField(default=True)  # هل الكود لسه شغال؟

    def is_expired(self):
        # الكود منتهي بعد دقيقة واحدة
        return (timezone.now() - self.created_at).total_seconds() > 60

    def __str__(self):
        return f"{self.lecture} | Code: {self.code} | Time: {self.created_at.strftime('%H:%M:%S')}"
