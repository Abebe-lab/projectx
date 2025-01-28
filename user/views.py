from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.views import PasswordResetView
from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm

import user
from dms.models import Document
from django.contrib import messages
from organogram.models import Profile
from django.contrib.auth.decorators import login_required  # Import login_required decorator
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, Count
from memotracker.models import MemoRoute, Memo

from memotracker.models import Memo
from django.contrib.auth.models import User
from django.db.models.functions import TruncMonth
from datetime import datetime, timezone
import calendar
from django.utils import timezone
from django.db.models.functions import TruncMonth, ExtractMonth, ExtractYear
from datetime import datetime, timedelta
from .forms import ProfileForm, CustomPasswordChangeForm
from memotracker.views import get_memo_route
from organogram.models import UserRole
from memotracker.views import count_unread_memos, show_notifications
from urllib.parse import urlparse, parse_qs
import json
from django.contrib.auth.hashers import make_password, check_password
from organogram.models import Profile
from django.contrib.auth.hashers import make_password

@login_required
def dashboard(request):
    user = request.user  # added part
    user_profile = request.user.profile
    preferences = user_profile.preference.get('dashboard_elements', [])

    # Set default preferences if not already set
    if not preferences:
        preferences = []

        # Set default preferences only if preferences list is empty
    # Get the logged-in user's ID
    user_id = request.user.id
    # Count personal memos where the logged-in user is either the "From user" or the "To user"
    personal_content_type = ContentType.objects.get(app_label='auth', model='user')
    personal_memo_count = Memo.objects.filter(object_id=user_id, content_type=personal_content_type).exclude(status__in=["draft", "closed"]).count()

    # Count the number of incoming and outgoing memos
    bu_content_type = ContentType.objects.get(app_label='organogram', model='businessunit')
    user_id = request.user.id
    user_role = UserRole.objects.get(user=request.user, active=True)
    business_unit_id = user_role.business_unit.id

    all_memos = Memo.objects.filter(Q(object_id=business_unit_id, content_type=bu_content_type) |
                                    Q(object_id=user_id, content_type=personal_content_type))
    if user_role.role.is_manager or user_role.deligated:
        outgoing_memo_count = all_memos.exclude(status__in=["draft", "closed"]).count()
    else:
        # outgoing_memo_count = all_memos.filter(Q(created_by=request.user) | Q(assigned_to=request.user)).exclude(status__in=["draft", "closed"]).count()

        #############################
        outgoing_memo_count = all_memos.filter(created_by=request.user).exclude(status__in=["draft", "closed"]).count()

        #############################
    memo_ids = get_memo_route(request, ["reversed"])

    # Count the number of incoming memos
    app_label = 'organogram'
    model_name = 'businessunit'
    content_type_id = ContentType.objects.get(app_label=app_label, model=model_name).id
    app_label = 'auth'
    model_name = 'user'
    content_type_user = ContentType.objects.get(app_label=app_label, model=model_name).id
    # filter incoming memos
    excluded_statuses = ["draft", "approved", "closed"]
    user_creation_time = user.date_joined

    incoming_memo_count = Memo.objects.filter(
        (Q(id__in=memo_ids) | Q(public=True, created_date__gte=user_creation_time)) &
        (Q(content_type_id=content_type_id) | Q(content_type_id=content_type_user)) &
        ~Q(public=True, created_by=request.user)
    ).exclude(Q(status__in=excluded_statuses)).count()

    #####################

    # incoming_memo_count = Memo.objects.filter(
    #     (
    #             Q(id__in=memo_ids) |
    #             Q(public=True, created_date__gte=user_creation_time) |
    #             Q(assigned_to=request.user)
    #     ) &
    #     (
    #             Q(content_type_id=content_type_id) |
    #             Q(content_type_id=content_type_user)
    #     ) &
    #     ~Q(public=True, created_by=request.user)
    # ).exclude(Q(status__in=excluded_statuses)).count()
    #####################

    external_content_type = ContentType.objects.get(app_label='organogram', model='externalcustomer')
    external_memo_count = Memo.objects.filter(
        Q(id__in=memo_ids) & Q(content_type=external_content_type)
    ).count()

    # Count the number of drafts, approved, and closed memos
    draft_memo_count = Memo.objects.filter(
        Q(status='draft', created_by=user) | Q(approvalroute__to_user=user, status='draft')).distinct().count()

    approved_memo_count = Memo.objects.filter(status='approved').count()
    closed_memo_count = Memo.objects.filter(status='closed').count()

    # Count the number of documents uploaded by the user or shared with
    my_files_count = Document.objects.filter(
        Q(uploaded_by_id=user_id) | Q(shared_documents__shared_with=request.user)
    ).distinct().count()

    current_year = timezone.now().year
    current_month = timezone.now().month

    # Create a dictionary to store memo counts for each month
    memo_counts_data = {}

    # Loop through the past 12 months, starting from twelve months ago and ending with the current month
    for month_offset in range(11, -1, -1):
        # Calculate the year and month for the current iteration
        year = current_year - (1 if current_month - month_offset <= 0 else 0)
        month = (current_month - month_offset) % 12

        # Filter MemoRoute objects by the year and month
        memo_routes = MemoRoute.objects.filter(
            Q(date_sent__year=year) & Q(date_sent__month=month)
        )

        memos = Memo.objects.filter(memo_date__year=year, memo_date__month=month)
        out_memos = memos.filter(Q(object_id=business_unit_id, content_type=bu_content_type) |
                                 Q(object_id=user_id, content_type=personal_content_type))
        if user_role.role.is_manager or user_role.deligated:
            outgoing = out_memos
        else:
            outgoing = out_memos.filter(Q(created_by=request.user) | Q(assigned_to=request.user))

        # Count memos for each category
        memo_counts_data[calendar.month_name[month] + ' ' + str(year)] = {
            'incoming_count': memo_routes.filter(Q(memo__id__in=memo_ids) & (Q(memo__content_type=bu_content_type) | Q(memo__content_type=personal_content_type))).values_list('memo_id', flat=True).distinct().count(),
            'outgoing_count': outgoing.exclude(status__in=["draft", "closed"]).count(),
            'personal_count': memos.filter(object_id=user_id, content_type=personal_content_type).exclude(status__in=["draft", "closed"]).count(),
            'external_count': memo_routes.filter(Q(id__in=memo_ids) and Q(memo__content_type=external_content_type)).count(),
            'draft_count': memos.filter(status='draft').count(),
            'approved_count': memos.filter(status='approved').count(),
            'closed_count': memos.filter(status='closed').count()
        }

    if request.method == 'GET':
        context = {
            'user_name': request.user.username,
            'preferences': preferences,
            'incoming_memo_count': incoming_memo_count,
            'outgoing_memo_count': outgoing_memo_count,
            'personal_memo_count': personal_memo_count,
            'external_memo_count': external_memo_count,
            'draft_memo_count': draft_memo_count,
            'approved_memo_count': approved_memo_count,
            'closed_memo_count': closed_memo_count,
            'my_files_count': my_files_count,
            'memo_counts_data': memo_counts_data,
        }
        return render(request, 'user/dashboard.html', context)
