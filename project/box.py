#box.py - build folder

from flask import Flask, render_template, session, url_for, redirect, flash, request, jsonify
import requests
import os
import json
import urllib2
import MySQLdb
from MySQLdb import escape_string as thwart
from dbconnect import connection
import gc
from project import app
from project import urlHome
from project import urlSF
from simple_salesforce import Salesforce

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4, landscape
import PyPDF2
from PyPDF2 import PdfFileMerger, PdfFileReader
from textwrap import wrap
import re

from flask_mail import Mail, Message
mail = Mail(app)

from flask.ext.login import LoginManager
from flask.ext.login import login_user , logout_user , current_user , login_required
from .decorators import require_apikey

boroughCode = {'Manhattan':1,
            'Bronx':2,
            'Brooklyn':3,
            'Kings':3,
            'Queens':4,
            'Staten Island':5,
            'Richmond':5}
boroughName = {1:'Manhattan',
                2:'Bronx',
                3:'Brooklyn',
                4:'Queens',
                5:'Staten Island'}

def writeBBL(sfdc):
    try:
        url = 'https://levelsolar.secure.force.com/api/services/apexrest/v2/opportunities?account_number='+sfdc
        json_r = requests.get(url).json()[0]
        street_address = json_r['contact']['street_address'].upper()
        city = json_r['account']['municipality']['county']['name']
        streetNumber = street_address.split(' ')[0]
        streetName = street_address.split(streetNumber+' ')[1].replace('SECOND METER','').replace("THIRD METER",'').replace("1ST FLOOR",'').replace("2ND FLOOR",'').replace("2ND METER",'').replace(' ','%20')

        url = 'https://api.cityofnewyork.us/geoclient/v1/address.json?houseNumber='+streetNumber+'&street='+streetName+'&borough='+str(boroughCode[city])+'&app_id=42484937&app_key=23ded44b1eb201476429d2b70d735724'
        json_r = requests.get(url).json()

        boroCode = boroughCode[city]
        block = json_r['address']['bblTaxBlock']
        lot = json_r['address']['bblTaxLot']
        binNum = json_r['address']['buildingIdentificationNumber']
        CBNo = json_r['address']['communityDistrict']


        sf = Salesforce(username='integration@levelsolar.com', password='HrNt7DrqaEfZmBqJRan9dKFzmQFp', security_token='yWlJG8lAKCq1pTBkbBMSVcKg')
        response = sf.query_all("SELECT (select RecordTypeId, Id, Block__c FROM Required_Documents__r) FROM Opportunity WHERE Account_Number__c='"+sfdc+"'")
        requiredDocId = response['records'][0]['Required_Documents__r']['records'][0]['Id']
        sfUpdate = {'Block__c':str(int(block)),
                    'Borough_Name__c':boroughName[boroCode],
                    'Borough_No__c':str(boroCode),
                    'Lot__c':str(int(lot)),
                    'BIN__c':str(binNum),
                    'C_B_No__c':str(CBNo)}
        sf.Required_Documents__c.update(requiredDocId,sfUpdate)
        url = 'http://lvl-dev.us-west-2.elasticbeanstalk.com/violation/'
        payload = {'cusnum': sfdc}
        sfUpdate = {'Violation_ECB__c':str(requests.post(url, data = json.dumps(payload)).text)}
        sf.Required_Documents__c.update(requiredDocId,sfUpdate)
        return jsonify(sfUpdate)
    except Exception as e:
        subject = 'BBL Problem'
        msg = Message(subject, sender='robotmarriao@gmail.com', recipients=['joey.jiao@levelsolar.com'])
        msg.body = sfdc + ' ' + str(e)
        # mail.send(msg)
        return str(e)

def ptfilesupdate(file_id, headers, pdfurl,file_name):
    url = 'https://upload.box.com/api/2.0/files/' + file_id + '/content'
    usock = urllib2.urlopen(pdfurl)
    buff = usock.read()
    files = { file_name: buff, }
    response = requests.post(url, headers=headers, files=files)
    if response.status_code != 201:
        subject = file_name + ' file upload - problem'
        msg = Message(subject, sender='robotmarriao@gmail.com', recipients=['joey.jiao@levelsolar.com'])
        msg.body = 'Files from closer app might not be uploaded. Please double check.'
        mail.send(msg)
    return 

