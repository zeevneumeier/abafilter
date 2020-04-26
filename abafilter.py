import os
import re
import json
import sys
from pprint import pprint
import time
import pytz
import threading
import pickle
from datetime import datetime
import calendar
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from tinydb import TinyDB, Query
import random
from gtts import gTTS
import io
import pygame
import hashlib
import pydub

DATETIME_PRINT_FORMAT = "%m/%d/%Y %H:%M:%S"
CLEANUP_LOOP_INTERVAL = 5*60
RESTART_INTERVAL = 12*60*60

WORKING_DIR = "./"

class spreadsheetSaver:

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    SPREADSHEET_ID = None
    #RANGE_NAME = 'Sheet1!A1:E'
    PICKLE_FILE_NAME  =  "abafilterSpreadsheetToken.pickle"
    
    creds = None
    service = None
    
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
                
                
        self.service = build('sheets', 'v4', credentials=self.creds)
        
    def getNaggingSettings(self):
    
        naggingSettingsTabName = "nagging settings"
    
        sheet = self.service.spreadsheets()
        
        #first check if we need to create a the sheet
        sheet_metadata = sheet.get(spreadsheetId=self.SPREADSHEET_ID).execute().get('sheets', '')
        sheetNames = [o["properties"]["title"] for o in sheet_metadata]
        if naggingSettingsTabName not in sheetNames:
        
            print("INFO: spreadsheetSaver.getNaggingSettings(): adding tab ", naggingSettingsTabName)
            body = {
                'requests': [{
                    "addSheet": {
                    "properties": {
                      "title": naggingSettingsTabName
                      }
                    }
                }]
            }
            result = self.service.spreadsheets().batchUpdate(
            spreadsheetId=self.SPREADSHEET_ID,
            body=body).execute()
            
        naggingSettings = sheet.values().get(spreadsheetId=self.SPREADSHEET_ID, range=naggingSettingsTabName, majorDimension="COLUMNS").execute().get('values', [])
        
        ret = []
        
        for col in naggingSettings:
            if len(col) < 5 or len(col[0].strip()) <= 0:
                continue
            
            domain = col[0]
            
            try:
                ret.append(nagger(domain, col[1], col[2], col[3], col[4:]))
            except Exception as e:
                print("spreadsheetSaver.getNaggingSettings() ERROR:" + domain)
                print(e)
            
            
            
        
        for r in ret:
            print(r)
            
        return ret
        
                
    def dumpUssage(self, sessions):
        
        now = datetime.now()
        cal= calendar.Calendar()
        
        currentHoursTab = "%02d-%i-hourly" % (now.month, now.year)
        currentDayTab = "%02d-%i" % (now.month, now.year)
        
        #rangeName = currentTab

        # Call the Sheets API
        sheet = self.service.spreadsheets()
        #result = sheet.values().get(spreadsheetId=self.SPREADSHEET_ID, range=rangeName).execute()
        #values = result.get('values', [])
        
        #first check if we need to create a the sheet
        sheet_metadata = sheet.get(spreadsheetId=self.SPREADSHEET_ID).execute().get('sheets', '')
        sheetNames = [o["properties"]["title"] for o in sheet_metadata]
        if currentHoursTab not in sheetNames:
        
            print("INFO: spreadsheetSaver.dumpUssage(): adding tab ", currentHoursTab)
            body = {
                'requests': [{
                    "addSheet": {
                    "properties": {
                      "title": currentHoursTab
                      }
                    }
                }]
            }
            result = self.service.spreadsheets().batchUpdate(
            spreadsheetId=self.SPREADSHEET_ID,
            body=body).execute()
            
        if currentDayTab not in sheetNames:
            print("INFO: spreadsheetSaver.dumpUssage(): adding tab ", currentDayTab)
            body = {
                'requests': [{
                    "addSheet": {
                    "properties": {
                      "title": currentDayTab
                      }
                    }
                }]
            }
            result = self.service.spreadsheets().batchUpdate(
            spreadsheetId=self.SPREADSHEET_ID,
            body=body).execute()
        
        
        #print (values)
        
        columns = []
        dayColumns = []
        temp = cal.itermonthdates(now.year, now.month)
        days = []
        domains = {}
        columnDataList = []
        dayColumnDataList = []
        columnHeading = []
        dayColumnHeading = []
        for day in temp:
            if day.month == now.month:
                #days.append(datetime.combine(day,datetime.min.time()).replace(tzinfo=pytz.timezone('US/Pacific')))
                days.append(datetime.combine(day,datetime.min.time()))
        
        for day in days:
            temp = day.replace(hour=0, minute=0, second=0, microsecond=0)
            dayColumns.append(temp)
            dayColumnHeading.append(day.strftime("%m/%d/%Y"))
            
            for h in range (24):
                temp = day.replace(hour=h, minute=0, second=0, microsecond=0)
                #print (temp.timestamp(), temp.strftime(DATETIME_PRINT_FORMAT))
                columns.append(temp)
                
                columnHeading.append(temp.strftime(DATETIME_PRINT_FORMAT))
        
        for col in columns:
            
            columnData = {}
            
            tsStart = col.timestamp()
            tsEnd = col.timestamp()+60*60
            total = 0
            
            results = sessions.getSessionsForTime(tsStart, tsEnd)
            
            #print ("$$$$$$$$$$$$$$$$$$$$$$$$$$", col.strftime(DATETIME_PRINT_FORMAT), col.timestamp(), col.timestamp()+60*60)
            for r in results:
                
                
                domain = r["domain"]
                contributionToThisHour = r["sessionEnd"] - r["sessionStart"]
                if r["sessionStart"] < tsStart:
                    contributionToThisHour = contributionToThisHour - (tsStart-r["sessionStart"])
                if r["sessionEnd"] > tsEnd:
                    contributionToThisHour = contributionToThisHour - (r["sessionEnd"] - tsEnd)
                
                #print (r["domain"], datetime.fromtimestamp(r["sessionStart"]).strftime(DATETIME_PRINT_FORMAT), datetime.fromtimestamp(r["sessionEnd"]).strftime(DATETIME_PRINT_FORMAT), r["sessionStart"], r["sessionEnd"], contributionToThisHour/60)
                
                '''
                if domain not in domains.keys():
                    domains[domain] = 0
                domains[domain] = domains[domain] + contributionToThisHour
                '''
                
                if domain not in columnData.keys():
                    columnData[domain] = 0
                columnData[domain] = columnData[domain]  + contributionToThisHour
                
                total = total + contributionToThisHour
              
            columnData["total"] = total
            columnDataList.append(columnData)
            
            
        for col in dayColumns:
            
            columnData = {}
            
            tsStart = col.timestamp()
            tsEnd = col.timestamp()+24*60*60
            total = 0
            
            results = sessions.getSessionsForTime(tsStart, tsEnd)
            
            #print ("$$$$$$$$$$$$$$$$$$$$$$$$$$", col.strftime(DATETIME_PRINT_FORMAT), col.timestamp(), col.timestamp()+60*60)
            for r in results:
                
                
                domain = r["domain"]
                contributionToThisDay = r["sessionEnd"] - r["sessionStart"]
                if r["sessionStart"] < tsStart:
                    contributionToThisDay = contributionToThisDay - (tsStart-r["sessionStart"])
                if r["sessionEnd"] > tsEnd:
                    contributionToThisDay = contributionToThisDay - (r["sessionEnd"] - tsEnd)
                
                #print (r["domain"], datetime.fromtimestamp(r["sessionStart"]).strftime(DATETIME_PRINT_FORMAT), datetime.fromtimestamp(r["sessionEnd"]).strftime(DATETIME_PRINT_FORMAT), r["sessionStart"], r["sessionEnd"], contributionToThisHour/60)
                
                if domain not in domains.keys():
                    domains[domain] = 0
                domains[domain] = domains[domain] + contributionToThisDay
                
                if domain not in columnData.keys():
                    columnData[domain] = 0
                columnData[domain] = columnData[domain]  + contributionToThisDay
                
                total = total + contributionToThisDay
              
            columnData["total"] = total
            dayColumnDataList.append(columnData)


            
        
        #domains = {k: v for k, v in sorted(domains.items(), key=lambda item: item[1], reverse=True)}
        domainsKeyList = [k for k, v in sorted(domains.items(), key=lambda item: item[1], reverse=True)]
        
        #first do hourly
        data = []
        data.append(["", "total"] + domainsKeyList)
        
        for c, columnData in enumerate(columnDataList):
            total = int(columnData["total"]/60)
            column = [columnHeading[c], total]
            for domain in domainsKeyList:
                if domain in columnData.keys():
                    column.append("%i"  % int(columnData[domain]/60))
                else:
                    column.append("")
            
            data.append(column)
        
        body = {
          "range": currentHoursTab,
          "majorDimension": "ROWS",
          "values": data
        }

        try:
            result = sheet.values().update(spreadsheetId=self.SPREADSHEET_ID,
            range=currentHoursTab, valueInputOption="RAW", body=body).execute()
        except Exception as err:
            print ("ERROR: spreadsheetSaver.dumpUssage failed to update sheet. Probably network error ", err)
                
        #now do daily
        data = []
        data.append(["", "total"] + domainsKeyList)
    
        for c, columnData in enumerate(dayColumnDataList):
            total = int(columnData["total"]/60)
            column = [dayColumnHeading[c], total]
            for domain in domainsKeyList:
                if domain in columnData.keys():
                    column.append("%i"  % int(columnData[domain]/60))
                else:
                    column.append("")
            
            data.append(column)
        
        body = {
          "range": currentDayTab,
          "majorDimension": "ROWS",
          "values": data
        }

        try:
            result = sheet.values().update(spreadsheetId=self.SPREADSHEET_ID,
            range=currentDayTab, valueInputOption="RAW", body=body).execute()
        except Exception as err:
            print ("ERROR: spreadsheetSaver.dumpUssage failed to update sheet. Probably network error ", err)
    
