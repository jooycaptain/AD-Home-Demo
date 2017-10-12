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
from box import sync, unsync
import numpy as np
import json
from simple_salesforce import Salesforce
from subprocess import call



from flask_mail import Mail, Message
mail = Mail(app)
from flask.ext.login import LoginManager
from flask.ext.login import login_user , logout_user , current_user , login_required
from .decorators import require_apikey
from .decorators import async

stat = {'0':'New',
        '1':'Surveyed',
        '1.5': 'Pending',
        '2': 'Approved',
        '3': 'Change design*',
        '4': 'Redesign*',
        '5': 'Draft',
        '6': 'Need',
        '7': 'Need',
        '8': 'Bad'}
QC = {'J':'Justin Gottlieb',
      'T':'Tina Gong',
      'Y':'Yao Wang',
      'E':'Meredith Johansen',
      'R':'Ren Yu',
      'M':'Michael Tarzian'}
#AMP:200n;RSI:2x10;RSP:16r;AUS:8599;
designIssue = ['Missing Meter Picture',
               'Detached Garage',
               'Obstruction Removal Needed',
               '3 Layers of Shingles',
               'Shingles/Roof to be Fixed',
               'Tree Removal Needed',
               'Two Systems Proposed',
               'Other',
               'Sealed Rafters',
               'Missing Sales Pictures',
               'Missing Utility Number',
               'Missing Electricity Consumption',
               'Energy Audit',
               'Rusted Meter',
               'Breaker Issue']
def issueStatus(issueBi):
    if issueBi[5:8].find('1') <> -1 or issueBi[11] == '1':
        return 'Draft'
    elif issueBi.find('1') <> -1:
        return 'Soft Close'
    else:
        return 'All Ok' 

def issueBitoStr(issueBi):
    if issueBi == '00000000000000000000':
        return ''
    issueLen = 20
    issueStr = 'x'
    for i in range(0,issueLen):
        if int(issueBi[i]) != 0:
            issueStr = issueStr+'; '+str(designIssue[i])
    return issueStr[3:] 

def issueBitoArr(issueBi):
    if issueBi == '00000000000000000000':
        return ''
    issueLen = 20
    issueArr = []
    for i in range(0,issueLen):
        if int(issueBi[i]) != 0:
            issueArr.append(str(designIssue[i]))
    return issueArr

def issueStrtoBi(issueList):
  try:
    if issueList == 'All Ok' or issueList == '':
        return '00000000000000000000'
    issueList = issueList.replace(',',';')
    issueLen = 20
    issueReturn = 'x'
    issue = np.zeros(issueLen)
    issueStr = np.array(issueList.split('; '))
    for item in issueStr:
      try:
        issue[designIssue.index(item)] = 1
      except:
        return 'Not good'
    for item in issue:
        issueReturn = issueReturn+str(int(item)) 
    return issueReturn[1:]
  except Exception as e:
        return str(e)

def ADInfo2SF(sfdc, info):
    try:
        sf = Salesforce(username='integration@levelsolar.com', password='HrNt7DrqaEfZmBqJRan9dKFzmQFp', security_token='yWlJG8lAKCq1pTBkbBMSVcKg')
        au = ''
        amp = ''
        rsi = ''
        rsp = ''
        if info.find('AUS:') != -1:
            au = info[info.find('AUS:')+4:info.find(';',info.find('AUS:'))]
        if info.find('AMP:') != -1:
            amp = info[info.find('AMP:')+4:info.find(';',info.find('AMP:'))]
        if info.find('RSI:') != -1:
            rsi = info[info.find('RSI:')+4:info.find(';',info.find('RSI:'))]
        if info.find('RSP:') != -1:
            rsp = info[info.find('RSP:')+4:info.find(';',info.find('RSP:'))]
        sfUpdate = {'Amperage__c':amp,'UsageKW__c':au,'Rafter_Size__c':rsi,'Rafter_Space__c':rsp}
        url = 'https://levelsolar.secure.force.com/api/services/apexrest/v2/opportunities?account_number=' + sfdc
        response_dict = requests.get(url).json()
        oppoId = response_dict[0]['id']
        response = sf.Opportunity.update(oppoId,sfUpdate)
        return 'good'
    except Exception as e:
        msg = Message('AD2SF something wrong', sender=('AD - Please Reply To All','adrobot@levelsolar.com'), recipients=['joey.jiao@levelsolar.com'])
        msg.body = str(e)
        mail.send(msg)
        return str(e)

def ADInfo2SFnologin(sfdc, info):
    au = ''
    amp = ''
    rsi = ''
    rsp = ''
    if info.find('AUS:') != -1:
        au = info[info.find('AUS:')+4:info.find(';',info.find('AUS:'))]
    if info.find('AMP:') != -1:
        amp = info[info.find('AMP:')+4:info.find(';',info.find('AMP:'))]
    if info.find('RSI:') != -1:
        rsi = info[info.find('RSI:')+4:info.find(';',info.find('RSI:'))]
    if info.find('RSP:') != -1:
        rsp = info[info.find('RSP:')+4:info.find(';',info.find('RSP:'))]
    sfUpdate = {'Amperage__c':amp,'UsageKW__c':au,'Rafter_Size__c':rsi,'Rafter_Space__c':rsp}
    url = 'https://levelsolar.secure.force.com/api/services/apexrest/v2/opportunities?account_number=' + sfdc
    response_dict = requests.get(url).json()
    oppoId = response_dict[0]['id']
    return oppoId, sfUpdate