def ptfiles(folder_id, headers, pdfurl):
    try:
        file_name = pdfurl.split('/')[-1]  
        dot = list()
        st = -1
        while (file_name.find('.', st+1) > -1):
            dot.append(file_name.find('.',st+1))
            st = file_name.find('.',st+1)
        file_name = file_name.replace('.', ' ', len(dot)-2)
        file_name = file_name.replace('.', ' - ', 1)
        file_name =  file_name.replace('_', ' ')
        if file_name.find('.pdf') == -1:
            file_name =  file_name.replace('pdf', '.pdf')
        url = 'https://api.box.com/2.0/folders/' + folder_id + '/items'
        json_r = requests.get(url, headers=headers).json()
        ck = 0
        for item in json_r['entries']:
            if item['name'] == file_name:
                pdf_id = item['id']
                ck = 1
        if ck == 0:
            url = 'https://upload.box.com/api/2.0/files/content'
            usock = urllib2.urlopen(pdfurl)
            buff = usock.read()
            files = { file_name: buff, }
            data = { 'folder_id': folder_id }
            response = requests.post(url, headers=headers, files=files, data=data)
            if response.status_code != 201:
                subject = file_name + ' file upload - problem'
                msg = Message(subject, sender='robotmarriao@gmail.com', recipients=['joey.jiao@levelsolar.com'])
                msg.body = 'Files from closer app might not be uploaded. Please double check.'
                mail.send(msg)
        else:
            ptfilesupdate(pdf_id, headers, pdfurl, file_name)
        return
    except Exception as e:
        subject = file_name + ' file upload - problem'
        msg = Message(subject, sender='robotmarriao@gmail.com', recipients=['joey.jiao@levelsolar.com'])
        msg.body = 'Files from closer app might not be uploaded. Please double check.' + str(e)
        mail.send(msg)
        return str(e)


def doit(url, headers, payload):
    r = requests.post(url, headers = headers, data = json.dumps(payload))
    return r
    
def add_collab_install(folderid, headers):
    url = 'https://api.box.com/2.0/collaborations'
    #lipostinstall
    payload = {'item': { 'id': folderid, 'type': 'folder'}, 'accessible_by': { 'id': '253388741', 'type': 'user' }, 'role': 'editor'}
    requests.post(url, headers = headers, data = json.dumps(payload))
    #shawn
    payload = {'item': { 'id': folderid, 'type': 'folder'}, 'accessible_by': { 'id': '213806466', 'type': 'user' }, 'role': 'viewer'}
    requests.post(url, headers = headers, data = json.dumps(payload))
    #seeman
    payload = {'item': { 'id': folderid, 'type': 'folder'}, 'accessible_by': { 'id': '214050441', 'type': 'user' }, 'role': 'editor'}
    requests.post(url, headers = headers, data = json.dumps(payload))
    return
  
salesteam = {'NY':'278421457',
             'MA':'280260993'}  
def add_collab_sales(folderid, headers, state):
    url = 'https://api.box.com/2.0/collaborations'
    #lipostinstall
    payload = {'item': { 'id': folderid, 'type': 'folder'}, 'accessible_by': { 'id': salesteam[state], 'type': 'user' }, 'role': 'editor'}
    requests.post(url, headers = headers, data = json.dumps(payload))
    return
 
@app.route("/sync/<sfdc>")
@login_required
def sync(sfdc):
    try:
        token = token_verify()
        headers =  {'Authorization': 'Bearer ' + token}
        url = urlHome+'boxid/' + sfdc + '?api_key=Jo3y1SAW3S0M3'
        response = requests.get(url).json()
        data = {"sync_state": "synced"}
        url='https://api.box.com/2.0/folders/'+str(response['IN_id'])
        response = requests.put(url, headers = headers, data = json.dumps(data))
        return 'Done'
    except Exception as e:
        return str(e)
       
