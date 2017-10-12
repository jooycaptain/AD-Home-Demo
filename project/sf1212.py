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

import time
from salesforce_bulk import SalesforceBulk
import json
from datetime import datetime, timedelta
from salesforce_bulk.util import IteratorBytesIO
import unicodecsv
from salesforce_bulk import CsvDictsAdapter

import requests
import sfConstants
import os
##lvluat##005f4000000IfrqAAC##admin@levelsolar.com.lvluat       ##New UAT
##lvldev##005c0000003RZfAAAW##joey.jiao@levelsolar.com.lvldev   ##New DEV
##########00539000005GkosAAC##integration@levelsolar.com.full   ##Old DEV
##########005q0000003OJwUAAW##integration@levelsolar.com.lvluat   ##New UAT
##########005f4000000JdJ4AAK##integration@levelsolar.com  ##New Production 
##########005f4000000Jd1UAAS##christian@levelsolar.com  ##New Production 

logPath = '/var/www/ADHome/project/static/sf/'
oldSFURl = 'https://levelsolar.my.salesforce.com/'
newSFURl = 'https://levelsolar2nd.lightning.force.com/'
# bulkOld = SalesforceBulk(username='integration@levelsolar.com.full', password='HrNt7DrqaEfZmBqJRan9dKFzmQFp', security_token='fKOeff9DhEU6y48yvlYwvE87', sandbox=True)
bulkOld = SalesforceBulk(username='integration@levelsolar.com', password='HrNt7DrqaEfZmBqJRan9dKFzmQFp', security_token='yWlJG8lAKCq1pTBkbBMSVcKg')
# bulkNew = SalesforceBulk(username='admin@levelsolar.com.lvluat', password='levelsolaruat1704', security_token='XcxQoJGjpnMgsVqUiA3DOuFcA', sandbox=True)
# bulkNew = SalesforceBulk(username='integration@levelsolar.com.lvluat', password='HrNt7DrqaEfZmBqJRan9dKFzmQFp', security_token='RH9EBerK4bu7nJ7XjKJtWzAPt', sandbox=True)
bulkNew = SalesforceBulk(username='lvlintegration@levelsolar.com', password='LS7vaQUIPSAR!', security_token='qfTKDt6kj7lphtBUKIb7JvhDB')
# bulkNew = SalesforceBulk(username='joey.jiao@levelsolar.com.lvldev', password='LS7vaQUIPSAR!', security_token='pAtrZvJb2FiKIylgrgJe0F9u', sandbox=True)

def secondToTime(second):
    return str(datetime.fromtimestamp(second/1000.0)).replace(' ', 'T')