@async
def emailNYCPermit(app,sfdc, title):
    with app.app_context():
        url = "https://levelsolar.secure.force.com/api/services/apexrest/v2/opportunities?account_number=" + str(sfdc)
        response_dict = requests.get(url).json()
        first = response_dict[0]['contact']['first_name']
        last = response_dict[0]['contact']['last_name']
        idName = str(sfdc)+' '+first + ' ' + last
        subject = idName + ' - Another '+str(title)+' Permit Pack Is Ready!'
        msg = Message(subject, sender='robotmarriao@gmail.com', recipients=['permitting@levelsolar.com','arraydesign@levelsolar.com'])
        # msg = Message(subject, sender='robotmarriao@gmail.com', recipients=['joey.jiao@levelsolar.com'])
        url = urlHome+'boxid/' + str(sfdc) + '?api_key=Jo3y1SAW3S0M3'
        response_dict = requests.get(url).json()
        PT = "https://levelsolar.app.box.com/files/0/f/"+response_dict["PT_id"]
        CAD = PT+"/1/f_"+response_dict["NYCPermit"]
        if response_dict["NYCPermit"] == 'no':
            msg.body = 'Link here: ' + PT
        else:
            msg.body = 'Link here: ' + CAD
        msg.body = msg.body+'\n\nAD Robot does not reply emails. Please reply to all.'
        mail.send(msg)


          
@app.route('/case/', methods=["GET", "POST"])
@login_required
def casedisplay():
  try:
    c,conn = connection()
    data = c.execute("SELECT * FROM cases where aptDate != 'On Hold' and (status != '5' and status != '6' and status != '7') or (aptDate = 'On Hold' and (status = '1.5' or status = '2')) or aptDate is null or aptDate = 'g2g-now'  ORDER BY FIELD(aptDate,'g2g-now') DESC, FIELD(aptDate,'Change Request') DESC, status, aptDate, PRB")
    CASE_DICT=[]
    SSP_count = 0
    realBack_count = 0
    listBack_count = 0
    for row in c:
        info = str(row[8])
        infock = 0
        PB = 0
        AD = 0
        SSP = 0
        GG = 0
        au = ''
        amp = ''
        rsi = ''
        rsp = ''
        UTT = ''
        ConE = '0'
        if str(row[8]).find('AUS:') != -1:
            au = info[info.find('AUS:')+4:info.find(';',info.find('AUS:'))]
            # if str(row[3]) == '1' and len(au) > 0:
            #     realBack_count += 1
        if str(row[8]).find('AMP:') != -1:
            amp = info[info.find('AMP:')+4:info.find(';',info.find('AMP:'))]
        if str(row[8]).find('RSI:') != -1:
            rsi = info[info.find('RSI:')+4:info.find(';',info.find('RSI:'))]
        if str(row[8]).find('RSP:') != -1:
            rsp = info[info.find('RSP:')+4:info.find(';',info.find('RSP:'))]
        if info.find('UTT:') != -1:
            UTT = info[info.find('UTT:')+4:info.find(';',info.find('UTT:'))]
            UTT = UTT.replace("-","")
            if len(UTT) > 12:
                ConE = '1'
        goog = str(row[5]).replace(" ","+")
        goog = goog.replace(",","")
        id = str(row[6])
        if id.find('CADid#') != -1:
            cad = id[id.find('CADid#')+6:id.find('CADid#')+17]
        else:
            cad = 'not completed'
        PTid = id[id.find('PTid#')+5:id.find('PTid#')+16].replace('I','')
        SFid = id[id.find('Design#')+7:id.find('Design#')+25]
        CONid = id[id.find('Account#')+8:id.find('Account#')+26]
        if id.find('ITid#') != -1:
            ITid = id[id.find('ITid#')+5:id.find('ITid#')+16].replace('A','')
        else:
            ITid = ''
        if str(row[8]).find('SSP') != -1:
            SSP = 1
        else:
            if str(row[3]) == '0':
                SSP_count += 1
        
        if str(row[9]).find('PB') != -1:
            PB = 1
        if str(row[9]).find('AD') != -1:
            AD = 1
        if str(row[9]).find('G2G') != -1:
            GG = 1
        if len(amp) > 0 and len(rsi) > 0 and len(rsp) > 0 and len(au) > 0: 
            infock = 1
        if row[11] == 'g2g-now' and str(rsi).find('seal') > -1 and str(rsp).find('seal') > -1:
            infock =''
        designIssues = issueBitoStr(row[14])
        issueCKBox = []
        for i in range(12,15):
            try:
                if str(row[14])[i] == '1':
                    issueCKBox.append('True')
                else:
                    issueCKBox.append('')
            except:
                issueCKBox.append('')
        issueCKBoxJoey = []
        for i in range(0,len(row[14])+1):
            try:
                if str(row[14])[i] == '1':
                    issueCKBoxJoey.append('True')
                else:
                    issueCKBoxJoey.append('')
            except:
                issueCKBoxJoey.append('')
        Status = str(row[3])
        CAD_date = ''
        tictok = 0
        try:
            if Status == '0' or Status == '1' or Status == '1.5' or Status == '2':
                CAD_date = str(row[11])
                if CAD_date != None and len(CAD_date) == 10:
                    month = int(CAD_date.split("/")[0])
                    day = int(CAD_date.split("/")[1].split("/",2)[0])
                    year = int('20'+CAD_date.split(str(day)+'/20')[1])
                    dateapt = datetime(year,month,day)
                    twod = datetime.now()+timedelta(days=3) > dateapt
                    onew = datetime.now()+timedelta(days=7) > dateapt
                    if twod and onew:
                        tictok = 2
                    elif onew and not twod:
                        tictok = 1
        except Exception as e:
            pass

        if str(row[3]) == '1' and row[11] != 'No Meeting':
            listBack_count +=1
        if str(row[3]) == '1' and len(au) > 0 and str(row[1]) == 'None' and row[11] != 'No Meeting':
            realBack_count += 1
        CASE_DICT.append({'Case#': row[0], 'Name': row[4], 'Address': row[5], 'Status': row[3], 'PTid': PTid, 'ITid': ITid,'CAD': cad,'SFid': SFid, 'Qc': row[2], 'Note': row[7], 'PRB': row[10], 'Designer': row[1], 'Info': row[8], 'amp': amp, 'rsi': rsi, 'rsp': rsp, 'au': au,'UTT': UTT, 'Infock': infock, 'PB': PB, 'AD': AD, 'SSP': SSP, 'GG': GG, 'GOOG': goog, 'Accountid': CONid, 'CADAPT': row[11], 'apt_ck': tictok, 'CADfile': row[12], 'ConE':ConE, 'Shading': row[13], 'issueCKBox': issueCKBox,'issueCKBoxJoey':issueCKBoxJoey, 'designIssues':designIssues})
    data = c.execute("SELECT status, COUNT(*) FROM cases where aptDate != 'On Hold' or (aptDate = 'On Hold' and (status = '1.5' or status = '2')) GROUP BY status")
    STATUS_DICT = []
    for row in c:
        STATUS_DICT.append({'Status': row[0], 'Count': row[1]})
    c.close()
    gc.collect()
    return render_template('dashboard.html',info=CASE_DICT ,count=STATUS_DICT, SSP_C = SSP_count, rBack_C = realBack_count,lBack_C = listBack_count, designIssue = designIssue)
  except Exception as e:
          return str(e)