class nagger:

    startMinutes = 0
    endMinutes = 0
    domain = ""
    frequency = 0
    messages = []
    lastNag = 0
    
    def __init__(self, domain, startString, endString, frequency, messages):
        
        self.domain = domain
        self.startMinutes = int(startString.split(":")[0])*60 + int(startString.split(":")[1])
        self.endMinutes = int(endString.split(":")[0])*60 + int(endString.split(":")[1])
        self.frequency = float(frequency)
        
        self.messages = messages

    def playNag(self, message):
        
        print("nagger.playNag(%s)" % message)
        
        filename = "/tmp/abafilter_nag_%s.wav" % hashlib.md5(message.encode('utf-8')).hexdigest()
        
        if not os.path.exists(filename):
            print (filename, "not found. Generating")
        
            myobj = gTTS(text=message, lang='en', slow=False)
            myobj.save("/tmp/abafilter_nag_temp.mp3")
            sound = pydub.AudioSegment.from_mp3("/tmp/abafilter_nag_temp.mp3")
            sound.export(filename, format="wav")
        
        pygame.mixer.init(24000, -16, 1, 2048)
        clock = pygame.time.Clock()

        try:
            pygame.mixer.music.load(filename)
        except pygame.error:
            print("nagger.playNag(%s) ERROR" % message, pygame.get_error())
            return
        
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            # check if playback has finished
            clock.tick(30)
        
        print("nagger.playNag(%s) done" % message)

    def ping(self):
        
        now = datetime.now()
    
        #print("PING")
        #print(now.hour, now.minute)
        
        nowTime = int(now.hour)*60 + int(now.minute)
        
        if nowTime > self.startMinutes and nowTime <= self.endMinutes:
            
            if now.timestamp() - self.lastNag > self.frequency * 60:
            
                print ("nagger.ping(%s) nagging" % self.domain)
                self.lastNag = now.timestamp()
                
                self.playNag(random.choice(self.messages))
                
            else:
                pass
            
                #print ("nagger.ping(%s) too soon to nag again" % self.domain)
                
        

    def __str__(self):
        
        return "nagger for %s from %i to %i every %i min with %i messages" % (self.domain, self.startMinutes, self.endMinutes, self.frequency, len(self.messages))

