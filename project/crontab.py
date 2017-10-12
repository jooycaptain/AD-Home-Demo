import requests
from flask import Flask, render_template, session, url_for, redirect, flash, request, jsonify
import MySQLdb
from MySQLdb import escape_string as thwart
from dbconnect import connection
import gc
import random
import time
from datetime import date,timedelta, datetime
import os
import numpy as np
import math
from pyexcel_xlsx import save_data
from collections import OrderedDict
from simple_salesforce import Salesforce
import random
import json
import sys
from reportlab.pdfgen import canvas
import PyPDF2
from PyPDF2 import PdfFileMerger, PdfFileReader, PdfFileWriter
import itertools

from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from smtplib import SMTP
import smtplib
import sys

from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from smtplib import SMTP
import smtplib
import calendar



opsBox = {'Suffolk':'17059556856',
          'Nassau':'17059546254',
          'Kings':'17059553221',
          'Queens':'17059558766',
          'Richmond':'17059551899',
          'Massachussets':'17059575921'}

opsManager = {'Suffolk': 
                  {'Name':'Josh Lilly','Phone':'(845) 321-3254'},
              'Nassau': 
                  {'Name':'Brandon Parlante','Phone':'(516) 660-8968'},
              'Kings': 
                  {'Name':'James Tornabene','Phone':'(913) 530-0149'},
              'Queens': 
                  {'Name':'Diego Aguilar','Phone':'(718) 593-1571'},
              'Richmond': 
                  {'Name':'Doug Huron','Phone':'(203) 816-7279'},
              'Massachussets': 
                  {'Name':'Zak Elgart','Phone':'(617) 290-8550'}
              }

panelManufactory = {
        '285S1C-G4':'LG Electronics',
        '300N1C-B3':'LG Electronics',
        '315N1C-G4':'LG Electronics',
        'LG 315N1C-C4':'LG Electronics',
        'LG 285W (LG285S1C-G4)':'LG Electronics',
        'LG 300W (LG300N1C-B3)':'LG Electronics',
        'LG 300W (LG300N1C-BC)':'LG Electronics',
        'LG 315W (LG315N1C-G4)':'LG Electronics',
        '315':'LG Electronics',
        'CertainTeed 290W (CT290M11-02)':'CertainTeed',
        'CertainTeed 285W (CT285M11-01)':'CertainTeed',
        'CT290M11-02':'CertainTeed',
        'CT285M11-01':'CertainTeed',
        'CT 285':'CertainTeed',
        '285':'CertainTeed',
        'CT 290':'CertainTeed',
        'Solstice CT 290':'CertainTeed',
        'Solstice CT 285':'CertainTeed'}

inverterManufactory = {
        'SE3000A-WAVE':'SolarEdge',
        'SE3800A-WAVE':'SolarEdge',
        'SE3800A-US':'SolarEdge',
        'SE5000A-US':'SolarEdge',
        'SE6000A-US':'SolarEdge',
        'SE7600A-US':'SolarEdge',
        'SE10000A-US':'SolarEdge',
        'SE11400A-US':'SolarEdge',
        'SE3800A-RGM':'SolarEdge',
        'SE5000A-RGM':'SolarEdge',
        'SE6000A-RGM':'SolarEdge',
        'SE7600A-RGM':'SolarEdge',
        'SE10000A-RGM':'SolarEdge',
        'SE11400A-RGM':'SolarEdge',
        'SE5000A-US @ 208V':'SolarEdge',
        'SE10000A-US @ 208V':'SolarEdge'}

urlHome = 'http://adhome.levelsolar.com/'
pdfPath = '/var/www/ADHome/download/pdf/'

from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.layout import LAParams
from pdfminer.converter import PDFPageAggregator
import pdfminer

def parse_obj(lt_objs, safeWord): 
    for obj in lt_objs:
        if isinstance(obj, pdfminer.layout.LTTextBoxHorizontal):
            if obj.get_text().replace('\n', '_').find(safeWord) > -1:
              return 1
            # print "%6d, %6d, %s" % (obj.bbox[0], obj.bbox[1], obj.get_text().replace('\n', '_'))
        elif isinstance(obj, pdfminer.layout.LTFigure):
            parse_obj(obj._objs, safeWord)
    return 0
