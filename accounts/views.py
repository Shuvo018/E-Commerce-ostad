from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import CustomerProfile, Address
from accounts.forms import ProfileForm, AddressForm, RegistrationForm


# Create your views here.

def register(request):
    if request.user.is_authenticated:
        return redirect('product_list')
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            CustomerProfile.objects.create(user=user)
            messages.success(request, "Successfully Registered!")
            return redirect('login')
    else:
        form = RegistrationForm()

    return render(request=request, template_name='accounts/register.html', context={'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('product_list')
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request=request, username=email, password=password)

        if user:
            login(request=request, user=user)
            return redirect('product_list')
        messages.error(request, 'Invalid credentials!')
    
    return render(request, 'accounts/login.html')

def logout(request):
    auth_logout(request=request)
    return redirect('login')

@login_required
def profile(request):
    customer = get_object_or_404(CustomerProfile, user=request.user)
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('profile')
    else:
        form = ProfileForm(instance=customer)
    return render(request, 'accounts/profile.html', {'form': form})

@login_required
def address_create(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save()
            customer = get_object_or_404(CustomerProfile, user=request.user)
            customer.address.add(address)
            # customer.address = address
            # customer.save()
            messages.success(request, 'Address added.')
            return redirect('address_list')
    else:
        form = AddressForm()
    return render(request, 'accounts/address_form.html', {'form': form})



@login_required
def address_list(request):
    customer = get_object_or_404(CustomerProfile, user=request.user)
    addresses = customer.address.all()
    return render(request, 'accounts/address_list.html', {'addresses': addresses})


@login_required
def address_update(request, pk):
    customer = get_object_or_404(CustomerProfile, user=request.user)
    address = get_object_or_404(Address, pk=pk, customer_profiles=customer)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, 'Address updated.')
            return redirect('address_list')
    else:
        form = AddressForm(instance=address)
    return render(request, 'accounts/address_form.html', {'form': form})



@login_required
def address_delete(request, pk):
    customer = get_object_or_404(CustomerProfile, user=request.user)
    address = get_object_or_404(Address, pk=pk, customer_profiles=customer)
    if request.method == 'POST':
        customer.address.remove(address)
        address.delete()
        messages.success(request, 'Address deleted.')
        return redirect('address_list')
    return render(request, 'accounts/address_confirm_delete.html', {'address': address})