class myDNS:

    domains = {}
    addresses = {}
    
    transactions = {}
    
    TRANSACTION_TIMEOUT = 1*60
    
    PICKLE_FILE_NAME = "abafilterDNS.pickle"
    
    def __init__(self, loadFromDisk=True):
        
        if loadFromDisk and os.path.exists(WORKING_DIR+"/"+self.PICKLE_FILE_NAME):
            with open(WORKING_DIR+"/"+self.PICKLE_FILE_NAME, 'rb') as file:
                obj = pickle.load(file)
                self.domains = obj["domains"]
                self.addresses = obj["addresses"]
    
    def askTransaction(self, transactionNum, domain):
        
        self.transactions[transactionNum] = {"domain": domain, "ts": time.time(), "numanswers": 0, "transactionNum": transactionNum}
        
    def answerTransaction(self, transactionNum, address):
    
        if transactionNum not in self.transactions.keys():
            print ("ERROR: DNS answer but no question", transactionNum)
            
        else:
            self.setAddress(self.transactions[transactionNum]["domain"], address)
            self.transactions[transactionNum]["numanswers"] = self.transactions[transactionNum]["numanswers"] + 1
    
    def answerTransactions(self, transactionNum, addresses):
    
        for address in addresses:
            self.answerTransaction(transactionNum, address)
            
    
    def setAddress(self, domain, address):
    
        if domain not in self.domains.keys():
            self.domains[domain] = set()
            
        self.domains[domain].add(address)
        
        self.addresses[address] = domain
        
    def getDomainForAddress(self, address):
        
        if address not in self.addresses.keys():
            return None
        
        return self.addresses[address]
    
    def cleanTransactions(self):
        
        print("myDNS running cleanup")
        
        deleteList = []
        now = time.time()
        keys = self.transactions.keys()
        for transactionNum in keys:
            transaction = self.transactions[transactionNum]
            if transaction["ts"] < now - self.TRANSACTION_TIMEOUT:
                if transaction["numanswers"] == 0:
                    #print ("WARNING: empty transaction timing out", transaction)
                    pass
                
                deleteList.append(transactionNum)
                
            
        for transactionNum in deleteList:
            #print ("remving transaction", self.transactions[transactionNum])
            del self.transactions[transactionNum]
                
    
    def dumpToDisk(self):
    
        print("myDNS dumping to disk")
    
        obj = {"domains": self.domains, "addresses": self.addresses}
        with open(WORKING_DIR+"/"+self.PICKLE_FILE_NAME, 'wb') as file:
            pickle.dump(obj, file)
            
    

