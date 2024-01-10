import os
import base64
import re
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from bs4 import BeautifulSoup
from nltk import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from nltk.tokenize.treebank import TreebankWordDetokenizer

# Set up NLTK
stop_words = set(stopwords.words('english'))

def clean_html(html_text):
    soup = BeautifulSoup(html_text, 'html.parser')
    return soup.get_text()

def preprocess_text(text):
    text = re.sub(r'\s+', ' ', text)  # Remove extra spaces
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    return text

def get_summary(text, ratio=0.2):
    sentences = sent_tokenize(text)
    words = word_tokenize(text)
    words = [word.lower() for word in words if word.isalpha() and word.lower() not in stop_words]
    
    frequency_dist = FreqDist(words)
    sorted_freq_dist = sorted(frequency_dist.items(), key=lambda x: x[1], reverse=True)
    
    summary_length = int(len(sentences) * ratio)
    selected_sentences = sorted_freq_dist[:summary_length]
    selected_sentences = [sentence[0] for sentence in selected_sentences]
    
    detokenizer = TreebankWordDetokenizer()
    summary = detokenizer.detokenize(selected_sentences)
    
    return summary

# Set up Gmail API
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
API_CREDENTIALS_FILE = 'C:/Users/steve/Downloads/Gmail Summary/credentials.json'
TOKEN_FILE = 'token.json'

def setup_gmail_api():
    flow = InstalledAppFlow.from_client_secrets_file(API_CREDENTIALS_FILE, SCOPES)
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    return creds

def read_email(service, user_id, msg_id):
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id).execute()
        return message
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def main():
    creds = setup_gmail_api()
    service = build('gmail', 'v1', credentials=creds)

    user_id = 'me'  # 'me' represents the authenticated user
    msg_id = 'YOUR_EMAIL_ID'  # Replace with the ID of the email you want to summarize

    email = read_email(service, user_id, msg_id)

    if email:
        # Extract email content
        if 'data' in email['payload']['body']:
            email_body = base64.urlsafe_b64decode(email['payload']['body']['data']).decode('utf-8')
        elif 'parts' in email['payload']:
            email_body = base64.urlsafe_b64decode(email['payload']['parts'][0]['body']['data']).decode('utf-8')
        else:
            print("Unable to extract email content.")
            return

        # Clean HTML and preprocess text
        cleaned_text = clean_html(email_body)
        preprocessed_text = preprocess_text(cleaned_text)

        # Summarize the email
        summary = get_summary(preprocessed_text)
        print("Email Summary:")
        print(summary)

if __name__ == '__main__':
    main()
