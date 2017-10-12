from flask import Flask, render_template, session, url_for, redirect, flash, request, jsonify, abort
#from flask_weasyprint import render_pdf, HTML
from flask_mail import Mail, Message
from wtforms import Form, BooleanField, TextField, PasswordField, validators
from passlib.hash import sha256_crypt
import MySQLdb
from MySQLdb import escape_string as thwart
from dbconnect import connection
import gc
import random
from functools import wraps
import requests
import json
import datetime
import numpy as np
import subprocess
from simple_salesforce import Salesforce
from datetime import date,timedelta, datetime
import re

urlHome = 'http://adhome.levelsolar.com/'
urlSF = 'https://levelsolar.secure.force.com/api/services/apexrest/'

app = Flask(__name__, static_path='/static')

app.config['DEBUG'] = True
app.config['SESSION_TYPE'] = 'filesystem'

app.config.update(
  DEBUG = True,
  MAIL_SERVER = 'smtp.gmail.com',
  MAIL_PORT = 465,
  MAIL_USE_SSL = True,
  MAIL_USE_TLS = False,
  MAIL_USERNAME = 'adrobot@levelsolar.com',
  MAIL_PASSWORD = 'robotimrobot'
  )
mail = Mail(app)

from flask.ext.login import LoginManager
from flask.ext.login import login_user , logout_user , current_user , login_required, UserMixin
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, name, id, active=True):
        self.name = name
        self.id = id
        self.active = active

    def is_active(self):
        return self.active

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True

@login_manager.user_loader
def load_user(id):
    c,conn = connection()
    data = c.execute("SELECT * FROM users WHERE uid = (%s)",
                            [thwart(id)])
    if int(data) == 0:
        return None
    row = c.fetchone()
    data = row[2]
    username = row[1]
    uid = row[0]
    c.close()
    conn.close()
    gc.collect()
    return User(username,uid)

from .decorators import async
from .decorators import require_apikey

import box
import SFcase
import pmatrix
import AD_api

from crontab import futureInstallData


