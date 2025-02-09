from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, send_file, session
from flask_cors import CORS
import google.generativeai as genai
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
import os
from dotenv import load_dotenv
import io
import json
import re
from datetime import datetime

# إضافة مكتبة reportlab
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from arabic_reshaper import reshape  # Import arabic_reshaper
from bidi.algorithm import get_display  # Import bidi algorithm


load_dotenv()

app = Flask(__name__, static_folder='.', static_url_path='')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'
db = SQLAlchemy(app)


class User1(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)  
    
    def __repr__(self):
        return f"<User(username='{self.username}')>"

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user1.id'), nullable=False) 
    rating = db.Column(db.Integer, default=0) # Default rating
    file_location = db.Column(db.String(255), nullable=False)
    
    user = db.relationship('User1', backref='files')

    def __repr__(self):
        return f"<File(id='{self.id}', user_id='{self.user_id}')>"

    def average_rating(self):
        ratings = [rating.rating for rating in self.ratings]
        if ratings:
            return sum(ratings) / len(ratings)
        return 0

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user1.id'), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('file.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)

    user = db.relationship('User1', backref='ratings')
    file = db.relationship('File', backref='ratings')
    def __repr__(self):
         return f"<Rating(id='{self.id}', user_id='{self.user_id}', file_id='{self.file_id}', rating='{self.rating}')>"
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user1.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    message_type = db.Column(db.String(50),nullable=False,default='text')
    file_location = db.Column(db.String(255),nullable=True) # For file messages
    
    # Define a relationship with the User1 model for easier querying
    sender = db.relationship('User1', backref='messages')
    
    def __repr__(self):
        return f"<Message(id='{self.id}', sender_id='{self.sender_id}')>"
        
with app.app_context():
    db.create_all()

CORS(app)

GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("No API key found, please set it in the .env file")

genai.configure(api_key=GOOGLE_API_KEY)

model = genai.GenerativeModel('gemini-pro')