@app.route('/case_lookup', methods=["POST"])
@login_required
def case_lookup():
  try:
    sfdc = request.form['user_search']
    c,conn = connection()
    x = c.execute("SELECT * FROM cases WHERE caseid = (%s)",
                    [thwart(sfdc)])
    if int(x) == 0:
        flash("No such case in the system.")
        
        return redirect(urlHome+'case')
    else:
        row = c.fetchone()
        return redirect(urlHome+'case/#'+stat[str(row[3])])
        
  except Exception as e:
          return str(e)

@app.route("/ssp/<sfdc>", methods=["GET", "POST"])
@require_apikey
def ssp(sfdc):
  try:
    if request.method == "POST":
            designer = request.form['designer']
    c,conn = connection()
    x = c.execute("SELECT * FROM cases WHERE caseid = (%s)",
                    [thwart(sfdc)])
    if int(x) == 0:
        return "No such case in the system."
    else:
        row = c.fetchone()
        info = row[8]
        if info == None:
            ssp = 'SSP'
        else:
            ssp = info+'SSP'
        c.execute("UPDATE cases SET info = (%s) WHERE caseid = (%s)",
                        [thwart(ssp),thwart(sfdc)])
        conn.commit()
        c.close()
        conn.close()
        gc.collect()
        flash('Great job on doing the SSP!')
    return redirect(urlHome+'case')
  except Exception as e:
        return str(e)
        
def CADadd_up(sfdc):
    url = urlHome+'boxid/' + sfdc + '?api_key=Jo3y1SAW3S0M3'
    response_dict = requests.get(url).json()
    CAD = response_dict["sharedCAD"]
    IN_id = 'https://levelsolar.app.box.com/files/0/f/'+response_dict["IN_id"]
    c,conn = connection()
    data = c.execute("SELECT * FROM cases WHERE caseid = (%s)",
                        [thwart(sfdc)])
    row = c.fetchone()
    qc = QC[row[2]]
    url = 'https://levelsolar.secure.force.com/api/services/apexrest/accounts?account_number=' + str(sfdc)
    json_r = requests.get(url).json()
    url = 'https://levelsolar.secure.force.com/api/services/apexrest/v2/cases?type_name=Design&account=' + json_r[0]['id']
    json_r = requests.get(url).json()
    S = len(json_r)-1
    designid = json_r[S]['id']
    
    sf = Salesforce(username='integration@levelsolar.com', password='HrNt7DrqaEfZmBqJRan9dKFzmQFp', security_token='yWlJG8lAKCq1pTBkbBMSVcKg')
    if sf.Case.get(designid)['Status'] != 'Closed':
        response = sf.Case.update(designid,{'Box_Install_Plan_Link__c':IN_id, 'CustomerPlan__c':CAD, 'Design_Checked_By__c':qc})
    data = c.execute("UPDATE cases SET CADfile = (%s) WHERE caseid = (%s)",
                        [thwart(CAD),thwart(sfdc)])
    c.execute("UPDATE cases SET status = '2' WHERE caseid = (%s)",
                            [thwart(sfdc)])
    time = datetime.now()
    time = time.strftime('%Y-%m-%d %H:%M:%S')
    c.execute("UPDATE revim SET reviewer = (%s) WHERE caseid = (%s) order by timein DESC limit 1",
                            [thwart(qc), thwart(sfdc)])
    c.execute("UPDATE revim SET timedone = (%s) WHERE caseid = (%s) order by timein DESC limit 1",
                            [thwart(str(time)), thwart(sfdc)])
    c.execute("INSERT INTO closm (caseid, timein) VALUES (%s, %s)",
                  [thwart(sfdc), thwart(str(time))])

    conn.commit()
    c.close()
    conn.close()
    gc.collect()
    return 'good'
    # return CAD, IN_id

@async
def async_approve(sfdc):
    with app.app_context():
        CADadd_up(sfdc)

@app.route("/approve/<sfdc>")
@login_required
def approve(sfdc):
  try:
    CADadd_up(sfdc)
    return 'ok'
  except Exception as e:
    return str(e) + ' Bad request!'

@app.route("/pbqc/<sfdc>")
@login_required
def prebmc_qc(sfdc):
  try:
    c,conn = connection()
    x = c.execute("SELECT * FROM cases WHERE caseid = (%s)",
                    [thwart(sfdc)])
    if int(x) == 0:
        return "No such case in the system."
    else:
        row = c.fetchone()
        status = row[3]
        if str(status) == '2':
            flash('Case already been approved!')
        else:
            qc = str(row[9])
            if qc.find('PB') == -1:
                qc = qc + 'PB'
                c.execute("UPDATE cases SET pending = (%s) WHERE caseid = (%s)",
                            [thwart(qc),thwart(sfdc)])
                conn.commit()
                c.close()
                conn.close()
                gc.collect()
            if qc.find('AD') != -1:
                async_approve(sfdc)
            
            
            flash('Thanks for your suggestion!')
    return redirect(urlHome+'case/#Pending')
  except Exception as e:
        return str(e)
        
@app.route("/adqc/<sfdc>")
@login_required
def adqcfront(sfdc):
  try:
    info = {'sfdc': sfdc}
    return render_template('adqcfront.html',info=info, urlHome=urlHome)
  except Exception as e:
    return str(e)
        