class tcpdumpLine:
    
    #types
    UDP = "UDP"
    DNS_ASK = "DNS ASK"
    DNS_ANSWER = "DNS ANSWER"
    #DATA_SYN = "DATA_SYN"
    #DATA_FIN = "DATA_FIN"
    #DATA_OTHER = "DATA_OTHER"
    DATA = "DATA"
    
    
    raw = ""
    type = ""
    timestamp = 0
    protocol = ""
    src = ""
    srcPort = ""
    dest = ""
    destPort  = ""
    validLine = False
    transactionNum = 0
    flags = ""
    
    #DNS
    answers = []
    domain = ""

    
    regexBase = "^([0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9]*) ([^ ]*) ([^ ]*) > ([^ ]*)"
    regexUPD = regexBase + " UDP,"
    regexDNSAsk = regexBase + " ([0-9]*)[+] (A*)[?] ([^ ]*)"
    regexDNSAnswer = regexBase + " ([0-9]*) ([0-9])\/[0-9]\/[0-9] (([ACNAME]+ [^ ]*[,]* )+)"
    regexData = regexBase + " Flags \[([SAFRUP.]+)\]"

    def __init__(self, line):
        #print ("********************************************")
        #print (line)
        
        self.raw = line
        
        x = re.search(self.regexUPD, line)
        
        if x:
            #UDP
            self.type = self.UDP
            self.loadBase(x)

        x = re.search(self.regexDNSAsk, line)
        
        if x:
            #DNS ASK
            self.type = self.DNS_ASK
            self.loadBase(x)
            self.transactionNum = x.group(5)
            self.recordType = x.group(6)
            self.domain = x.group(7)
            
        x = re.search(self.regexDNSAnswer, line)
        
        if x:
        
            #DNS Answer
            self.type = self.DNS_ANSWER
            self.loadBase(x)
            self.transactionNum = x.group(5)
            
            answer = x.group(7)
            
            answerList = answer.split(",")
            
            self.answers = []
            for answer in answerList:
                answer = answer.strip()
                temp = answer.split(" ")
                self.answers.append({"recordType": temp[0], "address": temp[1].replace(",","")})
            
        x = re.search(self.regexData, line)
        
        if x:
            
            #data
            
            self.flags = x.group(5)
            self.type = self.DATA
                
            self.loadBase(x)
        
            
    def loadBase(self, x):
        self.validLine = True
        self.timestamp = x.group(1)
        self.protocol = x.group(2)
        src = x.group(3)
        self.src = src[0:src.rindex(".")]
        self.srcPort = src[src.rindex(".")+1:]
        
        dest = x.group(4)
        self.dest = src[0:dest.rindex(".")]
        self.destPort = src[dest.rindex(".")+1:]
        
    def __str__(self):
        if not self.validLine:
            return ""
    
        
        if self.type == self.UDP:
            return "UDP: " + str(self.timestamp) + " " + self.protocol + " " + self.src + " " + self.dest
        if self.type == self.DNS_ASK:
            return "DNS ASK: " + str(self.timestamp) + " " + self.protocol + " " + self.src + " " + self.dest + " " + self.recordType + " " + self.domain
        if self.type == self.DNS_ANSWER:
            ret = "DNS ANSWER: " + str(self.timestamp) + " " + self.protocol + " " + self.src + " " + self.dest + " "
            for answer in self.answers:
                ret = ret + answer["recordType"] + " " + answer["address"] + ",  "
            
            return ret
        if self.type ==  self.DATA:
            return "DATA: " + str(self.timestamp) + " " + self.protocol + " " + self.src + " " + self.dest + " " + self.flags
                
            
        else:
            return "UNKNOWN: " + self.raw
        
        
    def test(self):
    
        #DNS Ask
        line = "14:32:38.929887 IP6 2601:644:680:78e0:b116:7a13:99e:888.64653 > 2001:558:feed::1.53: 38611+ AAAA? bsuepwsgmapu.hsd1.ca.comcast.net. (50)"
      
        r = self.regexDNSAsk
        
        print (line)
        print (r)
        
        x = re.search(r, line)
        print(x.groups())
        
        r = self.regexDNSAnswer
        x = re.search(r, line)
        print (x)
        
        print("******************************************")

        
        line = "14:32:38.935958 IP6 2001:558:feed::1.53 > 2601:644:680:78e0:b116:7a13:99e:888.28647: 30375 1/0/0 AAAA 2607:f8b0:4005:804::200a (77)"
        
        r = self.regexDNSAnswer

        print (line)
        print (r)

        x = re.search(r, line)
        print(x.groups())
        
        r = self.regexDNSAsk
        x = re.search(r, line)
        print (x)
        
        print("******************************************")
        
        line = "14:32:36.463952 IP6 2001:558:feed::1.53 > 2601:644:680:78e0:b116:7a13:99e:888.5341: 26614 7/0/0 CNAME youtube-ui.l.google.com., A 216.58.194.174, A 172.217.6.78, A 216.58.194.206, A 172.217.5.110, A 172.217.6.46, A 172.217.164.110 (163)"
        
        r = self.regexDNSAnswer

        print (line)
        print (r)

        x = re.search(r, line)
        print(x.groups())
        print(x.group(0))
        
        print("******************************************")
        
        line = "15:56:31.707111 IP6 2001:558:feed::1.53 > 2601:644:680:78e0:e0d3:8c:d4a:8e20.62330: 40399 3/1/0 CNAME gsp-ssl.ls-apple.com.akadns.net., CNAME gsp-ssl-geomap.ls-apple.com.akadns.net., CNAME gsp-ssl-dynamic.ls4-apple.com.akadns.net. (215)"
        
        r = self.regexDNSAnswer

        print (line)
        print (r)

        x = re.search(r, line)
        print(x.groups())
        print(x.group(0))
        
        print("******************************************")
        
        line = "14:32:26.827232 IP6 2600:1f18:4b5:ac01:57c4:ae19:5f88:c81.443 > 2601:644:680:78e0:b116:7a13:99e:888.63739: Flags [FP.], seq 46:77, ack 1, win 130, options [nop,nop,TS val 173727505 ecr 2705081351], length 31"

        r = self.regexData
        
        print (line)
        print (r)
        
        x = re.search(r, line)
        print(x.groups())



