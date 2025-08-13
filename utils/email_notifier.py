import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

def send_completion_email(recipient_email, success_count, total_count, process_name="Scraping"):
    """Send email notification when scraping is completed"""
    
    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASS")
    
    if not sender_email or not sender_password:
        print("❌ Email credentials not found in .env file")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = f"📈 Daily Stock Scraping Complete - {datetime.now().strftime('%m/%d/%Y')}"
        
        # Email body
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        date_str = datetime.now().strftime('%B %d, %Y')
        body = f"""
🎉 Daily Stock Data Scraping Complete!

Hi Dan,

Your daily scraping process has finished successfully for {date_str}.

📊 Today's Results:
• Total active tickers processed: {total_count}
• Successful data records: {success_count}
• Success rate: {(success_count/total_count*100):.1f}%
• Completed at: {current_time}

✅ All fresh stock data has been updated in your database and is ready for analysis.

Best regards,
Your Stock Scraper Bot
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email using Gmail SMTP
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email notification sent to {recipient_email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email notification: {e}")
        return False