@app.route("/adqcfront/<sfdc>")
@login_required
def ad_qc(sfdc):
  try:
    checker = sfdc[:1]
    sfdc = sfdc[1:]
    c,conn = connection()
    x = c.execute("SELECT * FROM cases WHERE caseid = (%s)",
                    [thwart(sfdc)])
    if int(x) == 0:
        return "No such case in the system."
    else:
        row = c.fetchone()
        status = row[3]
        if str(status) == '2':
            flash('Case already been approved!')
        else:
            qc = str(row[9])
            if qc.find('AD') == -1:
                qc = qc + 'AD'
                c.execute("UPDATE cases SET pending = (%s) WHERE caseid = (%s)",
                            [thwart(qc),thwart(sfdc)])
                c.execute("UPDATE cases SET qc = (%s) WHERE caseid = (%s)",
                            [thwart(checker), thwart(sfdc)])
                conn.commit()
                c.close()
                conn.close()
                gc.collect()
            if qc.find('PB') != -1:
                async_approve(sfdc)
            
            flash('Thanks for your suggestion!')
    return redirect(urlHome+'case/#Pending')
  except Exception as e:
        return str(e)

@app.route("/joeyinfo/<sfdc>", methods=["POST"])
@login_required
def joey_info(sfdc):
  try:
    info = request.form['Info']
    note = request.form['Note_Joey']

    c,conn = connection()
    x = c.execute("SELECT * FROM cases WHERE caseid = (%s)",
                    [thwart(sfdc)])
    row = c.fetchone()
    try:
        int(row[14])
        issueCheck = list(str(row[14]))
    except:
        issueCheck = list("00000000000000000000")
    for i in range(0,20):
        try:
            request.form['ckList'+str(i)]
            issueCheck[i] = '1'
        except:
            issueCheck[i] = '0'
    data = c.execute("UPDATE cases SET designIssue = (%s) WHERE caseid = (%s)",
                     [thwart("".join(issueCheck)),thwart(sfdc)])

    data = c.execute("UPDATE cases SET info = (%s) WHERE caseid = (%s)",
                     [thwart(info),thwart(sfdc)])
    data = c.execute("UPDATE cases SET note = (%s) WHERE caseid = (%s)",
                     [thwart(note),thwart(sfdc)])
    conn.commit()
    c.close()
    conn.close()
    gc.collect()
    return redirect(urlHome+'case/#joey')
  except Exception as e:
        return str(e)

@app.route("/caseinfo/<sfdc>", methods=["POST"])
@login_required
def case_info(sfdc):
  try:
    amp = request.form['total-amperage']
    rsi = request.form['rafter-sizing']
    rsp = request.form['rafter-spacing']
    au = request.form['annual-usage']
    note = request.form['design-note']
    info = 'AMP:'+amp+';RSI:'+rsi+';RSP:'+rsp+';AUS:'+au+';'
    c,conn = connection()
    x = c.execute("SELECT * FROM cases WHERE caseid = (%s)",
                    [thwart(sfdc)])
    row = c.fetchone()
    try:
        int(row[14])
        issueCheck = list(str(row[14]))
    except:
        issueCheck = list("00000000000000000000")
    for i in range(0,3):
        try:
            request.form['new_ckList'+str(i)]
            issueCheck[i+12] = '1'
        except:
            issueCheck[i+12] = '0'
    data = c.execute("UPDATE cases SET designIssue = (%s) WHERE caseid = (%s)",
                     [thwart("".join(issueCheck)),thwart(sfdc)])
    if row[8] == None:
        info = info
    else:
        info = info + row[8]
    data = c.execute("UPDATE cases SET note = (%s) WHERE caseid = (%s)",
                     [thwart(note),thwart(sfdc)])
    data = c.execute("UPDATE cases SET info = (%s) WHERE caseid = (%s)",
                     [thwart(info),thwart(sfdc)])
    ADInfo2SF(sfdc,info)
    conn.commit()
    c.close()
    conn.close()
    gc.collect()
    return redirect(urlHome+'case')
  except Exception as e:
        return str(e)
        
@app.route("/caseinfo_survey/<sfdc>", methods=["POST"])
@login_required
def case_info_survey(sfdc):
  try:
    amp = request.form['t-a']
    rsi = request.form['r-si']
    rsp = request.form['r-sp']
    au = request.form['a-u']
    note = request.form['d-n']
    info = 'AMP:'+amp+';RSI:'+rsi+';RSP:'+rsp+';AUS:'+au+';'
    c,conn = connection()
    x = c.execute("SELECT * FROM cases WHERE caseid = (%s)",
                    [thwart(sfdc)])
    row = c.fetchone()
    try:
        int(row[14])
        issueCheck = list(str(row[14]))
    except:
        issueCheck = list("00000000000000000000")
    for i in range(0,3):
        try:
            request.form['survey_ckList'+str(i)]
            issueCheck[i+12] = '1'
        except:
            issueCheck[i+12] = '0'
    data = c.execute("UPDATE cases SET designIssue = (%s) WHERE caseid = (%s)",
                     [thwart("".join(issueCheck)),thwart(sfdc)])
    if row[8] == None:
        info = info
    else:
        info = info + row[8]
    data = c.execute("UPDATE cases SET note = (%s) WHERE caseid = (%s)",
                     [thwart(note),thwart(sfdc)])
    data = c.execute("UPDATE cases SET info = (%s) WHERE caseid = (%s)",
                     [thwart(info),thwart(sfdc)])
    ADInfo2SF(sfdc,info)
    conn.commit()
    c.close()
    conn.close()
    gc.collect()
    return redirect(urlHome+'case/#Surveyed')
  except Exception as e:
        return str(e)
        
@app.route("/design_note/<sfdc>", methods=["POST"])
@require_apikey
def design_note(sfdc):
  try:
    note = request.form['note']
    c,conn = connection()
    x = c.execute("SELECT * FROM cases WHERE caseid = (%s)",
                    [thwart(sfdc)])
    row = c.fetchone()
    if row[7] == None:
        note = note
    else:
        note = row[7] + note
    data = c.execute("UPDATE cases SET note = (%s) WHERE caseid = (%s)",
                     [thwart(note),thwart(sfdc)])
    conn.commit()
    c.close()
    conn.close()
    gc.collect()
    return "Done"
  except Exception as e:
        return str(e)
        
