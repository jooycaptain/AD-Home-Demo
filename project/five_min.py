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
import sys, traceback
from flask.ext.login import LoginManager
from flask.ext.login import login_user , logout_user , current_user , login_required
from .decorators import require_apikey
from .decorators import async

pdfPath = '/var/www/ADHome/download/pdf/'

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

from flask import Flask, jsonify, render_template, request, json, redirect, flash
#from flask_weasyprint import HTML, render_pdf
import requests
import os
import json
from project import app
from project import urlHome
from flask_mail import Mail, Message

from reportlab.pdfgen import canvas
import PyPDF2
import requests
from textwrap import wrap
from datetime import datetime

from simple_salesforce import Salesforce
from reportlab.pdfgen import canvas



mail = Mail(app)

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
    return 'ok'

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
      return ' failed.'
  else:
    return ' failed.'

def five_min_pdf(custnum):
    url = "https://levelsolar.secure.force.com/api/services/apexrest/v2/accounts?account_number=" + custnum 
    response_dict = requests.get(url).json()
    url = 'https://levelsolar.secure.force.com/api/services/apexrest/contacts?account=' + response_dict[0]["id"]
    id = response_dict[0]["id"]
    response_dict = requests.get(url).json()
    zip = response_dict[0]['zip']
    street = response_dict[0]['street_address']
    state = response_dict[0]['state']
    name = response_dict[0]['name']
    city = response_dict[0]['city']
    pseg = response_dict[0]['account']['utility_account']
    url = 'https://levelsolar.secure.force.com/api/services/apexrest/v2/cases?type_name=install&account=' + id
    response_dict = requests.get(url).json()
    size = response_dict[0]['total_system_size']
    info = {'Customer_name': name,
            'PSEG_no': pseg,
            'Address_street': street,
            'System_size': size,
            'Address_cityzip': city + ', ' + state + ', ' +zip}
    html = render_template('5min_pdf.html', info=info)
    return HTML(string=html).write_pdf()
    
def num_ck(custnum):
    url = "https://levelsolar.secure.force.com/api/services/apexrest/accounts?account_number=" + custnum 
    response_dict = requests.get(url).json()
    if str(response_dict) == "[]":
        return "0"
    else:
        url = 'https://levelsolar.secure.force.com/api/services/apexrest/contacts?account=' + response_dict[0]["id"]
        response_dict = requests.get(url).json()
        return str(response_dict[0]['name'])

def ConedCertPDF(custum):
    url = 'https://levelsolar.secure.force.com/api/services/apexrest/v2/opportunities?account_number=' + str(custum)
    json_r = requests.get(url).json()
    name = json_r[0]['contact']['name']
    address = json_r[0]['contact']['street_address'] + ', ' + json_r[0]['contact']['city'] + ', ' + json_r[0]['contact']['state'] + ' ' + json_r[0]['contact']['zip']
    coned = json_r[0]['account']['utility_account']
    accoundID = json_r[0]['account']['id']
    install = json_r[0]['installed_date']
    dateInstall = datetime.strptime(install, "%Y-%m-%dT%H:%M:%S.%fZ")
    day = dateInstall.strftime('%d')
    month = dateInstall.strftime('%B')
    install = dateInstall.strftime('%m/%d/%Y')

    url = 'https://levelsolar.secure.force.com/api/services/apexrest/v2/cases?type_name=Design&account=' + accoundID
    json_r = requests.get(url).json()
    s = len(json_r) - 1
    inverter = json_r[s]['inverterModelNumber']


    c = canvas.Canvas(pdfPath + "delete.pdf")
    leftx = 71
    leftContent = 216
    topCustomer = 550

    c.setFont("Helvetica",12)
    c.drawString(leftContent,topCustomer-30,name)
    c.drawString(leftContent,topCustomer-45,address)
    c.drawString(leftContent+65,topCustomer-60,coned)
    c.drawString(leftContent,topCustomer-90,inverter)
    c.drawString(420,265,install)
    c.drawString(470,200,day)
    c.drawString(85,185,month)
    c.showPage()
    c.save()


    minutesFile = open(pdfPath + 'Con_Edison_PV_Contractor_Certification.pdf', 'rb')
    pdfReader = PyPDF2.PdfFileReader(minutesFile)
    minutesFirstPage = pdfReader.getPage(0)
    pdfWatermarkReader = PyPDF2.PdfFileReader(open(pdfPath + 'delete.pdf', 'rb'))
    minutesFirstPage.mergePage(pdfWatermarkReader.getPage(0))
    pdfWriter = PyPDF2.PdfFileWriter()
    pdfWriter.addPage(minutesFirstPage)


    resultPdfFile = open(pdfPath + 'empty.pdf', 'wb')
    pdfWriter.write(resultPdfFile)
    minutesFile.close()
    resultPdfFile.close()

    return