class session:

    sessionStart = 0
    sessionEnd = 0
    domain = ""
    previousSession = None
    active = True
    
    SESSION_TIMEOUT = 1*60
    
    def __init__(self, domain, dbRow = None):
        
        if not dbRow:
        
            self.domain = domain
            self.sessionStart = time.time()
        
        else:
            self.domain = dbRow["domain"]
            self.sessionStart = float(dbRow["sessionStart"])
            self.sessionEnd = float(dbRow["sessionEnd"])
            
    def checkIfStale(self):
    
        now = time.time()
        if self.sessionEnd < now - self.SESSION_TIMEOUT:
            self.active = False
            
        
    def ping(self):
        
        now = time.time()
        
        if self.sessionStart >  now - self.SESSION_TIMEOUT:
            self.sessionEnd = now
            
        elif self.sessionEnd > now - self.SESSION_TIMEOUT:
            self.sessionEnd = now
            
        else:
            temp = session(self.domain)
            temp.sessionStart = self.sessionStart
            temp.sessionEnd = self.sessionEnd
            temp.previousSession = self.previousSession
            temp.active = False
            
            self.sessionStart = now
            self.sessionEnd = now
            self.active = True
            self.previousSession = temp
        
  
    
    def saveToDB(self, db):
        
        Q = Query()
        db.upsert({'domain': self.domain, 'sessionStart': self.sessionStart, 'sessionEnd': self.sessionEnd, 'active': self.active}, (Q.domain == self.domain) & (Q.sessionStart == self.sessionStart))
        
        if self.previousSession:
            self.previousSession.active = False
            self.previousSession.saveToDB(db)
            self.previousSession = None
        
    def __str__(self):
    
        #print ("^^^^^^^^^^^^^^^^^^^^^^^^^ session.__str__" + self.domain + " " + datetime.fromtimestamp(self.sessionStart).strftime(DATETIME_PRINT_FORMAT))
    
        ret = "session " + self.domain + " (%s) " % self.active + datetime.fromtimestamp(self.sessionStart).strftime(DATETIME_PRINT_FORMAT) + " "
        
        if self.sessionEnd:
            ret = ret + datetime.fromtimestamp(self.sessionEnd).strftime(DATETIME_PRINT_FORMAT)
        
        if self.previousSession:
            ret = ret + " <- " + self.previousSession.__str__()
            
        return ret
    