def classify_text(text):
    try:
        prompt = f"""
        بناءً على نموذج التصميم التعليمي للدكتور محمد عطية خميس، قم بتحليل الإجابات التالية وإنشاء تصميم تعليمي مفصل ومنظم. يجب أن يشمل التصميم المراحل التالية:
        1.  **مرحلة التحليل:**
            *   تحديد المشكلة واحتياجات التعلم.
            *   تحديد خصائص المتعلمين.
            *   تحديد المهام الأساسية والمحتوى.
        2.  **مرحلة التصميم:**
            *   تحديد أهداف التعلم.
            *   تصميم بنية المحتوى.
            *   تحديد أساليب التقويم.
            *   تحديد استراتيجيات التعلم.
        3.  **مرحلة التطوير:**
            *   تطوير المحتوى (نصوص، وسائط متعددة، مواد داعمة).
            *   تصميم الأنشطة التفاعلية (تزامنية وغير تزامنية).
        4.  **مرحلة التنفيذ:**
            *   تحديد المنصة.
            *   تحديد آليات التنفيذ.
        5.  **مرحلة التقويم:**
            *   تقييم المتعلمين (اختبارات مرحلية ونهائية).
            *   تحديد آليات التغذية الراجعة.
        6.  **مرحلة التحسين:**
            *   تحليل التغذية الراجعة.
            *   إجراء التحسينات.

        بالإضافة إلى ذلك، قم بتضمين اقتراحات للاختبارات المرحلية والاختبار النهائي، وقدم قائمة بمصادر تعليمية مفيدة، واقترح شكلًا لموقع تعليمي للموضوع.

        الأسئلة والإجابات: {text}
        
        وهذا مثال على المخرج اللى مفروض يطلع مع مراعات تغير الموضوع وتطبيقه على الاسئله والاجوبه على حسب السؤال هترد وهكذه مثال عليه

1. مرحلة التحليل
أ) تحديد المشكلة واحتياجات التعلم
المشكلة: حاجة طلاب كلية التربية إلى تعلم إنتاج العروض التقديمية باستخدام Google Slides، كمهارة تقنية تدعم التعليم الإلكتروني.
الاحتياجات:
مهارات تقنية لإنتاج العروض التقديمية.
المعرفة الأساسية ببيئة Windows.
ب) خصائص المتعلمين
السن: 20 عامًا.
المرحلة: طلاب الفرقة الثالثة، كلية التربية.
النوع: مختلط.
البيئة: غير مهم (ريف أو مدينة).
ذوي الهمم: غير مطلوب دعم إضافي حاليًا.
المتطلبات القبلية: معرفة أساسية بالتعامل مع Windows.
ج) تحديد المهام
إنشاء عرض تقديمي جديد باستخدام Google Slides.
اختيار قالب مناسب للعرض.
تغيير خلفية العرض.
إضافة النصوص للشرائح.
2. مرحلة التصميم
أ) الأهداف التعليمية
بحلول نهاية المقرر، يجب أن يكون الطلاب قادرين على:

تعريف Google Slides.
إنشاء عرض تقديمي جديد.
اختيار قالب مناسب للعرض.
تغيير خلفية العرض.
إضافة النصوص إلى الشرائح.
ب) بنية المحتوى
الموديول الأول: تعريف عروض جوجل التقديمية.
الموديول الثاني: خطوات إنشاء عرض تقديمي جديد.
الموديول الثالث: اختيار قالب للعرض.
الموديول الرابع: تغيير خلفية العرض.
الموديول الخامس: إضافة النصوص إلى الشرائح.
ج) أساليب التقييم
أدوات القياس:
أسئلة اختيار من متعدد.
أسئلة تطبيقية (تنفيذ مهمة محددة عمليًا).
توقيت الاختبار:
بعد كل موديول (اختبار مرحلي).
بعد الانتهاء من جميع الموديولات (اختبار نهائي).
د) الاستراتيجيات التعليمية
تعلم فردي: لأداء المهام الأساسية.
تعلم جماعي: مجموعات من 3-5 أفراد للتعاون في الأنشطة التطبيقية.
3. مرحلة التطوير
أ) تطوير المحتوى
نصوص تعليمية:
تعريف Google Slides.
شرح مميزات واستخدامات العروض التقديمية.
وسائط متعددة:
مقاطع فيديو توضح الخطوات العملية.
صور توضيحية للخطوات.
مواد داعمة:
ملفات Word تتضمن الشروحات المكتوبة.
تسجيلات صوتية مختصرة للتوجيه.
ب) تصميم الأنشطة التفاعلية
نشاط تزامني: لقاء عبر Google Meet لتوضيح المهمة.
نشاط غير تزامني: إرسال الواجبات عبر Gmail.
4. مرحلة التنفيذ
أ) تنفيذ المحتوى
المنصة: Google Meet وGmail.
الدعم الفني: عبر جروب WhatsApp.
آليات التنفيذ:
تقديم الموديولات كجلسات تعليمية تزامنية وغير تزامنية.
مراقبة تقدم الطلاب باستخدام الاختبارات المرحلية.
5. مرحلة التقويم
أ) تقييم المتعلمين
اختبارات مرحلية:
بعد كل موديول لقياس استيعاب الخطوات.
اختبار نهائي:
يختبر إنشاء عرض تقديمي كامل.
سؤال نموذجي: "يمكن إضافة شريحة جديدة بكل الطرق التالية ماعدا:..."
الإجابات: أ) قائمة إدراج، ب) قائمة شريحة، ج) قائمة الإضافات، د) الزر الأيمن.
ب) التغذية الراجعة
جمع ملاحظات الطلاب عن سهولة استخدام المحتوى.
تقييم مدى تحقيق الأهداف التعليمية.
6. مرحلة التحسين
تحليل التغذية الراجعة: مراجعة ملاحظات الطلاب والمدرسين.
إجراء تحسينات:
تحديث المحتوى بناءً على تعليقات المستخدمين.
تحسين الأنشطة التفاعلية.




اقتراحات للاختبارات

1. الاختبارات المرحلية
موديول 1: تعريف Google Slides
سؤال 1: اختر الإجابة الصحيحة:
ما هي عروض Google Slides؟
أ) أداة لتحرير النصوص.
ب) أداة لإنشاء العروض التقديمية.
ج) أداة لتحرير الصور.
د) أداة لتخزين الملفات.

سؤال 2: اذكر وظيفتين أساسيتين لعروض Google Slides.

موديول 2: إنشاء عرض تقديمي جديد
سؤال 1: رتب الخطوات التالية لإنشاء عرض تقديمي جديد باستخدام Google Slides:

افتح قائمة "+ جديد".
افتح متصفح Google Chrome.
سجل الدخول إلى بريدك الإلكتروني.
اختر Google Slides.
(الإجابة الصحيحة: 2 - 3 - 1 - 4).
سؤال 2 (عملي): قم بإنشاء عرض تقديمي جديد واحفظه باسم "اختبار Google".

موديول 3: اختيار قالب مناسب
سؤال 1: اختر الإجابة الصحيحة:
لتغيير قالب العرض التقديمي، يجب أن تستخدم:
أ) قائمة File.
ب) قائمة Slide واختيار Change Theme.
ج) قائمة Edit.
د) قائمة View.

سؤال 2: قم بتحديد الفرق بين القالب الافتراضي والقوالب الجانبية في Google Slides.

موديول 4: تغيير الخلفية
سؤال 1: ما الخطوة الأولى لتغيير خلفية العرض التقديمي؟
أ) فتح قائمة File.
ب) فتح قائمة View.
ج) اختيار Change Background.
د) فتح قائمة Edit.

سؤال 2 (عملي): قم بتغيير لون الخلفية إلى اللون الأزرق في شريحة من اختيارك.

موديول 5: إضافة النصوص إلى الشرائح
سؤال 1: أكمل الجملة:
لإضافة نص إلى شريحة، يجب النقر على ... ثم كتابة النص.
(الإجابة: مربع النص Text Box).

سؤال 2 (عملي): أضف النص التالي إلى شريحة جديدة:
"مرحبًا بكم في تعلم Google Slides!"

2. الاختبار النهائي
مدة الاختبار: 30 دقيقة
عدد الأسئلة: 5 (مزيج من اختيار من متعدد، وأسئلة تطبيقية)

السؤال 1 (اختيار من متعدد):
يمكن إضافة شريحة جديدة بكل الطرق التالية ما عدا:
أ) قائمة إدراج Insert ثم شريحة جديدة.
ب) قائمة شريحة Slide ثم شريحة جديدة.
ج) قائمة الإضافات Add-ons ثم شريحة جديدة.
د) الزر الأيمن Right-click ثم شريحة جديدة.
(الإجابة: ج)

السؤال 2 (اختيار من متعدد):
ما هي الخطوة الأخيرة لتغيير خلفية شريحة في Google Slides؟
أ) اختيار اللون.
ب) النقر على Apply.
ج) اختيار Change Background.
د) فتح قائمة View.
(الإجابة: ب)

السؤال 3 (أسئلة تطبيقية):
قم بما يلي:

إنشاء عرض تقديمي جديد.
أضف شريحة جديدة بعنوان "اختبار Google".
غيّر خلفية الشريحة إلى اللون الأخضر.
السؤال 4 (كتابي):
اذكر خطوتين أساسيتين لاختيار قالب جديد للعرض التقديمي.

السؤال 5 (عملي):
قم بتحميل ملف Google Slides يحتوي على 3 شرائح:

الشريحة الأولى: تحتوي على نص "مرحبًا بكم".
الشريحة الثانية: خلفيتها زرقاء.
الشريحة الثالثة: تستخدم قالبًا مختلفًا.
ملاحظات للتنفيذ
الاختبارات العملية يمكن أن تكون عبر إرسال الواجبات على Gmail.
الأسئلة الكتابية واختيارات متعددة يمكن إجراؤها باستخدام Google Forms أو أي أداة تقييم إلكترونية.
هل ترغب في تفاصيل إضافية عن كيفية تصميم هذه الاختبارات رقميًا أو إعداد Google Forms؟




مصادر

1. مصادر تعليمية حول Google Slides
أ) مقاطع فيديو تعليمية
قناة Google Workspace على YouTube

تحتوي على شروحات تفصيلية حول كيفية استخدام جميع أدوات Google، بما في ذلك Google Slides.
رابط القناة
Simpletivity YouTube Channel

قناة تقدم دروسًا مبسطة عن Google Slides وطرق تحسين العروض التقديمية.
Simpletivity Channel
ب) أدلة مكتوبة
دليل Google Slides الرسمي

يحتوي على إرشادات خطوة بخطوة مدعومة بالصور.
Google Slides Help Center
دروس مجانية على موقع GCF Global

يشرح بالتفصيل كيفية استخدام Google Slides من الصفر.
GCF Google Slides Tutorial
2. تصميم الاختبارات الإلكترونية
أ) أدوات لإنشاء اختبارات تفاعلية
Google Forms

أداة مجانية لإنشاء اختبارات واختيارات متعددة مع تقييم تلقائي.
ابدأ باستخدام Google Forms
Quizizz

منصة لإنشاء اختبارات تفاعلية ومرحة، مثالية لتقييم الطلاب.
Quizizz
Kahoot!

أداة تعليمية تفاعلية مثالية لخلق مسابقات واختبارات في الوقت الفعلي.
Kahoot!
3. مصادر لإنشاء المحتوى
أ) قوالب جاهزة لـ Google Slides
Slides Carnival

موقع يقدم قوالب مجانية احترافية لـ Google Slides.
Slides Carnival
Template.net

يحتوي على مجموعة واسعة من القوالب التعليمية.
Template.net
ب) تصميم الرسوم والوسائط
Canva

لإنشاء صور ورسوميات احترافية يمكن إدراجها في Google Slides.
Canva
Unsplash

مكتبة ضخمة من الصور المجانية عالية الجودة.
Unsplash
4. مصادر أكاديمية حول التصميم التعليمي
كتاب: "التصميم التعليمي للتعلم الإلكتروني" - تأليف الدكتور محمد عطيو خميس

يعد مرجعًا شاملاً لتصميم المناهج الإلكترونية باستخدام التكنولوجيا.
موقع Instructional Design.org

يحتوي على مقالات متخصصة في التصميم التعليمي ونماذجه.
Instructional Design
5. موارد إضافية
LinkedIn Learning

يقدم دورات شاملة حول Google Slides وتقنيات التعليم الإلكتروني.
LinkedIn Learning
Coursera

دورات تعليمية مقدمة من جامعات عالمية عن التصميم التعليمي وتقنيات التدريس.
Coursera




اقتراح لتصميم موقع تعليمي

تصميم موقع تعليمي لتعلم Google Slides
1. الصفحة الرئيسية (Home Page)
العناصر الأساسية:
عنوان رئيسي جذاب: "ابدأ رحلتك مع Google Slides الآن!"
وصف مختصر: "تعلم كيفية إنشاء عروض تقديمية احترافية باستخدام أدوات Google الحديثة بأسلوب سهل وتفاعلي."
دعوة للعمل (CTA):
"ابدأ الآن" (زر للتسجيل).
"عرض المحتوى المجاني" (زر لتصفح المحتوى).
فيديو ترحيبي: مقطع فيديو قصير يشرح الهدف من الموقع.
2. صفحة "عن الدورة" (About the Course)
وصف شامل للدورة التعليمية:
الفئة المستهدفة: طلاب الجامعات والمعلمين.
الأهداف التعليمية:
تعريف Google Slides.
إنشاء عروض تقديمية احترافية.
استخدام القوالب وتخصيص الخلفيات.
مدة الدورة: 5 موديولات (2-3 ساعات).
الشهادات: شهادة إتمام معتمدة.
3. صفحة المحتوى التعليمي (Course Content)
هيكل الموديولات:

موديول 1: التعريف بـ Google Slides.
موديول 2: إنشاء عرض تقديمي جديد.
موديول 3: اختيار القوالب.
موديول 4: تغيير الخلفية.
موديول 5: إضافة النصوص والتخصيص.
داخل كل موديول:

فيديو تعليمي: خطوة بخطوة.
نص مكتوب: شرح مدعوم بالصور.
تمارين عملية: لتنفيذ المهارات المكتسبة.
اختبارات قصيرة: لقياس الفهم المرحلي.
4. صفحة الأنشطة التفاعلية (Interactive Activities)
نشاطات تزامنية:
جلسات مباشرة عبر Google Meet.
مناقشات حية باستخدام أدوات مثل Zoom أو MS Teams.
نشاطات غير تزامنية:
تحميل الواجبات من خلال الموقع.
لوحة مناقشة (Discussion Board) لطرح الأسئلة والإجابة عليها.
5. صفحة التقييمات (Assessments)
الاختبارات المرحلية:
أسئلة اختيار من متعدد وأسئلة تطبيقية بعد كل موديول.
الاختبار النهائي:
يشمل اختبارًا عمليًا لتحميل عرض تقديمي مكتمل.
لوحة التقييم: تعرض درجات الطالب مع ملاحظات تفصيلية.
6. صفحة الدعم (Support)
أقسام الدعم:
أسئلة شائعة (FAQs): حلول للمشاكل الشائعة.
تواصل معنا: نموذج إرسال استفسارات (اسم، بريد إلكتروني، الرسالة).
روابط مباشرة: لمصادر التعلم الخارجية مثل أدلة Google الرسمية.
7. صفحة الإنجازات (Achievements)
شهادات إتمام الدورة:
يمكن للطلاب تحميل شهادة PDF بمجرد إنهاء جميع الموديولات والاختبار النهائي.
لوحة عرض الإنجازات:
قائمة بالأنشطة المكتملة والاختبارات.
تصميم الواجهة (UI/UX)
الألوان والتصميم
ألوان مريحة ومرتبطة بجوجل: الأبيض مع ألوان Google (الأزرق، الأحمر، الأخضر، الأصفر).
خطوط بسيطة وسهلة القراءة.
أيقونات جذابة: للتنقل السريع بين الأقسام.
تجربة المستخدم (UX)
قائمة تنقل واضحة:
"الصفحة الرئيسية"، "عن الدورة"، "المحتوى"، "الأنشطة"، "التقييمات"، "الدعم".
إمكانية الوصول:
دعم ذوي الاحتياجات الخاصة (مثل النصوص البديلة، تكبير النص).
توافق مع الجوال:
تصميم مستجيب (Responsive Design) لجميع الأجهزة.
ميزات إضافية
نظام نقاط وتشجيع:
يكسب الطلاب نقاطًا لكل مهمة مكتملة.
منتدى للطلاب:
للتفاعل وتبادل الأفكار.
مدونة تعليمية:
مقالات تعليمية عن التصميم التقديمي وأفضل الممارسات.
        """
        response = model.generate_content([prompt])
        return response.text
    except Exception as e:
        print(f"Error: {e}")
        return "Error processing text"

