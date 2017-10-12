from flask import Flask, render_template, session, url_for, redirect, flash, request, jsonify
import MySQLdb
from MySQLdb import escape_string as thwart
from dbconnect import connection
from project import app
from project import urlHome
import gc
import random
import requests
from datetime import datetime
from datetime import date,timedelta
from box import sync, unsync, token_verify
import numpy as np
import json
from simple_salesforce import Salesforce
from reportlab.pdfgen import canvas
import PyPDF2
from PyPDF2 import PdfFileMerger, PdfFileReader


from flask_mail import Mail, Message
mail = Mail(app)

@app.route('/incentive/')
@login_required
def incentive():
    try:
        c,conn = connection()
        data = c.execute("SELECT * FROM incentivePrep ORDER BY FIELD(stage,'On Hold'), stage, lastModifiedDate DESC")
        CASE_DICT=[]
        SSP_count = 0
        realBack_count = 0
        listBack_count = 0
        for row in c:
            qcck = 1 if str(row[2]) == 'None' else 0
            IRFck = 1 if str(row[4]) == 'None' else 0
            BPck = 1 if str(row[5]) == 'None' else 0
            SCOLck = 1 if str(row[6]) == 'None' else 0
            
            
            CASE_DICT.append({'caseid': str(row[0]), 'name': str(row[1]),'qc': str(row[2]),'permit': str(row[3]),'IRF': str(row[4]),'BP': str(row[5]),'SCOL': str(row[6]),'note': str(row[7]),'stage': str(row[8]),'lastDate': str(row[9]),'IRFck':IRFck,'BPck':BPck,'SCOLck':SCOLck,'qcck':qcck})
        c.close()
        gc.collect()
        return render_template('nyserdaIncentive.html',info=CASE_DICT ,rBack_C = realBack_count,lBack_C = listBack_count)
    except Exception as e:
        return str(e)

@app.route('/incentive/incentiveremove/<sfdc>', methods=["GET"])
@login_required
def incentiveremove(sfdc):
  try:
    c,conn = connection()
    x = c.execute("SELECT * FROM incentivePrep WHERE caseid = (%s)",
                    [thwart(sfdc)])
    if int(x) == 0:
        return "No such case in file. Double check or create one."
    data = c.execute("DELETE FROM incentivePrep WHERE caseid = (%s)",
                [thwart(sfdc)])
    conn.commit()
    c.close()
    conn.close()
    gc.collect()
    flash('Case removed')
    return redirect(urlHome+'incentive')
  except Exception as e:
        return str(e)

def lookIntoPermit(permitId, qc):
    try:
        ck = 1 if str(qc) <> 'None' else 0

        c,conn = connection()
        token = token_verify()
        base='https://api.box.com/2.0/folders/'
        headers =  {'Authorization': 'Bearer ' + token}

        json_r = requests.get(base + permitId + '/items?limit=1000', headers=headers).json()
        data = c.execute("UPDATE incentivePrep SET SCOL = 'None', IRF = 'None', BP = 'None' WHERE folderId = (%s)",
                         [thwart(permitId)])
        for item in json_r['entries']:
            if item['type'] == 'file' and item['name'].upper().find('SCOL.PDF') > -1:
                scolId = item['id']
                data = c.execute("UPDATE incentivePrep SET SCOL = (%s) WHERE folderId = (%s)",
                         [thwart(scolId),thwart(permitId)])
                ck += 1
            if item['type'] == 'file' and item['name'].upper().find('IRF.PDF') > -1:
                irfId = item['id']
                data = c.execute("UPDATE incentivePrep SET IRF = (%s) WHERE folderId = (%s)",
                         [thwart(irfId),thwart(permitId)])
                ck += 1
            if item['type'] == 'file' and item['name'].upper().find('BP.PDF') > -1:
                bpId = item['id']
                data = c.execute("UPDATE incentivePrep SET BP = (%s) WHERE folderId = (%s)",
                         [thwart(bpId),thwart(permitId)])
                ck += 1

        today = str(datetime.today())[:10]
        data = c.execute("UPDATE incentivePrep SET lastModifiedDate = (%s) WHERE folderId = (%s)",
                         [thwart(today),thwart(permitId)])

        if ck ==4:
            data = c.execute("UPDATE incentivePrep SET stage = 'Ready' WHERE folderId = (%s)",
                         [thwart(permitId)])
            conn.commit()
            c.close()
            conn.close()
            gc.collect()
            return 'Ready'
        elif ck > 4:
            flash('Multiple files have the same suffix name. Please fix and try again.')
            return 'In Progress'
        else:
            data = c.execute("UPDATE incentivePrep SET stage = 'In Progress' WHERE folderId = (%s)",
                         [thwart(permitId)])
            conn.commit()
            c.close()
            conn.close()
            gc.collect()
            return 'In Progress'
    except Exception as e:
        return str(e)



