import json
import secrets
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .forms import ForgotPasswordForm, LoginForm, ResetPasswordForm, SignUpForm
from .models import CustomUser


def _authenticate_with_username_or_email(request, username_or_email, password):
    """Authenticate using username first, then fall back to email lookup."""
    user = authenticate(request, username=username_or_email, password=password)
    if user is not None:
        return user

    if "@" in username_or_email:
        try:
            matched_user = User.objects.get(email__iexact=username_or_email)
        except User.DoesNotExist:
            return None
        return authenticate(request, username=matched_user.username, password=password)

    return None


def _serialize_custom_user(user, custom_profile):
    """Build a JSON-safe payload for CustomUser details."""
    return {
        "id": custom_profile.id,
        "django_user_id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "user_type": custom_profile.user_type,
        "phone_number": custom_profile.phone_number,
        "is_verified": custom_profile.is_verified,
        "country": (
            {
                "id": custom_profile.country.id,
                "name": custom_profile.country.name,
            }
            if custom_profile.country
            else None
        ),
        "data": (
            {
                "id": custom_profile.data.id,
                "name": custom_profile.data.name,
                "data_type": custom_profile.data.data_type,
            }
            if custom_profile.data
            else None
        ),
        "dashboard_url": (
            {
                "id": custom_profile.dashboard_url.id,
                "name": custom_profile.dashboard_url.name,
                "url": custom_profile.dashboard_url.url,
            }
            if custom_profile.dashboard_url
            else None
        ),
        "created_at": custom_profile.created_at.isoformat() if custom_profile.created_at else None,
        "updated_at": custom_profile.updated_at.isoformat() if custom_profile.updated_at else None,
    }


def signup_view(request):
    """Handle user signup"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Do not log the user in immediately — require admin verification first
            messages.success(request, 'Account created successfully! Awaiting admin verification before you can login.')
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = SignUpForm()
    
    return render(request, 'accounts/signup.html', {'form': form})


def login_view(request):
    """Handle user login"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = _authenticate_with_username_or_email(request, username, password)
            
            if user is not None:
                # Ensure the user has a profile and is verified by admin
                try:
                    custom_profile = user.custom_profile
                except CustomUser.DoesNotExist:
                    messages.error(request, 'User profile not found. Contact administrator.')
                    return redirect('login')

                if not custom_profile.is_verified:
                    messages.error(request, 'Your account is not verified by an administrator yet.')
                    return redirect('login')

                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')


@login_required(login_url='login')
def dashboard_view(request):
    """Display user dashboard based on user type"""
    try:
        custom_user = request.user.custom_profile
        user_type = custom_user.user_type
    except CustomUser.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('logout')
    
    context = {
        'user_type': user_type,
        'custom_user': custom_user
    }
    
    if user_type == 'worker':
        return render(request, 'accounts/worker_dashboard.html', context)
    elif user_type == 'admin':
        return render(request, 'accounts/admin_dashboard.html', context)
    else:
        return render(request, 'accounts/dashboard.html', context)


def forgot_password_view(request):
    """Handle forgot password"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                # In production, you would send an email with a reset link
                # For now, we'll create a reset token and store it in session
                reset_token = secrets.token_urlsafe(32)
                request.session[f'reset_token_{user.id}'] = reset_token
                request.session[f'reset_user_id'] = user.id
                
                messages.success(request, 'Check your email for password reset instructions.')
                # In real application, send email here
                return redirect('reset_password', token=reset_token)
            except User.DoesNotExist:
                messages.error(request, 'No user found with this email.')
    else:
        form = ForgotPasswordForm()
    
    return render(request, 'accounts/forgot_password.html', {'form': form})


def reset_password_view(request, token=None):
    """Reset password with token"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    user_id = request.session.get('reset_user_id')
    if not user_id or request.session.get(f'reset_token_{user_id}') != token:
        messages.error(request, 'Invalid reset link.')
        return redirect('login')
    
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            try:
                user = User.objects.get(id=user_id)
                user.set_password(form.cleaned_data['password1'])
                user.save()
                del request.session[f'reset_token_{user_id}']
                del request.session['reset_user_id']
                messages.success(request, 'Password reset successfully! You can now login.')
                return redirect('login')
            except User.DoesNotExist:
                messages.error(request, 'User not found.')
    else:
        form = ResetPasswordForm()
    
    return render(request, 'accounts/reset_password.html', {'form': form})


