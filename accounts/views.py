import logging

from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from .forms import CustomUserCreationForm, ProfileUpdateForm

logger = logging.getLogger(__name__)


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
            except Exception:
                logger.exception('Registration failed')
                messages.error(request, 'Registration failed. Please try again.')
                return render(request, 'accounts/register.html', {'form': form})
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('products:product_list')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            try:
                form.save()
            except Exception:
                logger.exception('Profile update failed for user %s', request.user.pk)
                messages.error(request, 'Profile update failed. Please try again.')
                return render(request, 'accounts/profile.html', {'form': form})
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})