def check1212(bulk = bulkOld, bulkDev = bulkNew):
    timeStamp = time.strftime("%d/%m/%Y")
    job = bulk.create_query_job("Opportunity", contentType='JSON')
    batch = bulk.query(job, "select Id, Name, CreatedDate, leadId__c from Opportunity where CreatedDate = today")
    bulk.close_job(job)
    while not bulk.is_batch_done(batch):
        time.sleep(10)
    oppoExt = []
    convertedOppo = {}
    for result in bulk.get_all_results_for_query_batch(batch):
        result = json.load(IteratorBytesIO(result))
        oppoCount = len(result)
        msg = '<h1># of Opportunities converted in SF1: '+str(oppoCount)+'</h1>'
        for row in result:
            # print json.dumps(row, indent=4, sort_keys=True)
            convertedOppo[row['LeadId__c']] = {'createdDate':row['CreatedDate'],
                                        'oldSFId':row['Id'],
                                        'oldLeadId':row['LeadId__c'],
                                        'Name':row['Name']}
            oppoExt.append(row['LeadId__c'])
            

    job = bulk.create_query_job("Interaction__c", contentType='JSON')
    batch = bulk.query(job, "select Id, Name, CreatedDate, Subject__c, NewSalesforceExtID__c from Interaction__c where CreatedDate = today and (Subject__c = 'Closer Appointment' or Subject__c = 'CAD Appointment') AND CreatedById != '00539000005GkosAAC' order by CreatedDate")
    bulk.close_job(job)
    while not bulk.is_batch_done(batch):
        time.sleep(10)
    for result in bulk.get_all_results_for_query_batch(batch):
        result = json.load(IteratorBytesIO(result))
        oppoCount = len(result)
        msgInteraction = '<h1># of Interactions created in SF1: '+str(oppoCount)+'</h1>'
        for row in result:
            msgInteraction += '<p>@'+secondToTime(int(row['CreatedDate']))+' <a href="'+oldSFURl+str(row['Id'])+'" >SF1</a>'
            if row['NewSalesforceExtID__c']:
                msgInteraction += ' & <a href="'+newSFURl+str(row['NewSalesforceExtID__c'])+'" >SF2</a></p>'
            else:
                msgInteraction += ' & NOT IN SF2</p>'
    print json.dumps(convertedOppo, indent=4, sort_keys=True)

    if oppoExt:
        job = bulkDev.create_query_job("Opportunity", contentType='JSON')
        queryStr = "select Id, OldSalesforceExtID__c from opportunity where OldSalesforceExtID__c in " + str(oppoExt).replace("u'","'").replace('[','(').replace(']',')').replace(' ','') + " order by CreatedDate"
        batch = bulkDev.query(job, queryStr)
        bulkDev.close_job(job)
        while not bulkDev.is_batch_done(batch):
            time.sleep(10)
        for result in bulkDev.get_all_results_for_query_batch(batch):
            result = json.load(IteratorBytesIO(result))
            for row in result:
                msg += '<p>'+convertedOppo[row['OldSalesforceExtID__c']]['Name']+' @ '+secondToTime(int(convertedOppo[row['OldSalesforceExtID__c']]['createdDate']))+'</p>'
                msg += '<p><a href="'+oldSFURl+str(convertedOppo[row['OldSalesforceExtID__c']]['oldSFId'])+'" >SF1</a> & <a href="'+newSFURl+str(row['Id'])+'" >SF2</a></p>'
                convertedOppo.pop(row['OldSalesforceExtID__c'], None)
                print json.dumps(row, indent=4, sort_keys=True)
    for key in convertedOppo:
        print convertedOppo[key]
        msg += '<p>'+convertedOppo[key]['Name']+' @ '+secondToTime(convertedOppo[key]['createdDate'])+'</p>'
        msg += '<p><a href="'+oldSFURl+str(convertedOppo[key]['oldSFId'])+'" >SF1</a> & NOT IN SF2</p>'

    job = bulkDev.create_query_job("Event", contentType='JSON')
    batch = bulkDev.query(job, "select Id, CreatedDate, Subject, OldSalesforceExtID__c from Event where CreatedDate = today and (Subject = 'Closer Appointment' or Subject = 'CAD Appointment') AND CreatedById != '005f4000000JdJ4AAK' order by CreatedDate")
    bulkDev.close_job(job)
    while not bulkDev.is_batch_done(batch):
        time.sleep(10)
    convertedOppo = {}
    for result in bulkDev.get_all_results_for_query_batch(batch):
        result = json.load(IteratorBytesIO(result))
        oppoCount = len(result)
        msgInteraction += '<h1># of Events created in SF2: '+str(oppoCount)+'</h1>'
        for row in result:
            msgInteraction += '<p>@'+secondToTime(int(row['CreatedDate']))+' <a href="'+newSFURl+str(row['Id'])+'" >SF2</a>'
            if row['Id']:
                msgInteraction += ' & <a href="'+oldSFURl+str(row['OldSalesforceExtID__c'])+'" >SF1</a></p>'
            else:
                msgInteraction += ' & NOT IN SF1</p>'
            # print json.dumps(row, indent=4, sort_keys=True)

    errorEmail(str(timeStamp)+' - Today 1212', msg+msgInteraction)

def checkLeads1(bulk = bulkOld):
    job = bulk.create_query_job("Lead", contentType='JSON')
    batch = bulk.query(job, "Select id, Name, CreatedDate From Lead where NewSalesforceExtId__c = null and IsConverted = false")
    bulk.close_job(job)
    while not bulk.is_batch_done(batch):
        time.sleep(10)
    msg = ''
    for result in bulk.get_all_results_for_query_batch(batch):
        result = json.load(IteratorBytesIO(result))
        leadCount = len(result)
        if leadCount > 0:
            msg = '<h1># of Leads in SF1 donot have a NewSalesforceExtId: '+str(leadCount)+'</h1>'
        for row in result:
            msg += '<p>'+row['Name']+' @ '+secondToTime(int(row['CreatedDate']))+' <a href="'+oldSFURl+str(row['Id'])+'" >SF1</a>'
    if msg:
        print msg
        errorEmail('Orphan leads', msg)

def boxToken():
    url = 'http://adhome.levelsolar.com/'+ 'token/?api_key=Jo3y1SAW3S0M3'
    return requests.get(url).text