panelManufactory = {
        '285S1C-G4':'LG Electronics',
        '300N1C-B3':'LG Electronics',
        '315N1C-G4':'LG Electronics',
        'LG 285W (LG285S1C-G4)':'LG Electronics',
        'LG 300W (LG300N1C-B3)':'LG Electronics',
        'LG 315W (LG315N1C-G4)':'LG Electronics',
        'CertainTeed 290W (CT290M11-02)':'CertainTeed',
        'Solstice CT 290':'CertainTeed'}

inverterManufactory = {
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


@app.route("/installPack", methods=["GET","POST"])
@login_required
def installPack():
    error = ''
    try:
        if request.method == "GET":
            number = []
            nogood = []
            # msg = Message('Install Pack', sender=('AD - Please Reply To All','adrobot@levelsolar.com'), recipients=[str(request.form["email"]),'joey.jiao@levelsolar.com'])
            msg = Message('Install Pack', sender=('AD - Please Reply To All','adrobot@levelsolar.com'), recipients=['joey.jiao@levelsolar.com'])
            msg.body = "Tomorrow's scheduled installations: \n"
            
            # form = request.form
            # for i in range(1,11):
            #     numck = num_ck(str(request.form["user_search" + str(i)]))
            #     if numck == "0" and str(request.form["user_search" + str(i)]) != "":
            #         error = error + "Invalid customer#: " + str(request.form["user_search" + str(i)]) + "/ "
            #     elif numck != '0':
            #         number.append(str(request.form["user_search" + str(i)]))
                    # msg.body = msg.body + str(request.form["user_search" + str(i)]) + " " + numck + ' & '
            # msg.body = msg.body + 'no more.'
            today = str(datetime.today())[:10]+'T05:00:00.000+0000'
            sf = Salesforce(username='integration@levelsolar.com', password='HrNt7DrqaEfZmBqJRan9dKFzmQFp', security_token='yWlJG8lAKCq1pTBkbBMSVcKg')
            # response = sf.query("SELECT interaction__c.Contact__r.Accountnumber__c, ScheduledDate__c, Canceled__c FROM interaction__c WHERE Subject__c = 'Installation' AND ScheduledDate__c = today AND Canceled__c = false ")
            response = sf.query("SELECT interaction__c.Contact__r.Accountnumber__c, interaction__c.Contact__r.County__c, interaction__c.Contact__r.Name, interaction__c.Contact__r.Address__c, interaction__c.Contact__r.City_State_Zip__c, ScheduledDate__c, Canceled__c FROM interaction__c WHERE Subject__c = 'Installation' AND ScheduledDate__c = today AND Canceled__c = false ")
            # queryResult = {}
            installList = []
            for item in response['records']:
                installList.append(item['Contact__r']['Accountnumber__c'])
                msg.body = msg.body + item['Contact__r']['Accountnumber__c'] + ' ' + item['Contact__r']['Name'] + ' - ' + item['Contact__r']['Address__c'] + ', ' + item['Contact__r']['City_State_Zip__c'] + '\n'
            if len(installList) == 0:
                msg.body = msg.body + 'None\n'
                # return str(msg.body)
            else:
                # return str(installList).replace('[','(').replace(']',')').replace(' ','').replace('u','')
                
                response = sf.query_all("SELECT Contact_Opp__r.County__c, Contact_Opp__r.FirstName, Contact_Opp__r.LastName, Contact_Opp__r.Name, Contact_Opp__r.Address__c, Contact_Opp__r.City_State_Zip__c, Account_Number__c, id, Account.AD_Template__c, System_Size_KW__c, Installed_Panels_Model__c, Installed_Inverter_1__c, Installed_Inverter_2__c, Estimated_Production_kWh__c, No_of_Installed_Panels__c,box_install__c, (select Id, Status  FROM Cases__r WHERE (Record_Type_Bucket__c = 'design' OR Record_Type_Bucket__c = 'Design') and Status = 'Closed') FROM Opportunity WHERE Account_Number__c in " + str(installList).replace('[','(').replace(']',')').replace(' ','').replace('u',''))
                queryResult = {}
                designNotClosed = []
                missingInfo = []
                notDone = []
                for item in response['records']:
                  if item['Cases__r']:
                    info = {}
                    info['preFix'] = str(item['Account_Number__c']) + ' ' + item['Contact_Opp__r']['Name']
                    info['name'] = item['Contact_Opp__r']['Name']
                    info['idName'] = str(item['Account_Number__c']) + ' - ' + item['Contact_Opp__r']['Name']
                    info['cityStateZip'] = item['Contact_Opp__r']['City_State_Zip__c']
                    info['fullAddress'] =  item['Contact_Opp__r']['Address__c']
                    info['CADTemp'] = item['Account']['AD_Template__c']
                    info['pvSize'] = str(item['System_Size_KW__c']) + ' kW'
                    info['production'] = str(int(round(int(item['Estimated_Production_kWh__c']) * 19.07 , -2))) if item['Estimated_Production_kWh__c'] else None
                    info['panelNum'] = str(int(item['No_of_Installed_Panels__c'])) if item['No_of_Installed_Panels__c'] else None
                    info['inverterNum'] = '2' if item['Installed_Inverter_2__c'] != None else '1'
                    info['panelMan'] = panelManufactory[item['Installed_Panels_Model__c']] if item['Installed_Panels_Model__c'] else None 
                    info['inverterMan'] = inverterManufactory[item['Installed_Inverter_1__c']] if item['Installed_Inverter_1__c'] else None
                    info['installpackId'] = None

                    if item['box_install__c']:
                      info['installId'] = item['box_install__c']
                      token = token_verify()
                      headers =  {'Authorization': 'Bearer ' + token}
                      json_r = requests.get('https://api.box.com/2.0/folders/' + item['box_install__c'] + '/items?limit=1000', headers=headers).json()
                      for file in json_r['entries']:
                        if file['type'] == 'file' and file['name'].upper().find('12 INSTALL PACK.PDF') > -1:
                          info['installpackId']=file['id']
                    else:
                      url = urlHome + 'boxid/'+item['Account_Number__c'] + '?api_key=Jo3y1SAW3S0M3'
                      response = requests.get(url).json()
                      info['installpackId']=response['file9'] if response['file9'] != 'no' else None
                      info['installId'] = response['IN_id']

                    if len(info) == len(dict([(k,v) for k,v in info.items() if v is not None])):
                      # print json.dumps(info, indent=4, sort_keys=True)
                      queryResult[item['Account_Number__c']] = {'accountNumber':item['Account_Number__c']}
                      queryResult[item['Account_Number__c']].update(info)
                    else:
                      missingInfo.append(item['Account_Number__c'])
                  else:
                    designNotClosed.append(item['Account_Number__c'])

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

                        nameOut = "Filled.pdf"

                        if CADTemp == 'NY-1':
                          pathTemp = pdfPath + 'System Design Authorization - LI.pdf'
                          txtLocation = [txtGen(name,[190,520]),
                                              txtGen(production,[217,622]),
                                              txtGen(fullAddress,[190,502]),
                                              txtGen(cityStateZip,[190,484]),
                                              txtGen('$0',[190,465]),
                                              txtGen(str(pvSize),[463,520]),
                                              txtGen(str(panelNum),[463,502]),
                                              txtGen(panelMan,[463,484]),
                                              txtGen(str(inverterNum),[463,465]),
                                              txtGen(inverterMan,[463,447]),
                                              txtGen('SolarEdge',[463,429])]
                          writePage(pathTemp, pdfPath + '', nameOut, txtLocation,False)
                        elif CADTemp == 'NY-2':
                          pathTemp = pdfPath + 'System Design Authorization - NYC.pdf'  
                          txtLocation = [txtGen(name,[190,520+85]),
                                              txtGen(production,[270,657]),
                                              txtGen(fullAddress,[190,502+85]),
                                              txtGen(cityStateZip,[190,484+85]),
                                              txtGen('$0',[190,465+85]),
                                              txtGen(str(pvSize),[463,520+85]),
                                              txtGen(str(panelNum),[463,502+85]),
                                              txtGen(panelMan,[463,484+85]),
                                              txtGen(str(inverterNum),[463,465+85]),
                                              txtGen(inverterMan,[463,447+85]),
                                              txtGen('SolarEdge',[463,429+85])]
                          writePage(pathTemp, pdfPath + '', nameOut, txtLocation,False)
                        elif CADTemp == 'MA':
                          pathTemp = pdfPath + 'System Design Authorization - MA.pdf'   
                          txtLocation = [txtGen(name,[190,520]),
                                              txtGen(production,[467,608]),
                                              txtGen(fullAddress,[190,502]),
                                              txtGen(cityStateZip,[190,484]),
                                              txtGen('$0',[190,465]),
                                              txtGen(str(pvSize),[463,520]),
                                              txtGen(str(panelNum),[463,502]),
                                              txtGen(panelMan,[463,484]),
                                              txtGen(str(inverterNum),[463,465]),
                                              txtGen(inverterMan,[463,447]),
                                              txtGen('SolarEdge',[463,429])]
                          writePage(pathTemp, pdfPath + '', nameOut, txtLocation,False)
                        else:
                          notDone.append(custum)

                        token = token_verify()
                        headers =  {'Authorization': 'Bearer ' + token}
                        url = 'https://api.box.com/2.0/files/'+queryResult[custum]['installpackId']+'/content'
                        response = requests.get(url, headers=headers)
                        pdfFile = open(pdfPath + "Download.pdf", "wb")
                        pdfFile.write(response.content)
                        pdfFile.close()
                        with open(pdfPath + 'Filled.pdf', "rb") as f1, open(pdfPath + 'Download.pdf', "rb") as f2, open(pdfPath + 'empty.pdf', "wb") as outputStream:
                          file1 = PdfFileReader(f1, 'rb')
                          file2 = PdfFileReader(f2, 'rb')
                          output = PdfFileWriter()

                          if readPdf(pdfPath + 'Download.pdf','Bill Of Materials') == 2:
                            output.addPage(file2.getPage(0))
                            output.addPage(file2.getPage(1))
                            output.addPage(file1.getPage(0))
                            for i in range(3,file2.numPages):
                              output.addPage(file2.getPage(i))
                          elif readPdf(pdfPath + 'Download.pdf','Bill Of Materials') == 1:
                            output.addPage(file2.getPage(0))
                            output.addPage(file1.getPage(0))
                            for i in range(2,file2.numPages):
                              output.addPage(file2.getPage(i))
                          else:
                            notDone.append(str(custum) + ' cannot find BOM')
                          

                          output.write(outputStream)
                          outputStream.close()

                        with open(pdfPath + 'empty.pdf', "rb") as output:
                          url = 'https://upload.box.com/api/2.0/files/content'
                          files = { 'filename': (str(custum) + ' ' + name+' - 12 Install Pack.pdf', output.read()) }
                          data = { "parent_id": queryResult[custum]['installId'] }
                          # tryBox(url, data, files, headers)
                        with app.open_resource(pdfPath + "empty.pdf") as output:
                            msg.attach(str(custum) + ' ' + name+' - 12 Install Pack.pdf', "application/pdf", output.read())

                    except Exception as e:
                        notDone.append(str(custum) + ' ' + str(e))

                # msg.body = 'Please find your files here: \n'
                if len(designNotClosed) > 0 or len(missingInfo) > 0 or len(notDone) > 0:
                    msg.body = msg.body + '--------------------------------------------------\n'
                    msg.body = msg.body + 'AD please take a look into the following cases and prepare the Install Pack.\n'
                    msg.body = msg.body + 'Design Case Not Closed: ' + str(designNotClosed) + '\n' if len(designNotClosed) > 0 else msg.body
                    msg.body = msg.body + 'SF Info Incomplete: ' + str(missingInfo) + '\n' if len(missingInfo) > 0 else msg.body
                    msg.body = msg.body + 'Document Corrupted: ' + str(notDone) + '\n' if len(notDone) > 0 else msg.body

                mail.send(msg)
                if len(nogood) == 0:
                    flash('Files have been sent to your mail box!')
                
                return render_template('installPack.html', error=error)
        else:
            return render_template('installPack.html', error=error)
    except Exception as e:
        return str(e)


@app.route("/ConedCert", methods=["GET","POST"])
@require_apikey
def ConedCert():
    error = ''
    try:
        if request.method == "POST":
            number = []
            nogood = []
            msg = Message('ConEd Cert', sender=('AD - Please Reply To All','adrobot@levelsolar.com'), recipients=[str(request.form["email"]),'joey.jiao@levelsolar.com'])
            msg.body = 'Please find your files here: '
            form = request.form
            for i in range(1,11):
                numck = num_ck(str(request.form["user_search" + str(i)]))
                if numck == "0" and str(request.form["user_search" + str(i)]) != "":
                    error = error + "Invalid customer#: " + str(request.form["user_search" + str(i)]) + "/ "
                elif numck != '0':
                    number.append(str(request.form["user_search" + str(i)]))
                    # msg.body = msg.body + str(request.form["user_search" + str(i)]) + " " + numck + ' & '
            # msg.body = msg.body + 'no more.'
            if error != '':
                return render_template('ConED_Cert.html', error=error)
            else:
                for custum in number:
                    url = 'https://levelsolar.secure.force.com/api/services/apexrest/v2/opportunities?account_number=' + str(custum)
                    json_r = requests.get(url).json()
                    name = json_r[0]['contact']['name']
                    address = json_r[0]['contact']['street_address'] + ', ' + json_r[0]['contact']['city'] + ', ' + json_r[0]['contact']['state'] + ' ' + json_r[0]['contact']['zip']
                    coned = json_r[0]['account']['utility_account']
                    accoundID = json_r[0]['account']['id']
                    try:
                        install = json_r[0]['installed_date']
                        dateInstall = datetime.strptime(install, "%Y-%m-%dT%H:%M:%S.%fZ")
                        day = dateInstall.strftime('%d')
                        month = dateInstall.strftime('%B')
                        install = dateInstall.strftime('%m/%d/%Y')
                    except:
                        flash(str(custum) + ' does not have an install date in SF.')

                    url = 'https://levelsolar.secure.force.com/api/services/apexrest/v2/cases?type_name=Install&account=' + accoundID
                    json_r = requests.get(url).json()
                    s = len(json_r) - 1

                    inverter = json_r[s]['inverterModelNumber'].replace('&null','')
                    c = canvas.Canvas(pdfPath + "delete.pdf")
                    leftx = 71
                    leftContent = 216
                    topCustomer = 550


                    try:
                        c.setFont("Helvetica",12)
                        c.drawString(leftContent,topCustomer-30,name)
                        c.drawString(leftContent,topCustomer-45,address)
                        c.drawString(leftContent+65,topCustomer-60,str(coned))
                        c.drawString(leftContent,topCustomer-90,inverter)
                    
                        c.drawString(420,265,str(install))
                        c.drawString(470,200,str(day))
                        c.drawString(85,185,str(month))
                        c.showPage()
                        c.save()



                        minutesFile = open(pdfPath + 'Con_Edison_PV_Contractor_Certification.pdf', 'rb')
                        
                        pdfReader = PyPDF2.PdfFileReader(minutesFile)
                        minutesFirstPage = pdfReader.getPage(0)
                        pdfWatermarkReader = PyPDF2.PdfFileReader(open(pdfPath + 'delete.pdf', 'rb'))
                        minutesFirstPage.mergePage(pdfWatermarkReader.getPage(0))
                        pdfWriter = PyPDF2.PdfFileWriter()
                        pdfWriter.addPage(minutesFirstPage)


                        resultPdfFile = open(pdfPath + 'empty.pdf', 'wb')
                        pdfWriter.write(resultPdfFile)
                        minutesFile.close()
                        resultPdfFile.close()

                        with app.open_resource(pdfPath + "empty.pdf") as fp:
                            msg.attach(str(custum) + ' ' + name+' - ConEd Cert.pdf', "application/pdf", fp.read())
                    except Exception as e:
                        nogood.append(str(traceback.format_exc()))
                        nogood.append(str(e))

                mail.send(msg)
                if len(nogood) == 0:
                    flash('Files have been sent to your mail box!')
                else:
                    flash(str(nogood))
                
                return render_template('ConED_Cert.html', error=error)
        else:
            return render_template('ConED_Cert.html', error=error)
    except Exception as e:
        return str(e)

    

@app.route("/5min", methods=["GET","POST"])
@login_required
def five_min():
    error = ''
    try:
        if request.method == "POST":
            msg = Message('5 Mins test', sender=('AD - Please Reply To All','adrobot@levelsolar.com'), recipients=[str(request.form["email"]),'joey.jiao@levelsolar.com'])
            msg.body = '5 Mins test for: '
            form = request.form
            for i in range(1,11):
                numck = num_ck(str(request.form["user_search" + str(i)]))
                if numck == "0" and str(request.form["user_search" + str(i)]) != "":
                    error = error + "Invalid customer#: " + str(request.form["user_search" + str(i)]) + "/ "
                elif numck != '0':
                    msg.body = msg.body + str(request.form["user_search" + str(i)]) + " " + numck + ' & '
            msg.body = msg.body + 'no more.'
            if error != '':
                return render_template('5min.html', error=error)
            else:
                for i in range(1,11):
                    if str(request.form["user_search" + str(i)]) != "":
                        pdf = five_min_pdf(str(request.form["user_search" + str(i)]))
                        msg.attach(str(request.form["user_search" + str(i)]) + " 5min test.pdf", "application/pdf", pdf)
                mail.send(msg)
                flash('Files have been sent to your mail box!')
                return render_template('5min.html', error=error)
            #return five_min_pdf(str(request.form["user_search"]))
        else: # request.method == "GET"
            return render_template('5min.html', error=error)
    except Exception as e:
        return str(e)