@app.route("/incentiveNote/<permitId>", methods=["POST"])
@login_required
def incentiveNote(permitId):
  try:
    qc = request.form['incentQc']
    note = request.form['incentNote']

    c,conn = connection()
    data = c.execute("UPDATE incentivePrep SET qc = (%s) WHERE folderId = (%s)",
                     [thwart(qc),thwart(permitId)])
    data = c.execute("UPDATE incentivePrep SET note = (%s) WHERE folderId = (%s)",
                     [thwart(note),thwart(permitId)])
    conn.commit()
    c.close()
    conn.close()
    gc.collect()
    lookIntoPermit(permitId, qc)
    return redirect(urlHome+'incentive')
  except Exception as e:
        return str(e)

@app.route("/incentiveReady", methods=["GET"])
@login_required
def incentiveReady():
  try:
    c,conn = connection()
    x = c.execute("SELECT * from incentivePrep WHERE stage = 'Ready'")
    if int(x) == 0:
        return 'No one is ready.'
    else:
        token = token_verify()
        headers =  {'Authorization': 'Bearer ' + token}
        

        for row in c:
            if lookIntoPermit(row[3], row[2]) == 'Ready':
                merger = PdfFileMerger()
                for i in range (4,7):
                    url = 'https://api.box.com/2.0/files/'+str(row[i])+'/content'
                    response = requests.get(url, headers=headers)
                    pdfFile = open("/var/www/FlaskApp/project/static/pdf/MERGE.pdf", "wb")
                    pdfFile.write(response.content)
                    pdfFile.close()
                    merger.append(PdfFileReader(file("/var/www/FlaskApp/project/static/pdf/MERGE.pdf", 'rb')))
                merger.write("/var/www/FlaskApp/project/static/pdf/100NYSERDA.pdf")

                msg = Message('Box PDF', sender=('AD - Please Reply To All','adrobot@levelsolar.com'), recipients=['joey.jiao@levelsolar.com'])
                msg.body = 'Box files: '
                with app.open_resource("/var/www/FlaskApp/project/static/pdf/100NYSERDA.pdf") as fp:
                    msg.attach('Text Box.pdf', "application/pdf", fp.read())
                mail.send(msg)
            elif row[9] == 'Ready':
                data = c.execute("UPDATE incentivePrep SET stage = 'In Progress' WHERE caseid = (%s)",
                     [thwart(row[0])])


    conn.commit()
    c.close()
    conn.close()
    gc.collect()
    return redirect(urlHome+'incentive')
  except Exception as e:
        return str(e)

@app.route("/incentiveOnHold/<sfdc>", methods=["GET"])
@login_required
def incentiveOnHold(sfdc):
  try:

    c,conn = connection()
    x = c.execute("SELECT * FROM incentivePrep WHERE caseid = (%s)",
                    [thwart(sfdc)])
    row = c.fetchone()
    stage = 'In Progress' if str(row[8]) == 'On Hold' else 'On Hold'

    data = c.execute("UPDATE incentivePrep SET stage = (%s) WHERE caseid = (%s)",
                     [thwart(stage),thwart(sfdc)])
    today = str(datetime.today())[:10]
    data = c.execute("UPDATE incentivePrep SET lastModifiedDate = (%s) WHERE caseid = (%s)",
                     [thwart(today),thwart(sfdc)])
    conn.commit()
    c.close()
    conn.close()
    gc.collect()
    return redirect(urlHome+'incentive')
  except Exception as e:
        return str(e)

@app.route('/incentRead', methods=["POST"])
@login_required
def incentRead():
  try:
    today = str(datetime.today())[:10]
    stage = 'In Progress'
    casenum = request.form["user_search"]

    sf = Salesforce(username='integration@levelsolar.com', password='HrNt7DrqaEfZmBqJRan9dKFzmQFp', security_token='yWlJG8lAKCq1pTBkbBMSVcKg')
    
    response = sf.query_all("SELECT Contact_Opp__r.Name, box_permit__c FROM Opportunity WHERE Account_Number__c='"+str(casenum)+"'")
    name = response['records'][0]['Contact_Opp__r']['Name']
    permitBox = response['records'][0]['box_permit__c']

    
    c,conn = connection()

    x = c.execute("SELECT * FROM incentivePrep WHERE caseid = (%s)",
      [thwart(casenum)])    
    if int(x) > 0:
      flash("That case is already in the system, please choose another")
      return redirect(urlHome+'incentive')
    else:
      c.execute("INSERT INTO incentivePrep (caseid, name, folderId, lastModifiedDate, stage) VALUES (%s, %s, %s, %s, %s)",
              [thwart(casenum), thwart(name), thwart(permitBox), thwart(today), thwart(stage)])
      conn.commit()
      flash('Thanks for uploading')
      c.close()
      conn.close()
      gc.collect()
      
      return redirect(urlHome+'incentive')
  except Exception as e:
          return str(e)
