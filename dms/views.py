from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, JsonResponse, HttpResponse
from memotracker.models import Memo, MemoRoute
from memotracker.views import paginate_memos
from .forms import DocumentForm
from .models import Document, MemoToDMS
from django.contrib.auth.decorators import login_required
from organogram.models import UserRole, BusinessUnit, ExternalCustomer
from django.urls import reverse
from django.contrib import messages
from .models import User, SharedDocument
from django.contrib.auth.decorators import permission_required
import logging

@login_required
def index(request):
    current_user = request.user

    # Fetch documents uploaded by the user
    uploaded_documents = Document.objects.filter(uploaded_by=current_user)

    # Fetch documents shared with the user
    shared_documents = Document.objects.filter(shared_documents__shared_with=current_user)

    # Combine both querysets
    documents = uploaded_documents | shared_documents  # Union of both querysets

    # Remove duplicates if any
    documents = documents.distinct().order_by('-uploaded_date')

    # If the request is AJAX, handle the search
    search_query = request.GET.get('search_query', '')
    if search_query:
        documents = documents.filter(
            Q(title__icontains=search_query) |
            Q(document_number__icontains=search_query) |
            Q(category__name__icontains=search_query) |
            Q(uploaded_by__first_name__icontains=search_query) |
            Q(uploaded_by__last_name__icontains=search_query) |
            Q(uploaded_by__username__icontains=search_query)
        ).distinct()

    # Call the custom pagination method
    page_obj = paginate_memos(request, documents)

    # Check if the request is AJAX
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'dms/searched_document_results.html', {'page_obj': page_obj})

    return render(request, 'dms/index.html', {
        'page_obj': page_obj,
    })

def document_detail(request, pk):
    document = Document.objects.get(pk=pk)
    return render(request, 'dms/document_details.html', {
        'document': document
    })

def search_results(request):
    all_documents = Document.objects.filter(uploaded_by=request.user).order_by('-uploaded_at')
    if request.method == 'GET':
        # Get the selected option from the form
        selected_option = request.GET.get('search_by')
        # Perform the search based on the selected option
        if selected_option == 'document_number':
            # Perform search logic for document_number
            results = Document.objects.filter(document_number__icontains=request.GET.get('search_query'), uploaded_by=request.user)
        elif selected_option == 'title':
            # Perform search logic for title
            results = Document.objects.filter(title__icontains=request.GET.get('search_query'), uploaded_by=request.user)
        elif selected_option == 'category':
        # Perform search logic for title
            results = Document.objects.filter(category__name__icontains=request.GET.get('search_query'), uploaded_by=request.user)
        elif selected_option == 'uploaded_date':
            from_date = request.GET.get('search_query')
            to_date = request.GET.get('date_to')
            results = Document.objects.filter(uploaded_date__range=(from_date, to_date), uploaded_by=request.user)
        else:
            results = Document.objects.filter(uploaded_by=request.user).order_by('-created_date')

        # Prepare the context to pass to the template
        context = {
            'documents': results,
            'selected_option': selected_option,
        }

        return render(request, 'dms/index.html', context)

    return render(request, 'dms/index.html', {
        'documents': all_documents
    })

@login_required
@permission_required('dms.can_create_document', raise_exception=True)
def document_create(request):
    current_user = UserRole.objects.get(user=request.user, active=True)
    # file_url = request.GET.get('file_url', '')  # Get file_url from query parameters
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document_number = form.cleaned_data['document_number']

            # Check for existing documents with the same document number
            if Document.objects.filter(document_number=document_number).exists():
                form.add_error('document_number',
                               f'A document with the same document number "{document_number}" already exists. Please use a unique number.')
                return render(request, 'dms/document_create.html', {'form': form})
            document = form.save(commit=False)
            document.uploaded_by = current_user.user

            # Set object_id based on the owner type

            content_type_str = str(form.cleaned_data['content_type'])
            app_label, model_name = content_type_str.split(' | ')

            # Determine the non-form field value based on the owner type
            if model_name == 'user':
                object_type = current_user
            else:
                object_type = current_user.business_unit

            document.object_id = object_type.id

            # Validate the file
            file = form.cleaned_data.get('file')
            if file:
                max_size = 10 * 1024 * 1024  # 10MB
                allowed_types = ['application/pdf', 'image/jpeg', 'image/png']

                if file.size > max_size:
                    form.add_error('file', 'File size exceeds the maximum allowed limit.')
                    return JsonResponse({'message': 'error', 'errors': form.errors})

                if file.content_type not in allowed_types:
                    form.add_error('file', 'Invalid file type. Please upload a PDF, JPEG, or PNG file.')
                    return JsonResponse({'message': 'error', 'errors': form.errors})

            # Save the document
            document.save()

            # Handle the shared_with ManyToMany field
            shared_with_ids = form.cleaned_data.get('shared_with')
            if shared_with_ids:
                document.shared_with.set(shared_with_ids)

            return JsonResponse({'message': 'success', 'saved_document': document.id})
        else:
            return JsonResponse({'message': 'error', 'errors': form.errors})
    else:
        form = DocumentForm()
    return render(request, 'dms/document_create.html', {'form': form})