@app.route("/unsync/<sfdc>")
@require_apikey
def unsync(sfdc):
    try:
        url = 'http://adhome.levelsolar.com/'+ 'token/?api_key=Jo3y1SAW3S0M3'
        token = requests.get(url).text
        headers =  {'Authorization': 'Bearer ' + token}
        url = urlHome+'boxid/' + sfdc + '?api_key=Jo3y1SAW3S0M3'
        response = requests.get(url).json()
        salesFolder = response['SALE_id']
        salesId = response['salesteam']
        IN_id = response['IN_id']
        if salesFolder != 'no':
            collabId = '999999999'
            url = 'https://api.box.com/2.0/folders/' + str(salesFolder) + '/collaborations'
            response = requests.get(url, headers = headers).json()
            for items in response['entries']:
                if items['accessible_by']['id'] == salesId:
                    collabId = items['id']
            url = 'https://api.box.com/2.0/collaborations/' + collabId
            response = requests.delete(url, headers = headers)
        url='https://api.box.com/2.0/folders/'+str(IN_id)
        data = {"sync_state": "not_synced"}
        response = requests.put(url, headers = headers, data = json.dumps(data))
        # subject = 'Case removed, box unsync is done'
        # msg = Message(subject, sender='robotmarriao@gmail.com', recipients=['joey.jiao@levelsolar.com'])
        # msg.body = str(response.status_code) + ' ' + str(response.text)
        # mail.send(msg)
        return 'Done'
    except Exception as e:
        subject = 'Case removed, box unsync has error'
        msg = Message(subject, sender='robotmarriao@gmail.com', recipients=['joey.jiao@levelsolar.com'])
        msg.body = str(e)
        mail.send(msg)
        return str(e)
    
@app.route("/token/")
@require_apikey
def token_verify():
    try:
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url =  os.path.join(SITE_ROOT, 'static', 'box.json')    
        token = open(json_url)
        stored_json = json.load(token)
        token.close()
        refresh = stored_json['refresh']
        access = stored_json['access']
        url = 'https://api.box.com/2.0/folders/1763301834/items'
        headers =  {'Authorization': 'Bearer ' + access}
        json_r = requests.get(url, headers=headers)

        if json_r.status_code != 200:
            url = 'https://api.box.com/oauth2/token'
            payload = {'grant_type':'refresh_token','refresh_token':refresh,'client_id':'2jo785briaim4k39h64qs01ey46n2uag','client_secret':'y2HDXknQy5i19HLTWCOaTBBPImZ4J6kW'}
            
            json_r = requests.post(url, data=payload)  
            
            if json_r.status_code != 200:
                return redirect("https://app.box.com/api/oauth2/authorize?response_type=code&client_id=2jo785briaim4k39h64qs01ey46n2uag&state=security_token%3316J0oeiy", code=302)
            else:
                json_r = json_r.json()
                msg = {"refresh": json_r['refresh_token'], "access": json_r['access_token']}
                box = open(json_url,'w')
                stored_json = json.dump(msg,box)
                box.close()
                return str(json_r['access_token'])
        else:
            return str(access)
    except Exception as e:
        return str(e)

@app.route("/checklist/<sfdc>")
@login_required
def checklist(sfdc):
    try:
        url = 'http://adhome.levelsolar.com/token/'+ '?api_key=Jo3y1SAW3S0M3'
        token = requests.get(url).text
        headers =  {'Authorization': 'Bearer ' + token}
        url = urlHome+'boxid/' + sfdc + '?api_key=Jo3y1SAW3S0M3'
        response = requests.get(url)
        if response.text.find('Bad request!') == -1:
            response_dict = response.json()
            PTid = response_dict['PT_id']
            url = "https://levelsolar.secure.force.com/api/services/apexrest/v2/opportunities?account_number=" + sfdc
            response_dict = requests.get(url).json()
            try:
                fileToBox = []
                fileToBox.append(response_dict[0]['required_documents']['hosted_utilitydoc_url'])
                fileToBox.append(response_dict[0]['required_documents']['hosted_ppa_url'])
                fileToBox.append(response_dict[0]['required_documents']['hosted_hea_url'])
                fileToBox.append(response_dict[0]['required_documents']['hosted_saleschecklist_url'])
                fileToBox.append(response_dict[0]['required_documents']['hosted_schedule_z_url'])
                fileToBox.append(response_dict[0]['required_documents']['hosted_exhibit_h_url'])
                fileToBox.append(response_dict[0]['required_documents']['hosted_disclosure_agreement_url'])
                for item in fileToBox:
                    if item != None:
                        ptfiles(PTid, headers, item)
                return "Done"
            except:
                return "Files not found"
        else:
            return "Folder not done, try later"
    except Exception as e:
        return str(e)
        