# @app.route("/caseau/<sfdc>", methods=["POST"])
# def case_au(sfdc):
#   try:
#     au = request.form['annual-usage']
#     info = 'AUS:'+au+';'
#     c,conn = connection()
#     x = c.execute("SELECT * FROM cases WHERE caseid = (%s)",
#                     [thwart(sfdc)])
#     row = c.fetchone()
#     if row[8] == None:
#         info = info
#     else:
#         info = info + row[8]
#     data = c.execute("UPDATE cases SET info = (%s) WHERE caseid = (%s)",
#                      [thwart(info),thwart(sfdc)])
#     conn.commit()
#     c.close()
#     conn.close()
#     gc.collect()
#     return redirect(urlHome+'case/#New')
#   except Exception as e:
#         return str(e)
        
@app.route("/caseappdate_new/<sfdc>", methods=["POST"])
@require_apikey
def case_appdate_new(sfdc):
  try:
    date = request.form['app-date-new']
    if date.find('/') == 1:
        date = '0' + date
    if len(date) < 6:
        date = date + '/2017'
        if date.find('/',date.find('/')+1)-date.find('/') == 2:
            date = date[:date.find('/')+1] + '0' + date[date.find('/')+1:]
    c,conn = connection()
    data = c.execute("UPDATE cases SET aptDate = (%s) WHERE caseid = (%s)",
                     [thwart(date),thwart(sfdc)])
    conn.commit()
    c.close()
    conn.close()
    gc.collect()
    if len(date) <> 10:
        flash('Double check your date format. Case#: '+str(sfdc))
    return redirect(urlHome+'case/#New')
  except Exception as e:
        return str(e)
        
@app.route("/caseappdate/<sfdc>", methods=["POST"])
@require_apikey
def case_appdate(sfdc):
  try:
    date = request.form['app-date']
    if date.find('/') == 1:
        date = '0' + date
    if len(date) < 6:
        date = date + '/2017'
        if date.find('/',date.find('/')+1)-date.find('/') == 2:
            date = date[:date.find('/')+1] + '0' + date[date.find('/')+1:]
    c,conn = connection()
    data = c.execute("UPDATE cases SET aptDate = (%s) WHERE caseid = (%s)",
                     [thwart(date),thwart(sfdc)])
    conn.commit()
    c.close()
    conn.close()
    gc.collect()
    if len(date) <> 10:
        flash('Double check your date format. Case#: '+str(sfdc))
    return redirect(urlHome+'case/#Surveyed')
  except Exception as e:
        return str(e)



@async
def async_reject(app, sfdc, note):
    with app.app_context():
        url = urlHome+'casestatus/' + sfdc + '?api_key=Jo3y1SAW3S0M3'
        data = { 'status': '1' }
        response = requests.post(url, data=data)
        
        c,conn = connection()
        x = c.execute("SELECT * FROM cases WHERE caseid = (%s)",
                        [thwart(sfdc)])
        row = c.fetchone()
        Designer = str(row[1])
        subject = str(row[0]) + ' ' + str(row[4]) + ' - Design been rejected' 
        msg = Message(subject, sender=('AD - Please Reply To All','adrobot@levelsolar.com'), recipients=['arraydesign@levelsolar.com','designchange@levelsolar.com','michael.tarzian@levelsolar.com'])
        msg.body = Designer + ': ' + note + '\nStatus: ' + str(issueBitoStr(row[14]))
        data = c.execute("UPDATE cases SET note = (%s) WHERE caseid = (%s)",
                         [thwart(note),thwart(sfdc)])
        time = datetime.now()
        time = time.strftime('%Y-%m-%d %H:%M:%S')
        c.execute("UPDATE revim SET reviewer = 'Rejection' WHERE caseid = (%s) order by timein DESC limit 1",
                                [thwart(sfdc)])
        c.execute("UPDATE revim SET timedone = (%s) WHERE caseid = (%s) order by timein DESC limit 1", 
                                [thwart(str(time)), thwart(sfdc)])
        conn.commit()
        c.close()
        conn.close()
        gc.collect()
        mail.send(msg)
        url = urlHome+'design_matrix/'+ sfdc + '?api_key=Jo3y1SAW3S0M3'
        data = { 'status':'reject'}
        requests.post(url, data = data)

@app.route("/casereject/<sfdc>", methods=["POST"])
@login_required
def case_reject(sfdc):
  try:
    note = request.form['reject_note']
    async_reject(app, sfdc, note)
    flash('Your ANGER has been sent to the designer. GOOD JOB!')
    return redirect(urlHome+'case/#Pending')
  except Exception as e:
        return str(e)   
        
        
