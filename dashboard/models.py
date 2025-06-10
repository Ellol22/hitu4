from django.db import models
from accounts.models import Student  # استدعي الموديل بتاع الطالب
from django.contrib.auth.models import User

def image_upload(instance, filename):
    name, extension = filename.split(".")
    return "student-image/%s.%s" % (instance.student.user.username, extension)

class Dash(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE)  # ربط الصورة بالطالب
    image = models.ImageField(upload_to=image_upload, null=True, blank=True)
    
##################################################################################

def upload_announcement_image(instance, filename):
    return f"announcements/{instance.created_by.username}/{filename}"

class Announcement(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to=upload_announcement_image, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title