def create_pdf(title, content):
    buffer = io.BytesIO()

    # Register the Arabic font
    pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))  # Make sure 'arial.ttf' is in the same dir

    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    styles = getSampleStyleSheet()
    style = styles["Normal"]
    style.fontName = "Arial"
    style.fontSize = 18  # Increase font size
    style.alignment = TA_RIGHT
    style.wordWrap = 'CJK'
    style.leading = 26  # Increase line spacing


    story = []
    
    # Add Title to PDF
    title_style = styles["h1"]
    title_style.fontName = "Arial"
    title_style.alignment = TA_CENTER
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 18))  # Increase space after title


    # Process and add the content
    paragraphs = content.split('\n')
    current_section = []
    for paragraph in paragraphs:
      paragraph = paragraph.replace('*','•')
      reshaped_paragraph = reshape(paragraph)
      bidi_paragraph = get_display(reshaped_paragraph)
      if bidi_paragraph.strip():
          current_section.append(Paragraph(bidi_paragraph, style))
      else:
          # If empty line add section spacing
           if current_section:
            story.extend(current_section)
            story.append(Spacer(1, 12)) # Space between sections
            current_section = []

    if current_section:
        story.extend(current_section)
        story.append(Spacer(1, 12))


    doc.build(story)

    buffer.seek(0)
    return buffer