@app.route("/casestatus/<sfdc>", methods=["POST"])
@require_apikey
def case_status(sfdc):
  try:        
    c,conn = connection()
    x = c.execute("SELECT * FROM cases WHERE caseid = (%s)",
                    [thwart(sfdc)])
    if int(x) == 0:
        return "No such case in file. Double check or create one."
        
    ck = request.form['status']
    c.execute("SELECT * FROM cases WHERE caseid = (%s)",
            [thwart(sfdc)])
    row = c.fetchone()
    if str(ck) == '1':
        sync(sfdc)
        if row[1] != None:
            url = urlHome+'design_matrix/' + sfdc + '?api_key=Jo3y1SAW3S0M3'
            data = {'status': 'new'}
            requests.post(url, data = data)
        if str(row[6]).find('Design#') == -1:
            url = "https://levelsolar.secure.force.com/api/services/apexrest/accounts?account_number=" + sfdc
            response_dict = requests.get(url).json()
            sfid = response_dict[0]["id"]
            url = 'https://levelsolar.secure.force.com/api/services/apexrest/v2/cases?type_name=design&account=' + sfid

            response_dict = requests.get(url).json()
            size = len(response_dict)
            design = str(row[6]) + 'Design#' + response_dict[size-1]["id"]
            if str(row[6]).find('Account#') == -1:
                url = 'https://levelsolar.secure.force.com/api/services/apexrest/accounts?account=' + sfid
                response_dict = requests.get(url).json()
                size = len(response_dict)
                design = design +'Account#' + response_dict[size-1]['id']
            data = c.execute("UPDATE cases SET SFcase = (%s) WHERE caseid = (%s)",
                            [thwart(design),thwart(sfdc)])
        data = c.execute("UPDATE cases SET status = (%s) WHERE caseid = (%s)",
                            [thwart(ck),thwart(sfdc)])
        conn.commit()
        c.close()
        conn.close()
        gc.collect()
        return redirect(urlHome+'case/#Surveyed')
    elif str(ck) == '1.5':
        PT = ''
        if str(row[6]).find('PTid#') == -1:
            url = urlHome+'boxid/' + sfdc + '?api_key=Jo3y1SAW3S0M3'
            response_dict = requests.get(url).json()
            PT = str(row[6]) + 'PTid#' + response_dict["PT_id"] + 'ITid#' + response_dict["IN_id"]
        url = urlHome+'boxid/' + sfdc + '?api_key=Jo3y1SAW3S0M3'
        response_dict = requests.get(url).json()
        design = str(row[6]) + PT +'CADid#' + response_dict["file6"]

        data = c.execute("UPDATE cases SET SFcase = (%s) WHERE caseid = (%s)",
                        [thwart(design),thwart(sfdc)])
        data = c.execute("UPDATE cases SET status = (%s) WHERE caseid = (%s)",
                        [thwart(ck),thwart(sfdc)])
        data = c.execute("UPDATE cases SET pending = 'None' WHERE caseid = (%s)",
                        [thwart(sfdc)])
        time = datetime.now()
        time = time.strftime('%Y-%m-%d %H:%M:%S')
        data = c.execute("INSERT INTO revim (caseid, timein) VALUES (%s, %s)",
                  [thwart(sfdc), thwart(str(time))])

    elif str(ck) == '999':        
        x = c.execute("SELECT aptDate, info FROM cases WHERE caseid = (%s)",
                    [thwart(sfdc)])
        row = c.fetchone()
        if str(row[0]) == 'g2g-now':
            info = str(row[1])
            UTT = info[info.find('UTT:')+4:info.find(';',info.find('UTT:'))]
            UTT = UTT.replace("-","")
            if len(UTT) > 12:
                emailNYCPermit(app,sfdc,'NYC')
            else:
                emailNYCPermit(app,sfdc,'G2G')
        # syncProcess = unsync(sfdc)
        # url = 'http://adhome.levelsolar.com/unsync/'+ str(sfdc) +'?api_key=Jo3y1SAW3S0M3'
        # syncProcess = requests.get(url).text
        # subject = 'unsync done or not?'
        # msg = Message(subject, sender='robotmarriao@gmail.com', recipients=['joey.jiao@levelsolar.com'])
        # msg.body = str(syncProcess)
        # mail.send(msg)
        data = c.execute("DELETE FROM cases WHERE caseid = (%s)",
                [thwart(sfdc)])

    else:
        data = c.execute("UPDATE cases SET status = (%s) WHERE caseid = (%s)",
                        [thwart(ck),thwart(sfdc)])
    conn.commit()
    c.close()
    conn.close()
    gc.collect()
    return redirect(urlHome+'case/#Approved')
  except Exception as e:
    subject = str(sfdc) + ' something wrong when changing status'
    msg = Message(subject, sender='robotmarriao@gmail.com', recipients=['joey.jiao@levelsolar.com'])
    msg.body = 'Status cannot be updated: ' + str(e)
    mail.send(msg)
    return str(e)

@app.route('/case/caseremove/<sfdc>', methods=["GET","POST"])
@require_apikey
def caseremove(sfdc):
  try:
    # unsync(sfdc)
    c,conn = connection()
    x = c.execute("SELECT * FROM cases WHERE caseid = (%s)",
                    [thwart(sfdc)])
    if int(x) == 0:
        return "No such case in file. Double check or create one."
    data = c.execute("DELETE FROM cases WHERE caseid = (%s)",
                [thwart(sfdc)])
    conn.commit()
    c.close()
    conn.close()
    gc.collect()
    flash('Case removed')
    return redirect(urlHome+'case/#Bad')
  except Exception as e:
        return str(e)
        
@app.route("/sfutt/<sfdc>", methods=["GET"])
@require_apikey
def sfutt(sfdc):
  try:    
    url = "https://levelsolar.secure.force.com/api/services/apexrest/accounts?account_number=" + sfdc
    response_dict = requests.get(url).json()
    url = 'https://levelsolar.secure.force.com/api/services/apexrest/contacts?account=' + response_dict[0]["id"]
    response_dict = requests.get(url).json()
    size = len(response_dict)
    utility = response_dict[size-1]['account']['utility_account']
    if utility != None:
        utility = utility.replace("-","")
        info = 'UTT:'+utility+';'
        c,conn = connection()
        x = c.execute("SELECT * FROM cases WHERE caseid = (%s)",
                    [thwart(sfdc)])
        row = c.fetchone()
        if row[8] == None:
            info = info
        else:
            info = info + row[8]
        data = c.execute("UPDATE cases SET info = (%s) WHERE caseid = (%s)",
                            [thwart(info),thwart(str(sfdc))])
        conn.commit()
        c.close()
        conn.close()
        gc.collect()
    return 'Done'
  except Exception as e:
        return str(e)

#update from master/ custome3        
@app.route("/casenote/<sfdc>", methods=["POST"])
@require_apikey
def case_note(sfdc):
  try:        
    c,conn = connection()
    x = c.execute("SELECT * FROM cases WHERE caseid = (%s)",
                    [thwart(sfdc)])
    if int(x) == 0:
        return "No such case in file. Double check or create one."
    c.execute("SELECT * FROM cases WHERE caseid = (%s)",
            [thwart(sfdc)])
    note = request.form['note']
    data = c.execute("UPDATE cases SET note = (%s) WHERE caseid = (%s)",
                    [thwart(note),thwart(sfdc)])
    conn.commit()
    c.close()
    conn.close()
    gc.collect()
    return "done"
  except Exception as e:
        return str(e)
