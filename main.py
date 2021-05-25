import os
import re
import base64
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def getService():

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)

    return service

def getRequiredLabelID(serviceObj, labelName):
    responseObj = serviceObj.users().labels().list(userId="me").execute()
    labelList = responseObj.get('labels', [])

    reqId = None

    for label in labelList:
        if label['name'] == labelName:
            reqId = label['id']

    return reqId

def getMessagesIds(serviceObj, labelId, maxAmt):
    responseObj = serviceObj.users().messages().list(userId='me', maxResults=maxAmt, labelIds=[labelId]).execute()
    messages = responseObj.get('messages', [])

    messageIdList = []

    for message in messages:
        messageIdList.append(message['id'])

    return messageIdList

def getMessageBody(serviceObj, messageIds):

    messages = []

    for mId in messageIds:
        responseObj = serviceObj.users().messages().get(userId='me', id=mId).execute()
        payload = responseObj.get('payload', {})
        headers = payload.get('headers', [])
        messageBody = payload.get('parts')[0].get('body').get('data')

        for header in headers:
            if header['name'] == 'Subject':
                fileName = header['value']
                break
        
        decodedBody = base64.urlsafe_b64decode(messageBody.encode("utf-8")).decode("utf-8")

        messages.append({'name':fileName, 'body':decodedBody})
    

    return messages

def createFiles(problems):
    foldername = './problems/'
    for problem in problems:
        filename = problem.get('name')[21:] +'.cpp'
        pathname = foldername+filename
        print(filename)
        text = problem.get('body')

        question = re.split('-'*80, text)[0]

        # commenting the text
        question = '/*' + question + '*/'

        with open(pathname, 'w') as f:
            print('File Created')
            f.write(question)
        


if __name__ == "__main__":
    srv = getService()
    labelId = getRequiredLabelID(srv, 'Daily Coding Problem')
    mIDList = getMessagesIds(srv, labelId, 4)
    mess = getMessageBody(srv, mIDList)
    # print(mess)
    createFiles(mess)

