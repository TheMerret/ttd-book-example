from django.shortcuts import redirect
from django.core.mail import send_mail


def send_login_email(request):
    """отправить сообщение для входа в систему"""
    email = request.POST['email']
    send_mail(
        'Your login link for Superlists',
        'body text tbc',
        'noreply@superlists',
        [email],
    )
    return redirect('/')