
class nagger:


    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    SPREADSHEET_ID = None
    #RANGE_NAME = 'Sheet1!A1:E'
    PICKLE_FILE_NAME  =  "abafilterSpreadsheetToken.pickel"

    creds = None

    data = []

    def __init__(self, spreadsheetId):

        self.SPREADSHEET_ID = spreadsheetId

        if os.path.exists(WORKING_DIR+"/"+self.PICKLE_FILE_NAME):
            with open(WORKING_DIR+"/"+self.PICKLE_FILE_NAME, 'rb') as token:
                self.creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    WORKING_DIR+'/credentials.json', self.SCOPES)
                self.creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(WORKING_DIR+"/"+self.PICKLE_FILE_NAME, 'wb') as token:
                pickle.dump(self.creds, token)
