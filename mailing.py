import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email( to_email, info):
    # Email configuration
    from_email = "bhadri2919@gmail.com"  # Replace with your email
    from_password = "szaafkywoeklhlec"  # Replace with your email's app password

    try:
        # Create the email
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = 'Appointment Confirmation'
        body = info
        msg.attach(MIMEText(body, 'plain'))

        # Connect to the Gmail SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Start TLS encryption
        server.login(from_email, from_password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()

        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")