@login_required
@permission_required('dms.can_update_document', raise_exception=True)
def document_update(request, pk):
    document = get_object_or_404(Document, pk=pk)
    current_user = UserRole.objects.get(user=request.user, active=True)

    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES, instance=document)

        if form.is_valid():
            if form.has_changed():
                document = form.save(commit=False)
                document.uploaded_by = current_user.user

                # Set object_id based on the owner type
                content_type_str = str(form.cleaned_data['content_type'])
                app_label, model_name = content_type_str.split(' | ')
                object_type = current_user if model_name == 'user' else current_user.business_unit
                document.object_id = object_type.id

                # Validate the file
                if 'file' in request.FILES:
                    uploaded_file = request.FILES['file']
                    document.file = uploaded_file

                    # Check file size and content type
                    max_size = 10 * 1024 * 1024  # 10MB
                    allowed_types = ['application/pdf', 'image/jpeg', 'image/png']

                    if uploaded_file.size > max_size:
                        form.add_error('file', 'File size exceeds the maximum allowed limit.')
                        return render(request, 'dms/document_update.html', {'form': form, 'pk': pk})

                    if uploaded_file.content_type not in allowed_types:
                        form.add_error('file', 'Invalid file type. Please upload a PDF, JPEG, or PNG file.')
                        return render(request, 'dms/document_update.html', {'form': form, 'pk': pk})

                # Save the document
                document.save()

                # Handle the shared_with ManyToMany field
                shared_with_ids = form.cleaned_data.get('shared_with')
                if shared_with_ids:
                    document.shared_with.set(shared_with_ids)

                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'message': 'No changes were made.'})

        else:
            messages.error(request, 'Form data was not valid.')

    else:
        form = DocumentForm(instance=document)

    return render(request, 'dms/document_update.html', {'form': form, 'pk': pk})

def document_delete(request, pk):
    document = get_object_or_404(Document, pk=pk)
    if request.method == 'POST':
        document.delete()
        return redirect('index')
    return render(request, 'dms/document_delete.html', {
        'document': document
    })

# create a view for the document details form
def document_details(request, pk):
    document = get_object_or_404(Document, pk=pk)
    return render(request, 'dms/document_details.html', {
        'document': document
    })
@login_required
def share_document(request, document_id):
    document = get_object_or_404(Document, id=document_id)
    # Initialize document_privacy to handle both GET and POST requests
    document_privacy = document.privacy
    if request.method == 'POST':
        shared_with_ids = request.POST.getlist('shared_with')
        # Check if no users were selected
        if not shared_with_ids:
            messages.error(request, "Please select at least one user to share the document with.")
            return render(request, 'dms/document_share.html', {
                'document': document,
                'users': User.objects.exclude(id=request.user.id),
                'document_privacy': document_privacy
            })
        already_shared_users = []  # To keep track of users already shared with
        # Check for already shared documents before creating new entries
        for user_id in shared_with_ids:
            user = get_object_or_404(User, id=user_id)
            if SharedDocument.objects.filter(document=document, shared_with=user).exists():
                already_shared_users.append(user.username)  # Collect already shared usernames
                continue  # Skip creating a new entry for this user
            # Create SharedDocument entry only if not already shared
            SharedDocument.objects.get_or_create(document=document, shared_with=user)
        # Handle messages for already shared users
        if already_shared_users:
            for username in already_shared_users:
                messages.warning(request, f"Document already shared with {username}.")
        else:
            messages.success(request, "Document shared successfully!")
        return redirect('index')  # Redirect to a success page or the index

    # For GET request, display the share document form
    users = User.objects.exclude(id=request.user.id)  # Exclude the current user from the list
    return render(request, 'dms/document_share.html', {
        'document': document,
        'users': users,
        'document_privacy': document_privacy
    })


# The method that sends seen memo to DMS
@login_required
def send_memo_to_dms(request, memo_id):
    memo = get_object_or_404(Memo, id=memo_id)

    is_public = memo.public  # Assuming memo has a 'public' attribute

    # Check if there is a MemoRoute with the status 'seen' for the given memo
    seen_route = MemoRoute.objects.filter(memo=memo, status='seen').exists()
    # if not seen_route:
    if not is_public and not seen_route:
        return JsonResponse({
            'success': False,
            'message': "This memo has not been seen. Cannot send to DMS.",
            'redirect_url': reverse('memo_detail', args=[memo.id])  # Ensure this is valid
        })
    if request.method == "POST":
        existing_memo = MemoToDMS.objects.filter(memo=memo).exists()
        if existing_memo:
            return JsonResponse({'success': False, 'message': "This memo has already been sent to DMS."})
        else:
            memo_detail = MemoToDMS(memo=memo, sent_by=request.user)
            memo_detail.save()
            return JsonResponse({'success': True, 'message': "Memo has been sent to DMS successfully."})
    memo_details = MemoToDMS.objects.filter(memo=memo)
    page_obj = paginate_memos(request, memo_details)
    return render(request, 'dms/memo_sent_to_dms.html', {'memo': memo, 'page_obj': page_obj})

def count_memos_sent_to_dms(user):
    return MemoToDMS.objects.filter(sent_by=user).count()

@login_required
def list_in_dms(request):
    search_query = request.GET.get('search', '')
    # Get the current user
    current_user = request.user
    if search_query:
        memo_details = MemoToDMS.objects.filter(
            sent_by=current_user  # Filter by the current user
        ).filter(
            Q(memo__reference_number__icontains=search_query) |
            Q(memo__subject__icontains=search_query) |
            Q(sent_by__first_name__icontains=search_query) |
            Q(sent_by__last_name__icontains=search_query)
        )
    else:
        # memo_details = MemoToDMS.objects.all()
        memo_details = MemoToDMS.objects.filter(sent_by=current_user).order_by('-sent_date')
    page_obj = paginate_memos(request, memo_details)
    # Check if the request is AJAX using the content type
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'dms/searched_memo_results.html', {'page_obj': page_obj})
    return render(request, 'dms/memo_sent_to_dms.html', {'page_obj': page_obj, 'search_query': search_query})