#update from master/ custome3             
@app.route("/caseprb/<sfdc>", methods=["POST"])
@require_apikey
def case_prb(sfdc):
  try:        
    c,conn = connection()
    x = c.execute("SELECT * FROM cases WHERE caseid = (%s)",
                    [thwart(sfdc)])
    if int(x) == 0:
        return "No such case in file. Double check or create one."
    note = request.form['note']
    prbBi = issueStrtoBi(note.replace(',',';'))
    if prbBi == 'Not good':
        return 'Not good'
    data = c.execute("UPDATE cases SET designIssue = (%s) WHERE caseid = (%s)",
                    [thwart(prbBi),thwart(sfdc)])
    conn.commit()
    c.close()
    conn.close()
    gc.collect()
    return "done"
  except Exception as e:
        return str(e)

def writeClosm(sfdc):
    sf = Salesforce(username='integration@levelsolar.com', password='HrNt7DrqaEfZmBqJRan9dKFzmQFp', security_token='yWlJG8lAKCq1pTBkbBMSVcKg')
    response = sf.query_all("SELECT (select Assisted_By__c, Design_Checked_By__c  FROM Cases__r WHERE Record_Type_Bucket__c = 'design' AND (Status ='Closed' OR Status='Soft Closed'OR Status='Soft Close' OR Status = 'Draft')) FROM Opportunity WHERE Account_Number__c ='"+str(sfdc)+"'")['records'][0]['Cases__r']['records'][0]
    reviewer = response['Design_Checked_By__c']
    closer = response['Assisted_By__c']
    url = urlHome+'close_matrix?api_key=Jo3y1SAW3S0M3'
    data = { 'casenum': str(sfdc), 'reviewer':reviewer, 'closer':closer }
    requests.post(url, data=data)
    return 'ok'

@app.route('/case/caseLastCheck/<sfdc>', methods=["GET"])
@login_required
def caseLastCheck(sfdc):
  try:
    subject = 'Case Closed Notification'
    msg = Message(subject, sender=('AD - Please Reply To All','adrobot@levelsolar.com'), recipients=['joey.jiao@levelsolar.com'])
    
    c,conn = connection()
    x = c.execute("SELECT designIssue FROM cases WHERE caseid = (%s)",
                    [thwart(sfdc)])
    if int(x) == 0:
        return "No such case in file. Double check or create one."
    row = c.fetchone()

    sf = Salesforce(username='integration@levelsolar.com', password='HrNt7DrqaEfZmBqJRan9dKFzmQFp', security_token='yWlJG8lAKCq1pTBkbBMSVcKg')
    response = sf.query_all("SELECT Contact_Opp__r.Name, Account_Number__c, id, FirstName__c, LastName__c, Account.Address__c, Account.City__c,(select Notes__c, Pre_BMC_Status_Issue__c, Pre_BMC_Resolved__c FROM Pre_BMCs__r where Issue_Category__c = 'Design' AND Pre_BMC_Resolved__c =false and Pre_BMC_Status_Issue__c!='Meter is not grounded'), (select Id, Status  FROM Cases__r WHERE (Record_Type_Bucket__c = 'design' OR Record_Type_Bucket__c = 'Design') and Status != 'Previous Design' AND Status != 'Cancelled') FROM Opportunity WHERE Account_Number__c='"+str(sfdc)+"'")
    if response['records'][0]['Cases__r']['totalSize'] == 1:
        status = response['records'][0]['Cases__r']['records'][0]['Status']
        bmc = []
        for item in response['records']:
            try:
                for bmcs in item['Pre_BMCs__r']['records']:
                    bmc.append(bmcs['Pre_BMC_Status_Issue__c'])
            except:
                pass
        issueMissed = list(set(issueBitoArr(row[0])) - set(bmc))
        if len(issueMissed) >= 1 and issueMissed != ['Other']:
            for item in issueMissed:
                if item != 'Other':
                    flash('Issue: '+str(item)+' required in SF.')

        else:
            if issueStatus(row[0]) =='All Ok' and status == 'Closed':
                flash(str(sfdc)+' has been removed from AD Home.')
                url = urlHome+'casestatus/' + sfdc + '?api_key=Jo3y1SAW3S0M3'
                payload = {'status' : '999'}
                response = requests.post(url, data=payload)
                msg.body = str(sfdc) + ' removed.'
                writeClosm(sfdc)
                mail.send(msg)
            elif issueStatus(row[0]) =='Soft Close' and status == 'Soft Close':
                flash(str(sfdc)+' has been moved to Soft Close.')
                url = urlHome+'casestatus/' + sfdc + '?api_key=Jo3y1SAW3S0M3'
                payload = {'status' : '6'}
                response = requests.post(url, data=payload)
                msg.body = str(sfdc) + ' soft closed.'
                writeClosm(sfdc)
                mail.send(msg)
            elif issueStatus(row[0]) =='Draft' and status == 'Draft':
                flash(str(sfdc)+' has been moved to Draft.')
                url = urlHome+'casestatus/' + sfdc + '?api_key=Jo3y1SAW3S0M3'
                payload = {'status' : '5'}
                response = requests.post(url, data=payload)
                msg.body = str(sfdc) + ' draft.'
                writeClosm(sfdc)
                mail.send(msg)

            else:
                flash('Case not closed in SF yet.')
                
    else:
        flash('More than 1 Design Case opened in SF. Please fix before close.')


    conn.commit()
    c.close()
    conn.close()
    gc.collect()
    return redirect(urlHome+'case/#Approved')
  except Exception as e:
        return str(e)

