import sys
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient.http import MediaFileUpload



if __name__ == '__main__':

    print ("######## log saver ########")
    
    if len(sys.argv) < 4:
        print ("ussage logsaver WORKING_DIR logfile prefix")
    
    WORKING_DIR = sys.argv[1]
    logfile = sys.argv[2]
    prefix = sys.argv[3]

    SCOPES = ['https://www.googleapis.com/auth/drive']
    PICKLE_FILE_NAME  =  "abafilterLogsaverToken.pickle"

    creds = None

    if os.path.exists(WORKING_DIR+"/"+PICKLE_FILE_NAME):
        with open(WORKING_DIR+"/"+PICKLE_FILE_NAME, 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                WORKING_DIR+'/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(WORKING_DIR+"/"+PICKLE_FILE_NAME, 'wb') as token:
            pickle.dump(creds, token)

    service = build('drive', 'v3', credentials=creds)

    filename = logfile.split("/")[-1]
    filename = prefix + "_" + filename

    print ("uploading", filename)

    file_metadata = {'name': filename}
    media = MediaFileUpload(logfile,
                            mimetype='text/plain')
    file = service.files().create(body=file_metadata,
                                        media_body=media,
                                        fields='id').execute()
    print ('File ID: %s' % file.get('id'))

    
    
