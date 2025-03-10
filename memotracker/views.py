import os
from django import template
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db.models import Q, F, IntegerField, Value
from django.shortcuts import render, redirect, get_object_or_404
from organogram import forms
from .forms import MemoForm, MemoRouteForm, ApprovalRouteForm, MemoAttachmentForm, ExternalMemoForm
from datetime import datetime, date
from dms.models import Document
from organogram.models import BusinessUnit, UserRole, Role, ExternalCustomer, Profile

from .models import Memo, MemoAttachment, MemoRoute, ApprovalRoute
from .decorators import permission_required
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, FileResponse
from django.urls import reverse

from django.contrib import messages
from django.utils import timezone
from django.db.models.functions import Cast, Replace, Substr

# reportlab imports
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from django.conf import settings
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, ListFlowable, ListItem
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT, TA_JUSTIFY

from weasyprint import HTML
from django.templatetags.static import static
from django.template.loader import render_to_string
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.files.storage import default_storage  # Ensure this import is here
import base64

import io, pytz

from notification.models import Notification, NotificationType, NotificationRecipient
from datetime import date, timedelta

from ethiopian_date import EthiopianDateConverter
from ethio_date_converter import EthiopianDateConverter

import logging
from django.core.exceptions import ValidationError
from django.http import HttpResponseBadRequest

import datetime
from datetime import datetime

def filter_memos(request, memos):
    option = request.GET.get('option')
    value = request.GET.get('value')

    if option == 'reference_number':
        memos = memos.filter(reference_number__icontains=value)
    elif option == 'subject':
        memos = memos.filter(subject__icontains=value)
    elif option == 'memo_date':
        memos = memos.filter(memo_date__date=value)
    elif option == 'urgent':
        memos = memos.filter(urgent=True).order_by('last_updated')
    elif option == 'sender':
        app_label = 'organogram'
        model_name_bu = 'businessunit'
        model_name_ec = 'externalcustomer'
        content_type_bu = ContentType.objects.get(app_label=app_label, model=model_name_bu).id
        content_type_ec = ContentType.objects.get(app_label=app_label, model=model_name_ec).id
        memos = memos.filter(Q(object_id=value, content_type_id=content_type_bu) | Q(object_id=value,
                                                                                     content_type_id=content_type_ec))
    elif option == 'receiver':
        user_d_type = ContentType.objects.get(app_label='auth', model='user')
        bu_d_type = ContentType.objects.get(app_label='organogram', model='businessunit')
        user_ids = UserRole.objects.filter(business_unit_id=value).values_list('user_id', flat=True)
        memo_ids = MemoRoute.objects.filter(Q(from_user=request.user.id) & (
                Q(destination_id__in=user_ids, destination_type=user_d_type) |
                Q(destination_id=value, destination_type=bu_d_type))).values_list('memo_id', flat=True)
        memos = memos.filter(id__in=memo_ids)
    return memos