@app.route("/casedesigner/<sfdc>", methods=["POST"])
@login_required
def case_designer(sfdc):
  try:        
    designer = request.form['search_type']
    c,conn = connection()
    x = c.execute("SELECT * FROM cases WHERE caseid = (%s)",
                    [thwart(sfdc)])
    row = c.fetchone()
    url = urlHome+'design_matrix/' + str(sfdc) + '?api_key=Jo3y1SAW3S0M3'
    if int(x) == 0:
        return "No such case in file. Double check or create one."
    if designer == '8':
        data = { 'status':'fail'}
        requests.post(url, data = data)
        data = c.execute("UPDATE cases SET status = (%s) WHERE caseid = (%s)",
                        [thwart(designer),thwart(sfdc)])
    if designer == 'Survey Issue':
        url = 'https://levelsolar.secure.force.com/api/services/apexrest/v2/opportunities?account_number=' + str(sfdc)
        json_r = requests.get(url).json()
        accoundID = json_r[0]['account']['id']
        url = 'https://levelsolar.secure.force.com/api/services/apexrest/v2/cases?type_name=Survey&account=' + accoundID
        json_r = requests.get(url).json()
        for item in json_r:
            if item['status'] == 'Issue':
                data = c.execute("UPDATE cases SET status = '0' WHERE caseid = (%s)",
                        [thwart(sfdc)])
        flash('Missing Survey Issue in SF, try again.')

    else:
        if row[1] == None or row[1] == 'None':
            data = { 'status':'new', 'designer':designer }
            requests.post(url, data = data)
        else:
            data = { 'status':'change', 'designer':designer }
            requests.post(url, data = data)
        data = c.execute("UPDATE cases SET designer = (%s) WHERE caseid = (%s)",
                    [thwart(designer),thwart(sfdc)])
                    
    conn.commit()
    c.close()
    conn.close()
    gc.collect()
    return redirect(urlHome+'case/#Surveyed')
  except Exception as e:
        return str(e)

skylerZip = ['11212',
             '11236',
             '11207',
             '11208',
             '11203']

@app.route('/caseread', methods=["GET","POST"])
@require_apikey
def caseread():
  try:
    if request.method == 'POST':
          casenum = request.form["user_search"]
          
          url = "https://levelsolar.secure.force.com/api/services/apexrest/accounts?account_number=" + request.form["user_search"]
          response_dict = requests.get(url).json()
          sfid = response_dict[0]["id"]
          url = 'https://levelsolar.secure.force.com/api/services/apexrest/contacts?account=' + response_dict[0]["id"]
          response_dict = requests.get(url).json()
          size = len(response_dict)  
          first = response_dict[size-1]['first_name']
          last = response_dict[size-1]['last_name']
          casename = first + ' ' + last
          caseaddress = response_dict[size-1]['street_address']
          city = response_dict[size-1]['city']
          state = response_dict[size-1]['state']
          zip = response_dict[size-1]['zip']
          utility = response_dict[size-1]['account']['utility_account']
          county = response_dict[size-1]['account']['municipality']['county']['name']
          if utility == None:
              info = utility = 'UTT:Missing;'
          else:
              utility = 'UTT:'+utility.replace("-","")+';'
              info = utility

          sf = Salesforce(username='integration@levelsolar.com', password='HrNt7DrqaEfZmBqJRan9dKFzmQFp', security_token='yWlJG8lAKCq1pTBkbBMSVcKg')
          url = 'https://levelsolar.secure.force.com/api/services/apexrest/v2/opportunities?account_number=' + casenum
          response_dict = requests.get(url).json()
          oppoId = str(response_dict[0]['id'])

          url = urlHome + 'boxid/'+casenum + '?api_key=Jo3y1SAW3S0M3'
          response_dict = requests.get(url).json()
          boxIds = {}
          boxIds['box_arraydesign__c'] = response_dict['AD_id']
          boxIds['box_install__c'] = response_dict['IN_id']
          boxIds['box_permit__c'] = response_dict['PT_id']
          boxIds['box_sales__c'] = response_dict['SALE_id']
          sf.Opportunity.update(str(oppoId),boxIds)

          response = sf.query("SELECT UsageKW__c, Amperage__c, Rafter_Size__c, Rafter_Space__c FROM Opportunity WHERE Id = '" + oppoId + "'")
          for item in response['records']:
              amp = item['Amperage__c'] if item['Amperage__c'] else ''
              rsi = item['Rafter_Size__c']  if item['Rafter_Size__c'] else ''
              rsp = item['Rafter_Space__c']  if item['Rafter_Space__c'] else ''
              au = item['UsageKW__c']  if item['UsageKW__c'] else ''
          info = 'AMP:'+amp+';RSI:'+rsi+';RSP:'+rsp+';AUS:'+au+';'+info

          caseaddress = caseaddress + ', ' + city + ', ' + state + ', ' + zip + ', ' + county
          casestatus = '0'
          c,conn = connection()

          x = c.execute("SELECT * FROM cases WHERE caseid = (%s)",
              [thwart(casenum)])    
          if int(x) > 0:
              flash("That case is already in the system, please choose another")
              return redirect(urlHome+'case')
          else:
              c.execute("INSERT INTO cases (caseid, status, name, address, info) VALUES (%s, %s, %s, %s, %s)",
                      [thwart(casenum), thwart(casestatus), thwart(casename), thwart(caseaddress), thwart(info)])
              conn.commit()
              flash('Thanks for uploading')
              c.close()
              conn.close()
              gc.collect()
              # comment = '285W'
              # url = urlHome+'design_note/' + casenum + '?api_key=Jo3y1SAW3S0M3'
              # data = { 'note': comment }
              # response = requests.post(url, data=data)
              try:
                skylerZip.index(str(zip))
                comment = 'Brownsville'
                url = urlHome+'design_note/' + casenum + '?api_key=Jo3y1SAW3S0M3'
                data = { 'note': comment }
                response = requests.post(url, data=data)
              except:
                pass
              
              return redirect(urlHome+'case/#joey')
    else:
      return render_template('caseread.html')
  except Exception as e:
    msg = Message('Failed to load case to AD Home', sender=('AD - Please Reply To All','adrobot@levelsolar.com'), recipients=['joey.jiao@levelsolar.com','arraydesign@levelsolar.com'])
    msg.body = 'Please double check the name update or folder structure for case: '+casenum
    mail.send(msg)
    return str(e)