#return the page# of the first safeWord, 0 for no
def readPdf(filePath, safeWord):
  fp = open(filePath, 'rb')
  parser = PDFParser(fp)
  document = PDFDocument(parser)
  if not document.is_extractable:
      raise PDFTextExtractionNotAllowed
  rsrcmgr = PDFResourceManager()
  device = PDFDevice(rsrcmgr)
  laparams = LAParams()
  device = PDFPageAggregator(rsrcmgr, laparams=laparams)
  interpreter = PDFPageInterpreter(rsrcmgr, device)
  pageNum = 1

  for page in PDFPage.create_pages(document):
      interpreter.process_page(page)
      layout = device.get_result()
      if parse_obj(layout._objs, safeWord) == 1:
        fp.close()
        return pageNum
      pageNum = pageNum + 1
  fp.close()
  return 0

def boxToken():
    url = 'http://adhome.levelsolar.com/'+ 'token/?api_key=Jo3y1SAW3S0M3'
    return requests.get(url).text

def pythonSendEmail(msg, recipients):
    msg['From'] = 'adrobot@levelsolar.com'
    emaillist = [elem.strip().split(',') for elem in recipients]
    # msg['To'] = 'joey.jiao@levelsolar.com'
    msg['To'] = ', '.join(recipients)
    msg['Reply-to'] = 'adrobot@levelsolar.com'
    
    part = MIMEText("--------------------------------------------------\nAD Robot doesn't reply emails. Please reply to all.\nThank you!\n")
    msg.attach(part)
    server = smtplib.SMTP("smtp.gmail.com:587")
    server.ehlo()
    server.starttls()
    server.login("adrobot@levelsolar.com", "robotimrobot")
    server.sendmail(msg['From'], emaillist , msg.as_string())
    server.quit()

def writePage(pathTemp, pathOut, nameOut, txtLocation,land = True,font="Helvetica",fontSize=9.05):
    c = canvas.Canvas(pathOut+"delete.pdf")
    if land: 
        c.setPageSize(landscape(letter))
    leftx = 0
    leftContent = 1175
    topCustomer = 30

    c.setFont(font,fontSize)
    for item in txtLocation:
        if item['Centre']:
            c.drawCentredString(item['Location'][0],item['Location'][1],item['Text'])
        elif item['Right']:
            c.drawRightString(item['Location'][0],item['Location'][1],item['Text'])
        else:
            c.drawString(item['Location'][0],item['Location'][1],item['Text'])

    c.showPage()
    c.save()

    minutesFile = open(pathTemp, 'rb')
    pdfReader = PyPDF2.PdfFileReader(minutesFile)
    minutesFirstPage = pdfReader.getPage(0)
    pdfWatermarkReader = PyPDF2.PdfFileReader(open(pathOut+'delete.pdf', 'rb'))
    minutesFirstPage.mergePage(pdfWatermarkReader.getPage(0))
    pdfWriter = PyPDF2.PdfFileWriter()
    pdfWriter.addPage(minutesFirstPage)

    for pageNum in range(1, pdfReader.numPages):
        pageObj = pdfReader.getPage(pageNum)
        pdfWriter.addPage(pageObj)

    resultPdfFile = open(pathOut+nameOut, 'wb')
    pdfWriter.write(resultPdfFile)
    minutesFile.close()
    resultPdfFile.close()

def txtGen(text,location,centre=False,right=False):
    return {"Text":text,
            "Location":location,
            "Centre":centre,
            "Right":right}

def tryBox(url, data, files, headers):
  response = requests.post(url, data=data, files=files, headers=headers)
  if response.status_code == 409:
    response = response.json()
    url = url = 'https://upload.box.com/api/2.0/files/' + response['context_info']['conflicts']['id'] + '/content'
    response = requests.post(url, files=files, headers=headers).json()
  elif response.status_code == 401:
    response = requests.post(url, data=data, files=files, headers=headers)
    if response.status_code == 409:
      response = response.json()
      url = url = 'https://upload.box.com/api/2.0/files/' + response['context_info']['conflicts']['id'] + '/content'
      response = requests.post(url, files=files, headers=headers).json()
    elif response.status_code == 401:
      print str(custum) + ' failed.'
  else:
    print response.status_code

