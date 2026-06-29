# 📱 OTPAutomator

**ابزار خودکار تست و ارسال درخواست‌های OTP (کد تأیید) برای سرویس‌های مختلف ایرانی**

---

## 🚀 درباره پروژه
<div dir="rtl">

`OTPAutomator` یک اسکریپت پایتون است که با استفاده از یک فایل تنظیمات (`api.txt`)، درخواست‌های دریافت کد تأیید را به APIهای مختلف ارسال کرده و نتایج را به‌صورت ساختاریافته ذخیره می‌کند.
این ابزار برای **تست‌های امنیتی**، **تحلیل پاسخ‌ها**، و **شبیه‌سازی فرایند احراز هویت** در سرویس‌های مختلف طراحی شده است.

### ✨ ویژگی‌های کلیدی

- ✅ پشتیبانی از چندین سرویس‌دهنده (علی‌بابا، کالاهم‌رام، اسنپ‌فود، اسنپ‌تاکسی و ...)
- 🔐 مدیریت خودکار Nonce (استخراج توکن‌های امنیتی از صفحات HTML)
- 📦 پشتیبانی از فرمت‌های مختلف بدنه (JSON، `x-www-form-urlencoded`)
- 🍪 مدیریت Session و کوکی‌ها با استفاده از `requests.Session`
- 🚦 تشخیص Rate Limit (خطاهای ۴۰۰ حاوی کلمات `seconds` یا `rate`)
- 🔗 وابستگی بین APIها (قابلیت `depends_on` برای ترتیب اجرا)
- 💾 ذخیره‌سازی نتایج در فایل `result.txt` با فرمت خوانا
- 🧩 قابلیت گسترش آسان با اضافه کردن بلاک‌های جدید به `api.txt`

---

## 📦 نصب و راه‌اندازی

### پیش‌نیازها
- Python 3.6 یا بالاتر
- کتابخانه‌ی `requests`

### نصب کتابخانه
```bash
pip install requests
```

### دریافت پروژه
```bash
git clone https://github.com/your-username/OTPAutomator.git
cd OTPAutomator
```

## 🛠️ ساختار فایل‌ها
```text
OTPAutomator/
├── main.py          # اسکریپت اصلی
├── api.txt          # تنظیمات APIها (شما باید این فایل را بسازید)
├── result.txt       # خروجی نتایج (پس از اجرا ایجاد می‌شود)
├── .gitignore       # لیست فایل‌های نادیده گرفته شده در گیت
└── README.md        # این فایل
```

## ⚙️ نحوه استفاده

### ۱. تنظیم شماره تلفن

در فایل `main.py`، متغیر `PHONE` را با شماره‌ی خود جایگزین کنید:

```python
PHONE = '09123456789'   # شماره با صفر اول (برای اکثر سرویس‌ها)
```

> نکته: اگر سرویسی شماره را بدون صفر اول نیاز دارد (مثل اسنپ‌تاکسی)، از متغیر `{{phone_clean}}` در `api.txt` استفاده کنید (خود اسکریپت این جایگزینی را انجام می‌دهد).

### ۲. تنظیم فایل api.txt

این فایل شامل بلاک‌هایی برای هر API است. هر بلاک با `[id]` شروع می‌شود و شامل کلید‌های زیر است:

| کلید | توضیح | ضروری |
|------|-------|-------|
| `name` | نام نمایشی سرویس | خیر |
| `url` | آدرس کامل API | بله |
| `method` | متد HTTP (GET, POST, ...) | بله |
| `body` | بدنه درخواست (می‌تواند JSON یا رشته‌ی فرم) | خیر |
| `headers` | هدرهای درخواست (فرمت JSON) | خیر |
| `warmup` | آدرس صفحه‌ای که برای دریافت کوکی‌ها پیش‌بارگیری می‌شود | خیر |
| `extract_nonce` | نام فیلدی که باید از صفحه‌ی warmup استخراج شود | خیر |
| `depends_on` | وابستگی به API دیگر (اجرا بعد از آن) | خیر |
| `expected_fields` | فیلدهای مورد انتظار در پاسخ (فقط برای مستندات) | خیر |

> نکته: در `body` و `headers` می‌توانید از متغیرهای `{{phone}}` و `{{phone_clean}}` و همچنین هر متغیر دیگری که از `shared_data` استخراج شده (مثل `{{nonce_login_register}}`) استفاده کنید.

### ۳. اجرای اسکریپت

```bash
python main.py
```

پس از اجرا، نتایج به‌صورت زیر در ترمینال نمایش داده می‌شود و همچنین در فایل `result.txt` ذخیره می‌گردد.

---

## 📝 مثال فایل api.txt

در زیر یک نمونه از فایل تنظیمات برای چهار سرویس آورده شده است:

```ini
[alibaba-otp]
name = Alibaba.ir OTP
url = https://ws.alibaba.ir/api/v3/account/mobile/otp
method = POST
body = {"phoneNumber": "{{phone}}"}
headers = {
  "Accept": "application/json, text/plain, */*",
  "Content-Type": "application/json"
}
warmup = https://www.alibaba.ir/
expected_fields = result.tempToken, result.message

[Kalahamrah-otp]
name = Kalahamrah.com OTP
url = https://kalahamrah.com/wp-admin/admin-ajax.php
method = POST
body = action=login_register_together&value={{phone}}&captcha=&nonce={{nonce_login_register}}
headers = {
  "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
}
warmup = https://kalahamrah.com/panel/
extract_nonce = nonce_login_register
expected_fields = status, msg

[snappfood-otp]
name = Snappfood OTP
url = https://user.snappfood.ir/v1/auth/otp/send
method = POST
body = {"mobile_number": "{{phone}}", "type": "Customer"}
headers = {
  "Content-Type": "application/json"
}
warmup = https://snappfood.ir/
expected_fields = success

[snapptaxi-otp]
name = Snapp Taxi OTP
url = https://app.snapp.taxi/api/api-passenger-oauth/v3/mutotp
method = POST
body = {"cellphone": "+989{{phone_clean}}", "attestation": {"method": "skip", "platform": "skip"}, "extra_methods": []}
headers = {
  "Content-Type": "application/json"
}
warmup = https://app.snapp.taxi/login
expected_fields = success, data.token
```