def tryBox(url, data, files, headers):
    response = requests.post(url, data=data, files=files, headers=headers)
    if response.status_code == 409:
        response = response.json()
        url = 'https://upload.box.com/api/2.0/files/' + response['context_info']['conflicts']['id'] + '/content'
        response = requests.post(url, files=files, headers=headers).json()
    elif response.status_code == 401:
        response = requests.post(url, data=data, files=files, headers=headers)
        if response.status_code == 409:
            response = response.json()
            url = 'https://upload.box.com/api/2.0/files/' + response['context_info']['conflicts']['id'] + '/content'
            response = requests.post(url, files=files, headers=headers).json()
        elif response.status_code == 401:
            print files['filename'] + ' failed to upload to Box.'
    else:
        print response.status_code

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

def errorEmail(subject, msgBody = None):
    msg = MIMEMultipart()
    recipients = ['joey.jiao@levelsolar.com','ardavan.metghalchi@levelsolar.com','christian.vonhassell@levelsolar.com','alessandro.marra@levelsolar.com']
    msg['Subject'] = subject
    if msgBody:
        msg.preamble = 'Multipart massage.\n'
        # msg.html = msgBody
        part = MIMEText(msgBody, 'html')
        msg.attach(part)

    pythonSendEmail(msg, recipients)

def uploadBox(timeNow):
    token = boxToken()
    headers =  {'Authorization': 'Bearer ' + token}
    fileNames = ['Qinteraction12', 'Qoppo12', 'Qlead12', 'Ulead12', 'Uoppo12', 'Uinteraction12', 'Idoppo12', 'Idlead12', 'Idinteraction12','CleanOppo12', 'Qinteraction21', 'Qoppo21', 'Qlead21', 'Ulead21', 'Uoppo21', 'Uinteraction21', 'Idoppo21', 'Idlead21', 'Idinteraction21']
    parent_id = ''
    json_r = requests.get('https://api.box.com/2.0/folders/' + '34995084007/items?limit=1000', headers=headers).json()
    parentName = str(timeNow)[-10:].replace('/','-')
    for folder in json_r['entries']:
        if folder['name'] == parentName:
            parent_id = folder['id']
    if not parent_id:
        payload = {'name':parentName,'parent': {'id' : '34995084007'}}
        parent_id = requests.post('https://api.box.com/2.0/folders', headers = headers, data = json.dumps(payload)).json()['id']
    msg = ''
    for fileName in fileNames:
        with open(logPath + fileName + '.txt', "rb") as output:
            if os.fstat(output.fileno()).st_size > 2:
                json_data = output.read()
                url = 'https://upload.box.com/api/2.0/files/content'
                files = { 'filename': (str(timeNow)[:-11] + ' - ' + fileName + '.txt', json_data) }
                data = { "parent_id": parent_id }
                tryBox(url, data, files, headers)
                print fileName
                
                for item in json.loads(json_data):
                    if fileName.find('Uoppo') > -1 and item['resultId-success-created-error'][2] == 'true':
                        msg += '<p>'+sfConstants.nameTranslate[fileName]+': '+item['Name']+'</p>'
                        try:
                            msg += '<p><a href="'+sfConstants.oldSFURl+str(item['OldSalesforceExtID__c'])+'" >Old SF</a>'
                            if item['resultId-success-created-error'][0]:
                                msg += ' & <a href="'+sfConstants.newSFURl+str(item['resultId-success-created-error'][0])+'" >New SF</a></p>'
                            else:
                                msg += '</p>'
                        except:
                            msg += '<p><a href="'+sfConstants.newSFURl+str(item['NewSalesforceExtID__c'])+'" >New SF</a>'
                            if item['resultId-success-created-error'][0]:
                                msg += ' & <a href="'+sfConstants.oldSFURl+str(item['resultId-success-created-error'][0])+'" >Old SF</a></p>'
                            else:
                                msg += '</p>'
                    if fileName[0] != 'Q' and item['resultId-success-created-error'][3] and item['resultId-success-created-error'][3] != 'CANNOT_UPDATE_CONVERTED_LEAD:cannot reference converted lead:--':
                        msg += '<p>'+sfConstants.nameTranslate[fileName]+' : '+item['resultId-success-created-error'][3]+'</p>'
                        try:
                            msg += '<p><a href="'+sfConstants.oldSFURl+str(item['OldSalesforceExtID__c'])+'" >Old SF</a>'
                            if item['resultId-success-created-error'][0]:
                                msg += ' & <a href="'+sfConstants.newSFURl+str(item['resultId-success-created-error'][0])+'" >New SF</a></p>'
                            else:
                                msg += '</p>'
                        except:
                            msg += '<p><a href="'+sfConstants.newSFURl+str(item['NewSalesforceExtID__c'])+'" >New SF</a>'
                            if item['resultId-success-created-error'][0]:
                                msg += ' & <a href="'+sfConstants.oldSFURl+str(item['resultId-success-created-error'][0])+'" >Old SF</a></p>'
                            else:
                                msg += '</p>'
                        # print json.dumps(item, indent=4, sort_keys=True)
                
    if msg:
        errorEmail(str(timeNow)[:-11]+' - Migration Log Errors', msg)
                