@login_required

def edit_profile(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)

    if request.method == 'POST':
        if 'update_profile' in request.POST:
            profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Profile successfully updated.')
                return redirect('dashboard')  # Redirect after successful update

        elif 'remove_picture' in request.POST:
            if profile.profile_picture:
                profile.profile_picture.delete(save=False)  # Delete the file from storage
                profile.profile_picture = None  # Update the model field to None
                profile.save()  # Save the model

                messages.success(request, 'Profile picture removed successfully.')
                return redirect('dashboard')  # Redirect after removal

        elif 'change_password' in request.POST:
            password_form = CustomPasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                password_form.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Password has been successfully changed.')
                return redirect('dashboard')

    else:
        profile_form = ProfileForm(instance=profile)
        password_form = CustomPasswordChangeForm(user=request.user)

    context = {
        'profile_form': profile_form,
        'password_form': password_form,
    }
    return render(request, 'user/profile_edit.html', context)

@login_required
def password_change_done(request):
    return render(request, 'user/password_change_done.html')
class CustomLoginView(LoginView):
    def form_valid(self, form):
        response = super().form_valid(form)
        # Get the user object
        user = self.request.user
        # Get the profile associated with the user
        profile = Profile.objects.get(user=user)

        count_unread_memos(self.request)
        show_notifications(self.request)
        # Check if password is set
        if profile.password_set:
            url = self.request.META.get('HTTP_REFERER')
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            next_url = query_params.get("next", [None])[0]
            if next_url:
                return redirect(next_url)
            # If password is set, redirect to the dashboard
            return redirect('dashboard')  # Replace 'dashboard' with your actual dashboard URL name
        else:
            # If password is not set, redirect to the password change page
            return redirect(reverse('password_change'))  # Redirect to the named URL 'password_change'

