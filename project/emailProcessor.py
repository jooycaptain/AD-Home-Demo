
from flask import Flask, request, url_for
import simplejson
from project import app
from project import urlHome
import requests
import json
from datetime import datetime
from datetime import date,timedelta
#import pandas as pd
import csv
import os
#from pandastable import weeklystatus
import MySQLdb
from MySQLdb import escape_string as thwart
from dbconnect import connection
import gc
from box import sync, unsync

from flask_mail import Mail, Message
mail = Mail(app)

from flask.ext.login import LoginManager
from flask.ext.login import login_user , logout_user , current_user , login_required
from .decorators import require_apikey
from .decorators import async

@app.route('/emailNewDesign', methods=["POST"])
@require_apikey
def emailNewDesign():
    try:
        text = request.form["emailBody"]
        url = urlHome+'casestatus/' + text[text.find('SFDC #:')+8:text.find('Contact Name:')-2] + '?api_key=Jo3y1SAW3S0M3'
        payload = {'status' : '1'}
        response = requests.post(url, data=payload)
        subject = 'New Server New surveyed case: ' + text[text.find('SFDC #:')+8:text.find('Contact Name:')-2]
        msg = Message(subject, sender=('AD - Please Reply To All','adrobot@levelsolar.com'), recipients=['joey.jiao@levelsolar.com'])
        comment = text.split('Case Comments:')[1].split('Surveyor:')[0]
        comment = '#SURVEY NOTE# ' + comment[:-4]
        msg.body = str(response.status_code) + comment + '#END#' +text
        url = urlHome+'shading_matrix/' + text[text.find('SFDC #:')+8:text.find('Contact Name:')-2] + '?api_key=Jo3y1SAW3S0M3'
        requests.get(url)
        c,conn = connection()
        sfdc = text[text.find('SFDC #:')+8:text.find('Contact Name:')-2]
        
        if len(comment) > 15:
            url = urlHome+'design_note/' + text[text.find('SFDC #:')+8:text.find('Contact Name:')-2] +'?api_key=Jo3y1SAW3S0M3'
            data = { 'note': comment }
            response = requests.post(url, data=data)
        # mail.send(msg)
        return 'Ok'

    except Exception as e:
        msg = Message('Email Processor Inbound', sender=('AD - Please Reply To All','adrobot@levelsolar.com'), recipients=['joey.jiao@levelsolar.com'])
        msg.body = str(e) + text
        mail.send(msg)
        return str(e)

@app.route('/emailIssueResolved', methods=["POST"])
@require_apikey
def emailIssueResolved():
    try:
        text = request.form["emailBody"]
        subject = request.form["emailSubject"]
        msg = Message(subject, sender=('AD - Please Reply To All','adrobot@levelsolar.com'), recipients=['joey.jiao@levelsolar.com'])
        if text.find('New Server Missing Utility Number Resolved') <> -1:
            url = urlHome+'sfutt/' +  subject[:subject.find(' - Pre BMC Issue Resolved')] + '?api_key=Jo3y1SAW3S0M3'
            response = requests.get(url)
            if response.text.find('Done') <> -1:
                msg.body = subject[:subject.find(' - Pre BMC Issue Resolved')]+ ' Missing PSEG resolved' +str(response.text)
                mail.send(msg)
        return 'Ok'

    except Exception as e:
        msg = Message('Email Processor Inbound', sender=('AD - Please Reply To All','adrobot@levelsolar.com'), recipients=['joey.jiao@levelsolar.com'])
        msg.body = str(e) + text
        mail.send(msg)
        return str(e)

