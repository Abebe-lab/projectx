from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from memotracker.models import Memo, MemoRoute
from .forms import CustomerForm
from .models import ExternalCustomer, UserRole, BusinessUnit
from django.contrib.auth.decorators import login_required
from memotracker.decorators import permission_required
from django.db.models import Q, F
from django.http import JsonResponse
import json
from django.contrib.auth.models import User
from django.urls import reverse

@login_required
@permission_required('External Customer')
def get_all_customers(request):
    current_user = request.user
    user_role = UserRole.objects.get(user=current_user, active=True)
    manager = user_role.role.is_manager
    delegate = user_role.deligated
    all_customers = ExternalCustomer.objects.all()
    paginator = Paginator(all_customers, 10)  # Show 10 memos per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'customers': page_obj,
        'manager': manager,
        'delegate': delegate,
    }
    return render(request, 'organogram/customer.html', context)

@login_required
def search_customer(request):
    if request.method == 'GET':
        search_term = request.GET.get('search_term')
        results = ExternalCustomer.objects.filter(Q(name_en__icontains=search_term) | Q(name_am__icontains=search_term))
        paginator = Paginator(results, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context = {
            'customers': page_obj
        }
        return render(request, 'organogram/customer.html', context)

@login_required
def add_customer(request):
    form = CustomerForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, "Customer Saved!")
            return redirect('external_memo')
        else:
            messages.success(request, "Information is not Valid!")
            return redirect('customer')
    else:
        context = {'form': form, 'title': 'Add Customer'}
        return render(request, 'organogram/customer_form.html', context)

@login_required
def add_new_customer(request, caller=None):
    form = CustomerForm(request.POST or None)

    current_view = 'add_external_customer' if caller == 'routing' else 'add_new_customer'   # Set the current_view variable

    if request.method == 'POST':
        if form.is_valid():
            instance = form.save()
            messages.success(request, "Customer Saved!")
            if caller == 'routing':
                message = 'success'
                name = instance.name_en + ' - ' + instance.name_am
                return JsonResponse({'message': message, 'customer_name': name, 'customer_id': instance.id})
            else:
                return redirect('customer')
        else:
            messages.error(request, "Information is not Valid!")
            return redirect('customer')

    return render(request, 'organogram/customer_form.html', {
        'current_view': current_view,
        'title': 'Add Customer',
        'form': form,
    })

@login_required
def edit_customer(request, pk):
    edit_it = ExternalCustomer.objects.get(id=pk)
    form = CustomerForm(request.POST or None, instance=edit_it)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer Record Updated Successfully!')
            return redirect('customer')
    else:
        context = {'form': form, 'title': 'Edit Customer'}
        return render(request, 'organogram/customer_form.html', context)
@login_required
def delete_customer(request):
    if request.method == 'POST':
        pk = request.POST.get('id')
        external_customer = get_object_or_404(ExternalCustomer, id=pk)

        content_type_ec = ContentType.objects.get(app_label='organogram', model='externalcustomer').id
        related_memos = Memo.objects.filter(content_type_id=content_type_ec, object_id=external_customer.id)
        route = MemoRoute.objects.filter(destination_id=pk, destination_type_id=content_type_ec)

        if related_memos.exists() or route.exists():
            # return redirect('customer')
            return JsonResponse({'status': 'error', 'message': "External customer cannot be deleted as a memo is recorded.!"})
        else:
            external_customer.delete()
            # return redirect('customer')
            return JsonResponse({'status': 'success', 'message': 'Record Deleted Successfully!'})

    return redirect('customer')

@login_required
def get_bu_users(request, bu_id):
    current_user = request.user
    users = User.objects.annotate(is_manager=F('userrole__role__is_manager'),
                                  is_delegate=F('userrole__deligated')).values('id', 'first_name', 'last_name', 'is_manager', 'is_delegate'
                                                                               ).filter(userrole__business_unit__id=bu_id, userrole__active=True).exclude(id=current_user.id)
    # users = serialize('json', User.objects.values('id', 'username').filter(userrole__business_unit__id=bu_id))
    data = json.dumps(list(users))
    return JsonResponse({'message': 'success', 'users': data})

def get_business_units(request):
    business_units = BusinessUnit.objects.all()
    data = [{'id': bu.id, 'name': bu.name_en} for bu in business_units]
    return JsonResponse(data, safe=False)

# def get_personal_users(request):
#     personal_users = User.objects.all()
#     data = [{'id': pu.id, 'name': pu.first_name + ' ' + pu.last_name} for pu in personal_users]
#     return JsonResponse(data, safe=False)

def get_external_customers(request):
    external_customers = ExternalCustomer.objects.all()
    data = [{'id': ec.id, 'name': ec.name_en} for ec in external_customers]
    return JsonResponse(data, safe=False)