def futureInstallEmail():
    opsShared = {}
    token = boxToken()
    headers =  {'Authorization': 'Bearer ' + token}
    for item in opsBox:
      url = 'https://api.box.com/2.0/folders/'+opsBox[item]
      data = {"shared_link": {"access": "open"}}
      response = requests.put(url, headers=headers, data=json.dumps(data))
      if response.status_code == 200:
          opsShared[item] = str(response.json()['shared_link']['url'])
      else:
        print item + ' shared link broken'

    sf = Salesforce(username='integration@levelsolar.com', password='HrNt7DrqaEfZmBqJRan9dKFzmQFp', security_token='yWlJG8lAKCq1pTBkbBMSVcKg')

    recipients = ['joey.jiao@levelsolar.com','halvard.lange@levelsolar.com','david.bujan@levelsolar.com','james.landry@levelsolar.com','eric.negron@levelsolar.com','tom.pittsley@levelsolar.com','sam.magliaro@levelsolar.com','steve.greene@levelsolar.com','arraydesign@levelsolar.com','amy.depietto@levelsolar.com','michael.tarzian@levelsolar.com']
    # recipients = ['joey.jiao@levelsolar.com','jooycaptain@gmail.com'] 
    msg = MIMEMultipart()
    today = str(datetime.today())[:10]
    msg.preamble = 'Multipart massage.\n'

    if datetime.today().weekday() == 4:
      msg['Subject'] = "Install On " + str(datetime.today() + timedelta(2))[:10] + "(Sun) - " + str(datetime.today() + timedelta(4))[:10] + "(Tue)"
      response = sf.query("SELECT interaction__c.Contact__r.Accountnumber__c, interaction__c.Contact__r.County__c, interaction__c.Contact__r.Name, interaction__c.Contact__r.Address__c, interaction__c.Contact__r.City_State_Zip__c, ScheduledDate__c, Canceled__c, interaction__c.Contact__r.LASERCA__Home_State__c FROM interaction__c WHERE interaction__c.Opportunity__r.InstallDate__c = Null and Subject__c = 'Installation' AND ScheduledDate__c = NEXT_N_DAYS:4 AND ScheduledDate__c != TOMORROW AND Canceled__c = false ORDER BY interaction__c.Contact__r.County__c")
    else:
      msg['Subject'] = "Install On " + str(datetime.today() + timedelta(2))[:10] + "(" + calendar.day_name[(datetime.today() + timedelta(2)).weekday()][:3] + ")"
      response = sf.query("SELECT interaction__c.Contact__r.Accountnumber__c, interaction__c.Contact__r.County__c, interaction__c.Contact__r.Name, interaction__c.Contact__r.Address__c, interaction__c.Contact__r.City_State_Zip__c, ScheduledDate__c, Canceled__c, interaction__c.Contact__r.LASERCA__Home_State__c FROM interaction__c WHERE interaction__c.Opportunity__r.InstallDate__c = Null and Subject__c = 'Installation' AND ScheduledDate__c = NEXT_N_DAYS:2 AND ScheduledDate__c != TOMORROW AND Canceled__c = false ORDER BY interaction__c.Contact__r.County__c")

    msgBody = "<p>We have "+str(len(response['records']))+" upcoming scheduled installations. Links access to install packs</p>"
    msgBody = msgBody + '<table style="width:600px;border:1px solid black;margin-bottom:20px;padding-top:7px;padding-bottom:7px"><tr><th style="text-decoration:underline;width:25%;text-align:left">Warehouse</th><th style="text-decoration:underline;width:75%;text-align:left">Address</th></tr>'
    from collections import OrderedDict
    tomorrowInstall=OrderedDict()
    tomorrowInstall['Suffolk']=[]
    tomorrowInstall['Nassau']=[]
    tomorrowInstall['Kings']=[]
    tomorrowInstall['Queens']=[]
    tomorrowInstall['Richmond']=[]
    tomorrowInstall['Massachussets']=[]
    for item in response['records']:
      try:
        tomorrowInstall[item['Contact__r']['County__c']].append(item['Contact__r']['Accountnumber__c'] + ' ' + item['Contact__r']['Name'] + ' - ' + item['Contact__r']['Address__c'] + ', ' + item['Contact__r']['City_State_Zip__c']) if item['Contact__r']['LASERCA__Home_State__c'] <> 'MA' else tomorrowInstall['Massachussets'].append(item['Contact__r']['Accountnumber__c'] + ' ' + item['Contact__r']['Name'] + ' - ' + item['Contact__r']['Address__c'] + ', ' + item['Contact__r']['City_State_Zip__c'])
      except:
        tomorrowInstall['Massachussets'].append(item['Contact__r']['Accountnumber__c'] + ' ' + item['Contact__r']['Name'] + ' - ' + item['Contact__r']['Address__c'] + ', ' + item['Contact__r']['City_State_Zip__c'])
    for county in tomorrowInstall:
      # msgBody = msgBody + "<tr><td><a href='" + opsShared[county] + "'>" + county + ':</a><td>'
      if tomorrowInstall[county] <> []:
        for item in tomorrowInstall[county]:
          msgBody = msgBody + "<tr><td><a href='" + opsShared[county] + "'>" + county + ':</a><td>' + item + '</tr></td>'
      else:
        msgBody = msgBody + "<tr><td><a href='" + opsShared[county] + "'>" + county + ':</a><td>No Scheduled Installation.</tr></td>'
      # msgBody = msgBody + '\n'
    msgBody = msgBody + '</table>'

    part = MIMEText(msgBody, 'html')
    msg.attach(part)

    pythonSendEmail(msg, recipients)