@app.route('/emailChangeRequest', methods=["POST"])
@require_apikey
def emailChangeRequest():
    try:
        text = request.form["emailBody"]
        subject = 'New Server ' + request.form["emailSubject"]
        msg = Message(subject, sender=('AD - Please Reply To All','adrobot@levelsolar.com'), recipients=['joey.jiao@levelsolar.com'])
        if text.find('Design Change Approval: Pass') <> -1:
            sfdc = text.split('SFDC #: ')[1].split('Notes:')[0][:-4]
            msg.body = 'From email processor. Change design cases '  + str(sfdc)
            # sync(sfdc)
            url = urlHome+'caseread?api_key=Jo3y1SAW3S0M3'
            payload = {'user_search' : sfdc}
            response = requests.post(url, data=payload)
            note = '#CHANGE DESIGN#' + text.split('Notes: ')[1].split('Design Change Approval: Pass')[0][:-8]
            url = urlHome
            requests.post(url + '/casenote/' + sfdc + '?api_key=Jo3y1SAW3S0M3', data={'note':note})
            url = urlHome+'casestatus/' + sfdc + '?api_key=Jo3y1SAW3S0M3'
            payload = {'status' : '1'}
            response = requests.post(url, data=payload)
            url = urlHome+'caseappdate_new/' + sfdc +'?api_key=Jo3y1SAW3S0M3'
            # date = datetime.now() +timedelta(days=3)
            # payload = {'app-date-new' : date.__format__("%m/%d/%Y")}
            payload = {'app-date-new' : 'Change Request'}
            response = requests.post(url, data=payload)
            c,conn = connection()
            c.execute("UPDATE cases SET shading = 'Done' WHERE caseid = (%s)",
                [thwart(sfdc)])
            conn.commit()
            c.close()
            conn.close()
            gc.collect()
            # mail.send(msg)
        else:
            subject = 'Design Change No Approval'
            msg = Message(subject, sender=('AD - Please Reply To All','adrobot@levelsolar.com'), recipients=['joey.jiao@levelsolar.com','designchange@levelsolar.com','arraydesign@levelsolar.com'])
            msg.body = str(text)
            mail.send(msg)
        return 'Ok'


    except Exception as e:
        msg = Message('Email Processor Inbound', sender=('AD - Please Reply To All','adrobot@levelsolar.com'), recipients=['joey.jiao@levelsolar.com'])
        msg.body = str(e) + text
        mail.send(msg)
        return str(e)

@app.route('/emailCADOutcome', methods=["POST"])
@require_apikey
def emailCADOutcome():
    try:
        text = request.form["emailBody"]
        subject = request.form["emailSubject"]
        msg = Message(subject, sender=('AD - Please Reply To All','adrobot@levelsolar.com'), recipients=['joey.jiao@levelsolar.com'])
        msg.body = 'From email processor.'
        if text.find('Outcome: Good to Go') <> -1:
            sfdc = text[text.find('SFDC: ')+6:text.find('Municipality: ')-13]
            if text.find('[ Sealed Rafters ] - [ false ]') <> -1:
                mail.send(msg)
                subject = sfdc + ' ' + subject.replace('CAD Outcome', 'sealed rafters')
                url = "https://levelsolar.secure.force.com/api/services/apexrest/accounts?account_number=" + sfdc
                response_dict = requests.get(url).json()
                sfid = response_dict[0]["id"]
                url = 'https://levelsolar.secure.force.com/api/services/apexrest/contacts?account=' + response_dict[0]["id"]
                response_dict = requests.get(url).json()
                size = len(response_dict)
                first = response_dict[size-1]['first_name']
                last = response_dict[size-1]['last_name']
                name = first + ' ' + last
                address = response_dict[size-1]['street_address']
                city = response_dict[size-1]['city']
                state = response_dict[size-1]['state'] + ' ' + response_dict[size-1]['zip']
                if state == 'MA':
                    msg = Message(subject, sender=('AD - Please Reply To All','adrobot@levelsolar.com'), recipients=['jamesstout926@gmail.com','adcoordinator@levelsolar.com','permitting@levelsolar.com','arraydesign@levelsolar.com','julia.peterson@levelsolar.com'])
                else:
                    msg = Message(subject, sender=('AD - Please Reply To All','adrobot@levelsolar.com'), recipients=['jamesstout926@gmail.com','adcoordinator@levelsolar.com','permitting@levelsolar.com','arraydesign@levelsolar.com'])
                if response_dict[size-1]['phone'] != None:
                    phone = response_dict[size-1]['phone']
                elif response_dict[size-1]['mobilephone'] != None:
                    phone = response_dict[size-1]['mobilephone']  
                msg.body = 'This house has sealed rafters. \nPlease schedule an architect inspection.\n\nContact Name: ' + name + '\nAddress: ' + address + '\nCity: ' + city + '\nState: ' + state + '\nMobile Phone: ' + phone + '\n\nAD Robot does not reply emails. Please reply to all.'
                mail.send(msg)
        return 'Ok'

    except Exception as e:
        msg = Message('Email Processor Inbound', sender=('AD - Please Reply To All','adrobot@levelsolar.com'), recipients=['joey.jiao@levelsolar.com'])
        msg.body = str(e) + text
        mail.send(msg)
        return str(e)