def writeTxt(fileName, data):
    with open(fileName, 'w') as outfile:
        json.dump(data, outfile)

def readTxt(fileName):
    with open(fileName, 'r') as data_file:
        json_data = data_file.read()
    return json.loads(json_data)

def buildQueryBatch(sfBulk, items, sfObject, lastHourDateTime, idSet=[], newToOld = False):
    query = 'Select '
    for item in items:
        query += item + ', '
    query = query[:-2] + ' from ' + sfObject + ' where '
    if newToOld:
        if sfObject == 'event' or sfObject == 'interaction__c':
            query += "(Subject = 'Closer Appointment' or Subject = 'CAD Appointment') AND "
        query += "(LastModifiedDate >= "+lastHourDateTime + " AND LastModifiedById != '005f4000000JdJ4AAK' AND LastModifiedById != '005f4000000Jd1UAAS' AND isDeleted = false)"
    else:
        if sfObject == 'event' or sfObject == 'interaction__c':
            query += "(Subject__c = 'Closer Appointment' or Subject__c = 'CAD Appointment') AND "#ScheduledDate__c > today AND
        query += "(LastModifiedDate >= "+lastHourDateTime + " AND LastModifiedById != '00539000005GkosAAC' AND isDeleted = false)"
    if idSet:
        query += " OR Id in " + str(idSet).replace("u'","'").replace('[','(').replace(']',')').replace(' ','') + " "
    job = sfBulk.create_query_job(sfObject, contentType='JSON')
    batch = sfBulk.query(job, query)
    sfBulk.close_job(job)
    while not sfBulk.is_batch_done(batch):
        time.sleep(10)
    return batch

def remap(sfDict, formatMap, statusMap = None):
    for item in formatMap['name']:
        sfDict[formatMap['name'][str(item)]] = sfDict[str(item)]
    for item in formatMap['datetime']:
        if sfDict[str(item)]:
            sfDict[formatMap['datetime'][str(item)]] = str(datetime.fromtimestamp(sfDict[str(item)]/1000.0+14400)).replace(' ', 'T')
        else:
            sfDict[formatMap['datetime'][str(item)]] = None
    if statusMap:
        sfDict[statusMap['Name']] = statusMap[sfDict[statusMap['Name']]]
    fieldList = []
    for item in sfDict:
        fieldList.append(item)
    for item in fieldList:
        if item not in formatMap['target']:
            sfDict.pop(item, None)

def sfUpsert(sfObject, upsertList, extId, sfBulk):
    if upsertList:
        job_id = sfBulk.create_upsert_job(sfObject, contentType='CSV', external_id_name=extId, concurrency='Serial')
        content = CsvDictsAdapter(iter(upsertList))
        batch_id = sfBulk.post_batch(job_id, content)
        sfBulk.wait_for_batch(job_id, batch_id, timeout=120)
        results = sfBulk.get_batch_results(batch_id)
        for i in range(len(upsertList)):
            upsertList[i]['resultId-success-created-error'] = results[i]
        print json.dumps(upsertList, indent=4, sort_keys=True)
        sfBulk.close_job(job_id)
        print sfObject + " upsert done." 
    else:
        print "No " + sfObject + " to upsert"

def sfUpdate(sfObject, updateList, sfBulk):
    if updateList:
        job_id = sfBulk.create_update_job(sfObject, contentType='CSV', concurrency='Serial')
        content = CsvDictsAdapter(iter(updateList))
        batch_id = sfBulk.post_batch(job_id, content)
        sfBulk.wait_for_batch(job_id, batch_id, timeout=120)
        results = sfBulk.get_batch_results(batch_id)
        for i in range(len(updateList)):
            updateList[i]['resultId-success-created-error'] = results[i]
        print json.dumps(updateList, indent=4, sort_keys=True)
        sfBulk.close_job(job_id)
        print sfObject + " update done." 
    else:
        print "No " + sfObject + "  to update"