def futureInstall():
    headers =  {'Authorization': 'Bearer ' + boxToken()}
    for region in opsBox:
      json_r = requests.get('https://api.box.com/2.0/folders/' + opsBox[region] + '/items?limit=1000', headers=headers).json()
      for file in json_r['entries']:
        json_r = requests.delete('https://api.box.com/2.0/files/' + file['id'], headers=headers)

    sf = Salesforce(username='integration@levelsolar.com', password='HrNt7DrqaEfZmBqJRan9dKFzmQFp', security_token='yWlJG8lAKCq1pTBkbBMSVcKg')

    if datetime.today().weekday() == 4:
      response = sf.query("SELECT interaction__c.Contact__r.Accountnumber__c, interaction__c.Contact__r.County__c, interaction__c.Contact__r.Name, interaction__c.Contact__r.Address__c, interaction__c.Contact__r.City_State_Zip__c, ScheduledDate__c, Canceled__c FROM interaction__c WHERE interaction__c.Opportunity__r.InstallDate__c = Null and Subject__c = 'Installation' AND ScheduledDate__c = NEXT_N_DAYS:4 AND ScheduledDate__c != TOMORROW AND Canceled__c = false ORDER BY ScheduledDate__c")
    else:
      response = sf.query("SELECT interaction__c.Contact__r.Accountnumber__c, interaction__c.Contact__r.County__c, interaction__c.Contact__r.Name, interaction__c.Contact__r.Address__c, interaction__c.Contact__r.City_State_Zip__c, ScheduledDate__c, Canceled__c FROM interaction__c WHERE interaction__c.Opportunity__r.InstallDate__c = Null and Subject__c = 'Installation' AND ScheduledDate__c = NEXT_N_DAYS:2 AND ScheduledDate__c != TOMORROW AND Canceled__c = false ORDER BY interaction__c.Contact__r.County__c")
    print json.dumps(response, indent=4, sort_keys=True)
    installList = []
    for item in response['records']:
      installList.append(item['Contact__r']['Accountnumber__c'])
    futureInstallData(installList)
    print 'Job Done.'
      

