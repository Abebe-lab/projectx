from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from dms import apps
from organogram.models import ContentTypeModelField, ExternalCustomer, UserRole, BusinessUnit, Profile
from dms.models import Document
from ckeditor_uploader.fields import RichTextUploadingField
from django.db.models import Q
from dms.models import Document  # Import Document if needed

class Memo(models.Model):
    reference_number = models.CharField(max_length=50, unique=True)
    subject = models.CharField(max_length=300)
    content = RichTextUploadingField(blank=True, null=True) 
    memo_date = models.DateTimeField()
    created_date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='created_by')
    content_type = ContentTypeModelField(ContentType, verbose_name='Owner Type', null=True, on_delete=models.SET_NULL)
    object_id = models.PositiveIntegerField()
    owner = GenericForeignKey('content_type', 'object_id')
    urgent = models.BooleanField(default=False)
    public = models.BooleanField(default=False)
    keywords = models.CharField(max_length=100, blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)
    assigned_to = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='assigned_to')
    status = models.CharField(choices=[
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('sent', 'Sent'),
        ('closed', 'Closed')
    ], default='draft')
    due_date = models.DateTimeField(null=True, blank=True)
    attached_memos = models.ManyToManyField('self', blank=True)
    to_external = models.BooleanField(default=False)
    in_english = models.BooleanField(default=False)

    def __str__(self):
        return self.reference_number + ' - ' + self.subject

    def memo_status(self):
        """"Upon memo approval remove all approval routes"""
        pass

    def get_attached_memo_memos(self):
        """
        Returns a formatted string containing titles and reference numbers
        of attached memos.

        Returns:
            str: A formatted string, e.g., "Memo 1 (ABC123), Memo 2 (XYZ456)"
        """

        if not self.attached_memos.exists():
            return ""  # Return empty string if no attachments

        titles_and_refs = []
        for memo in self.attached_memo.all():
            title_and_ref = f"{memo.title} ({memo.reference_number})"  # Customize format as needed
            titles_and_refs.append(title_and_ref)
        
        return titles_and_refs

    def has_attachments(self):
        return self.attached_memos.count() > 0

    def get_route_status(self, request):
        user_role = UserRole.objects.get(user=request.user, active=True)
        bunit = user_role.business_unit
        manager = user_role.role.is_manager
        delegate = user_role.deligated
        user_type = ContentType.objects.get(model="user", app_label="auth")
        bu_type = ContentType.objects.get(model="businessunit", app_label="organogram")
        if manager or delegate:
            route = self.memoroute_set.filter(Q(destination_id=bunit.id, destination_type=bu_type) |
                                              Q(destination_id=request.user.id, destination_type=user_type)).order_by('-level').first()
        else:
            route = self.memoroute_set.filter(destination_id=request.user.id, destination_type=user_type).order_by('-level').first()
        if route:
            status = route.get_status_display()
        else:
            status = self.get_status_display()
        return status

    def get_memo_owner(self):
        owner = ""
        if self.content_type == ContentType.objects.get(model="user", app_label="auth"):
            profile = Profile.objects.get(user_id=self.object_id)
            if self.in_english:
                owner = profile.user.first_name + " " + profile.user.last_name
            else:
                owner = profile.full_name
        elif self.content_type == ContentType.objects.get(model="businessunit", app_label="organogram"):
            bu = BusinessUnit.objects.get(pk=self.object_id)
            if self.in_english:
                owner = bu.name_en
            else:
                owner = bu.name_am
        elif self.content_type == ContentType.objects.get(model="externalcustomer", app_label="organogram"):
            ec = ExternalCustomer.objects.get(pk=self.object_id)
            if self.in_english:
                owner = ec.name_en
            else:
                owner = ec.name_am
        return owner

    def get_memo_destination(self):
        destination = []
        if self.status == "sent":
            routes = self.memoroute_set.filter(level=1, carbon_copy=False)
            if routes:
                destination = self.get_memo_routes(routes)
            else:
                destination.append(self.get_memo_owner())
        else:
            destination.append(self.get_memo_owner())
        return destination

    def get_memo_routes(self, routes):
        destination = []
        dest_length = 0
        for route in routes:
            if route.destination_type.model == 'externalcustomer':
                external = ExternalCustomer.objects.get(pk=route.destination_id)
                if route.memo.in_english:
                    dest = external.name_en
                else:
                    dest = external.name_am
            elif route.destination_type.model == 'user':
                user = User.objects.get(pk=route.destination_id)
                profile = Profile.objects.get(user_id=route.destination_id)
                if route.memo.in_english:
                    dest = profile.user.first_name + " " + profile.user.last_name
                else:
                    dest = profile.full_name
            else:
                business_unit = BusinessUnit.objects.get(pk=route.destination_id)
                if route.memo.in_english:
                    dest = business_unit.name_en
                else:
                    dest = business_unit.name_am

            dest_length += len(dest)

            if dest_length < 50:
                destination.append(dest)
            else:
                destination.append('...')
                break

        return destination

    def get_memo_cc_destination(self):
        destination = []
        if self.status == "sent":
            routes = self.memoroute_set.filter(level=1, carbon_copy=True)
            if routes:
                destination = self.get_memo_routes(routes)
        return destination

    def get_memo_assigned_to(self):
        assigned_to = ""
        if self.assigned_to:
            if self.in_english:
                assigned_to = self.assigned_to.first_name + ' ' + self.assigned_to.last_name
            else:
                profile = Profile.objects.get(user=self.assigned_to)
                if profile and profile.full_name != "":
                    assigned_to = profile.full_name
                else:
                    assigned_to = self.assigned_to.first_name + ' ' + self.assigned_to.last_name
        return assigned_to