def sf12Query(lastHourDateTime, bulkOld=bulkOld):
    intLead = []
    intOppo = []
    batch = buildQueryBatch(bulkOld, sfConstants.interactionSF12, 'interaction__c', lastHourDateTime)
    data = []
    for result in bulkOld.get_all_results_for_query_batch(batch):
        result = json.load(IteratorBytesIO(result))
        for row in result:
            data.append(row)
            print json.dumps(row, indent=4, sort_keys=True)
    writeTxt(logPath+'Qinteraction12.txt', data)

    batch = buildQueryBatch(bulkOld, sfConstants.opportunitySF12, 'opportunity', lastHourDateTime, intOppo)
    data = []
    for result in bulkOld.get_all_results_for_query_batch(batch):
        result = json.load(IteratorBytesIO(result))
        for row in result:
            if  row['Lead__c'] and row['Lead__c'] not in intLead:
                data.append(row)
            print json.dumps(row, indent=4, sort_keys=True)
    writeTxt(logPath+'Qoppo12.txt', data)

    batch = buildQueryBatch(bulkOld, sfConstants.leadSF12, 'lead', lastHourDateTime, intLead)
    while not bulkOld.is_batch_done(batch):
        time.sleep(10)
    data = []
    for result in bulkOld.get_all_results_for_query_batch(batch):
        result = json.load(IteratorBytesIO(result))
        for row in result:
            if (row['MobilePhone'] or row['Phone'] or row['Email']) or row['Id'] in intLead:
                data.append(row)
                print json.dumps(row, indent=4, sort_keys=True)
    writeTxt(logPath+'Qlead12.txt', data)

def sf12Upsert(bulkNew=bulkNew):

    leads = []
    leadData = readTxt(logPath+'Qlead12.txt')
    for lead in leadData:
        lead['Company'] = str(lead['LASERCA__Home_Address__c']) + ' - ' + str(lead['LASERCA__Home_City__c']) + ' - ' + str(lead['LASERCA__Home_Zip__c'])
        remap(lead, sfConstants.leadToLead12, sfConstants.leadStatus12)
        leads.append(lead)
        print json.dumps(lead, indent=4, sort_keys=True)
    sfUpsert('Lead', leads, 'OldSalesforceExtID__c', bulkNew)
    writeTxt(logPath+'Ulead12.txt', leads)

    time.sleep(60)

    oppos = []
    oppoData = readTxt(logPath+'Qoppo12.txt')
    for oppo in oppoData:
        remap(oppo, sfConstants.oppoToOppo12, sfConstants.oppoStage12)
        oppos.append(oppo)
        print json.dumps(oppo, indent=4, sort_keys=True)
    sfUpsert('Opportunity', oppos, 'OldSalesforceExtID__c', bulkNew)
    writeTxt(logPath+'Uoppo12.txt', oppos)

    time.sleep(60)

    interactions = []
    interactionData = readTxt(logPath+'Qinteraction12.txt')
    for interaction in interactionData:
        try:
            interaction['OldSalesforceLeadID__c'] = interaction['Opportunity__r']['Lead__c']
        except:
            interaction['OldSalesforceLeadID__c'] = interaction['Lead__c']
        interaction['DurationInMinutes'] = 120
        remap(interaction, sfConstants.interactionToEvent12, sfConstants.interactionOutcome12)
        interactions.append(interaction)
        print json.dumps(interaction, indent=4, sort_keys=True)
    sfUpsert('Event', interactions, 'OldSalesforceExtID__c', bulkNew)
    writeTxt(logPath+'Uinteraction12.txt', interactions)