---

## 🧩 افزودن سرویس جدید

برای افزودن یک سرویس جدید، کافی است یک بلاک جدید به `api.txt` اضافه کنید:

1. شناسه‌ی یکتا برای بلاک انتخاب کنید (مثل `[my-service-otp]`).
2. آدرس URL، متد، بدنه و هدرها را مطابق مستندات آن سرویس وارد کنید.
3. اگر سرویس نیاز به استخراج Nonce دارد، `warmup` و `extract_nonce` را تنظیم کنید.
4. در صورت نیاز به ترتیب اجرا، از `depends_on` استفاده کنید.

مثال ساده برای یک سرویس JSON:

```ini
[my-service-otp]
name = My Service OTP
url = https://api.example.com/v1/otp
method = POST
body = {"phone": "{{phone}}"}
headers = {
  "Content-Type": "application/json",
  "Authorization": "Bearer token"
}
warmup = https://example.com/
expected_fields = status, message
```

---

## 📊 خروجی نتایج

نمونه خروجی در `result.txt`:

```text
=== API Test Results ===
Date: 2026-06-29 20:30:00
Phone: 09123456789
Total: 4

Summary: 4 passed, 0 rate-limited, 0 failed, 0 errors, 0 skipped

============================================================

[alibaba-otp] Alibaba.ir OTP
  URL: https://ws.alibaba.ir/api/v3/account/mobile/otp
  Method: POST
  Status: SUCCESS (HTTP 200)
  Time: 2026-06-29 20:30:01
  Response:
    {
        "result": {
            "tempToken": "abc123",
            "message": "کد تأیید ارسال شد"
        }
    }
```

---

## 🔒 نکات امنیتی

- هرگز شماره تلفن واقعی یا اطلاعات حساس را در مخزن گیت کامیت نکنید. از شماره‌های نمونه استفاده کنید.
- فایل‌های `api.txt` و `result.txt` را در `.gitignore` قرار دهید تا به‌طور تصادفی منتشر نشوند.
- اگر به‌تازگی اطلاعات حساسی را کامیت کرده‌اید، از `git filter-repo` یا `git reset` برای پاک کردن تاریخچه استفاده کنید.

---

## 🐛 رفع اشکال

### خطای `not a valid cellphone`
اطمینان حاصل کنید که شماره به فرمت درست ارسال می‌شود. برای سرویس‌هایی که شماره بین‌المللی می‌خواهند، از `{{phone_clean}}` (بدون صفر اول) استفاده کنید.

### خطای `400 Bad Request`
بدنه و هدرها را با مستندات سرویس تطبیق دهید. ممکن است نیاز به Nonce یا توکن داشته باشید که باید از صفحه‌ی `warmup` استخراج شود.

### خطای `403 Forbidden`
ممکن است محدودیت نرخ (Rate Limit) اعمال شده باشد یا IP شما مسدود شده است. صبر کنید و دوباره تست کنید.

---

## 🤝 مشارکت

اگر سرویس جدیدی اضافه کردید یا بهبودی در کد اعمال نمودید، خوشحال می‌شویم که Pull Request شما را ببینیم.

---

## 📜 مجوز

این پروژه تحت مجوز MIT منتشر شده است. استفاده تجاری و غیرتجاری آزاد است.

---

## ⚠️ سلب مسئولیت (Disclaimer)

استفاده از این ابزار صرفاً برای اهداف آموزشی، تست امنیتی و تحلیل مجاز است.

- این ابزار به‌منظور تست خودکار و تحلیل پاسخ‌های API سرویس‌های مختلف طراحی شده است.
- هیچ‌گونه استفادهٔ غیرمجاز، اسپم، ارسال انبوه درخواست، نقض حریم خصوصی، یا تلاش برای دور زدن محدودیت‌های سرویس‌ها توسط این ابزار پشتیبانی نمی‌شود.
- کاربر مسئول رعایت کامل قوانین و مقررات (Terms of Service) هر سرویس‌دهنده است.
- توسعه‌دهندهٔ این پروژه هیچ‌گونه مسئولیتی در قبال سوءاستفاده، خسارت‌های ناشی از استفادهٔ نادرست، مسدود شدن حساب‌ها، یا هرگونه عواقب قانونی و امنیتی ندارد.
- از این ابزار برای تست روی شماره‌های خود یا با اجازهٔ صریح مالک استفاده کنید.
- ارسال درخواست‌های مکرر و پشت سر هم ممکن است منجر به مسدود شدن IP یا شماره تلفن شما شود؛ بنابراین با فاصله‌ی زمانی مناسب تست کنید.

با استفاده از این ابزار، شما می‌پذیرید که تمامی مسئولیت‌های قانونی و اخلاقی بر عهدهٔ خودتان است و توسعه‌دهنده هیچ‌گونه تعهدی در قبال عواقب استفاده از آن ندارد.

---

## 📬 تماس

برای سوالات یا پیشنهادات، لطفاً یک Issue در گیت‌هاب باز کنید  

---

ساخته شده با ❤️ برای جامعه توسعه‌دهندگان ایرانی