class CustomPasswordChangeView(PasswordChangeView):
    success_url = reverse_lazy('dashboard')
    template_name = 'user/password_change.html'  # Update with your actual template name

    def form_valid(self, form):
        response = super().form_valid(form)
        # Update password_set attribute
        user = self.request.user
        profile = Profile.objects.get(user=user)
        profile.password_set = True
        profile.full_name = self.request.POST.get('full_name')
        profile.pin_code = make_password(self.request.POST.get('pin_code'))
        profile.security_answer_1 = self.request.POST.get('security_answer_1')
        profile.security_answer_2 = self.request.POST.get('security_answer_2')
        profile.security_answer_3 = self.request.POST.get('security_answer_3')
        profile.save()
        # Add success message
        messages.success(self.request, "Password changed successfully.")
        return response

    def form_invalid(self, form):
        # Add error messages for each form field
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"Error in {field}: {error}")
        # Redirect back to the password change page with error messages
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['modal_open'] = True  # Set flag to keep modal open
        return context


def dashboard_config(request):
    user_profile = request.user.profile
    preferences = user_profile.preference.get('dashboard_elements', [])

    if request.method == 'POST':
        selected_elements = request.POST.getlist('elements')

        # Update selected elements
        user_profile.preference['dashboard_elements'] = selected_elements

        # Save the updated profile
        user_profile.save()
        return redirect('dashboard')
    else:
        # If preferences are not set, use the default values
        if not preferences:
            preferences = []
            user_profile.preference['dashboard_elements'] = preferences
            user_profile.save()

        # Pass preferences to the template
        context = {
            'preferences': preferences
        }
        return render(request, 'user/dashboard_config.html', context)

def forgot_password(request):
    SECURITY_QUESTIONS = [
        ("Your birth year", "Your birth year"),
        ("Your grandmother's name", "Your grandmother's name"),
        ("Name of your elementary school", "Name of your elementary school"),
        ("Your favorite color", "Your favorite color"),
        ("Your first pet's name", "Your first pet's name"),
        ("City where you were born", "City where you were born"),
    ]

    if request.method == 'POST':
        username = request.POST.get('username')
        try:
            user = User.objects.get(username=username)
            profile = Profile.objects.get(user=user)

            # Check if answers provided by the user match the stored answers
            if (
                request.POST.get('answer1') == profile.security_answer_1 and
                request.POST.get('answer2') == profile.security_answer_2 and
                request.POST.get('answer3') == profile.security_answer_3
            ):
                # Store username in session
                request.session['reset_username'] = username
                # Redirect to the password reset page
                return redirect('password_reset')  # Replace with your actual password reset URL name
            else:
                # Incorrect answers, render the form again with an error message
                error = 'Incorrect answers provided.'
                return render(request, 'user/forgot_password.html', {
                    'error': error,
                    'security_questions': SECURITY_QUESTIONS  # Pass the list of security questions
                })
        except User.DoesNotExist:
            error = 'User does not exist.'
            return render(request, 'user/forgot_password.html', {'error': error, 'security_questions': SECURITY_QUESTIONS})
        except Profile.DoesNotExist:
            error = 'Profile does not exist for this user.'
            return render(request, 'user/forgot_password.html', {'error': error, 'security_questions': SECURITY_QUESTIONS})

    return render(request, 'user/forgot_password.html', {'error': False, 'security_questions': SECURITY_QUESTIONS})