def sf12Id(bulkOld=bulkOld):
    # oppoData = readTxt(logPath+'Uoppo12.txt')
    # insertedOppo = []
    # for lead in oppoData:
    #     if lead['resultId-success-created-error'][0]:
    #         insertedOppo.append(lead['resultId-success-created-error'][0])

    # insertedId = []
    # if insertedOppo:
    #     job = bulkNew.create_query_job("opportunity", contentType='JSON')
    #     queryStr = "select LeadId__c, OldSalesforceExtID__c from opportunity where Id in " + str(insertedOppo).replace("u'","'").replace('[','(').replace(']',')').replace(' ','') + " "
    #     batch = bulkNew.query(job, queryStr)
    #     while not bulkNew.is_batch_done(batch):
    #         time.sleep(10)
    #     for result in bulkNew.get_all_results_for_query_batch(batch):
    #         result = json.load(IteratorBytesIO(result))
    #         for row in result:
    #             insertedId.append({'LeadId__c':row['OldSalesforceExtID__c'],'NewSalesforceExtID__c':row['LeadId__c']})
    #     print json.dumps(insertedId, indent=4, sort_keys=True)

    # sfUpsert('opportunity', insertedId, 'LeadId__c', bulkOld)
    # writeTxt(logPath+'Idoppo12.txt', insertedId)

    leadData = readTxt(logPath+'Ulead12.txt')
    insertedId = []
    for lead in leadData:
        if lead['resultId-success-created-error'][2] == 'true' and lead['resultId-success-created-error'][0]:
            insertedId.append({'Id':lead['OldSalesforceExtID__c'],'NewSalesforceExtID__c':lead['resultId-success-created-error'][0]})
    print json.dumps(insertedId, indent=4, sort_keys=True)
    sfUpdate("Lead", insertedId, bulkOld)
    writeTxt(logPath+'Idlead12.txt', insertedId)

    interactionData = readTxt(logPath+'Uinteraction12.txt')
    insertedId = []
    for intetraction in interactionData:
        if intetraction['resultId-success-created-error'][2] == 'true' and intetraction['resultId-success-created-error'][0]:
            insertedId.append({'Id':intetraction['OldSalesforceExtID__c'],'NewSalesforceExtID__c':intetraction['resultId-success-created-error'][0]})
    print json.dumps(insertedId, indent=4, sort_keys=True)
    sfUpdate("interaction__c", insertedId, bulkOld)
    writeTxt(logPath+'Idinteraction12.txt', insertedId)

def sf21Query(lastHourDateTime, bulkNew=bulkNew):
    intLead = []
    intOppo = []
    batch = buildQueryBatch(bulkNew, sfConstants.eventSF21, 'event', lastHourDateTime, newToOld = True)
    data = []
    for result in bulkNew.get_all_results_for_query_batch(batch):
        result = json.load(IteratorBytesIO(result))
        for row in result:
            if not row['WhatId']: #Closer Appt, query lead
                # intLead.append(row['NewSalesforceLeadId__c'])
                data.append(row)
            # if row['WhatId']: #CAD Appt, query opportunity
                # intOppo.append(row['WhatId'])
                # data.append(row)  #not syncing CAD meeting before we map the external id on Opportunity
            print json.dumps(row, indent=4, sort_keys=True)
    writeTxt(logPath+'Qinteraction21.txt', data)

    batch = buildQueryBatch(bulkNew, sfConstants.opportunitySF21, 'opportunity', lastHourDateTime, intOppo, newToOld = True)
    data = []
    for result in bulkNew.get_all_results_for_query_batch(batch):
        result = json.load(IteratorBytesIO(result))
        for row in result:
            data.append(row)
            print json.dumps(row, indent=4, sort_keys=True)
    writeTxt(logPath+'Qoppo21.txt', data)

    batch = buildQueryBatch(bulkNew, sfConstants.leadSF21, 'lead', lastHourDateTime, intLead, newToOld = True)
    while not bulkNew.is_batch_done(batch):
        time.sleep(10)
    data = []
    for result in bulkNew.get_all_results_for_query_batch(batch):
        result = json.load(IteratorBytesIO(result))
        for row in result:
            if (row['MobilePhone'] or row['Phone'] or row['Email']) or row['Id'] in intLead:
                data.append(row)
                print json.dumps(row, indent=4, sort_keys=True)
    writeTxt(logPath+'Qlead21.txt', data)

