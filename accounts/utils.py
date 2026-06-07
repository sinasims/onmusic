import random
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import OTPCode, User


def get_sms_config():
    try:
        from main.models import Setting
        api_key = Setting.objects.get(key='sms_ir_api_key').value
        template_id = Setting.objects.get(key='sms_ir_template_id').value
        if api_key:
            return api_key, template_id
    except Exception:
        pass
    return settings.SMS_IR_API_KEY, settings.SMS_IR_TEMPLATE_ID


def generate_otp():
    return str(random.randint(100000, 999999))


def send_otp_sms(phone, code):
    api_key, template_id = get_sms_config()
    if not api_key or not template_id:
        return False
    try:
        import requests
        response = requests.post(
            'https://api.sms.ir/v1/send/verify',
            headers={
                'x-api-key': api_key,
                'Content-Type': 'application/json',
                'Accept': 'text/plain',
            },
            json={
                'mobile': phone,
                'templateId': int(template_id),
                'parameters': [
                    {'name': 'Code', 'value': code}
                ]
            },
            timeout=10
        )
        return response.ok
    except Exception:
        return False
    try:
        import requests
        response = requests.post(
            'https://api.sms.ir/v1/send/verify/',
            headers={
                'X-API-KEY': api_key,
                'Content-Type': 'application/json',
                'ACCEPT': 'application/json',
            },
            json={
                'Mobile': phone,
                'TemplateId': int(template_id),
                'Parameters': [
                    {'name': 'Code', 'value': code}
                ]
            },
            timeout=10
        )
        
        return response.ok
    except Exception:
        return False


def create_and_send_otp(phone):
    code = generate_otp()
    OTPCode.objects.filter(phone=phone, is_used=False).update(is_used=True)
    OTPCode.objects.create(phone=phone, code=code)
    sent = send_otp_sms(phone, code)
    return code, sent


def verify_otp(phone, code):
    expire_time = timezone.now() - timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
    otp = OTPCode.objects.filter(
        phone=phone, code=code, is_used=False, created_at__gte=expire_time
    ).first()
    if otp:
        otp.is_used = True
        otp.save()
        return True
    return False


def get_or_create_user(phone):
    user, created = User.objects.get_or_create(phone=phone, defaults={'username': phone})
    if created:
        user.set_unusable_password()
        user.save()
    return user, created