def futureInstallData(installList):
    # installList = ['134662']
    recipients = ['joey.jiao@levelsolar.com','arraydesign@levelsolar.com','michael.tarzian@levelsolar.com'] 
    msg = MIMEMultipart()
    today = str(datetime.today())[:10]
    msg.preamble = 'Multipart massage.\n'
    if datetime.today().weekday() == 4:
      msg['Subject'] = "Prepareing Install Packs For Next Mon & Tue"
    else:
      msg['Subject'] = "Prepareing Install Packs For " + str(datetime.today() + timedelta(2))[:10] + "(" + calendar.day_name[(datetime.today() + timedelta(2)).weekday()][:3] + ")"
    sf = Salesforce(username='integration@levelsolar.com', password='HrNt7DrqaEfZmBqJRan9dKFzmQFp', security_token='yWlJG8lAKCq1pTBkbBMSVcKg')
    response = sf.query_all("SELECT Contact_Opp__r.County__c, Contact_Opp__r.FirstName, Contact_Opp__r.LastName, Contact_Opp__r.Name, Contact_Opp__r.Address__c, Contact_Opp__r.City_State_Zip__c, Contact_Opp__r.LASERCA__Home_State__c, Account_Number__c, id, Account.AD_Template__c, System_Size_KW__c, Installed_Panels_Model__c, Installed_Inverter_1__c, Installed_Inverter_2__c, Estimated_Production_kWh__c, No_of_Installed_Panels__c,box_install__c, CAD_Specialist__r.Name, CAD_Specialist__r.Personal_Mobile__c, CAD_Specialist__r.DivisionManager__r.Name, CAD_Specialist__r.DivisionManager__r.Personal_Mobile__c, (select Id, Status, EstimatedProductionKWH__c, DesignArrayOutputKW__c  FROM Cases__r WHERE (Record_Type_Bucket__c = 'design' OR Record_Type_Bucket__c = 'Design') and Status = 'Closed'), (SELECT ScheduledDate__c FROM interactions__r WHERE interaction__c.Opportunity__r.InstallDate__c = Null and Subject__c = 'Installation' AND Canceled__c = false) FROM Opportunity WHERE Account_Number__c in " + str(installList).replace('[','(').replace(']',')').replace(' ','').replace('u',''))
    print json.dumps(response, indent=4, sort_keys=True)

    queryResult = {}
    designNotClosed = []
    missingInfo = []
    notDone = []
    for item in response['records']:
      if item['Cases__r']:
        info = {}
        info['preFix'] = str(item['Account_Number__c']) + ' ' + item['Contact_Opp__r']['Name']
        print info['preFix']
        info['name'] = item['Contact_Opp__r']['Name']
        info['idName'] = str(item['Account_Number__c']) + ' - ' + item['Contact_Opp__r']['Name']
        info['cityStateZip'] = item['Contact_Opp__r']['City_State_Zip__c']
        info['fullAddress'] =  item['Contact_Opp__r']['Address__c']
        info['CADTemp'] = item['Account']['AD_Template__c']
        info['pvSize'] = str(item['System_Size_KW__c']) + ' kW' if (item['System_Size_KW__c'] and item['System_Size_KW__c'] > 0) else str(item['Cases__r']['records'][0]['DesignArrayOutputKW__c'])
        info['production'] = str(int(round(int(item['Estimated_Production_kWh__c'].split('.')[0]) * 19.07 , -2))) if (item['Estimated_Production_kWh__c'] and item['Estimated_Production_kWh__c'] > 0)  else str(int(round(int(item['Cases__r']['records'][0]['EstimatedProductionKWH__c'].split('.')[0]) * 19.07 , -2)))
        info['panelNum'] = str(int(item['No_of_Installed_Panels__c'])) if item['No_of_Installed_Panels__c'] else None
        info['inverterNum'] = '2' if item['Installed_Inverter_2__c'] != None else '1'
        info['panelMan'] = panelManufactory[item['Installed_Panels_Model__c']] if item['Installed_Panels_Model__c'] else None 
        # info['CAD'] = str(item['CAD_Specialist__r']['Name'])
        # info['CADPhone'] = str(item['CAD_Specialist__r']['Personal_Mobile__c'])
        info['scheduledDate'] = str(item['Interactions__r']['records'][0]['ScheduledDate__c'])[:10]
        try:
          if item['Installed_Inverter_1__c'].find(';') > -1:
            info['inverterMan'] = inverterManufactory[item['Installed_Inverter_1__c'].split(';')[0]]
            info['inverterNum'] = '2'
          else:
            info['inverterMan'] = inverterManufactory[item['Installed_Inverter_1__c']] if item['Installed_Inverter_1__c'] else None
        except:
          info['inverterMan'] = None
          info['installpackId'] = None
        try:
          info['opsBox'] = opsBox[item['Contact_Opp__r']['County__c']] if item['Contact_Opp__r']['LASERCA__Home_State__c'] <> 'MA' else opsBox['Massachussets']
          # info['CADMan'] = opsManager[item['Contact_Opp__r']['County__c']]['Name'] if item['Contact_Opp__r']['LASERCA__Home_State__c'] <> 'MA' else opsManager['Massachussets']['Name']
          # info['CADManPhone'] = opsManager[item['Contact_Opp__r']['County__c']]['Phone'] if item['Contact_Opp__r']['LASERCA__Home_State__c'] <> 'MA' else opsManager['Massachussets']['Phone']
        except:
          info['opsBox'] = opsBox['Massachussets']
          # info['CADMan'] = opsManager['Massachussets']['Name']
          # info['CADManPhone'] = opsManager['Massachussets']['Phone']

        if item['box_install__c']:
          info['installId'] = item['box_install__c']
          token = boxToken()
          headers =  {'Authorization': 'Bearer ' + token}
          json_r = requests.get('https://api.box.com/2.0/folders/' + item['box_install__c'] + '/items?limit=1000', headers=headers).json()
          try:
            for file in json_r['entries']:
              if file['type'] == 'file' and file['name'].upper().find('12 INSTALL PACK.PDF') > -1:
                info['installpackId']=file['id']
          except:
            url = urlHome + 'boxid/'+item['Account_Number__c'] + '?api_key=Jo3y1SAW3S0M3'
            try:
              response = requests.get(url).json()
              info['installpackId']=response['file9'] if response['file9'] != 'no' else None
              info['installId'] = response['IN_id']
            except:
              info['installpackId'] = None
              info['installId'] = None
        else:
          url = urlHome + 'boxid/'+item['Account_Number__c'] + '?api_key=Jo3y1SAW3S0M3'
          try:
            response = requests.get(url).json()
            info['installpackId']=response['file9'] if response['file9'] != 'no' else None
            info['installId'] = response['IN_id']
          except:
            info['installpackId'] = None
            info['installId'] = None

        if len(info) == len(dict([(k,v) for k,v in info.items() if v is not None])):
          
          queryResult[item['Account_Number__c']] = {'accountNumber':item['Account_Number__c']}
          queryResult[item['Account_Number__c']].update(info)
        else:
          print json.dumps(info, indent=4, sort_keys=True)
          missingInfo.append(item['Account_Number__c'])
      else:
        designNotClosed.append(item['Account_Number__c'])

    print json.dumps(queryResult, indent=4, sort_keys=True)
    print 'Total ready: ' + str(len(queryResult))
    print 'Design Case Not Closed: ' + str(designNotClosed)
    print 'Missing Info: ' + str(missingInfo)
    if len(installList) > 1:
      msgBody = 'Upcoming Scheduled Install: ' + str(len(installList)) + '\n'
      # msgBody = msgBody + 'Install Packs Ready: ' + str(len(queryResult)) + '\n'
      part = MIMEText(msgBody)
      msg.attach(part)

    # notDone = installPackPDF(queryResult)

    for custum in queryResult:
      try:
        name = queryResult[custum]['name']
        fullAddress = queryResult[custum]['fullAddress']
        cityStateZip = queryResult[custum]['cityStateZip']
        pvSize = queryResult[custum]['pvSize']
        panelNum = queryResult[custum]['panelNum']
        panelMan = queryResult[custum]['panelMan']
        inverterNum = queryResult[custum]['inverterNum']
        inverterMan = queryResult[custum]['inverterMan']
        production = queryResult[custum]['production']
        CADTemp = queryResult[custum]['CADTemp']
        installDate = queryResult[custum]['scheduledDate']
        # CAD = queryResult[custum]['CAD']
        # CADMan = queryResult[custum]['CADMan']
        # CADManPhone = queryResult[custum]['CADManPhone']
        # CADPhone = queryResult[custum]['CADPhone']

        nameOut = "Filled.pdf"


        if CADTemp == 'NY-1':
          pathTemp = pdfPath + "System Design Authorization - LI.pdf"    
          txtLocation = [txtGen(name,[190,520]),
                              txtGen(production,[217,622]),
                              txtGen(fullAddress,[190,502]),
                              txtGen(cityStateZip,[190,484]),
                              txtGen('$0',[190,465]),
                              txtGen(installDate,[190,446]),
                              txtGen(str(pvSize),[463,520]),
                              txtGen(str(panelNum),[463,502]),
                              txtGen(panelMan,[463,484]),
                              txtGen(str(inverterNum),[463,465]),
                              txtGen(inverterMan,[463,447]),
                              txtGen('SolarEdge',[463,429])]
          writePage(pathTemp, pdfPath, nameOut, txtLocation,False)
        elif CADTemp == 'NY-2':
          pathTemp = pdfPath + "System Design Authorization - NYC.pdf"    
          txtLocation = [txtGen(name,[190,520+85]),
                              txtGen(production,[270,657]),
                              txtGen(fullAddress,[190,502+85]),
                              txtGen(cityStateZip,[190,484+85]),
                              txtGen('$0',[190,465+85]),
                              txtGen(installDate,[190,446+85]),
                              txtGen(str(pvSize),[463,520+85]),
                              txtGen(str(panelNum),[463,502+85]),
                              txtGen(panelMan,[463,484+85]),
                              txtGen(str(inverterNum),[463,465+85]),
                              txtGen(inverterMan,[463,447+85]),
                              txtGen('SolarEdge',[463,429+85])]
          writePage(pathTemp, pdfPath, nameOut, txtLocation,False)
        elif CADTemp == 'MA':
          pathTemp = pdfPath + "System Design Authorization - MA.pdf"    
          txtLocation = [txtGen(name,[190,520]),
                              txtGen(production,[467,608]),
                              txtGen(fullAddress,[190,502]),
                              txtGen(cityStateZip,[190,484]),
                              txtGen('$0',[190,465]),
                              txtGen(installDate,[190,446]),
                              txtGen(str(pvSize),[463,520]),
                              txtGen(str(panelNum),[463,502]),
                              txtGen(panelMan,[463,484]),
                              txtGen(str(inverterNum),[463,465]),
                              txtGen(inverterMan,[463,447]),
                              txtGen('SolarEdge',[463,429])]
          writePage(pathTemp, pdfPath, nameOut, txtLocation,False)
        else:
          notDone.append(custum)


        token = boxToken()
        headers =  {'Authorization': 'Bearer ' + token}
        url = 'https://api.box.com/2.0/files/'+queryResult[custum]['installpackId']+'/content'
        response = requests.get(url, headers=headers)
        pdfFile = open(pdfPath + "delete.pdf", "wb")
        pdfFile.write(response.content)
        pdfFile.close()
        print readPdf(pdfPath + 'delete.pdf','Secondary Contact name')
        print readPdf(pdfPath + 'delete.pdf','Bill Of Materials')
        with open(pdfPath + 'Filled.pdf', "rb") as f1, open(pdfPath + 'delete.pdf', "rb") as f2, open(pdfPath + 'empty.pdf', "wb") as outputStream:
          file1 = PdfFileReader(f1, 'rb')
          file2 = PdfFileReader(f2, 'rb')
          output = PdfFileWriter()

          if readPdf(pdfPath + 'delete.pdf','Bill Of Materials') == 2:
          
            output.addPage(file2.getPage(0))
            output.addPage(file2.getPage(1))
            output.addPage(file1.getPage(0))
            for i in range(3,file2.numPages):
              output.addPage(file2.getPage(i))
          elif readPdf(pdfPath + 'delete.pdf','Bill Of Materials') == 8:
            output.addPage(file2.getPage(0))
            output.addPage(file2.getPage(1))
            output.addPage(file2.getPage(2))
            output.addPage(file2.getPage(3))
            output.addPage(file2.getPage(4))
            output.addPage(file2.getPage(5))
            output.addPage(file2.getPage(6))
            output.addPage(file2.getPage(7))
            output.addPage(file1.getPage(0))
            for i in range(9,file2.numPages):
              output.addPage(file2.getPage(i))
          else:
            output.addPage(file2.getPage(0))
            output.addPage(file1.getPage(0))
            for i in range(2,file2.numPages):
              output.addPage(file2.getPage(i))

          output.write(outputStream)
          outputStream.close()

        with open(pdfPath + 'empty.pdf', "rb") as output:
          url = 'https://upload.box.com/api/2.0/files/content'
          # print output
          files = { 'filename': (str(custum) + ' ' + name+' - 12 Install Pack.pdf', output.read()) }
          data = { "parent_id": queryResult[custum]['installId'] }
          # tryBox(url, data, files, headers)
          data = { "parent_id": queryResult[custum]['opsBox'] }
          tryBox(url, data, files, headers)
        print str(custum) + ' install pack is ready.'

      except Exception as e:
        notDone.append(custum)
        print str(custum) + ' broken: ' + str(e)
        print queryResult[custum]
    if len(designNotClosed) <> 0 or len(missingInfo) <> 0 or len(notDone) <> 0:
      msgBody = '--------------------------------------------------\n'
      msgBody = msgBody + 'AD please take a look into the following cases and prepare the Install Pack.\n'
      msgBody = msgBody + 'Design Case Not Closed: ' + str(designNotClosed) + '\n' if len(designNotClosed) > 0 else msgBody
      msgBody = msgBody + 'SF Info Incomplete: ' + str(missingInfo) + '\n' if len(missingInfo) > 0 else msgBody
      msgBody = msgBody + 'Document Corrupted: ' + str(notDone) + '\n' if len(notDone) > 0 else msgBody
      part = MIMEText(msgBody)
      msg.attach(part)
    if len(installList) > 1:
      pythonSendEmail(msg, recipients)
    return notDone