def sf21Upsert(bulkOld=bulkOld):
    leads = []
    leadData = readTxt(logPath+'Qlead21.txt')
    for lead in leadData:
        # lead['Company'] = str(lead['LASERCA__Home_Address__c']) + ', ' + str(lead['LASERCA__Home_Zip__c'])
        remap(lead, sfConstants.leadToLead21, sfConstants.leadStatus21)
        leads.append(lead)
        print json.dumps(lead, indent=4, sort_keys=True)
    sfUpsert('Lead', leads, 'NewSalesforceExtID__c', bulkOld)
    writeTxt(logPath+'Ulead21.txt', leads)

    # oppos = []
    # oppoData = readTxt(logPath+'Qoppo21.txt')
    # for oppo in oppoData:
    #     remap(oppo, sfConstants.oppoToOppo21, sfConstants.oppoStage21)
    #     oppos.append(oppo)
    #     print json.dumps(oppo, indent=4, sort_keys=True)
    # sfUpsert('Opportunity', oppos, 'NewSalesforceExtID__c', bulkOld)
    # writeTxt(logPath+'Uoppo21.txt', oppos)

    interactions = []
    interactionData = readTxt(logPath+'Qinteraction21.txt')
    for interaction in interactionData:
        print json.dumps(interaction, indent=4, sort_keys=True)            
        if interaction['WhatId']:
            interaction['Opportunity__r.NewSalesforceExtID__c'] = interaction['NewSalesforceLeadId__c'] #write LeadId_c
        else:
            interaction['lead__r.NewSalesforceExtID__c'] = interaction['WhoId'] #write LeadId_c
        try:
            interaction['Assigned_To__c'] = sfConstants.sf2EmployeeId[interaction['Assigned_Employee__c']]
        except:
            interaction['Assigned_To__c'] = None
        # interaction['Assigned_To__c'] = None
        remap(interaction, sfConstants.interactionToEvent21, sfConstants.interactionOutcome21)
        interactions.append(interaction)
        print json.dumps(interaction, indent=4, sort_keys=True)
    sfUpsert('interaction__c', interactions, 'NewSalesforceExtID__c', bulkOld)
    writeTxt(logPath+'Uinteraction21.txt', interactions)

def sf21Id(bulkNew=bulkNew):
    # oppoData = readTxt(logPath+'Uoppo21.txt')
    # insertedOppo = []
    # for lead in oppoData:
    #     if lead['resultId-success-created-error'][2] == 'true' and lead['resultId-success-created-error'][0]:
    #         insertedOppo.append(lead['resultId-success-created-error'][0])

    # insertedId = []
    # if insertedOppo:
    #     job = bulkOld.create_query_job("opportunity", contentType='JSON')
    #     queryStr = "select LeadId__c, NewSalesforceExtID__c from opportunity where Id in " + str(insertedOppo).replace("u'","'").replace('[','(').replace(']',')').replace(' ','') + " "
    #     batch = bulkOld.query(job, queryStr)
    #     while not bulkOld.is_batch_done(batch):
    #         time.sleep(10)
    #     for result in bulkOld.get_all_results_for_query_batch(batch):
    #         result = json.load(IteratorBytesIO(result))
    #         for row in result:
    #             insertedId.append({'LeadId__c':row['OldSalesforceExtID__c'],'NewSalesforceExtID__c':row['LeadId__c']})
    #     print json.dumps(insertedId, indent=4, sort_keys=True)

    # sfUpsert('opportunity', insertedId, 'LeadId__c', bulkNew)
    # writeTxt(logPath+'Idoppo21.txt', insertedId)

    leadData = readTxt(logPath+'Ulead21.txt')
    insertedId = []
    for lead in leadData:
        if lead['resultId-success-created-error'][2] == 'true' and lead['resultId-success-created-error'][0]:
            insertedId.append({'Id':lead['NewSalesforceExtID__c'],'OldSalesforceExtID__c':lead['resultId-success-created-error'][0]})
    print json.dumps(insertedId, indent=4, sort_keys=True)
    sfUpdate("Lead", insertedId, bulkNew)
    writeTxt(logPath+'Idlead21.txt', insertedId)

    interactionData = readTxt(logPath+'Uinteraction21.txt')
    insertedId = []
    for lead in interactionData:
        if lead['resultId-success-created-error'][2] == 'true' and lead['resultId-success-created-error'][0]:
            insertedId.append({'Id':lead['NewSalesforceExtID__c'],'OldSalesforceExtID__c':lead['resultId-success-created-error'][0]})
    print json.dumps(insertedId, indent=4, sort_keys=True)
    sfUpdate("Event", insertedId, bulkNew)
    writeTxt(logPath+'Idinteraction21.txt', insertedId)