class mySessions:

    domains = {}
    
    #PICKLE_FILE_NAME  = "abafilterSessions.pickle"
    db = None
    
    def __init__(self, loadFromDisk=True):
        
        self.db = TinyDB(WORKING_DIR+"/"+'abafilterSessions.json')
        
        if loadFromDisk:
            fixitList = []
            Q = Query()
            results = self.db.search(Q.active == True)
            for r in results:
                if r["domain"] in self.domains.keys():
                    print ("WARNING: mySessions multiple active sessions for ", r["domain"])
                    
                    if self.domains[r["domain"]].sessionStart > r["sessionStart"]:
                        print("type 1")
                        fixitList.append(r)
                    else:
                        print("type 2")
                        fixitList.append({"domain": r["domain"], "sessionStart": self.domains[r["domain"]].sessionStart})
            
                self.domains[r["domain"]] = session(r["domain"], dbRow=r)
        
        for fixit in fixitList:
            print ("WARNING: mySessions: fixing session in DB ", fixit)
            Q = Query()
            self.db.update({'active': False}, (Q.domain == fixit["domain"]) & (Q.sessionStart == fixit["sessionStart"]))
        
        '''
        if loadFromDisk and os.path.exists(self.PICKLE_FILE_NAME):
            with open(self.PICKLE_FILE_NAME, 'rb') as file:
                obj = pickle.load(file)
                self.domains = obj["domains"]
        '''
    
    
    def ping(self, domain):
    
        domain = self.mergeDomains(domain)
        now = time.time()
        
        if domain not in self.domains.keys():
            self.domains[domain]  = session(domain)
        else:
            self.domains[domain].ping()
            
        return domain
    
    def mergeDomains(self, domain):
    
        if domain[-1] == ".":
            domain = domain[:-1]
        
        domainList = domain.split(".")
        
        return ".".join(domainList[-2:])

    def __str__(self):
    
        #print("&&&&&&&&&&&&&&&&&&&&& mySesisons.__str__")
    
        ret = ""
        for domain in self.domains:
            ret = ret + domain + ": " + self.domains[domain].__str__() + "\n"
            
        
        return ret
        
    def dumpToDisk(self):
    
        print("mySessions dumping to disk")
            
        fixitList = []
    
        for domain in self.domains:
        
            self.domains[domain].checkIfStale()
            self.domains[domain].saveToDB(self.db)
            
        
            if not self.domains[domain].active:
                print("mySessions.dumpToDisk() WARNING: removing stale domain ", domain, self.domains[domain].sessionEnd)
            
                fixitList.append(domain)
                
        for domain  in fixitList:
        
            del self.domains[domain]
            
    
    
    def getSessionsForTime(self, startTS, endTS):
    
        Q = Query()
        results = self.db.search((Q.sessionStart <= endTS) & (Q.sessionEnd >= startTS))
        return results