@app.route('/classify', methods=['POST'])
def classify():
    try:
        data = request.get_json()
        
        if 'questions_and_answers' not in data:
            return jsonify({'error': 'No questions and answers provided'}), 400

        questions_and_answers = data['questions_and_answers']
        print(questions_and_answers)
        classification_result = classify_text(questions_and_answers)
        cleaned_text = re.sub(r'[^\u0600-\u06FF\s\w\*\.\-:]', '', classification_result)


        
        topic =  list(json.loads(questions_and_answers).items())[0][1]
        

        pdf_buffer = create_pdf("Document" , cleaned_text)
        
        if pdf_buffer:
            # Generate a unique file name
            file_name = f"{topic}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
            file_path = os.path.join(".", file_name)

            # Save the file to disk
            with open(file_path, 'wb') as f:
                f.write(pdf_buffer.getvalue())

            # Get the user id from session if user is logged in
            user_id = session.get('user_id')
            if user_id:
                 # Create a file entry in the database
                new_file = File(user_id=user_id, file_location=file_path, rating=0)  # Default rating 0
                db.session.add(new_file)
                db.session.commit()
            
            return send_file(
            file_path,
            as_attachment=True,
            download_name=f'{topic}.pdf',
            mimetype='application/pdf'
            )
        else:
            return jsonify({'error': 'Failed to generate PDF'}), 500

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User1.query.filter_by(username=username,password=password).first()
        if user :
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('files_page'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        new_user = User1(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('User added successfully!', 'success')
        return redirect(url_for('add_user')) 

    users = User1.query.all()
    return render_template('add_user.html', users=users)

@app.route('/logout')
def logout():
  session.pop('user_id', None)
  return redirect(url_for('login'))
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/form')
def form():
    return render_template('form.html')

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
         content = request.form.get('message') # get message content
         message_type = 'text'

         user_id = session.get('user_id')

         # Handle file upload
         if 'file' in request.files:
            file = request.files['file']
            
            if file and file.filename != '':
              # Generate a unique file name
              file_name = f"chat_file_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
              file_path = os.path.join(".", file_name)
              file.save(file_path) # Save the file to disk
              message_type = "file"
              content = file.filename
         # Handle image upload
         if 'image' in request.files:
             image = request.files['image']
            
             if image and image.filename != '':
               # Generate a unique file name
               image_name = f"chat_image_{datetime.now().strftime('%Y%m%d%H%M%S')}_{image.filename}"
               image_path = os.path.join(".", image_name)
               image.save(image_path) # Save the file to disk
               message_type = "image"
               content = image_name

         if user_id:
           if message_type == 'text':
            #save a text message
              new_message = Message(sender_id=user_id, content=content,message_type=message_type)
           else:
            #save a file message or image message
              new_message = Message(sender_id=user_id, content=content,message_type=message_type, file_location = file_path if message_type == "file" else image_path )
           db.session.add(new_message)
           db.session.commit()


         return redirect(url_for('chat'))
    # Fetch messages from database
    messages = Message.query.order_by(Message.timestamp).all()
    return render_template('chat.html', messages=messages)



@app.route('/files', methods=['GET', 'POST'])
def files_page():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    user_files = File.query.filter_by(user_id=user_id).all()
    all_files = File.query.all()

    if request.method == 'POST':
        file_id = request.form.get('file_id')
        rating_value = request.form.get('rating')  # Changed to rating_value for clarity

        if file_id and rating_value:
            file_id = int(file_id)
            rating_value = int(rating_value)  # Convert to integer

            # Check if the user already rated the file
            existing_rating = Rating.query.filter_by(user_id=user_id, file_id=file_id).first()

            if existing_rating:
                existing_rating.rating = rating_value  # Update existing rating
                flash('Your rating was updated!', 'success')
            else:
                new_rating = Rating(user_id=user_id, file_id=file_id, rating=rating_value)
                db.session.add(new_rating)
                flash('Rating submitted successfully!', 'success')

            db.session.commit()  # Commit the changes

        return redirect(url_for('files_page'))

    return render_template('files.html', user_files=user_files, all_files=all_files)

if __name__ == '__main__':
    with app.app_context():
        # Add this line to delete the database file before creating all tables
        if os.path.exists('users.db'): # تعديل هنا لاستخدام users.db
             os.remove('users.db')
        db.create_all()
    app.run()