class ApprovalRoute(models.Model):
    memo = models.ForeignKey(Memo, on_delete=models.CASCADE)
    from_user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='approval_source')
    to_user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='approval_destination')
    comment = models.CharField(max_length=100)
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.memo.reference_number + ' : ' + self.from_user.first_name + ' -> ' + self.to_user.first_name

    def get_destination(self):
        return self.to_user.first_name + ' ' + self.to_user.last_name

class MemoAction(models.Model):
    description = models.CharField(blank=False, null=False)
    description_am = models.CharField(blank=False, null=False)

    def __str__(self):
        return f'{self.description}' + ' - ' + f'{self.description_am}'


class MemoRoute(models.Model):
    memo = models.ForeignKey(Memo, on_delete=models.CASCADE)
    from_user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='route_source')
    to_user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='route_destination')
    destination_type = ContentTypeModelField(ContentType, verbose_name='Destination Type', null=True, on_delete=models.SET_NULL)
    destination_id = models.PositiveIntegerField(default=0)
    destination = GenericForeignKey('destination_type', 'destination_id')
    level = models.IntegerField(default=1)
    carbon_copy = models.BooleanField(default=False)
    # is_read = models.BooleanField(default=False)
    memo_action = models.ForeignKey(MemoAction, null=True, on_delete=models.SET_NULL)
    remark = models.TextField()
    date_sent = models.DateTimeField(auto_now_add=True)
    date_viewed = models.DateTimeField(auto_now_add=True)
    status = models.CharField(choices=[
        ('notseen', 'Not Seen'),
        ('seen', 'Seen'),
        ('reversed', 'Reversed'),
        ('forwarded', 'Forwarded'),
        ('closed', 'Closed')
    ], default='notseen')

    def __str__(self):
        app_label = 'auth'
        model_name = 'user'
        destination_type = ContentType.objects.get(app_label=app_label, model=model_name)

        try:
            if self.destination_type == ContentType.objects.get(model='externalcustomer'):
                external = ExternalCustomer.objects.get(pk=self.destination_id)
                return f"{self.memo.reference_number} : {self.from_user.first_name} -> {external.name_en}"
            elif self.destination_type == destination_type:
                user = User.objects.get(pk=self.destination_id)
                return f"{self.memo.reference_number} : {self.from_user.first_name} -> {user.first_name}"
            else:
                bu = BusinessUnit.objects.get(pk=self.destination_id)
                return f"{self.memo.reference_number} : {self.from_user.first_name} -> {bu.name_en}"
        except ExternalCustomer.DoesNotExist:
            return f"{self.memo.reference_number} : {self.from_user.first_name} -> ExternalCustomer (ID: {self.destination_id} not found)"
        except User.DoesNotExist:
            return f"{self.memo.reference_number} : {self.from_user.first_name} -> User (ID: {self.destination_id} not found)"
        except BusinessUnit.DoesNotExist:
            return f"{self.memo.reference_number} : {self.from_user.first_name} -> BusinessUnit (ID: {self.destination_id} not found)"

    # def __str__(self):
    #     app_label = 'auth'
    #     model_name = 'user'
    #     destination_type = ContentType.objects.get(app_label=app_label, model=model_name)
    #     if self.destination_type == ContentType.objects.get(model='externalcustomer'):
    #         external = ExternalCustomer.objects.get(pk=self.destination_id)
    #         return self.memo.reference_number + ' : ' + self.from_user.first_name + ' -> ' + external.name_en
    #     elif self.destination_type == destination_type:
    #         user = User.objects.get(pk=self.destination_id)
    #         return self.memo.reference_number + ' : ' + self.from_user.first_name + ' -> ' + user.first_name
    #     else:
    #         bu = BusinessUnit.objects.get(pk=self.destination_id)
    #         return self.memo.reference_number + ' : ' + self.from_user.first_name + ' -> ' + bu.name_en

    def get_business_unit(self):
        if self.to_user:
            user_role = UserRole.objects.get(user=self.to_user, active=True)
            if user_role:
                return user_role.business_unit
    # def get_source_bu(self):
    #     if self.from_user:
    #         user_role = UserRole.objects.get(user=self.from_user, active=True)
    #         if user_role.business_unit:
    #             return user_role.business_unit.name_en
    #         else:  # Assuming it's a personal user
    #             return user_role.from_user.first_name  # Adjust according to your User model
    def get_source_bu(self):
        if self.from_user:
            user = self.from_user
            return user.first_name + ' ' + user.last_name
        else:
            bu = BusinessUnit.objects.get(user=self.from_user)
            return bu.name_en

    def get_destination(self):
        app_label = 'auth'
        model_name = 'user'
        destination_type = ContentType.objects.get(app_label=app_label, model=model_name)
        external_type = ContentType.objects.get(app_label='organogram', model='externalcustomer')
        if self.destination_type == external_type:
            external = ExternalCustomer.objects.get(pk=self.destination_id)
            return external.name_en
        elif self.destination_type == destination_type:
            user = User.objects.get(pk=self.destination_id)
            return user.first_name + ' ' + user.last_name
        else:
            bu = BusinessUnit.objects.get(pk=self.destination_id)
            return bu.name_en

    def get_memo_destination_as_user(self):
        users = []
        if self.destination_type.model == "user":
            user = User.objects.get(pk=self.destination_id)
            users.append(user.id)
        elif self.destination_type.model == "businessunit":
            user_roles = UserRole.objects.filter(Q(business_unit_id=self.destination_id, active=True) & (
                    Q(role__is_manager=True) | Q(deligated=True)))
            for user_role in user_roles:
                user = user_role.user
                users.append(user.id)
        return users

class MemoAttachment(models.Model):
    memo = models.ForeignKey(Memo, on_delete=models.CASCADE, blank=True, related_name="attachments")
    document = models.ForeignKey(Document, on_delete=models.CASCADE, blank=True)
    attachment_date = models.DateTimeField(auto_now_add=True)
    attached_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    permission = models.CharField(choices=[
        ('read', 'Read'),
        ('share', 'Share'),
    ], default='read')
    remark = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'Attachment for memo {self.memo.reference_number} ' + ' - ' + f'{self.document.title}'

    def get_attached_by_display(self):
        if self.attached_by:
            # return f"{self.attached_by.username} {self.attached_by.last_name}"
            return f"{self.attached_by.first_name} {self.attached_by.last_name}".strip()
        return "Unknown"