def main(SPREADSHEET_ID):
 
    startupTime = time.time()
 
    myAddress =  set()
    
    myDNSObj = myDNS()
    mySessionsObj = mySessions()
    mySpreadsheetSaverObj = spreadsheetSaver(SPREADSHEET_ID)
    naggers = {}
    
    
    
    
    def cleanupLoop():
        print("################ cleanup loop ################")
        
        
        
        print (datetime.now().strftime(DATETIME_PRINT_FORMAT))
        
        print("**************************************************")
        print(mySessionsObj)
        print("**************************************************")
        
        
        print("Cleaning transactions")
        myDNSObj.cleanTransactions()
        print("Saving DNS")
        myDNSObj.dumpToDisk()
        
        
        print("Saving sessions")
        try:
            mySessionsObj.dumpToDisk()
        except RuntimeError as err:
            print("WARNING: cleanupLoop sessions RuntimeError ", err)
        
        print("**************************************************")
        print(mySessionsObj)
        print("**************************************************")
        
        
    
        print("updating nagging settings")
        try:
        
            temp = mySpreadsheetSaverObj.getNaggingSettings()
            naggers.clear()
            for n in temp:
                naggers[n.domain] = n
            
            print(naggers)
        except RuntimeError as err:
            print("WARNING: cleanupLoop spreadsheet RuntimeError ", err)
        
        
        print("updating spreadsheets")
        try:
            mySpreadsheetSaverObj.dumpUssage(mySessionsObj)
        except RuntimeError as err:
            print("WARNING: cleanupLoop spreadsheet RuntimeError ", err)
        
        
        print("cleanup loop done")
        
        print ("checking restart status")
        
        now = time.time()
        if now > startupTime + RESTART_INTERVAL:
            print ("This process has been up for long enogh. Time for a restart")
        else:
        
            t = threading.Timer(CLEANUP_LOOP_INTERVAL, cleanupLoop)
            t.start()
        
    cleanupLoop()
    
        
    #pprint(myDNSObj.domains)
    
    #with os.popen('cat bla.out', buffering=1) as pse:
    with os.popen('tcpdump -l -n', buffering=1) as pse:
        
        while pse:
        
            #print ("checking restart status")
            now = time.time()
            if now > startupTime + RESTART_INTERVAL:
                print ("This process has been up for long enogh. Time for a restart")
                break
        
            line = pse.readline()
        
            if len(line):
                #print (line)
                line = tcpdumpLine(line)
                if line.validLine:
                    if line.type == line.DNS_ASK:
                        myDNSObj.askTransaction(line.transactionNum, line.domain)
                        
                        #might as well populate my address here
                        myAddress.add(line.src)
                        
                        #print(line)
                    if line.type == line.DNS_ANSWER:
                        answers = [answer["address"] for answer in line.answers]
                        myDNSObj.answerTransactions(line.transactionNum, answers)
                        
                        #print(line)
                    
                    if line.type == line.DATA or line.type == line.UDP:
                    
                        #print(line)
                        
                        if line.src not in myAddress:
                        
                            domain = myDNSObj.getDomainForAddress(line.src)
                            if domain:
                                
                                domain = mySessionsObj.ping(domain)
                                
                                #print ("talking to ", domain)
                                
                                #if domain == "youtube.com":
                                #    print ("YYYYYYYYO")
                                #    print (naggers.keys())
                                
                                if domain in naggers.keys():
                                    naggers[domain].ping()
                                
                                #print("**************************************************")
                                #print(mySessionsObj)
                                #print("**************************************************")
                                
                                
                            else:
                                pass
                                #print ("I don't know who this is ", line.src)
                                #print("**************************************************")
                                #pprint(myDNSObj.domains)
                    

            

                   
                    
                    #print("**************************************************")
                    #pprint(myDNSObj.domains)
                    #print(myDNSObj.transactions)

    
    
    
if __name__ == '__main__':

    #temp = tcpdumpLine("")
    #temp.test()

    print ("######## STARTING ABAFILTER ########")

    sys.path.append("/usr/local/bin/")

    if len(sys.argv) > 1:
        WORKING_DIR = sys.argv[1]
    
    SPREADSHEET_ID = '1c1wIVkNGuluoVmBTPuMH3FKdFnbmJ6i3JDcb8jY7wU8'
    
    if len(sys.argv) > 2:
        SPREADSHEET_ID = sys.argv[2]
        
    if len(sys.argv) > 3:
        CLEANUP_LOOP_INTERVAL = int(sys.argv[3])
        
    if len(sys.argv) > 4:
        RESTART_INTERVAL = int(sys.argv[4])
        
    print ("Working dir: %s, SPREADSHEET_ID: %s, CLEANUP_LOOP_INTERVAL: %i, RESTART_INTERVAL: %i, PATH: %s" % (WORKING_DIR, SPREADSHEET_ID, CLEANUP_LOOP_INTERVAL, RESTART_INTERVAL, os.environ['PATH']))

    main(SPREADSHEET_ID)
