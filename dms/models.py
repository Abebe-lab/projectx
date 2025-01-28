import logging
import os

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from pdf2image.exceptions import PDFPageCountError

from organogram.models import ContentTypeModelField, Profile, BusinessUnit, ExternalCustomer
from django.conf import settings
from django.contrib.auth.models import User
from easy_thumbnails.files import get_thumbnailer
from pdf2image import convert_from_path


# Create your models here.
class DocumentCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    class Meta:
        verbose_name_plural = "Document Categories"

    def __str__(self):
        return self.name

class Document(models.Model):
    title = models.CharField(max_length=100, blank=False, null=False)
    document_number = models.CharField(max_length=100, unique=True)
    # author = models.CharField(max_length=100, blank=True, null=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=False, related_name="documents_uploaded")
    privacy = models.CharField(choices=[
        ('public', 'Public'),
        ('private', 'Private')],
        default='private',
        max_length=15)
    description = models.TextField()
    content_type = ContentTypeModelField(ContentType, verbose_name='Owner Type', null=True, on_delete=models.SET_NULL)
    object_id = models.PositiveIntegerField()
    owner = GenericForeignKey('content_type', 'object_id')
    category = models.ForeignKey(DocumentCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="categories")
    created_date = models.DateField(blank=True, null=True)
    encryption_key = models.CharField(max_length=100, blank=True, null=True)
    file = models.FileField(upload_to=settings.DOCUMENT_PATH)
    # keywords = models.TextField(blank=True, null=True)
    uploaded_date = models.DateTimeField(auto_now_add=True)

    shared_with = models.ManyToManyField(User, through='SharedDocument', related_name='documents_shared_with')

    class Meta:
        permissions = [
            ("can_create_document", "Can create document"),
            ("can_share_document", "Can share document"),
            ("can_update_document", "Can update document"),
            ("can_delete_document", "Can delete document"),
        ]

    def __str__(self):
        return self.title

    def get_owner_name(self, in_english=True):
        owner = ""

        if self.content_type == ContentType.objects.get(model="user", app_label="auth"):
            profile = Profile.objects.get(user_id=self.uploaded_by)
            if in_english:
                owner = f"{profile.user.first_name} {profile.user.last_name}"
            else:
                owner = profile.full_name

        elif self.content_type == ContentType.objects.get(model="businessunit", app_label="organogram"):
            bu = BusinessUnit.objects.get(pk=self.object_id)
            owner = bu.name_en if in_english else bu.name_am

        elif self.content_type == ContentType.objects.get(model="externalcustomer", app_label="organogram"):
            ec = ExternalCustomer.objects.get(pk=self.object_id)
            owner = ec.name_en if in_english else ec.name_am

        return owner


    def get_thumbnail(self):
        file_extension = self.file.name.split('.')[-1]
        if file_extension.lower() == 'pdf':
            pages = convert_from_path(self.file.path)
            if pages:
                page_image = pages[0]
                try:
                    thumbnail_options = {'size': (100, 100)}

                    thumbnail = page_image.copy()
                    thumbnail.thumbnail(thumbnail_options['size'])
                    thumbnail_path = f"{self.file.path}_thumbnail.jpg"
                    thumbnail.save(thumbnail_path)
                    thumbnail_url = f"/media/Documents/{self.file.name.split('/')[-1]}_thumbnail.jpg"

                    return thumbnail_url
                except Exception as e:
                    print(f"Error saving image: {e}")
            return None
        else:
            thumbnailer = get_thumbnailer(self.file)
            thumbnail_options = {'size': (100, 100)}
            thumbnail = thumbnailer.get_thumbnail(thumbnail_options)
            return thumbnail.url
class SharedDocument(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='shared_documents')
    shared_with = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shared_documents_from')
    shared_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('document', 'shared_with')  # Prevent duplicate shares

    # def __str__(self):
    #     return f"{self.document.title} shared with {self.shared_with.username} on {self.shared_at}"

    def __str__(self):
        shared_with_username = self.shared_with.username if self.shared_with else "Unknown User"
        return f"{self.document.title} shared with {shared_with_username} on {self.shared_at}"

class MemoToDMS(models.Model):
    memo = models.ForeignKey('memotracker.Memo', on_delete=models.CASCADE, related_name="memo_details")
    sent_date = models.DateTimeField(auto_now_add=True)
    sent_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    # remarks = models.TextField(blank=True, null=True)

    # def __str__(self):
    #     return f'MemoDetail for {self.memo.reference_number} - Sent by {self.sent_by.username} on {self.sent_date}'

    def __str__(self):
        sent_by_username = self.sent_by.username if self.sent_by else "Unknown Sender"
        return f'MemoDetail for {self.memo.reference_number} - Sent by {sent_by_username} on {self.sent_date}'