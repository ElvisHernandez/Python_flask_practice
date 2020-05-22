from flask import render_template, current_app,g
from flask_mail import Mail, Message
from threading import Thread

def send_async_email(app, msg):
    print ("We're in the async email function")
    with app.app_context():
        mail.send(msg)

def send_email(to, subject, template, **kwargs):
    try:
        print ("We're in the send email function")
        app = current_app._get_current_object()
        msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + subject,
                  sender=app.config['FLASKY_MAIL_SENDER'], recipients=[to])
        msg.html = render_template(template + '.html', **kwargs)
        thr = Thread(target=send_async_email, args=[app, msg])
        thr.start()
        return thr
    except:
        print ('The email is not sending properly')

from . import mail