def cleanOppoSF2(bulkNew=bulkNew):
    job = bulkNew.create_query_job("Opportunity", contentType='JSON')
    batch = bulkNew.query(job, "select Id, AccountId, LeadId__c, OldSalesforceExtID__c from Opportunity where LeadId__c = null and AccountId = null")
    bulkNew.close_job(job)
    while not bulkNew.is_batch_done(batch):
        time.sleep(10)
    data = []
    datafull = []
    for result in bulkNew.get_all_results_for_query_batch(batch):
        result = json.load(IteratorBytesIO(result))
        for row in result:
            # row['OldSalesforceExtID__c'] = row['Id']
            datafull.append(row)
            row.pop('OldSalesforceExtID__c', None)
            row.pop('AccountId', None)
            row.pop('LeadId__c', None)
            row.pop('attributes', None)
            data.append(row)
            print json.dumps(row, indent=4, sort_keys=True)

    if data:
        job_id = bulkNew.create_delete_job("Opportunity", contentType='CSV')
        content = CsvDictsAdapter(iter(data))
        batch_id = bulkNew.post_batch(job_id, content)
        bulkNew.wait_for_batch(job_id, batch_id, timeout=120)
        results = bulkNew.get_batch_results(batch_id)
        for i in range(len(data)):
            datafull[i]['resultId-success-created-error'] = results[i]
        print json.dumps(datafull, indent=4, sort_keys=True)
        bulkNew.close_job(job_id)
        print "Clean opportunity done." 
    else:
        print "No opportunity to clean"
    writeTxt(logPath+'CleanOppo12.txt', datafull)

if __name__ == '__main__':
    subject = str(sys.argv[1])
    
    if subject == 'test':
        print 'testtesttesttesttesttesttesttesttesttesttest'
        bulkOldTest = SalesforceBulk(username='integration@levelsolar.com.full', password='HrNt7DrqaEfZmBqJRan9dKFzmQFp', security_token='fKOeff9DhEU6y48yvlYwvE87', sandbox=True)
        bulkNewTest = SalesforceBulk(username='integration@levelsolar.com.lvluat', password='HrNt7DrqaEfZmBqJRan9dKFzmQFp', security_token='RH9EBerK4bu7nJ7XjKJtWzAPt', sandbox=True)

        # cleanOppoSF2(bulkNew=bulkNewTest)
        lastHourDateTime = str(datetime.now() + timedelta(hours = -1.1)).replace(' ','T').split('.')[0]+'Z'
        lastHourDateTime = str(datetime.now() + timedelta(hours = 2.9)).replace(' ','T').split('.')[0]+'Z'
        # sf12Query(lastHourDateTime)
        # sf12Upsert()
        # sf12Id()
        timeStamp = time.strftime("%H:%M:%S")+'-'+time.strftime("%d/%m/%Y")
        uploadBox(timeStamp)
        # sf12Query(lastHourDateTime, bulkOld=bulkOldTest)
        # sf12Upsert(bulkNew=bulkNewTest)
        # sf21Query(lastHourDateTime, bulkNew=bulkNewTest)
        # sf21Query(lastHourDateTime, bulkNew=bulkNew)
        # sf21Upsert(bulkOld=bulkOldTest)
        # sf21Id(bulkNew=bulkNew)
    elif subject == 'check':
        pass
        # check1212()
    elif subject == 'checkLeads':
        # checkLeads1()
        pass
    elif subject == 'real':
        pass
        # try:
        #     cleanOppoSF2()
        #     timeStamp = time.strftime("%H:%M:%S")+'-'+time.strftime("%d/%m/%Y")
        #     lastHourDateTime = str(datetime.now() + timedelta(hours = 2.9)).replace(' ','T').split('.')[0]+'Z'
        #     start_time = time.time()
        #     sf12Query(lastHourDateTime)
        #     print("--- %s seconds ---" % (time.time() - start_time))
        #     start_time = time.time()
        #     sf12Upsert()
        #     print("--- %s seconds ---" % (time.time() - start_time))
        #     start_time = time.time()
        #     sf12Id()
        #     print("--- %s seconds ---" % (time.time() - start_time))
        #     start_time = time.time()

        #     # lastHourDateTime = str(datetime.now() + timedelta(hours = -1.1)).replace(' ','T').split('.')[0]+'Z'
        #     sf21Query(lastHourDateTime)
        #     print("--- %s seconds ---" % (time.time() - start_time))
        #     start_time = time.time()
        #     sf21Upsert()
        #     print("--- %s seconds ---" % (time.time() - start_time))
        #     start_time = time.time()
        #     sf21Id()
        #     print("--- %s seconds ---" % (time.time() - start_time))
        #     timeStamp = time.strftime("%H:%M:%S")+'-'+time.strftime("%d/%m/%Y")
        #     # uploadBox(timeStamp)
        #     print timeStamp
        # except Exception as e:
        #     print str(e)
        #     errorEmail('SF Migration Error: '+str(e))