@app.route("/boxid/<sfdc>", methods=["GET", "POST"])
@require_apikey
def box_id(sfdc):
    try:
        base='https://api.box.com/2.0/folders/'
        token = token_verify()
        headers =  {'Authorization': 'Bearer ' + token}
        custnum=sfdc
        url = urlSF + 'v2/opportunities?account_number=' + custnum
        response_dict = requests.get(url).json()
        first = response_dict[0]['contact']['first_name']
        last = response_dict[0]['contact']['last_name']
        city = response_dict[0]['contact']['city']
        state = response_dict[0]['contact']['state']
        county = response_dict[0]['account']['municipality']['county']['name']
        rep = response_dict[0]['closer']['name']
        name = last + ', ' + first
        folder_name = custnum + ' - ' + name
        AD_name = name + ' - Array Design'
        PT_name = name + ' - Permits'
        IN_name = name + ' - Install Plan'
        SS_name = name + ' - Site Survey'
        SALE_name = rep + '-' + sfdc + ' ' + first + ' ' + last
        
        json_r = requests.get(base + '1763301060/items?limit=1000', headers=headers).json()
        for item in json_r['entries']:
            if item['name'] == state:
                state_id = item['id']
        json_r = requests.get(base + state_id + '/items?limit=1000', headers=headers).json()
        for item in json_r['entries']:
            if item['name'] == county:
                county_id = item['id']
        json_r = requests.get(base + county_id + '/items?limit=1000', headers=headers).json()
        for item in json_r['entries']:
            if item['name'] == city:
                city_id = item['id']
        json_r = requests.get(base + city_id + '/items?limit=1000', headers=headers).json()
        for item in json_r['entries']:
            if item['name'] == folder_name:
                folder_id = item['id']

        json_r = requests.get(base + folder_id + '/items', headers=headers).json()
        for item in json_r['entries']:
            if item['name'] == PT_name:
                PT_id = item['id']
            if item['name'] == IN_name:
                IN_id = item['id']
            if item['name'] == AD_name:
                AD_id = item['id']
        json_r = requests.get(base + IN_id + '/items', headers=headers).json()
        SS_id = 'no'
        SALE_id = 'no'
        for item in json_r['entries']:
            if item['name'] == SS_name:
                SS_id = item['id']
            if item['name'] == SALE_name:
                SALE_id = item['id']
            

        json_r = requests.get(base + PT_id + '/items', headers=headers).json()
        basename= custnum + ' ' + first + ' ' + last
        files=[' - 1 Nyserda Install.pdf',' - 3 Nyserda Photos.pdf',' - 4 Electrical Diagram.pdf',' - 5 Nyserda PV.pdf',' - 8 permits pack.pdf',' - 9 Post install.pdf',' - 10 CAD Appt.pdf', ' - 11 Appendix need.pdf',' - Change Form.pdf',' - 8 NYC permits pack.pdf',' - 4 Electrical Diagram.pdf',' - 12 Install Pack.pdf','-SSP.pdf']
        files2= [basename +x for x in files]
        files_id=files

        for item in json_r['entries']:
                for i in range(0, 10):
                    if item['name'] == files2[i]:
                        files_id[i] = item['id']
                        
        json_r = requests.get(base + IN_id + '/items', headers=headers).json()
        for item in json_r['entries']:
                for i in range(10, 12):
                    if item['name'] == files2[i]:
                        files_id[i] = item['id']
        files_id[12] = 'no'
        if SS_id != 'no':
            json_r = requests.get(base + SS_id + '/items', headers=headers).json()  
            for item in json_r['entries']:
                if item['name'] == files2[12]:
                    files_id[12] = item['id']
                            
        for i in range(0, 13):
            if str(files_id[i]).find('.pdf') > 0:
                files_id[i] = 'no'
        url = 'https://api.box.com/2.0/files/'+str(files_id[6])
        data = {"shared_link": {"access": "open"}}
        response = requests.put(url, headers=headers, data=json.dumps(data))
        sharedCAD = 'no'
        json_r = requests.get(base + AD_id + '/items', headers=headers).json()
        img = 'no'
        for item in json_r['entries']:
            if item['name'] == 'o.png':
                img = item['id']
        if response.status_code == 200:
            sharedCAD = str(response.json()['shared_link']['url'])
        info = {'SF###': custnum,
                'Namee': first + ' ' + last,
                'PT_id': str(PT_id),
                'IN_id': str(IN_id),
                'SS_id': str(SS_id),
                'AD_id': str(AD_id),
                'SALE_id': str(SALE_id),
                'file0': str(files_id[0]),
                'file1': str(files_id[1]),
                'file2': str(files_id[2]),
                'file3': str(files_id[3]),
                'file4': str(files_id[4]),
                'file5': str(files_id[5]),
                'file6': str(files_id[6]),
                'file7': str(files_id[7]),
                'file8': str(files_id[10]),
                'file9': str(files_id[11]),
                'SSP': str(files_id[12]),
                'NYCPermit': str(files_id[9]),
                'sharedCAD': sharedCAD,
                'img':img,
                'salesteam': salesteam[state]}
        return jsonify(info)
    except Exception as e:
        return str(e) + ' Bad request!'

        