class CustomResetPasswordView(TemplateView):
    template_name = 'user/password_reset.html'

    def post(self, request, *args, **kwargs):
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        username = request.session.get('reset_username')  # Safe retrieval

        # Check if reset_username exists
        if username is None:
            return JsonResponse({'success': False, 'message': "You need to go through the password recovery process first."})

        if new_password1 != new_password2:
            return JsonResponse({'success': False, 'message': "New passwords do not match."})

        # Check if the username is provided
        if not username:
            return JsonResponse({'success': False, 'message': "Username is required to reset the password."})

        user = get_object_or_404(User, username=username)
        profile = Profile.objects.get(user=user)

        # Reset password
        user.set_password(new_password1)
        user.save()

        # Update session auth hash
        update_session_auth_hash(request, user)

        # Set password_set attribute in profile to True
        profile.password_set = True
        profile.save()

        # Clear the session
        del request.session['reset_username']

        # Return a JSON response for success
        return JsonResponse({'success': True, 'message': "Password reset successfully."})
def accept_pin(request):
    current_user = request.user
    if request.method == 'POST':
        pin = json.loads(request.body)['pin']
        profile = Profile.objects.get(user=current_user)

        try:
            # Check if the provided PIN matches the stored hashed PIN
            if check_password(pin, profile.pin_code):
                message = "success"
            else:
                message = "error"
        except Exception as e:
            print("=================")
            print(e)
            message = "error"

        return JsonResponse({'message': message})

    else:
        context = {'form': "form", 'title': 'Add PIN Code'}
        return render(request, 'user/pin_code_modal.html', context)
def forgot_pin(request):
    SECURITY_QUESTIONS = [
        ("Your birth year", "Your birth year"),
        ("Your grandmother's name", "Your grandmother's name"),
        ("Name of your elementary school", "Name of your elementary school"),
        ("Your favorite color", "Your favorite color"),
        ("Your first pet's name", "Your first pet's name"),
        ("City where you were born", "City where you were born"),
    ]

    if request.method == 'POST':
        username = request.POST.get('username')
        answer1 = request.POST.get('answer1')
        answer2 = request.POST.get('answer2')
        answer3 = request.POST.get('answer3')

        try:
            user = User.objects.get(username=username)
            profile = Profile.objects.get(user=user)

            if (profile.security_answer_1 == answer1 and
                profile.security_answer_2 == answer2 and
                profile.security_answer_3 == answer3):
                return redirect('reset_pin', username=username)
            else:
                messages.error(request, "Security answers do not match.")
        except User.DoesNotExist:
            messages.error(request, "User does not exist.")
        except Profile.DoesNotExist:
            messages.error(request, "Profile does not exist for this user.")

    return render(request, 'user/forgot_pin.html', {
        'error': None,
        'security_questions': SECURITY_QUESTIONS  # Pass the list of security questions
    })

def reset_pin(request, username):
    if request.method == 'POST':
        new_pin = request.POST.get('new_pin')
        confirm_pin = request.POST.get('confirm_pin')

        if new_pin != confirm_pin:
            return JsonResponse({'success': False, 'message': 'PINs do not match.', 'clear_pin': True})

        user = get_object_or_404(User, username=username)
        user.profile.pin_code = make_password(new_pin)
        user.profile.save()

        return JsonResponse({'success': True})

    return render(request, 'user/reset_pin.html', {'username': username, 'error': None})