@async
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, recipients, text_body, html_body):
    msg = Message(subject, sender=('AD - Please Reply To All','adrobot@levelsolar.com'), recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    send_async_email(app, msg)

@async
def caseValidator_v2(app):
    with app.app_context():
        try:
          today = str(datetime.today())[:10]+'T05:00:00.000+0000'
          # return today
          sf = Salesforce(username='integration@levelsolar.com', password='HrNt7DrqaEfZmBqJRan9dKFzmQFp', security_token='yWlJG8lAKCq1pTBkbBMSVcKg')
          c,conn = connection()

          #cases in AD Home but not g2g or change design
          ADHome = []
          data = c.execute("SELECT caseid FROM cases WHERE aptDate NOT LIKE '%g2g-%' AND note NOT LIKE '%#CHANGE DESIGN#%' OR aptDate IS NULL")    
          for row in c:
              ADHome.append(str(row[0]))

          #cases will have a CAD meeting
          SFMeeting = []
          response = sf.query_all("SELECT interaction__c.Contact__r.Accountnumber__c, ScheduledDate__c FROM interaction__c WHERE Subject__c = 'CAD Appointment' AND ScheduledDate__c >= today AND Canceled__c = false AND Outcome_Submitted__C ='' ")
          for item in response['records']:
            SFMeeting.append(item['Contact__r']['Accountnumber__c'])

          #cases in AD Home will not have a meeting
          leftOver = list(set(ADHome) - set(SFMeeting))

          #cases in SF are canceled
          SFCancel = []
          response = sf.query_all("SELECT Account_Number__c FROM Opportunity WHERE StageName = 'Closed Lost' AND LastModifiedDate >= today")
          for item in response['records']:
            SFCancel.append(item['Account_Number__c'])

          #cases in AD Home are actually canceled
          needToCLean = []
          needToCLean = list(set(SFCancel) & set(ADHome))

          #removed canceled cases from AD Home
          for sfdc in needToCLean:
            url = urlHome + 'case/caseremove/'+str(sfdc)+'?api_key=Jo3y1SAW3S0M3'
            requests.get(url)

          #update no meeting case in AD Home
          for sfdc in leftOver:
            data = c.execute("UPDATE cases SET aptDate = 'No Meeting' WHERE caseid = (%s)",
                                [thwart(sfdc)])


          # return str(needToCLean).replace('u','q')
          # return str(len(needToCLean))


          conn.commit()
          c.close()
          conn.close()
          gc.collect()
          if len(needToCLean) > 0:
            subject = 'Following cases have been removed from AD Home'
            msg = Message(subject, sender='robotmarriao@gmail.com', recipients=['joey.jiao@levelsolar.com'])
            msg.body = str(needToCLean).replace('u','')
            mail.send(msg)
          return 'Good'
        except Exception as e:
          subject = 'Something wrong with case validator'
          msg = Message(subject, sender='robotmarriao@gmail.com', recipients=['joey.jiao@levelsolar.com'])
          msg.body = str(e)
          mail.send(msg)


designIssueSplit = {'Missing Meter Picture':'Design Change',
                     'Detached Garage':'Array Design',
                     'Panel location, access and clearance not acceptable':'Array Design',
                     'Obstruction Removal Needed':'Michael Kaffka',
                     '3 Layers of Shingles':'Michael Kaffka',
                     'Shingles/Roof to be Fixed':'Michael Kaffka',
                     'Bad Shingles':'Michael Kaffka',
                     'Tree Removal Needed':'Michael Kaffka',
                     'Two Systems Proposed':'Array Design',
                     'Pre G2G Design Change':'Array Design',
                     'Site Survey Needs Second Visit':'Array Design',
                     'Site Survey Info Missing':'Array Design',
                     'AD Request':'Array Design',
                     'Other':'Array Design',
                     'Sealed Rafters':'Array Design',
                     'Missing Sales Pictures':'Design Change',
                     'Bad TSRF':'Design Change',
                     'Missing Utility Number':'Design Change',
                     'Missing Electricity Consumption':'Design Change',
                     'Energy Audit':'Design Change',
                     'Rusted Meter':'Design Change',
                     'Breaker Issue':'Design Change',
                     'Breaker Issue - Missing Cover':'Design Change',
                     'CO Issues':'Design Change',
                     'Obvious violations or safety concerns':'Electrical',
                     'Trenching is needed':'Electrical',
                     'Meter pan condition not acceptable':'Electrical',
                     'Meter pan access and space requirements not acceptable':'Electrical',
                     'Panel location, access and clearance not acceptable':'Electrical',
                     'Water main is not accessible':'Electrical',
                     'Weather head condition / point of attachment not acceptable':'Electrical',
                     'Panel upgrade/swap needed':'Electrical',
                     'Floating rafters':'Ops',
                     'Visible signs of pre existing home damage':'Ops',
                     'Shingle type and condition not acceptable':'Ops',
                     'Exterior of roof surfaces does not appears Flat and is not structurally sound':'Ops',
                     'Interior of surfaces does not appear structurally sound':'Ops',
                     'More than 1 layer of plywood':'Ops',
                     'No access to attic':'Ops',
                     'More than 2 layers of shingles':'Ops',
                     'Signs of pre existing roof issues interior or exterior':'Ops'}

@app.route("/G2GWBMC/")
@require_apikey
def G2GWBMC():
  try:
    today = str(datetime.today())
    subject = 'G2Gs are waiting! ' + today[:10]
    msg = Message(subject, sender=('AD - Please Reply To All','adrobot@levelsolar.com'), recipients=['arraydesign@levelsolar.com','designchange@levelsolar.com','joey.jiao@levelsolar.com','michael.kaffka@levelsolar.com','colleen.long@levelsolar.com','josh.lilly@levelsolar.com','brandon.parlante@levelsolar.com','diego.aguilar@levelsolar.com','james.tornabene@levelsolar.com','anthony.quezada@levelsolar.com','zak.elgart@levelsolar.com','steven.elliott@levelsolar.com','pamela.bortnick@levelsolar.com','gabrielle.andersen@levelsolar.com','andrew.drewchin@levelsolar.com','steven.cook@levelsolar.com','opsissues@levelsolar.com','michael.tarzian@levelsolar.com','halvard.lange@levelsolar.com','sam.magliaro@levelsolar.com','stella.miller@levelsolar.com','samantha.taylor@levelsolar.com','makeda.barrett@levelsolar.com','laura.suarez@levelsolar.com'])

    c,conn = connection()
    data = c.execute("select caseid, status, aptDate, info from cases where status = '1' and (aptDate != 'On Hold')")
    backlog = 0
    realBacklog = 0
    realBacklog2d = 0
    needconsumption2d = 0
    realBacklog2dmore = 0
    needconsumption2dmore = 0
    nycBacklog = 0
    pendingClose = 0
    for row in c:
        info = str(row[3])
        au = 0
        if info.find('AUS:') != -1:
            au = info[info.find('AUS:')+4:info.find(';',info.find('AUS:'))]
        if len(au) > 0 and row[2] != 'g2g-now':
            realBacklog +=1
            try:
                CAD_date = str(row[2])
                if CAD_date != 'g2g-now' and CAD_date != None:
                    month = int(CAD_date.split("/")[0])
                    day = int(CAD_date.split("/")[1].split("/",2)[0])
                    year = int('20'+CAD_date.split(str(day)+'/20')[1])
                    dateapt = datetime(year,month,day)
                    twod = datetime.now()+timedelta(days=3) > dateapt
                    onew = datetime.now()+timedelta(days=7) > dateapt
                    if twod:
                        realBacklog2d += 1
                    else:
                        realBacklog2dmore += 1
            except Exception as e:
                realBacklog2dmore += 1
        else:
            try:
                CAD_date = str(row[2])
                if CAD_date != 'g2g-now' and CAD_date != None:
                    month = int(CAD_date.split("/")[0])
                    day = int(CAD_date.split("/")[1].split("/",2)[0])
                    year = int('20'+CAD_date.split(str(day)+'/20')[1])
                    dateapt = datetime(year,month,day)
                    twod = datetime.now()+timedelta(days=3) > dateapt
                    onew = datetime.now()+timedelta(days=7) > dateapt
                    if twod:
                        needconsumption2d += 1
                    else:
                        needconsumption2dmore += 1
            except Exception as e:
                needconsumption2dmore += 1
        if row[2] == 'g2g-now':
            nycBacklog +=1
        backlog +=1

    data = c.execute("select caseid, status, aptDate, info from cases where (status = '2' or status = '1.5') and (aptDate != 'On Hold')")
    for row in c:
      pendingClose += 1

    msg.html = '<html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"><style type="text/css" media="screen">table {border-collapse:collapse;width: 100%;}th, td {text-align:left;padding: 8px;}tr:nth-child(even){background-color: #f2f2f2}</style></head><body><table style="width:1200;border:1px solid black;margin-bottom:20px;padding-top:7px;padding-bottom:7px"><tr><th style="text-decoration:underline;width:12%;text-align:left">AD Backlog</th><th style="text-decoration:underline;width:22%;text-align:left">CAD In 2 Days</th><th style="text-decoration:underline;width:22%;text-align:left">CAD More Than 2 Days</th><th style="text-decoration:underline;width:22%;text-align:left">Design Pending To Be Closed</th><th style="text-decoration:underline;width:22%;text-align:left">G2G Finalization</th></tr>'
    msg.html = msg.html + '<tr><td>#</td><td>' + str(realBacklog2d) + '</td><td>' + str(realBacklog2dmore) + '</td><td>' + str(pendingClose) + '</td><td>' + str(nycBacklog) + '</td></tr></table>'

    

    sf = Salesforce(username='integration@levelsolar.com', password='HrNt7DrqaEfZmBqJRan9dKFzmQFp', security_token='yWlJG8lAKCq1pTBkbBMSVcKg')
    today = str(datetime.today())
    response = sf.query_all("SELECT Id, StageName, Latest_CAD_Outcome__c FROM Opportunity WHERE (Latest_CAD_Outcome__c = 'goodtogo' OR Latest_CAD_Outcome__c = 'Good to Go') AND (StageName = 'Array Design' or StageName = 'Array Design Ready')")
    OppowG2G = []
    for item in response['records']:
      try:
        OppowG2G.append(item['Id'])
      except:
        pass

    response = sf.query("SELECT Case.Contact.Accountnumber__c,Case.Opportunity__r.Id, Status FROM Case WHERE Record_Type_Bucket__c = 'design' AND (Status = 'Soft Close' OR Status = 'Draft') AND Case.Opportunity__r.Id in " + str(OppowG2G).replace("u'","'").replace('[','(').replace(']',')').replace(' ',''))
    G2GSoftId = []
    for item in response['records']:
      G2GSoftId.append(item['Opportunity__r']['Id'])

    response = sf.query_all("SELECT AccountNumber__c, Pre_BMC_Status_Issue__c, Pre_BMC__c.Opportunity__r.Id FROM Pre_BMC__c WHERE AccountNumber__c !=null AND Pre_BMC_Resolved__c = false AND Pre_BMC__c.Opportunity__r.Id in " + str(OppowG2G).replace("u'","'").replace('[','(').replace(']',')').replace(' ',''))
    G2GwBMCId = []
    for item in response['records']:
      G2GwBMCId.append(item['Opportunity__r']['Id'])

    G2GBMCBacklogID = list(set(G2GSoftId) & set(G2GwBMCId))

    response = sf.query_all("SELECT AccountNumber__c, Pre_BMC_Status_Issue__c, Pre_BMC__c.Opportunity__r.Id, Pre_BMC__c.Opportunity__r.SalesRepE__c, Id, Pre_BMC__c.Contact__r.Name, Notes__c, Opportunity__r.SalesRepE__r.Name FROM Pre_BMC__c WHERE AccountNumber__c !=null AND Pre_BMC_Status_Issue__c != 'Meter is not grounded' AND Pre_BMC_Resolved__c = false AND Pre_BMC__c.Opportunity__r.Id in " + str(G2GBMCBacklogID).replace("u'","'").replace('[','(').replace(']',')').replace(' ',''))

    msg.html = msg.html + '<table style="width:1200;border:1px solid black;margin-bottom:20px;padding-top:7px;padding-bottom:7px"><tr><th style="text-decoration:underline;width:12%;text-align:left">AD Waiting List</th><th style="text-decoration:underline;width:22%;text-align:left">CAD In 2 Days Need Consumption</th><th style="text-decoration:underline;width:44%;text-align:left">CAD More Than 2 Days Need Consumption</th><th style="text-decoration:underline;width:22%;text-align:left">G2G With Issues</th></tr>'
    msg.html = msg.html + '<tr><td>#</td><td>' + str(needconsumption2d) + '</td><td>' + str(needconsumption2dmore) + '</td><td>' + str(len(response['records'])) + '</td></tr></table>'

    # msg.html = msg.html + '<div>Current Size of Pre-BMC Backlog with G2G: ' + str(len(G2GwBMCId)) + '<br>'

    g2gRespobsibleList = {'Michael Kaffka':0,
                          'Design Change':0,
                          'Array Design':0,
                          'Electrical':0,
                          'Ops':0}

    for item in response['records']:
      g2gRespobsibleList[designIssueSplit[item['Pre_BMC_Status_Issue__c']]] += 1
    
    msg.html = msg.html + '<p>G2G With Issues Breakdown</p>'

    msg.html = msg.html + '<table style="width:300px;border:1px solid black;margin-bottom:20px;padding-top:7px;padding-bottom:7px"><tr><th style="text-decoration:underline;width:80%;text-align:left">G2G With Issue</th><th style="text-decoration:underline;width:20%;text-align:left">#</th></tr>'
    msg.html = msg.html + '<tr><td>Michael Kaffka Follow Up</td><td>' + str(g2gRespobsibleList['Michael Kaffka']) + '</td></tr>'
    msg.html = msg.html + '<tr><td>CAD Coordinator Follow Up</td><td>' + str(g2gRespobsibleList['Design Change']) + '</td></tr>'
    msg.html = msg.html + '<tr><td>Array Design Follow Up</td><td>' + str(g2gRespobsibleList['Array Design']) + '</td></tr>'
    msg.html = msg.html + '<tr><td>Electrical Team Follow Up</td><td>' + str(g2gRespobsibleList['Electrical']) + '</td></tr>'
    msg.html = msg.html + '<tr><td>Ops Team Follow Up</td><td>' + str(g2gRespobsibleList['Ops']) + '</td></tr></table>'
    # msg.html = msg.html + '<table style="width:600;border:1px solid black;margin-bottom:20px;padding-top:7px;padding-bottom:7px"><tr><th style="text-decoration:underline;width:60%;text-align:left">AD Waiting List</th><th style="text-decoration:underline;width:40%;text-align:left">CAD In 2 Days Need Consumption</th></tr>'
    
    msg.html = msg.html + '<p>Michael Kaffka:</p><table style="width:1200px;border:1px solid black;margin-bottom:20px;padding-top:7px;padding-bottom:7px"><tr><th style="text-decoration:underline;width:10%;text-align:left">SFDC</th><th style="text-decoration:underline;width:15%;text-align:left">Name</th><th style="text-decoration:underline;width:15%;text-align:left">Consultant</th><th style="text-decoration:underline;width:20%;text-align:left">Pre-BMC</th><th style="text-decoration:underline;width:40%;text-align:left">Pre-BMC Note</th></tr>'
    for item in response['records']:
      if designIssueSplit[item['Pre_BMC_Status_Issue__c']] == 'Michael Kaffka':
        msg.html = msg.html + '<tr><td><a href="https://levelsolar.my.salesforce.com/'+item['Opportunity__r']['Id']+'" >' + item['AccountNumber__c'] + '</a></td><td>' + item['Contact__r']['Name'] + '</td><td>' + item['Opportunity__r']['SalesRepE__r']['Name'] + '</td><td><a href="https://levelsolar.my.salesforce.com/'+item['Id']+'" >' + item['Pre_BMC_Status_Issue__c'] + '</a></td>'
        try:
          msg.html = msg.html+'<td>'+item['Notes__c']+'</td></tr>'
        except:
          msg.html = msg.html+'<td>' +'</td></tr>'
    msg.html = msg.html + '</table>'

    msg.html = msg.html +  '<p>CAD Coordinator:</p><table style="width:1200px;border:1px solid black;margin-bottom:20px;padding-top:7px;padding-bottom:7px"><tr><th style="text-decoration:underline;width:10%;text-align:left">SFDC</th><th style="text-decoration:underline;width:15%;text-align:left">Name</th><th style="text-decoration:underline;width:15%;text-align:left">Consultant</th><th style="text-decoration:underline;width:20%;text-align:left">Pre-BMC</th><th style="text-decoration:underline;width:40%;text-align:left">Pre-BMC Note</th></tr>'
    for item in response['records']:
      if designIssueSplit[item['Pre_BMC_Status_Issue__c']] == 'Design Change':
        msg.html = msg.html + '<tr><td><a href="https://levelsolar.my.salesforce.com/'+item['Opportunity__r']['Id']+'" >' + item['AccountNumber__c'] + '</a></td><td>' + item['Contact__r']['Name'] + '</td><td>' + item['Opportunity__r']['SalesRepE__r']['Name'] + '</td><td><a href="https://levelsolar.my.salesforce.com/'+item['Id']+'" >' + item['Pre_BMC_Status_Issue__c'] + '</a></td>'
        try:
          msg.html = msg.html+'<td>'+item['Notes__c']+'</td></tr>'
        except:
          msg.html = msg.html+'<td>' +'</td></tr>'
    msg.html = msg.html + '</table>'

    msg.html = msg.html + '<p>Array Design:</p><table style="width:1200px;border:1px solid black;margin-bottom:20px;padding-top:7px;padding-bottom:7px"><tr><th style="text-decoration:underline;width:10%;text-align:left">SFDC</th><th style="text-decoration:underline;width:15%;text-align:left">Name</th><th style="text-decoration:underline;width:15%;text-align:left">Consultant</th><th style="text-decoration:underline;width:20%;text-align:left">Pre-BMC</th><th style="text-decoration:underline;width:40%;text-align:left">Pre-BMC Note</th></tr>'
    for item in response['records']:
      if designIssueSplit[item['Pre_BMC_Status_Issue__c']] == 'Array Design':
        msg.html = msg.html + '<tr><td><a href="https://levelsolar.my.salesforce.com/'+item['Opportunity__r']['Id']+'" >' + item['AccountNumber__c'] + '</a></td><td>' + item['Contact__r']['Name'] + '</td><td>' + item['Opportunity__r']['SalesRepE__r']['Name'] + '</td><td><a href="https://levelsolar.my.salesforce.com/'+item['Id']+'" >' + item['Pre_BMC_Status_Issue__c'] + '</a></td>'
        try:
          msg.html = msg.html+'<td>'+item['Notes__c']+'</td></tr>'
        except:
          msg.html = msg.html+'<td>' +'</td></tr>'
    msg.html = msg.html + '</table>'

    msg.html = msg.html + '<p>Electrical Team:</p><table style="width:1200px;border:1px solid black;margin-bottom:20px;padding-top:7px;padding-bottom:7px"><tr><th style="text-decoration:underline;width:10%;text-align:left">SFDC</th><th style="text-decoration:underline;width:15%;text-align:left">Name</th><th style="text-decoration:underline;width:15%;text-align:left">Consultant</th><th style="text-decoration:underline;width:20%;text-align:left">Pre-BMC</th><th style="text-decoration:underline;width:40%;text-align:left">Pre-BMC Note</th></tr>'
    for item in response['records']:
      if designIssueSplit[item['Pre_BMC_Status_Issue__c']] == 'Electrical':
        msg.html = msg.html + '<tr><td><a href="https://levelsolar.my.salesforce.com/'+item['Opportunity__r']['Id']+'" >' + item['AccountNumber__c'] + '</a></td><td>' + item['Contact__r']['Name'] + '</td><td>' + item['Opportunity__r']['SalesRepE__r']['Name'] + '</td><td><a href="https://levelsolar.my.salesforce.com/'+item['Id']+'" >' + item['Pre_BMC_Status_Issue__c'] + '</a></td>'
        try:
          msg.html = msg.html+'<td>'+item['Notes__c']+'</td></tr>'
        except:
          msg.html = msg.html+'<td>' +'</td></tr>'
    msg.html = msg.html + '</table>'

    msg.html = msg.html + '<p>Ops Team:</p><table style="width:1200px;border:1px solid black;margin-bottom:20px;padding-top:7px;padding-bottom:7px"><tr><th style="text-decoration:underline;width:10%;text-align:left">SFDC</th><th style="text-decoration:underline;width:15%;text-align:left">Name</th><th style="text-decoration:underline;width:15%;text-align:left">Consultant</th><th style="text-decoration:underline;width:20%;text-align:left">Pre-BMC</th><th style="text-decoration:underline;width:40%;text-align:left">Pre-BMC Note</th></tr>'
    for item in response['records']:
      if designIssueSplit[item['Pre_BMC_Status_Issue__c']] == 'Ops':
        msg.html = msg.html + '<tr><td><a href="https://levelsolar.my.salesforce.com/'+item['Opportunity__r']['Id']+'" >' + item['AccountNumber__c'] + '</a></td><td>' + item['Contact__r']['Name'] + '</td><td>' + item['Opportunity__r']['SalesRepE__r']['Name'] + '</td><td><a href="https://levelsolar.my.salesforce.com/'+item['Id']+'" >' + item['Pre_BMC_Status_Issue__c'] + '</a></td>'
        try:
          msg.html = msg.html+'<td>'+item['Notes__c']+'</td></tr>'
        except:
          msg.html = msg.html+'<td>' +'</td></tr>'
    msg.html = msg.html + '</table>'
    

    msg.html = msg.html + '<h4>--------------------------------------------------</h4><p>Thank you!</p></body></html>'
      
    mail.send(msg)
    return 'good'
  except Exception as e:
    subject = 'G2G w BMC email didnot go out'
    msg = Message(subject, sender='robotmarriao@gmail.com', recipients=['joey.jiao@levelsolar.com'])
    msg.body = str(e)
    mail.send(msg)
    return str(e) + ' ' + str(item)

@app.route("/salesFolder/")
@require_apikey
def salesFolder():
  try:
    today = str(datetime.today())
    subject = 'Sales Folder Update ' + today[:10]
    msg = Message(subject, sender=('AD - Please Reply To All','adrobot@levelsolar.com'), recipients=['adteam@levelsolar.com','arraydesign@levelsolar.com'])
    # msg = Message(subject, sender=('AD - Please Reply To All','adrobot@levelsolar.com'), recipients=['joey.jiao@levelsolar.com'])

    sf = Salesforce(username='integration@levelsolar.com', password='HrNt7DrqaEfZmBqJRan9dKFzmQFp', security_token='yWlJG8lAKCq1pTBkbBMSVcKg')
    
    today = str(datetime.today())[:10]+'T05:00:00.000+0000'
    response = sf.query("SELECT Case.Contact.Accountnumber__c, Status FROM Case WHERE Record_Type_Bucket__c = 'design' AND (Status ='Closed' OR Status = 'Cancelled') AND LastModifiedDate >= today")
    SFClosed = []
    for item in response['records']:
      SFClosed.append(item['Contact']['Accountnumber__c'])


    base='https://api.box.com/2.0/folders/'
    token = box.token_verify()
    headers =  {'Authorization': 'Bearer ' + token}
    json_r = requests.get(base + '2658582399/items?limit=1000&offset=0', headers=headers).json()
    json_r2 = requests.get(base + '2658582399/items?limit=1000&offset=1000', headers=headers).json()

    folder = {}
    for item in json_r['entries']:
      try:
        numbers =  map(int, re.findall(r'\d+', item['name']))
        for number in numbers:
          folder[number]=item['id']
      except Exception as e:
        pass

    for item in json_r2['entries']:
      try:
        numbers =  map(int, re.findall(r'\d+', item['name']))
        for number in numbers:
          folder[number]=item['id']
      except Exception as e:
        pass
    msg.html = 'Current Size of Shared Folder: ' + str(json_r['total_count']) + ' Subfolders <br>'

    response = sf.query_all("SELECT AccountNumber__c, Pre_BMC_Status_Issue__c, Pre_BMC__c.Opportunity__r.Id FROM Pre_BMC__c WHERE AccountNumber__c !=null AND Pre_BMC_Resolved__c = false AND Pre_BMC_Status_Issue__c='Missing Sales Pictures' AND Opportunity_Stage__c != 'Closed Lost' AND Pre_BMC_Postponed__c = false")
    PhotoBMC = []
    BMCInShare = []
    CaseGone = []
    for item in response['records']:
      PhotoBMC.append(item['AccountNumber__c'])

    for item in folder:
      try:
        
        if str(item) in SFClosed:
          requests.delete(base + folder[item] + '?recursive=true', headers=headers)
          CaseGone.append(item)
        if str(item) in PhotoBMC:
          folder_response = requests.get(base + folder[item] + '?fields=modified_at,modified_by', headers=headers).json()
          modifyedDate = datetime.strptime(folder_response['modified_at'][:-6], "%Y-%m-%dT%H:%M:%S")+timedelta(days=1)
          today = datetime.strptime(str(datetime.today())[:10]+'T00:00:00', "%Y-%m-%dT%H:%M:%S")
          if modifyedDate > today:
            msg.html = msg.html + '<br><a href="https://levelsolar.app.box.com/files/0/f/'+folder[item]+'" >' + str(item) + '</a> modified by: ' + folder_response['modified_by']['name'] + ' at: ' + folder_response['modified_at'][:-6]
          BMCInShare.append(str(item))
      except Exception as e:
        return str(e) + ' wrong here'

    NotInBox = list(set(PhotoBMC) - set(BMCInShare))
    if len(NotInBox) > 0:
      msg.html = msg.html + '<br><br>' +'Following folders have been removed from Shared, but have a Pre-BMC of Missing Sales Pictures open. Sales will need a new one to upload.'
      msg.html = msg.html + '<br>' + str(NotInBox).replace('u','')
    if len(CaseGone) > 0:
      msg.html = msg.html + '<br><br>' +'Following folders have been removed from Shared because Design case is closed.'
      msg.html = msg.html + '<br>' + str(CaseGone).replace('u','')
    mail.send(msg)
    return 'good'
  except Exception as e:
    return str(e)

@app.route("/caseValidator/")
@require_apikey
def caseValidator():
  try:
    today = str(datetime.today())[:10]+'T05:00:00.000+0000'
    # return today
    sf = Salesforce(username='integration@levelsolar.com', password='HrNt7DrqaEfZmBqJRan9dKFzmQFp', security_token='yWlJG8lAKCq1pTBkbBMSVcKg')
    c,conn = connection()

    #cases in AD Home but not g2g or change design
    ADHome = []
    data = c.execute("SELECT caseid FROM cases WHERE aptDate NOT LIKE '%g2g-%' AND aptDate != 'Change Request' AND note NOT LIKE '%#CHANGE DESIGN#%' OR aptDate IS NULL")    
    for row in c:
        ADHome.append(str(row[0]))

    #cases will have a CAD meeting
    SFMeeting = []
    response = sf.query_all("SELECT interaction__c.Contact__r.Accountnumber__c, ScheduledDate__c FROM interaction__c WHERE Subject__c = 'CAD Appointment' AND ScheduledDate__c >= today AND Canceled__c = false AND Outcome_Submitted__C ='' ")
    for item in response['records']:
      SFMeeting.append(item['Contact__r']['Accountnumber__c'])

    #cases in AD Home will not have a meeting
    leftOver = list(set(ADHome) - set(SFMeeting))

    #cases in SF are canceled
    SFCancel = []
    response = sf.query_all("SELECT Account_Number__c FROM Opportunity WHERE StageName = 'Closed Lost'")
    for item in response['records']:
      SFCancel.append(item['Account_Number__c'])

    #cases in AD Home are On Hold
    SFOnHold = []
    response = sf.query_all("SELECT Account_Number__c FROM Opportunity WHERE StageName = 'On Hold'")
    for item in response['records']:
      SFOnHold.append(item['Account_Number__c'])

    #cases in AD Home are actually canceled
    needToCLean = []
    needToCLean = list(set(SFCancel) & set(ADHome))

    #cases in AD Home are actually on hold
    onHold = []
    onHold = list(set(SFOnHold) & set(ADHome))

    #removed canceled cases from AD Home
    for sfdc in needToCLean:
      url = urlHome + 'case/caseremove/'+str(sfdc) +'?api_key=Jo3y1SAW3S0M3'
      requests.get(url)

    #update no meeting case in AD Home
    for sfdc in leftOver:
      data = c.execute("UPDATE cases SET aptDate = 'No Meeting' WHERE caseid = (%s)",
                          [thwart(sfdc)])

    #update on hold case in AD Home
    for sfdc in onHold:
      data = c.execute("UPDATE cases SET aptDate = 'On Hold' WHERE caseid = (%s)",
                          [thwart(sfdc)])

    conn.commit()
    c.close()
    conn.close()
    gc.collect()
    if len(needToCLean) > 0:
      subject = 'Following cases have been removed from AD Home'
      msg = Message(subject, sender='robotmarriao@gmail.com', recipients=['joey.jiao@levelsolar.com'])
      msg.body = str(needToCLean).replace('u','')
      mail.send(msg)
    return 'Good'
  except Exception as e:
    subject = 'Something wrong with case validator'
    msg = Message(subject, sender='robotmarriao@gmail.com', recipients=['joey.jiao@levelsolar.com'])
    msg.body = str(e)
    mail.send(msg)

@app.route("/aptUpdate/")
@require_apikey
def aptUpdate():
  try:
    today = str(datetime.today())[:10]+'T05:00:00.000+0000'
    sf = Salesforce(username='integration@levelsolar.com', password='HrNt7DrqaEfZmBqJRan9dKFzmQFp', security_token='yWlJG8lAKCq1pTBkbBMSVcKg')
    response = sf.query("SELECT interaction__c.Contact__r.Accountnumber__c, ScheduledDate__c FROM interaction__c WHERE Subject__c = 'CAD Appointment' AND ScheduledDate__c >= today AND Canceled__c = false AND Outcome__c ='' ")
    c,conn = connection()
    listUpdate = []
    listOut = []

    for item in response['records']:
      x = c.execute("SELECT * FROM cases WHERE caseid = (%s)",
                    [thwart(str(item['Contact__r']['Accountnumber__c']))])
      row = c.fetchone()
      if int(x) != 0 and str(row[11]).find('g2g') == -1:
        dateDay = item['ScheduledDate__c'][8:10]
        aptDate = datetime.strptime(item['ScheduledDate__c'][:-5], "%Y-%m-%dT%H:%M:%S.%f")
        if int(item['ScheduledDate__c'][11:13]) < 5:
          aptDate = str(aptDate+timedelta(days=-1))
        else:
          aptDate = str(aptDate)
        if row[11] == None or row[11][:2] != aptDate[5:7] or row[11][3:5] != aptDate[8:10]:
          date = aptDate[5:7]+'/'+aptDate[8:10]+'/'+item['ScheduledDate__c'][:4]
          data = c.execute("UPDATE cases SET aptDate = (%s) WHERE caseid = (%s)",
                     [thwart(date),thwart(str(item['Contact__r']['Accountnumber__c']))])
          listUpdate.append([item['Contact__r']['Accountnumber__c'],row[11],aptDate])
      elif int(x) == 0:
        url = 'https://levelsolar.secure.force.com/api/services/apexrest/v2/opportunities?account_number=' + item['Contact__r']['Accountnumber__c']
        response_dict = requests.get(url).json()
        try:
          if response_dict[0]["array_design_completed_date"] == None:
            listOut.append(item['Contact__r']['Accountnumber__c'])
        except:
          pass
    
    if len(listOut) > 0:
      subject = 'Please double check the following cases'
      msg = Message(subject, sender='robotmarriao@gmail.com', recipients=['adcoordinator@levelsolar.com','michael.tarzian@levelsolar.com'])
      msg.body = 'The following cases are not in AD Home, but will have a meeting soon: ' + str(listOut).replace('u','')
      mail.send(msg)
    
    if len(listUpdate) > 0:
      subject = 'Following cases has been updated'
      msg = Message(subject, sender='robotmarriao@gmail.com', recipients=['joey.jiao@levelsolar.com'])
      msg.body = str(listUpdate).replace('u','')
      mail.send(msg)
    conn.commit()
    c.close()
    conn.close()
    gc.collect()

    c,conn = connection()

    response = sf.query_all("SELECT Id, StageName, Latest_CAD_Outcome__c, Good_to_Go_Date__c FROM Opportunity WHERE (Latest_CAD_Outcome__c = 'goodtogo' OR Latest_CAD_Outcome__c = 'Good to Go') AND (StageName = 'Array Design' or StageName = 'Array Design Ready')")
    OppowG2G = []
    for item in response['records']:
      try:
        OppowG2G.append(item['Id'])
      except:
        pass

    response = sf.query("SELECT Case.Contact.Accountnumber__c, Status FROM Case WHERE Record_Type_Bucket__c = 'design' AND (Status = 'New') AND Case.Opportunity__r.Id in " + str(OppowG2G).replace("u'","'").replace('[','(').replace(']',')').replace(' ',''))
    G2GNew = []
    for item in response['records']:
      G2GNew.append(item['Contact']['Accountnumber__c'])
    print "New Design Cases With A G2G: " + str(len(G2GNew))
    print str(G2GNew).replace('u','')

    response = sf.query("SELECT Case.Contact.Accountnumber__c, Status FROM Case WHERE Record_Type_Bucket__c = 'design' AND (Status = 'Soft Close' OR Status = 'Draft') AND Case.Opportunity__r.Id in " + str(OppowG2G).replace("u'","'").replace('[','(').replace(']',')').replace(' ',''))
    G2GSoft = []
    for item in response['records']:
      G2GSoft.append(item['Contact']['Accountnumber__c'])

    response = sf.query_all("SELECT AccountNumber__c, Pre_BMC_Status_Issue__c, Pre_BMC__c.Opportunity__r.Id FROM Pre_BMC__c WHERE AccountNumber__c !=null AND Pre_BMC_Resolved__c = false AND Pre_BMC_Status_Issue__c != 'Meter is not grounded' AND Pre_BMC__c.Opportunity__r.Id in " + str(OppowG2G).replace("u'","'").replace('[','(').replace(']',')').replace(' ',''))
    G2GwBMC = []
    for item in response['records']:
      G2GwBMC.append(item['AccountNumber__c'])

    G2GSoftBacklog = list(set(G2GSoft) - set(G2GwBMC))
    G2GNoHome = []
    for item in G2GSoftBacklog:
      x = c.execute("SELECT * FROM cases WHERE caseid = (%s)",
                    [thwart(str(item))])
      if int(x) == 0:
        G2GNoHome.append(str(item))
      else:
        row = c.fetchone()
        if int(x) != 0 and str(row[11]) != 'g2g-now':
          data = c.execute("UPDATE cases SET aptDate = 'g2g-now' WHERE caseid = (%s)",
                       [thwart(str(item))])
        if int(x) != 0 and float(row[3]) > 2:
          url = urlHome+'casestatus/' + str(item) + '?api_key=Jo3y1SAW3S0M3'
          payload = {'status' : '1'}
          response = requests.post(url, data=payload)        
        
    if len(G2GNoHome) > 0:
      subject = 'Following G2G cases not in AD Home but needs to be finalized'
      msg = Message(subject, sender='robotmarriao@gmail.com', recipients=['joey.jiao@levelsolar.com'])
      msg.body = str(G2GNoHome).replace('u','')
      mail.send(msg)
    conn.commit()
    c.close()
    conn.close()
    gc.collect()
    return 'Good'
  except Exception as e:
    subject = 'CAD Apt sync problem'
    msg = Message(subject, sender='robotmarriao@gmail.com', recipients=['joey.jiao@levelsolar.com'])
    msg.body = 'Syncing has some problem: ' + str(e) + str(item)
    mail.send(msg)
    return str(e)
 
@app.route("/shawnMail/")
@login_required
def shawnMail():
  try:
    shawnSubject = str(request.args.get('shawnSubject'))
    if shawnSubject.find('-') == -1:
      return jsonify(result='Select issues first!')
    shawnContent = str(request.args.get('shawnContent'))
    shawnMsg = str(request.args.get('shawnMsg'))
    if shawnMsg.find('More to say? (Click to edit)') >= 0:
      shawnMsg = ''
    else:
      shawnMsg = shawnMsg+'\n'
    subject = shawnSubject[9:]
    recipients=['arraydesign@levelsolar.com','lenny.ruchefsky@levelsolar.com@levelsolar.com','permitting@levelsolar.com','eric.negron@levelsolar.com','david.bujan@levelsolar.com','tom.pittsley@levelsolar.com','nick.truong@levelsolar.com','Pat.Duffy@levelsolar.com','michael.tarzian@levelsolar.com']
    # recipients=['joey.jiao@levelsolar.com']
    send_email(subject, recipients, 'Hi There:\n\n' + shawnContent + '\n' + shawnMsg + '\nAD Robot does not reply emails. Please reply to all. Thank you!', '')
    return jsonify(result='Sent!')

  except Exception as e:
    return jsonify(result=str(e))

@app.route("/background_process/")
@login_required
def background_process():
  try:
    months = int(request.args.get('months'))
    consumption = float(request.args.get('consumption'))
    m = int(datetime.now().strftime("%m"))
    distribution = [9.43,8.6,7.88,6.27,6.85,9.28,10.38,9.81,8.04,7.33,7.52,8.61]
    if months > m - 1:
        share = np.sum(distribution[:m-1]) + np.sum(distribution[11-months+m:]) 
    else:
        share = np.sum(distribution[m-months-1:m-1])
    consumption = int(consumption/share*100)
    return jsonify(result=consumption)
    sfid = request.args.get('sfid')
    if str(lang).lower() == 'python':
        return jsonify(result='You are wise!')
    else:
        return  jsonify(result='Try again')
  except Exception as e:
        return jsonify(result=str(e))

@app.route("/fetchInstallPack", methods=["POST"])
@login_required
def fetchInstallPack():
  try:
    notDone=[]
    installList = []
    installList.append(str(request.form["sfidInstall"]))
    # return str(installList)
    notDone = futureInstallData(installList)
    # return str(notDone)
    if len(notDone) <> 0:
      flash(request.form["sfidInstall"] + ' Document Corrupted. Try again.')
      flash(str(notDone))
    else:
      flash(request.form["sfidInstall"] + ' Install Pack Fetched.')
    return redirect(urlHome+'case/#Support')
  except Exception as e:
    return str(e)

@app.route("/calljoey", methods=["POST"])
@login_required
def call_joey():
  try:
    note = request.form['msg_joey']
    recip = request.form['request_email']
    subject = 'Your request for AD Home/ Service ticket#:' + str(int(random.random()*10000000))
    msg = Message(subject, sender=('AD - Please Reply To All','adrobot@levelsolar.com'), recipients=['joey.jiao@levelsolar.com',recip])
    # sender=('AD - Please Reply To All','adrobot@levelsolar.com')
    recipients=['joey.jiao@levelsolar.com',recip]
    msg.body = note
    send_email(subject, recipients, note, '')
    # mail.send(msg)
    flash('Joey will reach back to you very soon!')
    return redirect(urlHome+'case')
  except Exception as e:
        return str(e) 

@app.route("/calljoeyIncentive", methods=["POST"])
@login_required
def call_joeyIncentive():
  try:
    note = request.form['msg_joey']
    recip = request.form['request_email']
    subject = 'Your request for AD Home/ Service ticket#:' + str(int(random.random()*10000000))
    msg = Message(subject, sender=('AD - Please Reply To All','adrobot@levelsolar.com'), recipients=['joey.jiao@levelsolar.com',recip])
    # sender=('AD - Please Reply To All','adrobot@levelsolar.com')
    recipients=['joey.jiao@levelsolar.com',recip]
    msg.body = note
    send_email(subject, recipients, note, '')
    # mail.send(msg)
    flash('Joey will reach back to you very soon!')
    return redirect(urlHome+'incentive')
  except Exception as e:
        return str(e) 


          
@app.route("/privacy/")
def privacy():
  try:
    return render_template("privacy.html")
  except Exception as e:
    return str(e)

@app.route("/terms/")
def terms():
  try:
    return render_template("terms.html")
  except Exception as e:
    return str(e)



@app.route('/logout/')
@login_required
def logout():
    session.clear()
    logout_user()
    flash("You have been logged out!")
    gc.collect()
    return redirect(urlHome)

@app.route('/', methods=["GET","POST"])
def login():
  try:
    if session['logged_in'] and session['logged_in'] == True:
      return redirect(urlHome + 'case')
  except:
    error = ''
    try:
      c, conn = connection()
      if request.method == "POST":
          data = c.execute("SELECT * FROM users WHERE email = (%s)",
                          [thwart(request.form['email'])])
          if int(data) == 0:
              error = "Invalid credentials, try again."
          row = c.fetchone()
          data = row[2]
          username = row[1]
          uid = row[0]
          rank = row[6]
          if sha256_crypt.verify(request.form['password'], data) and rank <> None:
              session['logged_in'] = True
              session['username'] = username
              session['userRank'] = rank
              flash("You are now logged in")
              gc.collect()
              login_user(User(username, uid))
              return redirect(request.args.get('next') or (urlHome + 'case'))
              # return redirect(urlHome + 'case')
          elif rank == None:
              error = "Admin will approve your account very soon."
              gc.collect()
              return render_template("homepage.html", error=error)
          else:
              error = "Invalid credentials, try again."
              gc.collect()
              return render_template("homepage.html", error=error)
      else:
        return render_template("homepage.html", error=error)
    except Exception as e:
        # flash(e)
        return render_template("homepage.html", error=error)

class RegistrationForm(Form):
    username = TextField('Username', [validators.Length(min=4, max=20)])
    email = TextField('Email Address', [validators.Length(min=6, max=50)])
    password = PasswordField('New Password', [
        validators.Required(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')
    accept_tos = BooleanField('I accept the <a href="/terms/" target="blank">Terms of Service</a> and <a href="/privacy/" target="blank">Privacy Notice</a>')

#AD rank #1
#Admin #999
@app.route('/register/', methods=["GET","POST"])
def register_page():
  try:
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
      username = form.username.data
      email = form.email.data
      term = form.accept_tos.data
      password = sha256_crypt.encrypt((str(form.password.data)))
      c,conn = connection()
      x = c.execute("SELECT * FROM users WHERE username = (%s)",
          [thwart(username)])
      if int(x) > 0:
          flash("That username is already taken, please choose another one")
          return render_template('register.html', form=form)
      else:
          c.execute("INSERT INTO users (username, password, email) VALUES (%s, %s, %s)",
                  [thwart(username), thwart(password), thwart(email)])
          conn.commit()
          c.close()
          conn.close()
          gc.collect()
          flash('Thanks for registering. Your registration will be approved very soon.')
          msg = Message("New Registration On AD Home", sender=('AD - Please Reply To All','adrobot@levelsolar.com'), recipients=['joey.jiao@levelsolar.com'])
          msg.body = "Username: " + username + "\nEmail: " + email + "\n\n\n\nhttp://adhome.levelsolar.com/userApprove/" + username + "?api_key=Jo3y1SAW3S0M3"
          mail.send(msg)
          return redirect(urlHome + 'case')
    else:
      return render_template('register.html',form=form)
  except Exception as e:
          return str(e)

@app.route('/userApprove/<user>')
@require_apikey
def userApprove(user):
  try:
    c,conn = connection()
    x = c.execute("SELECT * FROM users WHERE username = (%s)",
        [thwart(user)])
    if int(x) > 0:
      c.execute("UPDATE users SET rank = 1 WHERE username = (%s)",
                    [thwart(user)])
      conn.commit()
      c.close()
      conn.close()
      gc.collect()
      return 'User approved'
    else:
      conn.commit()
      c.close()
      conn.close()
      gc.collect()
      return 'No such user'
  except Exception as e:
          return str(e)