# @app.route("/build/") 
def build():
    try:
        token = token_verify()
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url =  os.path.join(SITE_ROOT, 'static', 'account.json')    
        info = open(json_url)
        stored_json = json.load(info)
        first = stored_json['first']
        last = stored_json['last']
        county = stored_json['county']
        city = stored_json['city']
        utilitydoc = stored_json['utilitydoc']
        ppa = stored_json['ppa']
        hea = stored_json['hea']
        cklist = stored_json['cklist']
        custnum = str(stored_json['custnum'])
        zip = stored_json['zip']
        state = stored_json['state']
        address = stored_json['address']
        utt = stored_json['utt']
        rep = stored_json['rep']
        state = stored_json['state']
        schedulez = stored_json['schedulez']
        exhibith = stored_json['exhibith']
        disclosure = stored_json['disclosure']
        
        name = last + ', ' + first
        foldername = custnum + ' - ' + name
        headers =  {'Authorization': 'Bearer ' + token}

        url = 'https://api.box.com/2.0/folders/1763301060/items?limit=1000'
        json_r = requests.get(url, headers=headers).json()
        for item in json_r['entries']:
            if item['name'] == state:
                state_id = item['id']
        url = 'https://api.box.com/2.0/folders/' + state_id + '/items?limit=1000'
        json_r = requests.get(url, headers=headers).json()
        for item in json_r['entries']:
            if item['name'] == county:
                county_id = item['id']
        url = 'https://api.box.com/2.0/folders/' + county_id + '/items?limit=1000'
        json_r = requests.get(url, headers=headers).json()

        for item in json_r['entries']:
            if item['name'] == city:
                city_id = item['id']

        url = 'https://api.box.com/2.0/folders'
        payload = {'name': foldername, 'parent': {'id': city_id}}
        customer_root_id = doit(url, headers, payload).json()['id']

        payload = {'name':name + ' - Array Design', 'parent': {'id': customer_root_id}}
        customer_ad_id = doit(url, headers, payload).json()['id']

        payload = {'name':name + ' - Install Plan','parent': {'id' : customer_root_id}}
        customer_install_id = doit(url, headers, payload).json()['id']
        add_collab_install(customer_install_id, headers)
        
        if utt.find('Con') >= 0:
            url = 'https://api.box.com/2.0/collaborations'
            #michael
            payload = {'item': { 'id': customer_install_id, 'type': 'folder'}, 'accessible_by': { 'id': '201264102', 'type': 'user' }, 'role': 'editor'}
            requests.post(url, headers = headers, data = json.dumps(payload))
        
        url = 'https://api.box.com/2.0/folders'
        payload = {'name':name + ' - Permits','parent': {'id' : customer_root_id}}
        customer_pt_id = doit(url, headers, payload).json()['id']
        
        if utilitydoc != None:
            ptfiles(customer_pt_id, headers, utilitydoc)
        if ppa != None:
            ptfiles(customer_pt_id, headers, ppa)
        if hea != None:
            ptfiles(customer_pt_id, headers, hea)
        if cklist != None:
            ptfiles(customer_pt_id, headers, cklist)
        if schedulez != None:
            ptfiles(customer_pt_id, headers, schedulez)
        if exhibith != None:
            ptfiles(customer_pt_id, headers, exhibith)
        if disclosure != None:
            ptfiles(customer_pt_id, headers, disclosure)

        payload = {'name':name + ' - Site Survey','parent': {'id' : customer_install_id}}
        customer_ss_id = doit(url, headers, payload).json()['id']
        
        payload = {'name':rep + '-' + custnum + ' ' + first + ' ' + last,'parent': {'id' : customer_install_id}}
        customer_sales_id = doit(url, headers, payload).json()['id']
        add_collab_sales(customer_sales_id, headers, state)
        try:
            payload = {'name':rep + '-' + custnum + ' ' + first + ' ' + last,'parent': {'id' : '2658582399'}}
            shared_sales_id = doit(url, headers, payload).json()['id']
        except:
            pass
        payload = {'name':name + ' - Install Post-Install Photos','parent': {'id' : customer_install_id}}
        customer_post_id = doit(url, headers, payload).json()['id']
        #add_collab_install(customer_post_id, headers)
        
        payload = {'name':name + ' - Service Photos','parent': {'id' : customer_install_id}}
        customer_service_id = doit(url, headers, payload).json()['id']
        #add_collab_install(customer_service_id, headers)
        
        payload = {'name':name + ' - Electrical Post-Install Photos','parent': {'id' : customer_install_id}}
        customer_elec_id = doit(url, headers, payload).json()['id']
        #add_collab_install(customer_elec_id, headers)
        
        payload = {'name':name + ' - Fund Documents','parent': {'id' : customer_pt_id}}
        customer_fund_id = doit(url, headers, payload).json()['id']

        payload = {'name':name + ' - CAD Closer','parent': {'id' : customer_pt_id}}
        customer_CADCloser_id = doit(url, headers, payload).json()['id']
        url = 'https://api.box.com/2.0/collaborations'
        payload = {'item': { 'id': customer_CADCloser_id, 'type': 'folder'}, 'accessible_by': { 'id': '407285007', 'type': 'user' }, 'role': 'editor'}
        doit(url, headers, payload) 
        

        
        url = 'https://api.box.com/2.0/collaborations'
        if state == 'NY':
            payload = {'item': { 'id': customer_ss_id, 'type': 'folder'}, 'accessible_by': { 'id': '213804720', 'type': 'user' }, 'role': 'editor'}
        else:
            payload = {'item': { 'id': customer_ss_id, 'type': 'folder'}, 'accessible_by': { 'id': '304083871', 'type': 'user' }, 'role': 'editor'}
        doit(url, headers, payload) 

        url = urlHome+'caseread?api_key=Jo3y1SAW3S0M3'
        payload = {'user_search' : custnum}
        response1 = requests.post(url, data=payload)
        flash("New case coming in:" + str(custnum))
        
        c,conn = connection()

        url = urlSF + 'v2/opportunities?account_number=' + custnum
        response_dict = requests.get(url).json()
        account_id = response_dict[0]['account']['id']
        oppo_id = response_dict[0]['id']
        sf = Salesforce(username='integration@levelsolar.com', password='HrNt7DrqaEfZmBqJRan9dKFzmQFp', security_token='yWlJG8lAKCq1pTBkbBMSVcKg')
        boxIds = {}
        boxIds['box_arraydesign__c'] = customer_ad_id
        boxIds['box_install__c'] = customer_install_id
        boxIds['box_permit__c'] = customer_pt_id
        boxIds['box_sales__c'] = customer_sales_id
        boxIds['box_electricalphotos__c'] = customer_elec_id
        boxIds['box_funddocuments__c'] = customer_fund_id
        boxIds['box_installphotos__c'] = customer_post_id
        sf.Opportunity.update(str(oppo_id),boxIds)

        design = 'PTid#' + str(customer_pt_id) + 'ITid#' + str(customer_install_id) +'Account#' + str(account_id)
        data = c.execute("UPDATE cases SET SFcase = (%s) WHERE caseid = (%s)",
                            [thwart(design),thwart(str(custnum))])
        conn.commit()
        c.close()
        conn.close()
        gc.collect()
        data = {"sync_state": "not_synced"}
        url='https://api.box.com/2.0/folders/'+str(customer_root_id)
        response = requests.put(url, headers = headers, data = json.dumps(data))
        
        flash(name + "'s folder done!")
        url = urlHome+'ssp_matrix?api_key=Jo3y1SAW3S0M3'
        data = { 'casenum': custnum, 'status':'new', 'designer':'' }
        requests.post(url, data=data)
        try:
            writeBBL(custnum)
        except:
            pass
        
        return "OK"
    except Exception as e:
        subject = custnum + ' box folder - problem'
        msg = Message(subject, sender='robotmarriao@gmail.com', recipients=['adcoordinator@levelsolar.com'])
        if str(e).find("'id'") > -1 :
            msg.body = 'A half way through folder exists in Box. Please delete that folder and build it again.'
        else:
            msg.body = 'Folder might not be done. Inform Joey please: ' + str(e)
        mail.send(msg)
        return str(e)

    