# Pagination method
def paginate_memos(request, memos):
    paginator = Paginator(memos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return page_obj

def get_memo_route(request, excluded_statuses=[""]):
    user = request.user
    user_role = UserRole.objects.get(user=user, active=True)
    business_unit = user_role.business_unit
    manager = user_role.role.is_manager
    delegate = user_role.deligated
    type_user = ContentType.objects.get(app_label='auth', model='user')
    type_bu = ContentType.objects.get(app_label='organogram', model='businessunit')
    if manager or delegate:
        memo_ids = MemoRoute.objects.filter(Q(destination_id=business_unit.id, destination_type=type_bu) |
                                            Q(destination_id=user.id, destination_type_id=type_user.id)).exclude(
            status__in=excluded_statuses).values_list('memo_id', flat=True)
    else:
        memo_ids = MemoRoute.objects.filter(destination_id=user.id, destination_type_id=type_user.id).exclude(
            status__in=excluded_statuses).values_list('memo_id', flat=True)
    return memo_ids

# All memo list method
def list_all_memo(request):
    memo_ids = get_memo_route(request)
    memos = Memo.objects.filter(id__in=memo_ids) | Memo.objects.filter(public=True).order_by('-last_updated')
    memos = filter_memos(request, memos)
    page_obj = paginate_memos(request, memos)
    business_units = BusinessUnit.objects.all()
    users = User.objects.all()
    external = ExternalCustomer.objects.all()
    options = ['All', 'reference_number', 'subject', 'memo_date', 'urgent']
    default_option = 'All'
    current_value = request.GET.get('value', '')

    return render(request, 'memotracker/memo_list.html', {
        'page_obj': page_obj,
        'options': options,
        'default_option': default_option,
        'current_value': current_value,
        'back_btn_url': 'list_all_memo',
        'business_units': business_units,
        'users': users,
        'external': external,
        'listName': 'List of Memo'
    })


# Draft memo list
@login_required
@permission_required('Draft Memo')
def draft_memo_list(request):
    current_user = request.user
    user_id = current_user.id
    user_role = UserRole.objects.get(user=current_user, active=True)
    business_unit_id = user_role.business_unit.id
    app_label = 'organogram'
    model_name = 'businessunit'
    content_type_bu = ContentType.objects.get(app_label=app_label, model=model_name).id
    app_label = 'auth'
    model_name = 'user'
    content_type_user = ContentType.objects.get(app_label=app_label, model=model_name).id
    drafts = Memo.objects.filter(
        Q(object_id=user_id, content_type_id=content_type_user) |
        Q(object_id=business_unit_id, content_type_id=content_type_bu)
    ).filter(status='draft').order_by('-last_updated')
    drafts = filter_memos(request, drafts)
    page_obj = paginate_memos(request, drafts)
    business_units = BusinessUnit.objects.all()
    users = User.objects.all()

    return render(request, 'memotracker/memo_list.html', {
        'page_obj': page_obj,
        'business_units': business_units,
        'users': users,
        'back_btn_url': 'draft_memo_list',
        'listName': 'Draft Memo',
        'user_role': user_role,
        'option': request.GET.get('option'),
        'value': request.GET.get('value', '')
    })


# Personal memo list
@login_required
@permission_required('Personal Memo')
def personal_memo_list(request):
    current_user = request.user
    user_id = current_user.id
    app_label = 'auth'
    model_name = 'user'
    excluded_statuses = ["draft", "closed"]
    content_type_id = ContentType.objects.get(app_label=app_label, model=model_name).id
    memos = (Memo.objects.filter(object_id=user_id, content_type_id=content_type_id).
             exclude(status__in=excluded_statuses).order_by('-last_updated'))
    memos = filter_memos(request, memos)
    page_obj = paginate_memos(request, memos)
    users = User.objects.all()
    options = ['All', 'reference_number', 'subject', 'memo_date', 'urgent']
    default_option = 'All'
    current_value = request.GET.get('value', '')

    return render(request, 'memotracker/memo_list.html', {
        'page_obj': page_obj,
        'options': options,
        'default_option': default_option,
        'current_value': current_value,
        'back_btn_url': 'personal_memo_list',
        'users': users,
        'listName': 'Personal Memo',
    })

def count_unread_memos(request, listName=None):
    user = request.user
    user_role = UserRole.objects.get(user=user, active=True)
    business_unit = user_role.business_unit

    user_d_type = ContentType.objects.get(app_label='auth', model='user')
    bu_d_type = ContentType.objects.get(app_label='organogram', model='businessunit')
    ec_d_type = ContentType.objects.get(app_label='organogram', model='externalcustomer')

    filter_conditions = Q(destination_type=user_d_type, destination_id=user.id)

    if user_role.role.is_manager or user_role.deligated:
        filter_conditions |= Q(destination_type=bu_d_type, destination_id=business_unit.id)

    # Initialize unread count
    unread_count = 0

    if listName == 'Incoming Memo':
        filter_conditions &= ~Q(memo__content_type=ec_d_type) & Q(status='notseen')

        unread_count = MemoRoute.objects.filter(filter_conditions).count()

    elif listName == 'External Letter':
        filter_conditions &= Q(memo__content_type=ec_d_type) & Q(status='notseen')
        unread_count = MemoRoute.objects.filter(filter_conditions).count()
    elif listName == 'Draft Memo':
        # Count drafts in the Memo model

        unread_count = Memo.objects.filter(
            Q(status='draft', created_by=user) | Q(approvalroute__to_user=user, status='draft')).distinct().count()

    return JsonResponse({'message': 'success', 'count': unread_count})


# send notifications
def show_notifications(request):
    user = request.user
    user_role = UserRole.objects.get(user=user, active=True)
    business_unit = user_role.business_unit

    user_d_type = ContentType.objects.get(app_label='auth', model='user')
    bu_d_type = ContentType.objects.get(app_label='organogram', model='businessunit')
    ec_d_type = ContentType.objects.get(app_label='organogram', model='externalcustomer')

    memos = MemoRoute.objects.filter(
        (Q(destination_type=user_d_type, destination_id=user.id) |
         Q(destination_type=bu_d_type, destination_id=business_unit.id)) & Q(status='notseen')
    )

    notifications = []

    for memo in memos:
        due_date = memo.memo.due_date
        if due_date:
            remain_date = (due_date.date() - timezone.now().date()).days
            notification_message, recipients = handle_notification_message(memo, remain_date, user_d_type)

            if notification_message and recipients:
                notify_type = NotificationType.objects.get(name="Reminder")
                # memo_detail_url = reverse('memo_detail', args=[memo.memo.id])

                if memo.memo.content_type == ContentType.objects.get(model='externalcustomer'):
                    memo_list = "External Letter"
                else:
                    memo_list = "Incoming Memo"
                memo_detail_url = "/memotracker/memo/" + str(memo.memo.id) + "/" + memo_list

                # Include all recipients in notification creation (combined list)
                all_recipients = recipients

                for recipient in all_recipients:
                    if not NotificationRecipient.objects.filter(
                            recipient=recipient,
                            notification__message=notification_message,
                            notification__created_date__gte=date.today() - timedelta(days=1)
                    ).exists():
                        notification = Notification.create_notification(request.user, notify_type,
                                                                        notification_message, memo_detail_url)
                        NotificationRecipient.objects.filter(
                            recipient=recipient,
                            notification__message=notification_message,
                            notification__created_date__lt=date.today() - timedelta(days=1)
                        ).delete()
                        save_notification(recipient, notification)
                        notifications.append(notification_message)

    return notifications

def get_recipients(memo, user_d_type):
    if memo.destination_type == user_d_type:
        return [User.objects.get(pk=memo.destination_id)]
    else:
        # Return actual User objects instead of IDs
        user_roles = UserRole.objects.filter(
            Q(business_unit_id=memo.destination_id, active=True) &
            (Q(role__is_manager=True) | Q(deligated=True))
        )
        return [user_role.user for user_role in user_roles]

def handle_notification_message(memo, remain_date, user_d_type):
    notification_message = ""
    recipients = get_recipients(memo, user_d_type)

    if 0 < remain_date <= 3:
        # Notification to destination only
        recipients = get_recipients(memo, user_d_type)
        notification_message = f"Only {remain_date} days remaining for unseen memo with Reference No: {memo.memo.reference_number}"

    elif remain_date == 0:
        # Notification to destination only
        recipients = get_recipients(memo, user_d_type)
        notification_message = f"Today is the last date for unseen memo with Reference No: {memo.memo.reference_number}"

    elif remain_date < 0:
        # Notification to destination, created_by, and parent managers/delegations
        creator_role = UserRole.objects.filter(user=memo.memo.created_by, active=True).first()
        if creator_role:
            recipients.append(creator_role.user)

        if memo.destination_type.model == 'businessunit':
            destination_user = UserRole.objects.filter(Q(business_unit_id=memo.destination_id, active=True) & (
                    Q(role__is_manager=True) | Q(deligated=True)))
        else:
            destination_user = UserRole.objects.filter(user_id=memo.destination_id, active=True)

        if creator_role:
            if creator_role.business_unit.parent:
                parent_roles = UserRole.objects.filter(
                    Q(business_unit=creator_role.business_unit.parent, active=True) &
                    (Q(role__is_manager=True) | Q(deligated=True))
                )
                recipients.extend(user_role.user for user_role in parent_roles)

        if memo.destination_type != user_d_type:
            to_user_role = UserRole.objects.filter(business_unit_id=memo.destination_id, active=True).first()
        else:
            to_user_role = UserRole.objects.filter(user_id=memo.destination_id, active=True).first()
        if to_user_role.business_unit.parent:
            parent_unit = to_user_role.business_unit.parent
            parent_roles = UserRole.objects.filter(
                Q(business_unit=parent_unit.id, active=True) &
                (Q(role__is_manager=True) | Q(deligated=True))
            )
            recipients.extend(user_role.user for user_role in parent_roles)

        notification_message = f"The memo with Reference No: {memo.memo.reference_number} has not been seen by {', '.join(f'{recipient.user.first_name} {recipient.user.last_name}' for recipient in destination_user)}."

    return notification_message, recipients

# Incoming memo list
@login_required
@permission_required('Incoming Memo')
def incoming_memo_list(request):
    current_user = request.user
    memo_ids = get_memo_route(request, ["reversed"])
    app_label = 'organogram'
    model_name = 'businessunit'
    content_type_id = ContentType.objects.get(app_label=app_label, model=model_name).id
    app_label = 'auth'
    model_name = 'user'
    content_type_user = ContentType.objects.get(app_label=app_label, model=model_name).id
    # filter incoming memos
    excluded_statuses = ["draft", "approved", "closed"]

    user_creation_time = current_user.date_joined

    memos = Memo.objects.filter(
        (Q(id__in=memo_ids) | Q(public=True, created_date__gte=user_creation_time)) &
        (Q(content_type_id=content_type_id) | Q(content_type_id=content_type_user)) &
        ~Q(public=True, created_by=request.user)
    ).exclude(Q(status__in=excluded_statuses)).order_by('-last_updated')


    memos = filter_memos(request, memos)
    page_obj = paginate_memos(request, memos)

    business_units = BusinessUnit.objects.all()
    users = User.objects.all()
    external = ExternalCustomer.objects.all()
    options = ['All', 'reference_number', 'subject', 'memo_date', 'urgent']
    default_option = 'All'
    current_value = request.GET.get('value', '')

    return render(request, 'memotracker/memo_list.html', {
        'page_obj': page_obj,
        'options': options,
        'default_option': default_option,
        'current_value': current_value,
        'back_btn_url': 'incoming_memo_list',
        'users': users,
        'business_units': business_units,
        'external': external,
        # 'unread_count_incoming': unread_count_incoming,
        'listName': 'Incoming Memo',
        # 'check_notification': check_notification
    })


# Outgoing memo list
@login_required
@permission_required('Outgoing Memo')
def outgoing_memo_list(request):
    current_user = request.user
    user_id = current_user.id
    user_role = UserRole.objects.get(user=current_user, active=True)
    business_unit_id = user_role.business_unit.id

    app_label = 'auth'
    model_name = 'user'
    content_type_pid = ContentType.objects.get(app_label=app_label, model=model_name).id
    app_label = 'organogram'
    model_name = 'businessunit'

    excluded_statuses = ["draft", "closed"]
    content_type_id = ContentType.objects.get(app_label=app_label, model=model_name).id
    all_memos = (Memo.objects.filter(Q(object_id=business_unit_id, content_type_id=content_type_id) |
                                     Q(object_id=user_id, content_type_id=content_type_pid))
                 .exclude(status__in=excluded_statuses).order_by('-last_updated'))
    if user_role.role.is_manager or user_role.deligated:
        memos = all_memos
    else:
        # memos = all_memos.filter(Q(created_by=current_user) | Q(assigned_to=current_user))
        #############################
        memos = all_memos.filter(created_by=current_user)
        #############################
    memos = filter_memos(request, memos)
    page_obj = paginate_memos(request, memos)
    business_units = BusinessUnit.objects.all()
    users = User.objects.all()
    options = ['All', 'reference_number', 'subject', 'memo_date', 'urgent']
    default_option = 'All'
    current_value = request.GET.get('value', '')

    return render(request, 'memotracker/memo_list.html', {
        'page_obj': page_obj,
        'options': options,
        'default_option': default_option,
        'current_value': current_value,
        'back_btn_url': 'outgoing_memo_list',
        'business_units': business_units,
        'users': users,
        'listName': 'Outgoing Memo'
    })


# External memo list
@login_required
@permission_required('External Letter')
def external_memo_list(request):
    user = request.user
    user_role = UserRole.objects.get(user=user, active=True)
    business_unit = user_role.business_unit.name_en

    current_user = request.user
    memo_ids = get_memo_route(request, ["reversed"])
    app_label = 'organogram'
    model_name = 'externalcustomer'
    content_type_id = ContentType.objects.get(app_label=app_label, model=model_name).id
    memos = Memo.objects.filter(
        (Q(id__in=memo_ids) | Q(created_by=current_user)) & Q(content_type_id=content_type_id)).order_by(
        '-last_updated')
    memos = filter_memos(request, memos)
    page_obj = paginate_memos(request, memos)

    external = ExternalCustomer.objects.all()
    options = ['All', 'reference_number', 'subject', 'memo_date', 'urgent']
    default_option = 'All'
    current_value = request.GET.get('value', '')
    new_memo_link = reverse('external_memo')  # Assuming 'external_memo' is the correct URL name

    return render(request, 'memotracker/memo_list.html', {
        'page_obj': page_obj,
        'options': options,
        'default_option': default_option,
        'current_value': current_value,
        'back_btn_url': 'external_memo_list',
        'listName': 'External Letter',
        'new_memo_link': new_memo_link,
        'current_view': 'external_memo_list',  # Add this line to set the current view
        'external': external,
        'business_unit': business_unit,

    })

# Approved memo list
def approved_memo_list(request):
    current_user = request.user
    user_role = UserRole.objects.get(user=current_user, active=True)
    manager = user_role.role.is_manager
    delegate = user_role.deligated

    business_unit_id = user_role.business_unit.id

    app_label = 'organogram'
    model_name = 'businessunit'
    content_type_id = ContentType.objects.get(app_label=app_label, model=model_name).id
    if manager or delegate:
        approved = (Memo.objects.filter(Q(object_id=business_unit_id, content_type_id=content_type_id) &
                                        Q(status="approved")).order_by('-last_updated'))

        # approved = Memo.objects.filter(status="approved").order_by('-last_updated')
    else:
        approved = Memo.objects.filter(created_by=current_user, status="approved").order_by('-last_updated')
    memos = filter_memos(request, approved)
    page_obj = paginate_memos(request, memos)
    options = ['All', 'reference_number', 'subject', 'memo_date', 'urgent']
    default_option = 'All'
    current_value = request.GET.get('value', '')
    business_units = BusinessUnit.objects.all()
    users = User.objects.all()
    return render(request, 'memotracker/memo_list.html', {
        'page_obj': page_obj,
        'options': options,
        'default_option': default_option,
        'current_value': current_value,
        'back_btn_url': 'approved_memo_list',
        'business_units': business_units,
        'users': users,
        'listName': 'Approved Memo',
    })


# Sent memo list
def sent_memo_list(request):
    current_user = request.user
    user_id = current_user.id

    user_role = UserRole.objects.get(user=current_user, active=True)
    business_unit_id = user_role.business_unit.id
    manager = user_role.role.is_manager
    delegate = user_role.deligated

    app_label = 'auth'
    model_name = 'user'
    content_type_pid = ContentType.objects.get(app_label=app_label, model=model_name).id
    app_label = 'organogram'
    model_name = 'businessunit'

    content_type_id = ContentType.objects.get(app_label=app_label, model=model_name).id
    if manager or delegate:
        sent = Memo.objects.filter(
            (Q(object_id=business_unit_id, content_type_id=content_type_id) |
             Q(object_id=user_id, content_type_id=content_type_pid)) &
            Q(status="sent")
        ).order_by('-last_updated')
        # sent = Memo.objects.filter(status="sent").order_by('-last_updated')
    else:
        sent = Memo.objects.filter(created_by=current_user, status="sent").order_by('-last_updated')

    memos = filter_memos(request, sent)
    page_obj = paginate_memos(request, memos)
    business_units = BusinessUnit.objects.all()
    users = User.objects.all()
    external = ExternalCustomer.objects.all()
    options = ['All', 'reference_number', 'subject', 'memo_date', 'urgent']
    default_option = 'All'
    current_value = request.GET.get('value', '')

    return render(request, 'memotracker/memo_list.html', {
        'page_obj': page_obj,
        'options': options,
        'default_option': default_option,
        'current_value': current_value,
        'back_btn_url': 'sent_memo_list',
        'business_units': business_units,
        'users': users,
        'external': external,
        'listName': 'Sent Memo',
    })


# Closed memo list
def closed_memo_list(request):
    current_user = request.user
    user_role = UserRole.objects.get(user=current_user, active=True)
    manager = user_role.role.is_manager
    delegate = user_role.deligated
    if manager or delegate:

        closed = Memo.objects.filter(status="closed").order_by('-last_updated')
    else:
        closed = Memo.objects.filter(created_by=current_user, status="closed").order_by('-last_updated')

    memos = filter_memos(request, closed)
    page_obj = paginate_memos(request, memos)
    business_units = BusinessUnit.objects.all()
    users = User.objects.all()
    external = ExternalCustomer.objects.all()
    options = ['All', 'reference_number', 'subject', 'memo_date', 'urgent']
    default_option = 'All'
    current_value = request.GET.get('value', '')

    return render(request, 'memotracker/memo_list.html', {
        'page_obj': page_obj,
        'options': options,
        'default_option': default_option,
        'current_value': current_value,
        'back_btn_url': 'closed_memo_list',
        'business_units': business_units,
        'users': users,
        'external': external,
        'listName': 'Closed Memo',
    })


# def to_ethiopian(year, month, day):
#     # Calculate the Ethiopian date from the Gregorian date
#     # Determine if the Gregorian year is a leap year
#     is_gregorian_leap_year = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
#
#     # Days in each month of the Gregorian calendar
#     days_in_gregorian_months = [31, 28 + (1 if is_gregorian_leap_year else 0), 31, 30, 31, 30,
#                                 31, 31, 30, 31, 30, 31]
#
#     # Calculate the total days from the start of the Gregorian year
#     day_of_year = sum(days_in_gregorian_months[:month - 1]) + day
#
#     # Ethiopian year starts on Meskerem 1
#     # Gregorian year starts on January 1
#     if month < 9 or (month == 9 and day < 11):
#         eth_year = year - 8  # Ethiopian year is 8 years behind
#     else:
#         eth_year = year - 7  # Ethiopian year is 7 years behind
#
#     # Calculate Ethiopian day and month
#     if day_of_year > 254:  # After September 11
#         eth_day_of_year = day_of_year - 254  # 254 days from January 1 to September 10
#     else:
#         eth_day_of_year = day_of_year + (365 if is_gregorian_leap_year else 364) - 254
#
#     # Ethiopian months have 30 days for the first 13 months
#     eth_month = (eth_day_of_year - 1) // 30 + 1
#     eth_day = (eth_day_of_year - 1) % 30 + 1
#
#     return eth_day, eth_month, eth_year

@login_required
def memo_detail(request, pk, list_name=None):
    user_role = UserRole.objects.get(user=request.user, active=True)
    memo = get_object_or_404(Memo, pk=pk)
    memo_routes = memo.memoroute_set.filter(level=1).order_by('-date_sent')
    cc_list = []
    direct_list = []
    type_external = ContentType.objects.get(app_label='organogram', model='externalcustomer')
    type_user = ContentType.objects.get(app_label='auth', model='user')
    type_bu = ContentType.objects.get(app_label='organogram', model='businessunit')

    for route in memo_routes:
        if route.destination_type == type_external:
            try:
                to_external = ExternalCustomer.objects.get(pk=route.destination_id)
                external = to_external.name_en if memo.in_english else to_external.name_am
            except ObjectDoesNotExist:
                external = "<Object Removed>"
            external_item = {"name": external, "type": "External", "status": route.status}
            (cc_list if route.carbon_copy else direct_list).append(external_item)

        elif route.destination_type == type_user:
            to_user = UserRole.objects.get(user_id=route.destination_id)
            try:
                profile = Profile.objects.get(user_id=route.destination_id)
                full_name = profile.full_name if profile.full_name else f"{to_user.user.first_name} {to_user.user.last_name}"
            except ObjectDoesNotExist:
                full_name = f"{to_user.user.first_name} {to_user.user.last_name}"

            bu_name = to_user.business_unit.name_en if memo.in_english else to_user.business_unit.name_am
            user_item = {"name": f"{full_name} [{bu_name}]", "type": "User", "status": route.status}
            (cc_list if route.carbon_copy else direct_list).append(user_item)

        else:
            bu = BusinessUnit.objects.get(pk=route.destination_id)
            internal = bu.name_en if memo.in_english else bu.name_am
            bu_item = {"name": internal, "type": "BU", "status": route.status}
            (cc_list if route.carbon_copy else direct_list).append(bu_item)

    cc_list_count = len(cc_list)
    direct_list_count = len(direct_list)

    user_roles = UserRole.objects.filter(user__in=[memo.created_by, memo.assigned_to])
    business_units = [user_role.business_unit.name_en if memo.in_english else user_role.business_unit.name_am for
                      user_role in user_roles]

    # Check the length of business_units before accessing indexes
    business_unit_created_by = business_units[0] if len(business_units) > 0 else None
    business_unit_assigned_to = business_units[1] if len(business_units) > 1 else None


    is_outgoing_memo = memo.content_type.model == 'businessunit' and memo.object_id == user_role.business_unit_id and not memo_routes.filter(
        destination_type=type_user, destination_id=request.user.id).exists()

    linked_memos = memo.attached_memos.all()

    if list_name in ['Incoming Memo', 'External Letter']:
        manager = user_role.role.is_manager
        delegate = user_role.deligated
        user_routes = memo.memoroute_set.filter(Q(status='notseen') & (
                Q(destination_type=type_user, destination_id=request.user.id) |
                Q(destination_type=type_bu, destination_id=user_role.business_unit_id)))

        if user_routes:
            for user_route in user_routes:
                destination_user = UserRole.objects.filter(user_id=user_route.destination_id,
                                                           active=True) if user_route.destination_type == type_user else UserRole.objects.filter(
                    business_unit_id=user_route.destination_id, active=True)
                if destination_user.filter(user=request.user).exists():
                    user_route.status = 'seen'
                    user_route.date_viewed = timezone.now()
                    user_route.save()

    # eth_day, eth_month, eth_year = to_ethiopian(memo.memo_date.year, memo.memo_date.month, memo.memo_date.day)
    # eth_date_str = f"{eth_day:02d}/{eth_month:02d}/{eth_year}"

    memo_date = memo.memo_date
    converter = EthiopianDateConverter()
    try:
        eth_day, eth_month, eth_year = converter.to_ethiopian(memo_date.year, memo_date.month, memo_date.day)
        date_str = f"{eth_year}/{eth_month:02d}/{eth_day:02d}"
    except Exception as e:
        print(f"Error during date conversion: {e}")
        date_str = "Invalid date"

    return render(request, 'memotracker/memo_detail.html', {
        'memo': memo,
        'business_units': business_units,
        'user_role': user_role,
        'users': User.objects.all(),
        'isOutgoingMemo': is_outgoing_memo,
        'external': ExternalCustomer.objects.all(),
        'business_unit_created_by': business_unit_created_by,
        'business_unit_assigned_to': business_unit_assigned_to,
        'linked_memos': linked_memos,
        'direct_list': direct_list,
        'cc_list': cc_list,
        'direct_list_count': direct_list_count,
        'cc_list_count': cc_list_count,
        'listName': list_name,
        'ethDate': eth_date_str,
    })


def memohistory(request):
    # Fetch all memos and their routes
    memos_with_routes = Memo.objects.prefetch_related('memoroute_set').all()
    return render(request, 'memotracker/memohistory.html', {'memos_with_routes': memos_with_routes})


def memohistory_detail(request, memo_id):
    # Fetch details for a specific memo
    memo = Memo.objects.get(id=memo_id)
    memo_routes = memo.memoroute_set.all().order_by('-date_sent')

    approval_routes = memo.approvalroute_set.all().order_by('-created_date')
    context = {
        'memo': memo,
        'title': 'All Routes',
        'back_btn_url': 'list_all_memo',
        'memo_routes': memo_routes,
        'approval_routes': approval_routes
    }
    return render(request, 'memotracker/memohistory_form.html', context)

def access_denied(request):
    return render(request, 'memotracker/access_denied.html', {})

def create_memo_attachments(memo_id, attachment_ids):
    for attachment_id in attachment_ids:
        attachment = Document.objects.get(id=attachment_id)

        # Create and save MemoAttachment instance
        memo_attachment = MemoAttachment(memo=memo_id, document=attachment)
        memo_attachment.save()

def link_memo_attachments(memo, attachment_ids):
    # get attached memos

    if attachment_ids:
        related_memos = Memo.objects.filter(id__in=attachment_ids)
        memo.attached_memos.set(related_memos)

def attach_docs():
    pass

def ethiopianDateFormatter(date):
    ethiopian_date = EthiopianDateConverter.to_ethiopian(date.year, date.month, date.day)
    dateParts = str(ethiopian_date).split('-')
    return f"{dateParts[2]}/{dateParts[1]}/{dateParts[0]}"

@login_required
@permission_required('Create Memo')
def create_memo(request):
    user_role = UserRole.objects.get(user=request.user,
                                     active=True)  # Assuming you have a function to get the user role
    bu = user_role.business_unit
    dept_users = User.objects.filter(userrole__business_unit=bu).exclude(id=request.user.id)

    last_bu_ref_number = bu.last_memo_ref_number
    last_ref_number = f'IPDC/{bu.code}/{last_bu_ref_number}/{str(date.today().year)}'

    profile = Profile.objects.get(user=request.user)
    last_personal_memo_ref_number = f'P{request.user.id}/{profile.last_personal_memo_ref_number}/{str(date.today().year)}'

    # Get the available memos for the current user
    available_memos = get_available_memos(request.user)

    if request.method == 'POST':
        attachments = request.POST.get('attachments')
        attachment_ids = attachments.split(',')  # Split attachment IDs into a list
        # form = MemoForm(request.POST, user_id=user_role.user.id, bunit_id=user_role.business_unit.id)
        form = MemoForm(request.POST, user=request.user, bunit_id=bu.id)  # Pass the current user and business unit ID

        message = ""

        if form.is_valid():
            memo = form.save(commit=False)
            memo.created_by = user_role.user
            memo.keywords = str('')

            linked_memos = [] or request.POST.getlist('memo_ids')  # Get the linked memos from the form

            content_type_str = str(form.cleaned_data['content_type'])
            app_label, model_name = content_type_str.split(' | ')
            # Determine the non-form field value based on the owner type
            if model_name == 'user':
                object_id = user_role.user.id
            else:
                object_id = user_role.business_unit.id

                # Set the non-form field value on the model instance
            memo.object_id = object_id

            # if save draft button is clicked
            if 'save_draft' in request.POST:  # Check if the 'Save Draft' button was clicked
                memo.status = 'draft'  # Set the status to 'draft'
                memo.reference_number = f"{memo.reference_number}-{str(datetime.today().time().hour)}:{str(datetime.today().time().minute)}:{str(datetime.today().time().second)}"

                memo.memo_date = datetime.today()
                memo.save()

                # if memo has document attachments
                if attachment_ids[0] != '':
                    create_memo_attachments(memo, attachment_ids)

                # if there are linked memos to the memo
                if linked_memos:
                    link_memo_attachments(memo, linked_memos)

                return redirect('draft_memo_list')  # Redirect to the memo list view
            elif 'send_memo' in request.POST:  # Check if the 'Send Memo' button was clicked
                # memo.status = 'sent'  # Set the status to 'pending'
                try:
                    if memo.content_type != ContentType.objects.get(model='user'):
                        bu = user_role.business_unit
                        bu.last_memo_ref_number += 1
                        bu.save()

                    if memo.content_type == ContentType.objects.get(model='user'):
                        profile.last_personal_memo_ref_number += 1
                        profile.save()

                    memo.status = 'sent'
                    memo.save()

                    # if memo has document attachments

                    if attachment_ids[0] != '':
                        create_memo_attachments(memo, attachment_ids)

                    # if there are linked memos to the memo
                    if linked_memos:
                        link_memo_attachments(memo, linked_memos)

                    message = save_memo_route(request, memo)
                except Exception as e:
                    message = f"Memo Saving Failed: {str(e)}"
            elif 'approval_send' in request.POST:
                try:
                    memo.status = 'draft'  # Set the status to 'draft'
                    memo.reference_number = f"{memo.reference_number}-{str(datetime.today().time().hour)}:{str(datetime.today().time().minute)}:{str(datetime.today().time().second)}"
                    memo.save()

                    # if memo has document attachments
                    if attachment_ids[0] != '':
                        create_memo_attachments(memo, attachment_ids)

                    # if there are linked memos to the memo
                    if linked_memos:
                        link_memo_attachments(memo, linked_memos)

                    message = save_approval_route(request, memo)
                except Exception as e:
                    message = f"Memo Saving Failed: {str(e)}"

        else:
            print('Failed to save memo')
            for field, errors in form.errors.items():
                for error in errors:
                    message += f"Error in field '{field}': {error}"
        return JsonResponse({'message': message})
    else:
        # form = MemoForm(user_id=user_role.user.id, bunit_id=user_role.business_unit.id)
        form = MemoForm(user=request.user, bunit_id=bu.id)  # Pass the current user and business unit ID

    # ethDate = ethiopianDateFormatter(datetime.today())

    return render(request, 'memotracker/create_memo.html', {
        'form': form,
        'memo_type': user_role,
        'last_ref_number': last_ref_number,
        'last_personal_memo_ref_number': last_personal_memo_ref_number,
        'user_id': user_role.user.id,
        'bunit_code': bu.code,
        'available_memos': available_memos,
        'dept_users': dept_users,
        # 'ethDate': ethDate

    })

@login_required
def external_memo(request):
    user_role = UserRole.objects.get(user=request.user, active=True)
    org_list = ExternalCustomer.objects.all()
    available_documents = Document.objects.all()

    if request.method == 'POST':
        form = ExternalMemoForm(request.POST, request.FILES, org_list=org_list)
        message = ""
        if form.is_valid():
            memo = form.save(commit=False)
            memo.created_by = user_role.user
            memo.keywords = ''

            external_content_type = ContentType.objects.get(model='externalcustomer', app_label='organogram')
            memo.content_type_id = external_content_type.id
            memo.object_id = form.cleaned_data.get('customer').id

            # Extract the document id from the form.cleaned_data dictionary
            document_id = form.cleaned_data.get('document', None)

            form.fields["document"].choices = [(str(document.id), document.title) for document in available_documents]
            if 'send_memo' in request.POST:
                memo.status = 'sent'
                memo.save()

                if document_id is not None:
                    attachment_ids = [document_id]
                    print(f'Selected Document ID: {document_id}')
                    create_memo_attachments(memo, attachment_ids)
                message = save_memo_route(request, memo)
        else:
            print("Failed to save memo")
            for field, errors in form.errors.items():
                for error in errors:
                    message += f"Error in field '{field}': {error}"
        return JsonResponse({'message': message})
    else:
        form = ExternalMemoForm(org_list=org_list)
        form.fields["document"].choices = [(str(document.id), document.title) for document in available_documents]

    return render(request, 'memotracker/external_memo.html',
                  {'form': form, 'org_list': org_list, 'listName': ExternalCustomer})
def save_notification(recipient, notification):
    notification = NotificationRecipient.create_notification_recipient(recipient, notification)
    if notification.pk is not None:
        print("Notification created successfully!")
    else:
        print("Notification not created successfully!")


def save_destination(request, form_data, memo, prev_memo_route, new_ref_number, destination_list, destination_type,
                     carbon_copy_list):
    user_role = UserRole.objects.get(user=request.user, active=True)
    i = 0
    message = ""

    notify_type = NotificationType.objects.get(name="Incoming Memo")
    notification_message = f"{request.user.first_name} {request.user.last_name} has sent memo with Reference No: {memo.reference_number}!"

    memo_list = "External Letter" if memo.content_type == ContentType.objects.get(
        model='externalcustomer') else "Incoming Memo"
    url = f"/memotracker/memo/{memo.id}/{memo_list}"

    notification = Notification.create_notification(request.user, notify_type, notification_message, url)

    for destination_id in destination_list:
        form_data['destination_id'] = destination_id
        form_data['destination_type'] = destination_type
        form_data['carbon_copy'] = carbon_copy_list[i]

        if prev_memo_route is not None:
            form_data['level'] = prev_memo_route.level + 1

        form = MemoRouteForm(form_data or None, current_user=request.user)

        if form.is_valid():
            memo_route = form.save(commit=False)
            memo_route.destination_id = destination_id
            memo_route.destination_type = destination_type
            memo_route.save()
            recipients = []

            if destination_type != ContentType.objects.get(model='user'):
                user_roles = UserRole.objects.filter(
                    Q(business_unit_id=destination_id, active=True) &
                    (Q(role__is_manager=True) | Q(deligated=True))
                )
                recipients.extend(user_role1.user for user_role1 in user_roles)
            else:
                recipients.append(User.objects.get(pk=destination_id))

            if prev_memo_route is not None:
                prev_memo_route.status = "forwarded"
                prev_memo_route.save()

            if memo.status in ['draft', 'approved']:
                if memo.content_type != ContentType.objects.get(model='user'):
                    user_role.business_unit.last_memo_ref_number += 1
                    user_role.business_unit.save()
                if memo.content_type == ContentType.objects.get(model='user'):
                    profile = Profile.objects.get(user=request.user)
                    profile.last_personal_memo_ref_number += 1
                    profile.save()

                out_notification_message = f"The memo you drafted as: {memo.reference_number} is sent with Reference No: {new_ref_number}!"
                memo.reference_number = new_ref_number
                memo.status = 'sent'
                memo.save()

                new_message = f"{request.user.first_name} {request.user.last_name} has sent memo with Reference No: {memo.reference_number}!"
                notification.message = new_message
                notification.save()

                if request.user.id != memo.created_by_id:
                    out_url = f"/memotracker/memo/{memo.id}/Outgoing Memo"
                    out_notify_type = NotificationType.objects.get(name="Reminder")
                    out_recipient = memo.created_by
                    draft_notification = Notification.create_notification(request.user, out_notify_type,
                                                                          out_notification_message, out_url)
                    save_notification(out_recipient, draft_notification)

            # Create notification for the assigned user with the "Reminder" type
            if memo.assigned_to:
                assigned_notify_type = NotificationType.objects.get(
                    name="Reminder")  # Get the Reminder notification type
                assigned_notification_message = f"You are assigned to follow up the sent memo with Reference No: {memo.reference_number}."
                assigned_notification = Notification.create_notification(request.user, assigned_notify_type,
                                                                         assigned_notification_message,
                                                                         url)  # Use Reminder type
                save_notification(memo.assigned_to, assigned_notification)
                print(
                    f"Notification sent to assigned user: {memo.assigned_to}, Message: {assigned_notification_message}")

            for recipient in recipients:
                save_notification(recipient, notification)

            message = "success"
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    message += f"Error in field '{field}': {error}"
        i += 1
    return message
def save_memo_route(request, memo):
    to_external_list = request.POST.get('to_external_list').split(",")
    to_user_list = request.POST.get('to_user_list').split(",")
    to_bu_list = request.POST.get('to_bu_list').split(",")
    to_external_cc_list = request.POST.get('external_carbon_copy_list').split(",")
    to_user_cc_list = request.POST.get('carbon_copy_list').split(",")
    to_bu_cc_list = request.POST.get('bu_carbon_copy_list').split(",")
    #################
    # Get the assigned user ID from the form
    assigned_to_id = request.POST.get('assigned_to')
    if assigned_to_id:
        to_user_list.append(assigned_to_id)  # Add the assigned user to the to_user_list
    ################
    form_data = request.POST.copy()
    user_role = UserRole.objects.get(user=request.user, active=True)
    manager = user_role.role.is_manager
    delegate = user_role.deligated
    new_ref_number = memo.reference_number

    if memo.status == "draft" or memo.status == "approved":
        year = datetime.today().year
        month = datetime.today().month
        today_day = datetime.today().day

        if month < 9:
            eth_year = year - 8
        elif month >= 9:
            if month == 9:
                if today_day in range(1, 12):
                    eth_year = year - 8
                    if eth_year % 4 == 3:
                        if today_day not in range(1, 12):
                            eth_year = year - 7
                    else:
                        if today_day not in range(1, 11):
                            eth_year = year - 7
                else:
                    eth_year = year - 7
            else:
                eth_year = year - 7

        memo_year = str(date.today().year) if memo.in_english else eth_year
        if memo.content_type != ContentType.objects.get(model='user'):
            bu = user_role.business_unit
            bu_reference_code = f'IPDC/{bu.code}' if memo.in_english else f'ኢፓልኮ/{bu.code}'
            bu_memo = Memo.objects.filter(Q(reference_number__contains=f'IPDC/{bu.code}') | Q(
                reference_number__contains=f'ኢፓልኮ/{bu.code}')).filter(
                Q(reference_number__endswith=str(datetime.today().year)) | Q(reference_number__endswith=eth_year))
            if bu_memo.count() == 0:
                last_bu_ref_number = 1
                new_ref_number = f'{bu_reference_code}/{last_bu_ref_number}/{memo_year}'
            elif memo.status == "draft" or memo.status == "approved":
                last_bu_ref_number = bu.last_memo_ref_number + 1
                new_ref_number = f'{bu_reference_code}/{last_bu_ref_number}/{memo_year}'
        else:
            profile = Profile.objects.get(user=request.user)
            personal_reference_code = f'P{request.user.id}'
            personal_memo = Memo.objects.filter(reference_number__contains=personal_reference_code).filter(
                Q(reference_number__endswith=str(datetime.today().year)) | Q(reference_number__endswith=eth_year))
            if personal_memo.count() == 0:
                last_personal_ref_number = 1
            else:
                last_personal_ref_number = profile.last_personal_memo_ref_number + 1
                profile.last_personal_memo_ref_number = last_personal_ref_number
                profile.save()
            new_ref_number = f'{personal_reference_code}/{str(last_personal_ref_number)}/{memo_year}'

    message = ""
    user_d_type = ContentType.objects.get(app_label='auth', model='user')
    bu_d_type = ContentType.objects.get(app_label='organogram', model='businessunit')
    bu_id = user_role.business_unit_id
    user_id = request.user.id

    if manager or delegate:
        prev_memo_route = MemoRoute.objects.filter(Q(memo_id=memo.id) & (
                    Q(destination_id=user_id, destination_type=user_d_type) | Q(destination_id=bu_id,
                                                                                destination_type=bu_d_type))).order_by(
            '-level').all().first()
    else:
        prev_memo_route = MemoRoute.objects.filter(memo_id=memo.id, destination_id=user_id,
                                                   destination_type=user_d_type).order_by(
            '-level').all().first()
    form_data['memo'] = memo

    if request.POST.get('to_external_list') != '':
        if isinstance(to_external_list, list):
            destination_list = to_external_list
            destination_type = ContentType.objects.get(model='externalcustomer')
            carbon_copy_list = to_external_cc_list

            message = save_destination(request, form_data, memo, prev_memo_route, new_ref_number,
                                       destination_list, destination_type, carbon_copy_list)
    if request.POST.get('to_user_list') != '':
        if isinstance(to_user_list, list):
            destination_list = to_user_list

            destination_type = ContentType.objects.get(model='user')
            carbon_copy_list = to_user_cc_list

            message = save_destination(request, form_data, memo, prev_memo_route, new_ref_number,
                                       destination_list, destination_type, carbon_copy_list)

    if request.POST.get('to_bu_list') != '':
        if isinstance(to_bu_list, list):
            destination_list = to_bu_list
            destination_type = ContentType.objects.get(model='businessunit')
            carbon_copy_list = to_bu_cc_list
            # Check if "Select All" is clicked
            if 'select_all' in destination_list:
                user_role = UserRole.objects.get(user=request.user, active=True)
                current_user_bu_id = user_role.business_unit.id
                destination_list = [bu.id for bu in BusinessUnit.objects.all().exclude(id=current_user_bu_id)]  # Replace with your BusinessUnit model

            message = save_destination(request, form_data, memo, prev_memo_route, new_ref_number,
                                       destination_list, destination_type, carbon_copy_list)

    return message
def save_approval_route(request, memo):
    to_user = User.objects.get(id=request.POST.get('to_user_list'))
    form_data = request.POST.copy()
    form_data['memo'] = memo
    # form_data['to_user'] = to_user
    destination_id = request.POST.get('to_user_list')
    destination_type = ContentType.objects.get(model='user')
    form_data['destination_id'] = destination_id
    form_data['destination_type'] = destination_type
    initial_data = {
        'form_type': "Approval Route"}
    form = ApprovalRouteForm(form_data or None, initial=initial_data, current_user=request.user)
    message = ""
    if form.is_valid():
        form.save()
        recipient = to_user
        notify_type = NotificationType.objects.get(name="Approval Memo")
        notification_message = request.user.first_name + " " + request.user.last_name + " have Sent Memo with Reference No: " + memo.reference_number + "!"
        if memo.status == "draft":
            memo_list = "Draft Memo"
        else:
            memo_list = "Outgoing Memo"
        url = "/memotracker/memo/" + str(memo.id) + "/" + memo_list
        notification = Notification.create_notification(request.user, notify_type, notification_message, url)
        save_notification(recipient, notification)
        message = "success"
    else:
        for field, errors in form.errors.items():
            for error in errors:
                message += f"Error in field '{field}': {error}"
    return message


@login_required
def memo_route(request, memo_id=None):
    if request.POST:
        memo = Memo.objects.get(id=memo_id)
        message = save_memo_route(request, memo)
        return JsonResponse({'message': message})
    else:
        current_user_role = Role.objects.get(Q(userrole__user__id=request.user.id) & Q(userrole__active=True))
        delegate = UserRole.objects.get(user_id=request.user.id)
        is_manager = current_user_role.is_manager
        is_delegated = delegate.deligated
        department = delegate.business_unit
        is_to_external = False
        content_type = "None"
        memo_status = "draft"
        current_user_bu = UserRole.objects.get(user=request.user, active=True).business_unit.id

        if memo_id is not None:
            memo = Memo.objects.get(id=memo_id)
            memo_status = memo.status
            is_to_external = memo.to_external
            app_label, model_name = str(memo.content_type).split(' | ')
            if model_name == 'user':
                content_type = "Personal"
            else:
                content_type = "Business Unit"
        initial_data = {
            'form_type': "Memo Route",
            'memo': memo_id,
            'memo_status': memo_status,
            'content_type': content_type,
            'from_user': request.user.id,
            'is_manager': is_manager,
            'is_delegate': is_delegated,
            'department': department,
            'is_to_external': is_to_external,
            'current_user_bu': current_user_bu,

        }

        form = MemoRouteForm(initial=initial_data, current_user=request.user)
        return render(request, 'memotracker/memo_route_form.html',
                      {'form': form, 'title': 'Add Memo Route', 'cancel_btn_url': 'memo_route_history'})
@login_required
def memo_route_to_all(request, memo_id=None):
    user_role = UserRole.objects.get(user=request.user, active=True)
    bu = user_role.business_unit
    profile = Profile.objects.get(user=request.user)

    if request.method == 'POST':
        attachments = request.POST.get('attachments')
        attachment_ids = []
        if attachments is not None:
            attachment_ids = attachments.split(',')

        # Change user_id to user
        form = MemoForm(request.POST, user=request.user, bunit_id=user_role.business_unit.id)

        if memo_id is not None:
            memo = Memo.objects.get(id=memo_id)
            form = MemoForm(request.POST, instance=memo, user=request.user, bunit_id=user_role.business_unit.id)

        if form.is_valid():
            memo = form.save(commit=False)
            memo.keywords = str('')
            if memo_id is None:
                memo.created_by = user_role.user
            else:
                reference = memo.reference_number
                if memo.content_type.model == 'businessunit':
                    parts = memo.reference_number.split('/')
                    code = '/'.join(parts[:2])
                    year = parts[3][:4]
                    last_number = bu.last_memo_ref_number + 1
                    reference = code + '/' + str(last_number) + '/' + year
                elif memo.content_type.model == 'user':
                    parts = memo.reference_number.split('/')
                    code = '/'.join(parts[:1])
                    year = parts[2][:4]
                    last_number = profile.last_personal_memo_ref_number + 1
                    reference = code + '/' + str(last_number) + '/' + year
                memo.reference_number = reference

            linked_memos = request.POST.getlist('memo_ids')
            content_type_str = str(form.cleaned_data['content_type'])
            app_label, model_name = content_type_str.split(' | ')

            if model_name == 'user':
                object_id = user_role.user.id
            else:
                object_id = user_role.business_unit.id

            memo.object_id = object_id

            try:
                if memo.content_type != ContentType.objects.get(model='user'):
                    bu.last_memo_ref_number += 1
                    bu.save()

                if memo.content_type == ContentType.objects.get(model='user'):
                    profile.last_personal_memo_ref_number += 1
                    profile.save()

                memo.status = 'sent'
                memo.save()

                if attachment_ids and attachment_ids[0] != '':
                    create_memo_attachments(memo, attachment_ids)

                if linked_memos:
                    link_memo_attachments(memo, linked_memos)

                notify_type = NotificationType.objects.get(name="Public Memo")
                if memo.content_type.model == 'businessunit':
                    sender = BusinessUnit.objects.get(id=memo.object_id).name_en
                else:
                    sender = request.user.first_name + " " + request.user.last_name
                notification_message = f"{sender} has sent a memo with Reference No: {memo.reference_number}!"
                url = f"/memotracker/memo/{memo.id}/Incoming Memo"
                notification = Notification.create_notification(request.user, notify_type, notification_message, url)
                users = User.objects.all().exclude(id=request.user.id)
                for user in users:
                    save_notification(user, notification)
                print(f"Memo with reference number {memo.reference_number} successfully sent to all.")
            except Exception as e:
                print(f"Memo saving failed: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    print(f"Error in field '{field}': {error}")

    return redirect('outgoing_memo_list')

def memo_route2(request, memo_id, attachment_link=None):  # Added attachment_link parameter
    user_role = UserRole.objects.get(user=request.user, active=True)
    bu = user_role.business_unit
    last_bu_ref_number = bu.last_memo_ref_number + 1
    new_ref_number = f'IPDC/{bu.code}/{last_bu_ref_number}/{str(date.today().year)}'

    if request.POST:
        form = MemoRouteForm(request.POST or None, current_user=request.user)
        if form.is_valid():
            form.save()

            memo_routes = MemoRoute.objects.filter(memo_id=memo_id)
            memo = Memo.objects.get(id=memo_id)
            if memo_routes.count() == 1 and memo.status == 'draft':
                # Update the memo reference number
                memo.reference_number = new_ref_number
                bu.last_memo_ref_number += 1
                bu.save()
                memo.status = 'sent'
                memo.save()

            # Additional handling for attachment_link
            if attachment_link:
                # Perform actions with the attachment_link, e.g., save it to the Memo model
                memo.attachment_link = attachment_link
                memo.save()

            messages.success(request, 'Memo route added successfully.')
            return redirect('memo_route_history', memo_id=memo_id, list_name="Outgoing Memo")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    print(f"Error in field '{field}': {error}")
    else:
        current_user_role = Role.objects.get(Q(userrole__user__id=request.user.id) & Q(userrole__active=True))
        delegate = UserRole.objects.get(user_id=request.user.id)
        is_manager = current_user_role.is_manager
        is_delegated = delegate.deligated
        department = delegate.business_unit
        initial_data = {
            'memo': memo_id,
            'from_user': request.user.id,
            'is_manager': is_manager,
            'is_delegate': is_delegated,
            'department': department
        }
        form = MemoRouteForm(initial=initial_data, current_user=request.user)

    return render(request, 'memotracker/memo_route_form.html',
                  {'form': form, 'title': 'Add Memo Route', 'cancel_btn_url': 'memo_route_history'})


@login_required
def edit_memo_route(request, pk):
    edit_it = MemoRoute.objects.get(id=pk)
    if request.method == 'POST':
        to_external_list = request.POST.get('to_external_list').split(",")
        to_user_list = request.POST.get('to_user_list').split(",")
        to_bu_list = request.POST.get('to_bu_list').split(",")
        to_external_cc_list = request.POST.get('external_carbon_copy_list').split(",")
        to_user_cc_list = request.POST.get('carbon_copy_list').split(",")
        to_bu_cc_list = request.POST.get('bu_carbon_copy_list').split(",")
        carbon_copy_list = False
        if request.POST.get('to_user_list') != '':
            if isinstance(to_user_list, list):
                destination_list = to_user_list[0]
                destination_type = ContentType.objects.get(model='user')
                if to_user_cc_list[0] == 'true':
                    carbon_copy_list = True

        if request.POST.get('to_bu_list') != '':
            if isinstance(to_bu_list, list):
                destination_list = to_bu_list[0]
                destination_type = ContentType.objects.get(model='businessunit')
                if to_bu_cc_list[0] == 'true':
                    carbon_copy_list = True

        if request.POST.get('to_external_list') != '':
            if isinstance(to_external_list, list):
                destination_list = to_external_list[0]
                destination_type = ContentType.objects.get(model='externalcustomer')
                if to_external_cc_list[0] == 'true':
                    carbon_copy_list = True

        form_data = request.POST.copy()
        form_data['destination_id'] = destination_list
        form_data['destination_type'] = destination_type
        form_data['carbon_copy'] = carbon_copy_list
        form_data['level'] = edit_it.level
        form = MemoRouteForm(form_data or None, instance=edit_it, current_user=request.user)
        message = ""
        if form.is_valid():
            edit_it.destination_id = destination_list
            edit_it.destination_type = destination_type
            edit_it.carbon_copy = carbon_copy_list
            edit_it.save()
            messages.success(request, 'Memo Forwarding Updated Successfully!')
            message = "success"
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    message += f"Error in field '{field}': {error}"
        return JsonResponse({'message': message})
    else:
        user_role = UserRole.objects.get(user=request.user, active=True)
        is_manager = user_role.role.is_manager
        is_delegated = user_role.deligated
        department = ""
        external = ""
        if edit_it.destination_type == ContentType.objects.get(app_label='organogram', model='externalcustomer'):
            destination_id = edit_it.destination_id
            external = ExternalCustomer.objects.get(id=destination_id)
            form_type = "Memo Route-Edit to External"
        elif edit_it.destination_type == ContentType.objects.get(app_label='auth', model='user'):
            destination_id = edit_it.destination_id
            department = UserRole.objects.get(user_id=destination_id, active=True).business_unit.id
            form_type = "Memo Route-Edit to User"
        else:
            destination_id = edit_it.destination_id
            department = destination_id
            form_type = "Memo Route-Edit to Business Unit"
        app_label, model_name = str(edit_it.memo.content_type).split(' | ')
        if model_name == 'user':
            content_type = "Personal"
        elif model_name == 'external customer':
            content_type = "External Customer"
        else:
            content_type = "Business Unit"
        current_user_bu = UserRole.objects.get(user=request.user, active=True).business_unit.id
        initial_data = {
            'form_type': form_type,
            'memo': edit_it.memo_id,
            'memo_status': edit_it.memo.status,
            'content_type': content_type,
            'from_user': request.user.id,
            'destination_id': destination_id,
            'memo_action': edit_it.memo_action,
            'remark': edit_it.remark,
            'carbon_copy': edit_it.carbon_copy,
            'title': 'Edit Memo Route',
            'is_manager': is_manager,
            'is_delegate': is_delegated,
            'department': department,
            'external': external,
            'is_to_external': edit_it.memo.to_external,
            'current_user_bu': current_user_bu
        }
        form = MemoRouteForm(initial=initial_data, current_user=request.user)
        return render(request, 'memotracker/memo_route_form.html',
                      {'form': form, 'title': 'Sending Memo', 'cancel_btn_url': 'memo_route_history'})


@login_required
def delete_memo_route(request, list_name):
    pk = request.POST.get('id')
    delete_it = MemoRoute.objects.get(id=pk)
    change_previous_route_status(delete_it)
    delete_it.delete()
    return redirect('memo_route_history', delete_it.memo_id, list_name)


def change_previous_route_status(memo_route):
    prev_level = memo_route.level - 1
    prev_routes = MemoRoute.objects.filter(memo_id=memo_route.memo.id, level=prev_level)
    if prev_routes:
        for route in prev_routes:
            if route.destination_type.model == 'user':
                if route.destination_id == memo_route.from_user.id:
                    if route.status == 'forwarded':
                        route.status = 'seen'
                        route.save()
            elif route.destination_type.model == 'businessunit':
                users = UserRole.objects.filter(Q(business_unit__id=route.destination_id, active=True) & Q(
                    Q(role__is_manager=True) | Q(deligated=True)))
                for user in users:
                    if memo_route.from_user.id == user.user_id:
                        if route.status == 'forwarded':
                            route.status = 'seen'
                            route.save()

@login_required
def reverse_memo_route(request, list_name):
    pk = request.POST.get('id')
    reverse_it = MemoRoute.objects.get(id=pk)
    change_previous_route_status(reverse_it)
    reverse_it.status = 'reversed'
    reverse_it.save()
    recipient = []
    if request.user == reverse_it.from_user:
        if reverse_it.destination_type.model == 'user':
            recipient.append(User.objects.get(pk=reverse_it.destination_id))
        elif reverse_it.destination_type.model == 'businessunit':
            user_roles = UserRole.objects.filter(Q(business_unit__id=reverse_it.destination_id, active=True) & Q(
                Q(role__is_manager=True) | Q(deligated=True)))
            for user_role in user_roles:
                recipient.append(user_role.user)
        list_type = "Outgoing Memo"
    else:
        recipient.append(reverse_it.from_user)
        list_type = "Incoming Memo"
    notify_type = NotificationType.objects.get(name="Reverse Memo")
    sender = request.user.first_name + " " + request.user.last_name
    notification_message = sender + " have Reversed memo with Reference No: " + reverse_it.memo.reference_number + "!"
    url = "/memotracker/memo/" + str(reverse_it.memo.id) + "/" + list_type
    notification = Notification.create_notification(request.user, notify_type, notification_message, url)

    for user in recipient:
        save_notification(user, notification)

    # return redirect('memo_route_history', reverse_it.memo_id, list_name)
    return redirect('incoming_memo_list')

@login_required
def approval_route(request, memo_id=None):
    if request.POST:
        try:
            memo = Memo.objects.get(id=memo_id)
            message = save_approval_route(request, memo)
        except Exception as e:
            message = f"Memo Approval Saving Failed: {str(e)}"
        return JsonResponse({'message': message})
    else:
        user_role = UserRole.objects.get(user_id=request.user.id)
        department = user_role.business_unit
        content_type = "None"
        memo_status = "draft"
        if memo_id is not None:
            app_label, model_name = str(Memo.objects.get(id=memo_id).content_type).split(' | ')
            if model_name == 'user':
                content_type = "Personal"
            else:
                content_type = "Business Unit"
        initial_data = {
            'form_type': "Approval Route",
            'content_type': content_type,
            'memo_status': memo_status,
            'memo': memo_id,
            'from_user': request.user.id,
            'department': department
        }
        approval_form = ApprovalRouteForm(initial=initial_data, current_user=request.user)
        return render(request, 'memotracker/memo_route_form.html',
                      {'form': approval_form, 'title': 'Add Approval Route', 'cancel_btn_url': 'memo_approval_history'})


@login_required
def edit_approval_route(request, pk):
    edit_it = ApprovalRoute.objects.get(id=pk)
    if request.method == 'POST':
        initial_data = {
            'form_type': "Approval Route"
        }
        form_data = request.POST.copy()
        form_data['to_user'] = request.POST.get('to_user_list')
        form = ApprovalRouteForm(form_data, initial=initial_data, instance=edit_it,
                                 current_user=request.user)
        message = ""
        if form.is_valid():
            form.save()
            messages.success(request, 'Memo Forwarding Updated Successfully!')
            message = "success"
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    message += f"Error in field '{field}': {error}"
        return JsonResponse({'message': message})
    else:
        user_role = UserRole.objects.get(user_id=request.user.id)
        department = user_role.business_unit
        initial_data = {
            'form_type': "Approval Route",
            'user_role': user_role,
            'memo': edit_it.memo_id,
            'from_user': request.user.id,
            'to_user': edit_it.to_user.id,
            'comment': edit_it.comment,
            'title': 'Edit Memo Approval',
            'department': department
        }
        form = ApprovalRouteForm(initial=initial_data, current_user=request.user)
        return render(request, 'memotracker/memo_route_form.html',
                      {'form': form, 'title': 'Add Memo Route', 'cancel_btn_url': 'memo_approval_history'})


@login_required
def delete_memo_approval(request):
    pk = request.POST.get('id')
    delete_it = ApprovalRoute.objects.get(id=pk)
    delete_it.delete()
    return redirect('memo_approval_history', delete_it.memo_id)


@login_required
def approve_memo(request):
    user_role = UserRole.objects.get(user=request.user,
                                     active=True)
    memo_id = request.POST.get('id')
    memo = Memo.objects.get(id=memo_id)
    new_ref_number = memo.reference_number
    if memo.content_type != ContentType.objects.get(model='user'):
        bu = user_role.business_unit
        bu_reference_code = f'IPDC/{bu.code}' if memo.in_english else f'ኢፓልኮ/{bu.code}'
        bu_memo = Memo.objects.filter(reference_number__contains=bu_reference_code).filter(
            reference_number__contains=date.today().year, reference_number__endswith=str(datetime.today().year))
        if bu_memo.count() == 0:
            last_bu_ref_number = 1
            new_ref_number = f'{bu_reference_code}/{last_bu_ref_number}/{str(date.today().year)}'
        elif memo.status == "draft":
            last_bu_ref_number = bu.last_memo_ref_number + 1
            new_ref_number = f'{bu_reference_code}/{last_bu_ref_number}/{str(date.today().year)}'
    memo.reference_number = new_ref_number
    memo.status = 'approved'
    memo.save()
    return redirect('outgoing_memo_list')


@login_required
def edit_memo(request, memo_id):
    user_role = UserRole.objects.get(user=request.user,
                                     active=True)  # Assuming you have a function to get the user role
    bu = user_role.business_unit
    last_bu_ref_number = bu.last_memo_ref_number
    last_ref_number = f'IPDC/{bu.code}/{last_bu_ref_number}/{str(date.today().year)}'

    profile = Profile.objects.get(user=request.user)
    last_personal_memo_ref_number = f'P{request.user.id}/{profile.last_personal_memo_ref_number}/{str(date.today().year)}'

    memo = get_object_or_404(Memo, pk=memo_id)

    if request.method == 'POST':
        form = MemoForm(request.POST, instance=memo, user_id=user_role.user.id, bunit_id=user_role.business_unit.id)
        if form.is_valid():
            memo = form.save(commit=False)  # don't save the form yet
            form.save()
            return redirect('draft_memo_list')
        else:
            message = ''
            print('Failed to save memo')
            for field, errors in form.errors.items():
                for error in errors:
                    message += f"Error in field '{field}': {error}"
            print(message)
    else:
        form = MemoForm(instance=memo, user_id=user_role.user.id, bunit_id=user_role.business_unit.id)

    # ethDate = ethiopianDateFormatter(datetime.today())
    return render(request, 'memotracker/edit_memo.html', {
        'user_role': user_role,
        'form': form,
        'memo': memo,
        # 'ethDate': ethDate,
        'last_ref_number': last_ref_number,
        'listName': 'Draft Memo',
        'last_personal_memo_ref_number': last_personal_memo_ref_number,
    })


@login_required
def delete_memo(request):
    memo = get_object_or_404(Memo, pk=request.POST.get('id'))
    if request.method == 'POST':
        memo.delete()
        return redirect('draft_memo_list')

    return render(request, 'memotracker/draft_memo_list.html', {
        'memo': memo
    })


@login_required
# list of all attachements for a memo
def memo_attachments_list(request, pk):
    memo = get_object_or_404(Memo, id=pk)
    attachments = memo.attachments.all().order_by(
        '-attachment_date')  # attachements here is a relatedname for memo.forighkey field
    rows_per_page = 10
    paginator = Paginator(attachments, rows_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'memotracker/memo_attachments_list.html', {
        'page_obj': page_obj,
        'attachments': attachments,
        'memo': memo
    })


@login_required
def memo_attachment_add(request, memo_id):
    memo = Memo.objects.get(id=memo_id)
    if request.method == 'POST':
        form = MemoAttachmentForm(request.POST, memo_id=memo_id)
        if form.is_valid():
            # attached_attribute will take the value of the currently logged in user
            memo_attachment = form.save(commit=False)
            memo_attachment.attached_by = request.user
            form.save()
            return redirect('memo_detail', memo_id)
    else:
        form = MemoAttachmentForm(memo_id=memo_id)

    return render(request, 'memotracker/memo_attachment_add.html', {
        'form': form,
        'memo_id': memo_id,
        'memo': memo
    })


# delete attachment
@login_required
def memo_attachment_delete(request):
    attachment = get_object_or_404(MemoAttachment, pk=request.POST.get('id'))
    if request.method == 'POST':
        attachment.delete()
        return redirect('memo_attachments_list', attachment.memo.id)

    return render(request, 'memotracker/memo_attachment_delete.html', {
        'attachment': attachment,
    })

# update attachment
@login_required
def memo_attachment_update(request, memo_id, attachment_id):
    memo_attachment = get_object_or_404(MemoAttachment, memo__id=memo_id, id=attachment_id)
    if request.method == 'POST':
        form = MemoAttachmentForm(request.POST, instance=memo_attachment)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.save()
            return redirect('memo_attachments_list', memo_attachment.memo.id)
    else:
        form = MemoAttachmentForm(instance=memo_attachment, memo_id=memo_id)

    return render(request, 'memotracker/memo_attachment_update.html', {
        'form': form,
        'attachment': memo_attachment,
        'memo_id': memo_id,
    })


@login_required
def memo_approval_history(request, memo_id):
    memo = Memo.objects.get(id=memo_id)
    approval_routes = memo.approvalroute_set.all().order_by('created_date')
    current_user_role = Role.objects.get(Q(userrole__user__id=request.user.id) & Q(userrole__active=True))
    delegate = UserRole.objects.get(user_id=request.user.id)
    is_manager = current_user_role.is_manager
    is_delegated = delegate.deligated
    disable = True
    if is_manager:
        if not is_delegated:
            if memo.status == 'draft':
                disable = False
    else:
        if is_delegated:
            if memo.status == 'draft':
                disable = False
    context = {
        'memo': memo,
        'title': 'Approval Routing Information',
        'disable': disable,
        'back_btn_url': 'draft_memo_list',
        'memo_routes': approval_routes,
        'current_user': request.user
    }
    return render(request, 'memotracker/memohistory_form.html', context)


@login_required
def memo_route_history(request, memo_id, list_name):
    memo = Memo.objects.get(id=memo_id)
    all_routes = memo.memoroute_set.all().order_by('date_sent')
    memo_routes2 = MemoRoute.objects.none()
    userrole = UserRole.objects.get(user=request.user, active=True)

    if list_name == 'Incoming Memo' or list_name == 'External Letter':
        manager = userrole.role.is_manager
        delegate = userrole.deligated
        user_d_type = ContentType.objects.get(app_label='auth', model='user')
        bu_d_type = ContentType.objects.get(app_label='organogram', model='businessunit')
        ext_d_type = ContentType.objects.get(app_label='organogram', model='externalcustomer')
        user_id = request.user.id
        cur_index = []
        if manager or delegate:
            bu_id = userrole.business_unit_id
            current_user_route = all_routes.filter(
                Q(destination_type=bu_d_type, destination_id=bu_id) | Q(destination_type=user_d_type,
                                                                        destination_id=user_id) | Q(
                    from_user_id=user_id))
        else:
            if list_name == 'External Letter':
                current_user_route = all_routes.filter(from_user_id=user_id)
            else:
                current_user_route = all_routes.filter(destination_type=user_d_type, destination_id=user_id)
        if current_user_route.exists():
            for index, route in enumerate(all_routes):
                if route in current_user_route:
                    cur_index.append(index)
            j = 0
            for index in cur_index:
                memo_routes2 = memo_routes2 | all_routes.filter(id=all_routes[index].id)
                if index > 0:
                    for i in range(index - 1, -1, -1):
                        user_ids = []
                        if all_routes[i].destination_type == user_d_type:
                            user_ids.append(all_routes[i].destination_id)
                        else:
                            user_role = UserRole.objects.filter(
                                Q(business_unit_id=all_routes[i].destination_id, active=True) & (
                                        Q(deligated=True) | Q(role__is_manager=True))).values_list('user_id', flat=True)
                            user_ids = list(user_role)
                        from_user_id = current_user_route[j].from_user_id
                        if from_user_id in user_ids:
                            memo_routes2 = memo_routes2 | all_routes.filter(id=all_routes[i].id)
                memo_routes2 = memo_routes2 | memo_forwarder(all_routes, current_user_route[j], memo_routes2)
                if current_user_route[j].status == "notseen":
                    route = current_user_route[j]
                    destination_id = ""
                    destination_type = ""
                    if route.destination_type == user_d_type:
                        destination_id = request.user.id
                        destination_type = user_d_type
                    elif manager or delegate:
                        destination_id = userrole.business_unit_id
                        destination_type = bu_d_type
                    if route.destination_type == destination_type and route.destination_id == destination_id:
                        route.status = "seen"
                        route.date_viewed = timezone.now()
                        route.save()
                j += 1
    else:
        memo_routes2 = all_routes
    context = {
        'memo': memo,
        'title': 'Memo Routing Information',
        'list_name': list_name,
        'userrole': userrole,
        'memo_routes': sorted(memo_routes2, key=lambda x: (x.level, x.date_sent, int(not x.carbon_copy)),
                              reverse=False),
        # 'memo_routes': memo_routes2.sort(key=lambda x: x.date_sent, reverse=True),
        'current_user': request.user
    }
    return render(request, 'memotracker/memohistory_form.html', context)


# def memo_forwarder1(all_routes, route, memo_routes):
#     to_user = User.objects.get(pk=route.destination_id)
#     forwards = all_routes.filter(from_user=to_user, level=route.level + 1)
#     if forwards.exists():
#         for forward in forwards:
#             item = all_routes.filter(id=forward.id)
#             memo_routes = memo_routes | item
#             memo_routes = memo_forwarder1(all_routes, forward, memo_routes)
#     return memo_routes

def memo_forwarder(all_routes, route, memo_routes):
    user_d_type = ContentType.objects.get(app_label='auth', model='user')
    user_ids = []
    if route.destination_type == user_d_type:
        user_ids.append(route.destination_id)
    else:
        user_role = UserRole.objects.filter(Q(business_unit_id=route.destination_id, active=True) & (
                    Q(deligated=True) | Q(role__is_manager=True))).values_list('user_id', flat=True)
        user_ids = list(user_role)
    forwards = all_routes.filter(from_user_id__in=user_ids, level=route.level + 1)
    if forwards.exists():
        for forward in forwards:
            item = all_routes.filter(id=forward.id)
            memo_routes = memo_routes | item
            memo_routes = memo_forwarder(all_routes, forward, memo_routes)
    return memo_routes


def update_attached_memos(request):
    if request.method == 'POST':
        memo_id = request.POST.get('memo_id')
        attached_memo_ids = request.POST.getlist('attached_memo_ids')

        memo = get_object_or_404(Memo, pk=memo_id)
        memo.attached_memos.set(attached_memo_ids)
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request'})


# returns memos either written by the current user or sent to the current user
# def get_available_memos(user):
#     memos = MemoRoute.objects.raw('''
#         SELECT * FROM memotracker_memoroute
#         WHERE id IN (
#             SELECT MIN(id)
#             FROM memotracker_memoroute
#             WHERE from_user_id = %s OR to_user_id = %s
#             GROUP BY memo_id
#         )
#     ''', [user.id, user.id])
#     return memos



# returns memos either written by the current user or sent to the current user
def get_available_memos(user):
    memos = MemoRoute.objects.filter(
        Q(from_user=user) | Q(to_user=user)
    ).distinct('memo_id')
    return memos

@login_required
def generate_report(request, memo_id, format):
    user_role = UserRole.objects.get(user=request.user, active=True)
    memo = get_object_or_404(Memo, pk=memo_id)
    memo_routes = memo.memoroute_set.filter(level=1).order_by('-date_sent')

    cc_list = []
    direct_list = []

    # Initialize a variable for the source signature
    source_signature = None

    # Fetching the source user's information
    created_by_role = UserRole.objects.get(user=memo.created_by)
    source_bu = created_by_role.business_unit

    # Retrieve the source signature
    if source_bu.bu_signature:
        try:
            source_signature_path = source_bu.bu_signature.path
            with open(source_signature_path, 'rb') as img_file:
                source_signature = base64.b64encode(img_file.read()).decode('utf-8')
        except FileNotFoundError:
            source_signature = None

    type_user = ContentType.objects.get(app_label='auth', model='user')
    type_bu = ContentType.objects.get(app_label='organogram', model='businessunit')

    for route in memo_routes:
        if route.destination_type == type_user:
            to_user = UserRole.objects.get(user_id=route.destination_id)
            full_name = to_user.user.first_name + ' ' + to_user.user.last_name
            if not memo.in_english:
                profile = Profile.objects.get(user=to_user.user)
                full_name = profile.full_name if profile and profile.full_name else full_name
            user = f"{full_name} [{to_user.business_unit.name_am if not memo.in_english else to_user.business_unit.name_en}]"
            (cc_list if route.carbon_copy else direct_list).append(user)

        elif route.destination_type == type_bu:
            bu = BusinessUnit.objects.get(pk=route.destination_id)
            if bu.code not in ["RAS", "CA"]:
                (cc_list if route.carbon_copy else direct_list).append(
                    bu.name_am if not memo.in_english else bu.name_en)

        else:
            try:
                to_external = ExternalCustomer.objects.get(pk=route.destination_id)
                external = to_external.name_am if not memo.in_english else to_external.name_en
            except ObjectDoesNotExist:
                external = "<Object Removed>"
            (cc_list if route.carbon_copy else direct_list).append(external)

    cc_list_count = len(cc_list)
    direct_list_count = len(direct_list)

    user_roles = UserRole.objects.filter(user__in=[memo.created_by, memo.assigned_to])
    business_unit_created_by = user_roles.first().business_unit.name_en if memo.in_english else user_roles.first().business_unit.name_am
    from_field = to = subject = referenceNumber = date = business_unit_created_by = ''

    # Format the date as a string
    memo_date = timezone.localtime(memo.memo_date, timezone=pytz.timezone('Etc/GMT-3'))

    if memo.in_english:
        date_str = memo_date.strftime('%d/%m/%Y')
        from_field = 'From:'
        if memo.public:
            to = 'To: All IPDC Staff'
        else:
            to = 'To:'
        subject = 'Subject:'
        referenceNumber = 'Ref Number:'
        date = 'Date:'
        cc = "CC:"
        if memo.content_type.model == 'user':
            business_unit_created_by = memo.created_by.first_name + ' ' + memo.created_by.last_name
        else:
            business_unit_created_by = [user_role.business_unit.name_en for user_role in user_roles][0]

    else:
        # eth_day, eth_month, eth_year = to_ethiopian(memo.memo_date.year, memo.memo_date.month, memo.memo_date.day)
        # date_str = f"{eth_day:02d}/{eth_month:02d}/{eth_year}"

        memo_date = memo.memo_date
        converter = EthiopianDateConverter()
        try:
            eth_day, eth_month, eth_year = converter.to_ethiopian(memo_date.year, memo_date.month, memo_date.day)
            date_str = f"{eth_year}/{eth_month:02d}/{eth_day:02d}"
        except Exception as e:
            print(f"Error during date conversion: {e}")
            date_str = "Invalid date"


        from_field = 'ከ:'
        if memo.public:
            to = 'ለ፡ ኮርፖሬሽኑ የስራ ኃላፊዎች እና ሰራተኞች በሙሉ'
        else:
            to = 'ለ:'
        subject = 'ጉዳዩ:'
        referenceNumber = 'ቁጥር:'
        date = 'ቀን:'
        cc = 'ግልባጭ:'
        if memo.content_type.model == 'user':
            business_unit_created_by = memo.created_by.first_name + ' ' + memo.created_by.last_name
        else:
            business_unit_created_by = [user_role.business_unit.name_am for user_role in user_roles][0]
    # Handle PDF generation

    if format == 'pdf':
        content_paragraphs = memo.content.split('\n')
        sender_bu = user_role.business_unit  # Get the sender's business unit
        def get_header_footer_paths(bu, to_external=False):
            # Initialize paths as None
            header_image_path = default_storage.path(
                bu.internal_header_image.name) if bu.internal_header_image else None
            footer_image_path = default_storage.path(
                bu.internal_footer_image.name) if bu.internal_footer_image else None

            # Also check for external headers and footers
            external_header_image_path = default_storage.path(
                bu.external_header_image.name) if bu.external_header_image else None
            external_footer_image_path = default_storage.path(
                bu.external_footer_image.name) if bu.external_footer_image else None

            # If images are not found, check parent business unit
            if not header_image_path or not footer_image_path:
                parent_bu = bu.parent
                if parent_bu:
                    header_image_path = header_image_path or (
                        default_storage.path(
                            parent_bu.internal_header_image.name) if parent_bu.internal_header_image else None
                    )
                    footer_image_path = footer_image_path or (
                        default_storage.path(
                            parent_bu.internal_footer_image.name) if parent_bu.internal_footer_image else None
                    )
                    external_header_image_path = external_header_image_path or (
                        default_storage.path(
                            parent_bu.external_header_image.name) if parent_bu.external_header_image else None
                    )
                    external_footer_image_path = external_footer_image_path or (
                        default_storage.path(
                            parent_bu.external_footer_image.name) if parent_bu.external_footer_image else None
                    )

                    # Check grandparent if necessary
                    grandparent_bu = parent_bu.parent
                    if grandparent_bu:
                        header_image_path = header_image_path or (
                            default_storage.path(
                                grandparent_bu.internal_header_image.name) if grandparent_bu.internal_header_image else None
                        )
                        footer_image_path = footer_image_path or (
                            default_storage.path(
                                grandparent_bu.internal_footer_image.name) if grandparent_bu.internal_footer_image else None
                        )
                        external_header_image_path = external_header_image_path or (
                            default_storage.path(
                                grandparent_bu.external_header_image.name) if grandparent_bu.external_header_image else None
                        )
                        external_footer_image_path = external_footer_image_path or (
                            default_storage.path(
                                grandparent_bu.external_footer_image.name) if grandparent_bu.external_footer_image else None
                        )

            # Return paths based on the to_external flag
            if to_external:
                return external_header_image_path, external_footer_image_path
            else:
                # Check if both header and footer paths are still None
                if not header_image_path or not footer_image_path:
                    raise ValueError(
                        "Error: Header and footer images are not available for the business unit or its parent.")

                return header_image_path, footer_image_path

        # Use source_bu for header/footer images
        if source_bu:
            try:
                if memo.to_external:
                    header_image_path, footer_image_path = get_header_footer_paths(source_bu, to_external=True)
                else:
                    header_image_path, footer_image_path = get_header_footer_paths(source_bu)

            except ValueError as e:
                return HttpResponse(status=404, content=str(e))
            # Debugging: Check if image files exist
            if not header_image_path or not os.path.exists(header_image_path):
                print(f"Header image not found at: {header_image_path}")
            if not footer_image_path or not os.path.exists(footer_image_path):
                print(f"Footer image not found at: {footer_image_path}")

            # Read header and footer images
            try:
                header_image_data = None
                footer_image_data = None
                if header_image_path and os.path.exists(header_image_path):
                    with open(header_image_path, 'rb') as f:
                        header_image_data = base64.b64encode(f.read()).decode('utf-8')
                if footer_image_path and os.path.exists(footer_image_path):
                    with open(footer_image_path, 'rb') as f:
                        footer_image_data = base64.b64encode(f.read()).decode('utf-8')

            except FileNotFoundError:
                return HttpResponse(status=404, content='Error: Header or footer image not found.')

            # Prepare context for PDF
            context = {
                'referenceNumber': referenceNumber,
                'date_str': date_str,
                'business_unit_created_by': business_unit_created_by,
                'to': to,
                'subject': subject,
                'cc': cc,
                'direct_list': direct_list,
                'cc_list': cc_list,
                'memo_content': content_paragraphs,
                'from_field': from_field,
                'header_image': header_image_data,
                'footer_image': footer_image_data,
                'source_signature': source_signature,
                'source_bu': source_bu,
                'memo': memo,
                # 'bu_code': source_bu.code  # Ensure to pass the correct business unit code
            }

            # Render the PDF
            html = render_to_string('pdf_template.html', context)


            pdf = HTML(string=html).write_pdf()

            if request.GET.get('download') == 'true':
                # Save the PDF to the reports directory
                pdf_file_path = os.path.join(settings.MEDIA_ROOT, 'memos', f'memo_{memo_id}.pdf')
                with open(pdf_file_path, 'wb') as pdf_file:
                    pdf_file.write(pdf)

                # Create a response for downloading the PDF
                response = HttpResponse(pdf, content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="memo.pdf"'  # This triggers a download
                return response
            else:
                # Create a response object for inline viewing
                response = HttpResponse(pdf, content_type='application/pdf')
                response['Content-Disposition'] = 'inline; filename="memo.pdf"'  # For viewing in browser
                return response  # Return the response object
    else:
        return JsonResponse({'error': 'Unsupported format'}, status=400)  # Handle other formats

def header_footer(canvas, doc, sender_bu):
    canvas.saveState()
    header_image_path = default_storage.path(sender_bu.internal_header_image.name) if sender_bu.internal_header_image else 'default_internal_header.jpg'
    canvas.drawImage(header_image_path, 0, doc.pagesize[1] - 100, width=doc.pagesize[0], height=100, mask='auto')

    footer_image_path = default_storage.path(sender_bu.internal_footer_image.name) if sender_bu.internal_footer_image else 'default_headquarter_footer.jpg'
    canvas.drawImage(footer_image_path, 0, 0, width=doc.pagesize[0], height=100, mask='auto')

    canvas.restoreState()

def header_footer_external(canvas, doc, sender_bu):
    canvas.saveState()
    header_image_path = default_storage.path(sender_bu.external_header_image.name) if sender_bu.external_header_image else 'default_external_header.jpg'
    canvas.drawImage(header_image_path, 0, doc.pagesize[1] - 100, width=doc.pagesize[0], height=100, mask='auto')

    footer_image_path = default_storage.path(sender_bu.external_footer_image.name) if sender_bu.external_footer_image else 'default_headquarter_footer.jpg'
    canvas.drawImage(footer_image_path, 0, 0, width=doc.pagesize[0], height=100, mask='auto')

    canvas.restoreState()
def memo_detail_api(request, pk):
    memo = get_object_or_404(Memo, pk=pk)
    if memo is not None:
        return JsonResponse({'content': memo.content})
    return JsonResponse({'error': 'Invalid request'})