@login_required(login_url='login')
def profile_view(request):
    """View user profile"""
    try:
        custom_user = request.user.custom_profile
    except CustomUser.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('logout')
    
    context = {
        'custom_user': custom_user
    }
    return render(request, 'accounts/profile.html', context)


@login_required(login_url='login')
def manage_workers_view(request):
    """Admin view to manage workers"""
    try:
        custom_user = request.user.custom_profile
    except CustomUser.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('logout')
    
    # Check if user is admin
    if custom_user.user_type != 'admin':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    # Get all workers (non-admin users)
    workers = CustomUser.objects.filter(user_type='worker').select_related('country', 'data', 'dashboard_url', 'django_user')
    
    context = {
        'workers': workers
    }
    return render(request, 'accounts/manage_workers.html', context)


@login_required(login_url='login')
def edit_worker_view(request, worker_id):
    """Admin view to edit individual worker"""
    try:
        admin_user = request.user.custom_profile
    except CustomUser.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('logout')
    
    # Check if user is admin
    if admin_user.user_type != 'admin':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    try:
        worker = CustomUser.objects.get(id=worker_id, user_type='worker')
    except CustomUser.DoesNotExist:
        messages.error(request, 'Worker not found.')
        return redirect('manage_workers')
    
    if request.method == 'POST':
        from .models import Country, Data, DashboardURL
        
        # Handle form submission
        country_id = request.POST.get('country')
        data_id = request.POST.get('data')
        dashboard_url_id = request.POST.get('dashboard_url')
        is_verified = request.POST.get('is_verified') == 'on'
        
        # Update worker
        if country_id:
            try:
                worker.country = Country.objects.get(id=country_id)
            except Country.DoesNotExist:
                pass
        
        if data_id:
            try:
                worker.data = Data.objects.get(id=data_id)
            except Data.DoesNotExist:
                pass
        
        if dashboard_url_id:
            try:
                worker.dashboard_url = DashboardURL.objects.get(id=dashboard_url_id)
            except DashboardURL.DoesNotExist:
                pass
        
        worker.is_verified = is_verified
        worker.save()
        
        messages.success(request, f'Worker {worker.django_user.username} updated successfully!')
        return redirect('manage_workers')
    
    from .models import Country, Data, DashboardURL
    
    context = {
        'worker': worker,
        'countries': Country.objects.all(),
        'data_list': Data.objects.all(),
        'dashboard_urls': DashboardURL.objects.all(),
    }
    return render(request, 'accounts/edit_worker.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def api_login_view(request):
    """JSON API login endpoint for external clients such as Labelme."""
    try:
        payload = json.loads(request.body.decode("utf-8")) if request.body else {}
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"success": False, "message": "Invalid JSON body."}, status=400)

    username = payload.get("username") or request.POST.get("username")
    password = payload.get("password") or request.POST.get("password")
    if not username or not password:
        return JsonResponse(
            {"success": False, "message": "username and password are required."},
            status=400,
        )

    user = _authenticate_with_username_or_email(request, username, password)
    if user is None:
        return JsonResponse({"success": False, "message": "Invalid credentials."}, status=401)

    try:
        custom_profile = user.custom_profile
    except CustomUser.DoesNotExist:
        return JsonResponse(
            {"success": False, "message": "User profile not found. Contact administrator."},
            status=403,
        )

    if not custom_profile.is_verified:
        return JsonResponse(
            {"success": False, "message": "Account is not verified by an administrator yet."},
            status=403,
        )

    login(request, user)

    return JsonResponse(
        {
            "success": True,
            "message": "Login successful.",
            "session_key": request.session.session_key,
            "user": _serialize_custom_user(user, custom_profile),
        }
    )