@app.route('/folder', defaults={'code':None}, methods=['GET', 'POST'])
@app.route("/folder/<code>", methods=["GET", "POST"])
@require_apikey
def search(code):
    try:
        if request.method == "POST":
            try:
                custnum = request.form["user_search"]
                returnCk = 0
            except:
                custnum = str(request.data).split('<sf:Account_Number__c>')[1].split('</sf:Account_Number__c>')[0]
                returnCk = 1

            c,conn = connection()
            x = c.execute("SELECT * FROM cases WHERE caseid = (%s)",
                    [thwart(str(custnum))])
            if int(x) != 0:
                if returnCk:
                    return '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soapenv:Body><notifications xmlns="http://soap.sforce.com/2005/09/outbound"><Ack>true</Ack></notifications></soapenv:Body></soapenv:Envelope>'
                else:
                    flash('Case already in AD Home')
                    return redirect(urlHome+'case')

            url = "https://levelsolar.secure.force.com/api/services/apexrest/v2/opportunities?account_number=" + str(custnum)
            response_dict = requests.get(url).json()
            first = response_dict[0]['contact']['first_name']
            last = response_dict[0]['contact']['last_name']
            name = first + ' ' + last
            address = response_dict[0]['contact']['street_address']
            city = response_dict[0]['contact']['city']
            state = response_dict[0]['contact']['state']
            zip = response_dict[0]['contact']['zip']
            utt = response_dict[0]['account']['utility']['name']
            county = response_dict[0]['account']['municipality']['county']['name']
            rep = response_dict[0]['closer']['name']

            try:
                utilitydoc = response_dict[0]['required_documents']['hosted_utilitydoc_url']
                ppa = response_dict[0]['required_documents']['hosted_ppa_url']
                hea = response_dict[0]['required_documents']['hosted_hea_url']
                cklist = response_dict[0]['required_documents']['hosted_saleschecklist_url']
                schedulez = response_dict[0]['required_documents']['hosted_schedule_z_url']
                exhibith = response_dict[0]['required_documents']['hosted_exhibit_h_url']
                disclosure = response_dict[0]['required_documents']['hosted_disclosure_agreement_url']
            except:
                utilitydoc = None
                ppa = None
                hea = None
                cklist = None
                schedulez = None
                exhibith = None
                disclosure = None

            
            SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
            json_url = os.path.join(SITE_ROOT, 'static', 'account.json')
            
            msg = {"city": city, "first": first, "last": last, "address": address, "zip": zip, "state": state, "county": county, "custnum": custnum, "utilitydoc": utilitydoc, "ppa": ppa, "hea": hea, "cklist": cklist, "utt": utt, "rep": rep, "schedulez":schedulez, "exhibith":exhibith, "disclosure":disclosure}
            account = open(json_url,'w')
            stored_json = json.dump(msg, account)
            account.close()
            build()
            if returnCk:
                return '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soapenv:Body><notifications xmlns="http://soap.sforce.com/2005/09/outbound"><Ack>true</Ack></notifications></soapenv:Body></soapenv:Envelope>'
            else:
                return redirect(urlHome+'case')
        elif code != None:
            payload = {'grant_type':'authorization_code','code':code,'client_id':'2jo785briaim4k39h64qs01ey46n2uag','client_secret':'y2HDXknQy5i19HLTWCOaTBBPImZ4J6kW'}
            url = 'https://api.box.com/oauth2/token'
            json_r = requests.post(url, data=payload).json()
            SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
            json_url =  os.path.join(SITE_ROOT, 'static', 'box.json')
            msg = {'refresh': json_r['refresh_token'], 'access': json_r['access_token']}
            box = open(json_url,'w')
            stored_json = json.dump(msg,box)
            build()
            return redirect(urlHome+'case')
        else: # request.method == "GET"
            return render_template("front.html")
    except Exception as e:
        subject = custnum + ' box folder - problem'
        msg = Message(subject, sender='robotmarriao@gmail.com', recipients=['adcoordinator@levelsolar.com'])
        if str(e).find("local variable 'city_id' referenced before assignment") > -1:
            msg.body = "Double check the spelling of the city name. You might need to create a new city folder, or let CSR fix the spelling."
        elif str(e).find("'NoneType' object has no attribute '__getitem__'") > -1:
            msg.body = "Double check if we're missing fields of Utility Type or Sales Closer or Municipality or County."
        else:
            msg.body = 'Folder might not be done. Inform Joey please: ' + str(e)
        mail.send(msg)
        return str(e)