##########################################################################################
def failedEmail(subject):
  msg = MIMEMultipart()
  recipients = ['joey.jiao@levelsolar.com']
  msg['Subject'] = subject
  pythonSendEmail(msg, recipients)


if __name__ == '__main__':
  subject = str(sys.argv[1])

  if subject == 'performanceAD':
      pass
      # if datetime.today().weekday() == 5:
      #     url = urlHome + 'performanceWeekly?api_key=Jo3y1SAW3S0M3'
      #     # requests.get(url)
      # elif datetime.today().weekday() != 6:
      #     url = urlHome + 'performanceDaily?api_key=Jo3y1SAW3S0M3'
      #     requests.get(url)
      # else:
      #     pass
      # url = urlHome + 'G2GWBMC?api_key=Jo3y1SAW3S0M3'
      # requests.get(url)

  elif subject == 'performanceWeek':
      pass
      # url = urlHome + 'performanceDaily?api_key=Jo3y1SAW3S0M3'
      # requests.get(url)
  elif subject == 'backlogUpdate':
      pass
      # url = urlHome + 'aptUpdate?api_key=Jo3y1SAW3S0M3'
      # requests.get(url)
  elif subject == 'homeClean':
      pass
      # url = urlHome + 'caseValidator?api_key=Jo3y1SAW3S0M3'
      # requests.get(url)
      # url = urlHome + 'salesFolder?api_key=Jo3y1SAW3S0M3'
      # requests.get(url)
  elif subject == 'futureInstallEmail':
      pass
      # if datetime.today().weekday() < 5:
      #   try:
      #     futureInstallEmail()
      #   except Exception as e:
      #     print str(e)
      #     failedEmail('futureInstallEmail Failed')
  elif subject == 'futureInstallPack':
      pass
      # if datetime.today().weekday() < 5:
      #   try:
      #     futureInstall()
      #   except Exception as e:
      #     print str(e)
      #     failedEmail('futureInstallPack Failed')
  elif subject == 'installPackTest':
    futureInstallData(['133618'])
  elif subject == 's3':
    import boto3
    import datetime
    today = datetime.datetime.today().strftime('%m/%d/%Y')
    s3 = boto3.resource('s3')
    bucket = s3.Bucket('levelsolar-install-img')
    productionContent = []
    recipients = ['joey.jiao@levelsolar.com','alessandro.marra@levelsolar.com','ardavan.metghalchi@levelsolar.com','michael.tarzian@levelsolar.com','christian.vonhassell@levelsolar.com','scott.lomando@levelsolar.com','david.bujan@levelsolar.com','eric.negron@levelsolar.com ']
    msg = MIMEMultipart()
    msg.preamble = 'Multipart massage.\n'
    msg['Subject'] = "Today's new install photos!"
    msgBody = ''
    for obj in bucket.objects.all():
      key = obj.key
      # print obj.last_modified.strftime('%m/%d/%Y')
      if str(key).find('production/')> -1 and today == obj.last_modified.strftime('%m/%d/%Y'):
        productionContent.append(['share.levelsolar.com/c/'+str(key).replace('production/','').replace('.jpg',''),obj.last_modified])
        sfId = str(key).replace('production/','').replace('.jpg','')
        msgBody = msgBody + '<p><a href="https://levelsolar.my.salesforce.com/'+sfId+'" >'+sfId+'</a>(Link goes to SF, photo goes to Landing page):</p>'
        msgBody = msgBody + '<div><a href="http://share.levelsolar.com/c/'+sfId+'"><img src="https://s3.amazonaws.com/levelsolar-install-img/production/'+sfId+'.jpg" width="600"></a></div>'

    if len(msgBody) > 0:
      part = MIMEText(msgBody, 'html')
      msg.attach(part)
      pythonSendEmail(msg, recipients)