@app.route("/boxMonitor/", methods=["GET"])
@login_required
def boxMonitor():
    try:
        base='https://api.box.com/2.0/folders/'

        # token = token_verify()
        # return str(token_verify())
        url = 'http://adhome.levelsolar.com/token/' + '?api_key=Jo3y1SAW3S0M3'
        token = requests.get(url).text
        headers =  {'Authorization': 'Bearer ' + token}

        
        info = {"Database":[],'id':'1763301060', 'link': 'https://levelsolar.app.box.com/files/0/f/1763301060'}


        json_r = requests.get(base + '1763301060/items?limit=1000', headers=headers).json()
        info['totalCount'] = json_r['total_count']
        for state in json_r['entries']:
            info['Database'].append({"State":state['name'], "id":state['id'], 'link':'https://levelsolar.app.box.com/files/0/f/'+state['id'], 'below'+state['name']:[]})
            json_State = requests.get(base + state['id']+'/items?limit=1000', headers=headers).json()
            info['Database'][-1]['totalCount'] = json_State['total_count']
            for county in json_State['entries']:
                info['Database'][-1]['below'+state['name']].append({'County':county['name'], 'id':county['id'],'link':'https://levelsolar.app.box.com/files/0/f/'+county['id'], 'below'+county['name']:[]})
                json_City = requests.get(base + county['id']+'/items?limit=1000', headers=headers).json()
                info['Database'][-1]['below'+state['name']][-1]['totalCount'] = json_City['total_count']
                for city in json_City['entries']:
                    info['Database'][-1]['below'+state['name']][-1]['below'+county['name']].append({'City':city['name'], 'id':city['id'],'link':'https://levelsolar.app.box.com/files/0/f/'+city['id'], 'below'+city['name']:{}})
                    json_Customer = requests.get(base + city['id']+'/items?limit=0', headers=headers).json()
                    info['Database'][-1]['below'+state['name']][-1]['below'+county['name']][-1]['below'+city['name']]['totalCount'] = json_Customer['total_count']
        return jsonify(info)
    except Exception as e:
        # return jsonify(info) + str(e)
        return str(e) + ' Bad request!'
    


