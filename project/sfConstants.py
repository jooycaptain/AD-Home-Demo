nameTranslate = {
    'Ulead12' : 'Upsert leads to new SF',
    'Uoppo12' : 'New opportunity created in new SF',
    'Uinteraction12' : 'Upsert events to new SF',
    'Idlead12' : 'Update lead ids to old SF',
    'Idoppo12' : 'Update opportunity ids to old SF',
    'Idinteraction12' : 'Update interaction ids to old SF',
    'Ulead21' : 'Upsert leads to old SF',
    'Uoppo21' : 'New opportunity created in old SF',
    'Uinteraction21' : 'Upsert interactions to old SF',
    'Idlead21' : 'Update lead ids to new SF',
    'Idoppo21' : 'Update opportunity ids to new SF',
    'Idinteraction21' : 'Update event ids to new SF',
    'CleanOppo12' : 'Stand alone oppotunity has not been removed from SF2'
}
oldSFURl = 'https://levelsolar.my.salesforce.com/'
newSFURl = 'https://levelsolar2nd.lightning.force.com/'

interactionSF12 = ['Id', 'Outcome__c', 'ScheduledDate__c', 'Subject__c', 'Confirmed__c', 'Rescheduled__c', 'Opportunity__r.Lead__c', 'Lead__c', 'Assigned_To__c','LastModifiedById', 'LastModifiedDate', 'Canceled__c']

leadSF12 = ['Id', 'Ambassador__c', 'DoNotCall', 'Email', 'LASERCA__Home_Address__c', 'LASERCA__Home_City__c', 'LASERCA__Home_Zip__c', 'LASERCA__Home_State__c', 'LeadSource', 'Lead_Source_Details__c', 'Status', 'MobilePhone', 'FirstName', 'LastName', 'Company', 'Phone', 'Roof_Rating__c', 'ZipCodeRegion__c', 'Rating_Roof_Type__c', 'Utility__c', 'CountyRegion__c', 'Municipality__c', 'LastModifiedDate','LastModifiedById', 'Description', 'Latest_Interaction_Scheduled_Date__c']

leadToLead12 = {
    'name':{
        'Id': 'OldSalesforceExtID__c',
        'ZipCodeRegion__c': 'Region__r.OldSalesforceExtID__c',
        'Utility__c': 'Utility__r.OldSalesforceExtID__c',
        'Lead_Source_Details__c': 'Lead_Source_Detail__c',
        'Roof_Rating__c': 'Rating',
        'Latest_Interaction_Scheduled_Date__c': 'Appointment_Date_And_Time__c',
        'LASERCA__Home_City__c': 'City',
        'LASERCA__Home_State__c': 'State',
        'LASERCA__Home_Zip__c': 'PostalCode',
        'LASERCA__Home_Address__c': 'Street'
    },
    'target': ['City', 'FirstName', 'LastName', 'PostalCode', 'State', 'Region__r.OldSalesforceExtID__c', 'Email', 'Status', 'Company', 'Phone', 'OldSalesforceExtID__c', 'Street', 'MobilePhone', 'Rating', 'LeadSource', 'DoNotCall', 'Description','Appointment_Date_And_Time__c', 'Utility__r.OldSalesforceExtID__c'],
    'datetime': {
        # 'Latest_Interaction_Scheduled_Date__c':'Latest_Interaction_Scheduled_Date__c',
        'Appointment_Date_And_Time__c':'Appointment_Date_And_Time__c'
    }
}
leadStatus12 = {
    'Name': 'Status',
    "Interested, Closer Appt Not Yet Set":'New',
    "Cold Lead":'New',
    "Appointment Set":'Appointment Set',
    "Did Not Sit":'Appointment Unattended',
    "Sat, Not Converted":'Appointment Sat',
    "Converted - Sale":'Converted - Sale',
    "Dismissed":'Unqualified',
    "Not Yet Contacted":'Unqualified',
    "Qualified & Recyclable":'Working'
}

opportunitySF12 = ['Id', 'Amount', 'LeadSource', 'Name', 'StageName', 'LastModifiedDate', 'Lead__c', 'CreatedDate','LastModifiedById', 'Site_Survey_Completed_Date__c', 'Latest_CAD_Outcome__c', 'Latest_CAD_Outcome_Date__c', 'Town_Permit_Submitted__c', 'Town_Permit_Received__c', 'InstallDate__c', 'Electrical_Inspection_Complete__c', 'Town_Inspection_Completed__c', 'Utility_Post_Install_Permit_Completed__c', 'Placed_in_Service__c', 'Ambassador__c', 'SalesRepE__c', 'System_Size_KW__c', 'No_of_Installed_Panels__c', 'ClosedLostReason__c', 'Estimated_Production_kWh__c', 'ContractType__c', 'Deal_Type__c']

oppoToOppo12 = {
    'name':{
        'Lead__c': 'OldSalesforceExtID__c',
        'CreatedDate': 'CloseDate',
        'ContractType__c': 'Contract_Type__c',
        'ClosedLostReason__c': 'Closed_Lost_Reason__c'
          
    },
    'datetime': {
        'CreatedDate': 'CloseDate',
        'Latest_CAD_Outcome_Date__c': 'Latest_CAD_Outcome_Date__c',
        'Town_Permit_Received__c': 'Town_Permit_Received__c',
        'InstallDate__c': 'Install_Date__c'      
    },
    'target': ['Name', 'StageName', 'CloseDate', 'Amount', 'OldSalesforceExtID__c', 'Site_Survey_Completed_Date__c', 'Latest_CAD_Outcome__c', 'Latest_CAD_Outcome_Date__c', 'Town_Permit_Submitted__c', 'Town_Permit_Received__c','Install_Date__c', 'Electrical_Inspection_Complete__c', 'Town_Inspection_Completed__c', 'Utility_Post_Install_Permit_Completed__c', 'Placed_in_Service__c', 'System_Size_KW__c', 'No_of_Installed_Panels__c', 'Closed_Lost_Reason__c', 'Estimated_Production_kWh__c']
}
oppoStage12 = {
    'Name': 'StageName',
    'New Customer': 'Sale',
    'Site Survey': 'Sale',
    'Array Design': 'Sale',
    'Array Design Ready': 'Sale',
    'Good to Go': 'Good to Go',
    'Pre-Install Permits Submitted': 'Permits Submitted',
    'Town Permit Received': 'Permits Submitted',
    'Installation Date Confirmed': 'Permits Submitted',
    'Installed': 'Installed',
    'Required Post-Install Inspection': 'Installed',
    'System Placed in Service': 'In Service',
    'Completed': 'In Service',
    'Closed Lost': 'Closed Lost',
    'On Hold': 'On Hold'
}
interactionToEvent12 = {
    'name':{
        'Id': 'OldSalesforceExtID__c',
        # 'Lead__c' :'OldSalesforceLeadID__c',
        'Assigned_To__c' :'Assigned_Employee__r.OldSalesforceExtID__c',
        'Subject__c' : 'Subject'
    },
    'target': ['Assigned_Employee__r.OldSalesforceExtID__c', 'Rescheduled__c', 'ActivityDateTime', 'DurationInMinutes', 'Outcome__c', 'OldSalesforceExtID__c', 'OldSalesforceLeadID__c', 'Subject'],
    'datetime': {
        'ScheduledDate__c': 'ActivityDateTime'
    }
}
interactionOutcome12 = {
    
}
sf2EmployeeId = {
    'a08f4000000G6DFAA0' : 'a023900000Uuf3MAAR', #Patrick Beane
    'a08f4000000G6DGAA0' : 'a023900000UkxaFAAR', #Amit Shenoy
    'a08f4000000G6DHAA0' : 'a027000000PxIOQAA3', #Nestor Colon
    'a08f4000000G6DIAA0' : 'a027000000LLP5tAAH', #Robert Schack
    'a08f4000000G6DJAA0' : 'a023900000WAJW5AAP', #Timothy Kim
    'a08f4000000G6DKAA0' : 'a023900000VRdm7AAD', #Alex Ma
    'a08f4000000G6DLAA0' : 'a023900000SSclhAAD', #Zach Rydout
    'a08f4000000G6DMAA0' : 'a023900000UQH7VAAX', #Tyler Willis
    'a08f4000000G6DNAA0' : 'a023900000Xjl8TAAR', #Greg Colichio
    'a08f4000000G6DOAA0' : 'a027000000QsUeEAAV', #Michael Desiderio
    'a08f4000000G6DPAA0' : 'a027000000QsCBXAA3', #Justin Schimmenti
    'a08f4000000G6DQAA0' : 'a027000000Qfg5HAAR', #David Neiger
    'a08f4000000G6DRAA0' : 'a023900000V1UySAAV', #Fitzgerald Charles
    'a08f4000000G6DSAA0' : 'a027000000KTGuLAAX', #Jonathan Cohen
    'a08f4000000G6DTAA0' : 'a023900000U3X37AAF', #Chris Duggan
    'a08f4000000G6DUAA0' : 'a023900000YeQwQAAV', #Software Test
    'a08f4000000G6DVAA0' : 'a023900000Yf9wtAAB', #Chris Poole
    'a08f4000000G6DWAA0' : 'a023900000SXRAUAA5', #Daniel Charest
    'a08f4000000G6DXAA0' : 'a023900000SXRAeAAP', #Matt Simonson
    'a08f4000000G6DYAA0' : 'a027000000Rlv53AAB', #Andrew Field
    'a08f4000000G6DZAA0' : 'a023900000YewQcAAJ', #Andrew Bean
    'a08f4000000G6DaAAK' : 'a027000000Pue0ZAAR', #Richard Kahn
    'a08f4000000G6DbAAK' : 'a023900000UwL3CAAV', #Arthur Handy
    'a08f4000000G6DcAAK' : 'a023900000UwL37AAF', #Ozzy Sheikh
    'a08f4000000G6DdAAK' : 'a027000000RvoO8AAJ', #Ryan Samida
    'a08f4000000G6DeAAK' : 'a023900000Ui9s7AAB', #Tricia Fontaine
    'a08f4000000G6DfAAK' : 'a023900000Ui9sBAAR', #Brandon Toron
    'a08f4000000G6DgAAK' : 'a023900000Uuf3CAAR', #Sherard Bishop
    'a08f4000000G6C6AAK' : 'a023900000SXRAPAA5', #Diego Aguilar
    'a08f4000000G6C7AAK' : 'a023900000U7CzUAAV', #Zak Elgart
    'a08f4000000G6C8AAK' : 'a023900000U7CzoAAF', #Doug Huron
    'a08f4000000G6C9AAK' : 'a023900000U7CztAAF', #James Tornabene
    'a08f4000000G6CAAA0' : 'a027000000IKyZxAAL', #Steven Elliott
    'a08f4000000G6CBAA0' : 'a027000000NhnDLAAZ', #Josh Lilly
    'a08f4000000G6CCAA0' : 'a027000000Pue0yAAB', #Brandon Parlante
    'a08f4000000G6CDAA0' : 'a027000000Rlv4oAAB', #Mac Smith
    'a08f4000000G6CEAA0' : 'a027000000SeRyOAAV' #Andrew Drewchin
}
sf2EmployeeIdUAT = {
    'a01q000000BRRy2AAH' : 'a023900000UQkZlAAL', #Lloyd Schiffres
    'a01q000000BRRy3AAH' : 'a027000000NhnD6AAJ', #Tyler Rhoton
    'a01q000000BRRy4AAH' : 'a023900000VfShQAAV', #Solomon Ibragimov
    'a01q000000BRRy5AAH' : 'a027000000Q86blAAB', #Bradley Bell
    'a01q000000BRRy6AAH' : 'a027000000QeGTpAAN', #Jared Huston
    'a01q000000BRRy7AAH' : 'a023900000UjiQAAAZ', #Grant Horner
    'a01q000000BRRy8AAH' : 'a023900000U7CzjAAF', #Lahsann Rogers
    'a01q000000BRRy9AAH' : 'a023900000V1Uy3AAF', #Raphael Mosenkis
    'a01q000000BRRyAAAX' : 'a023900000UajYjAAJ', #Robert Markowitz
    'a01q000000BRRyBAAX' : 'a023900000UajYyAAJ', #Kenneth Starling
    'a01q000000BRRyCAAX' : 'a023900000UPdQ0AAL', #Doreen Turpin
    'a01q000000BRRyDAAX' : 'a023900000U5FDGAA3', #Efrain Rivera
    'a01q000000BRRyEAAX' : 'a023900000UiZR5AAN', #Kevin Hindley
    'a01q000000BRRyFAAX' : 'a023900000V07v0AAB', #Alex Feldman
    'a01q000000BRRyGAAX' : 'a027000000OuChFAAV', #Mark Campbell
    'a01q000000BRRyHAAX' : 'a023900000VRNiUAAX', #Jeffrey Perez
    'a01q000000BRRyIAAX' : 'a023900000U3IybAAF', #Matt Crowther
    'a01q000000BRRyJAAX' : 'a023900000UwL3RAAV', #Michael Young-Cho
    'a01q000000BRRyKAAX' : 'a027000000Pue0oAAB', #Anthony Quezada
    'a01q000000BRRyLAAX' : 'a023900000Ui9s9AAB', #Tim Hutchens
    'a01q000000BRRyMAAX' : 'a023900000UwL3MAAV', #Gavin Kent
    'a01q000000BRRyNAAX' : 'a023900000UPazdAAD', #Eric Byron
    'a01q000000BRRvjAAH' : 'a023900000Uuf3MAAR', #Patrick Beane
    'a01q000000BRRvlAAH' : 'a027000000PxIOQAA3', #Nestor Colon
    'a01q000000BRRvmAAH' : 'a027000000LLP5tAAH', #Robert Schack
    'a01q000000BRRvnAAH' : 'a023900000WAJW5AAP', #Timothy Kim
    'a01q000000BRRvoAAH' : 'a023900000SSclhAAD', #Zach Rydout
    'a01q000000BRRvpAAH' : 'a023900000UQH7VAAX', #Tyler Willis
    'a01q000000BRRvqAAH' : 'a023900000U7CzZAAV', #Laurel Payne
    'a01q000000BRRvrAAH' : 'a023900000Xjl8TAAR', #Greg Colichio
    'a01q000000BRRvsAAH' : 'a027000000QsUeEAAV', #Michael Desiderio
    'a01q000000BRRvtAAH' : 'a027000000QsCBXAA3', #Justin Schimmenti
    'a01q000000BRRvuAAH' : 'a027000000Qfg5HAAR', #David Neiger
    'a01q000000BRRvvAAH' : 'a023900000VIRT5AAP', #Kevin Mange
    'a01q000000BRRvwAAH' : 'a023900000V1UySAAV', #Fitzgerald Charles
    'a01q000000BRRvxAAH' : 'a023900000UajYoAAJ', #Richard Oldaker
    'a01q000000BRRvyAAH' : 'a027000000KTGuLAAX', #Jonathan Cohen
    'a01q000000BRRvzAAH' : 'a027000000Px6vSAAR', #Francis D'Erasmo
    'a01q000000BRRw0AAH' : 'a023900000YeQwQAAV', #Software Test
    'a01q000000BRRw1AAH' : 'a023900000SXRAUAA5', #Daniel Charest
    'a01q000000BRRw2AAH' : 'a023900000SXRAPAA5', #Diego Aguilar
    'a01q000000BRRw3AAH' : 'a023900000SXRAeAAP', #Matt Simonson
    'a01q000000BRRw5AAH' : 'a027000000Pue0ZAAR', #Richard Kahn
    'a01q000000BRRw7AAH' : 'a023900000UwL37AAF', #Ozzy Sheikh
    'a01q000000BRRw8AAH' : 'a027000000RvoO8AAJ', #Ryan Samida
    'a01q000000BRRw9AAH' : 'a023900000Ui9s7AAB', #Tricia Fontaine
    'a01q000000BRRwAAAX' : 'a023900000Ui9sAAAR', #Ryan Teed
    'a01q000000BRRwBAAX' : 'a023900000Ui9sBAAR', #Brandon Toron
    'a01q000000BRRwCAAX' : 'a023900000Uuf3CAAR', #Sherard Bishop
    'a01q000000BRRxuAAH' : 'a023900000UkxaFAAR', #Amit Shenoy
    'a01q000000BRRxvAAH' : 'a023900000VRdm7AAD', #Alex Ma
    'a01q000000BRRxwAAH' : 'a023900000U3X37AAF', #Chris Duggan
    'a01q000000BRRxxAAH' : 'a023900000YewQcAAJ', #Andrew Bean
    'a01q000000BRnDNAA1' : 'a023900000UwL32AAF', #Lisette Billups
    'a01q000000BRRxyAAH' : 'a023900000UwL3CAAV' #Arthur Handy
}

eventSF21 = ['Id', 'Cancelled__c', 'Company_Lead__c', 'OldSalesforceExtID__c', 'OldSalesforceLeadID__c', 'Outcome__c', 'Rescheduled__c', 'WhoId', 'WhatId', 'Subject', 'ActivityDateTime', 'LastModifiedDate', 'NewSalesforceLeadId__c', 'Assigned_Employee__c', 'LastModifiedById']
opportunitySF21 = ['Id', 'LeadSource', 'CreatedDate', 'LeadId__c', 'Name', 'StageName', 'CloseDate', 'Amount', 'OldSalesforceExtID__c', 'Site_Survey_Completed_Date__c', 'Latest_CAD_Outcome__c', 'Latest_CAD_Outcome_Date__c', 'Town_Permit_Submitted__c', 'Town_Permit_Received__c','Install_Date__c', 'Electrical_Inspection_Complete__c', 'Town_Inspection_Completed__c', 'Utility_Post_Install_Permit_Completed__c', 'Placed_in_Service__c', 'System_Size_KW__c', 'No_of_Installed_Panels__c', 'Closed_Lost_Reason__c', 'Estimated_Production_kWh__c', 'LastModifiedById']
leadSF21 = ['Id', 'City', 'FirstName', 'LastName', 'PostalCode', 'State', 'Region__c', 'Email', 'Status', 'Company', 'Phone', 'OldSalesforceExtID__c', 'Street', 'MobilePhone', 'Rating', 'LeadSource', 'DoNotCall', 'Description','Appointment_Date_And_Time__c', 'LastModifiedDate', 'LastModifiedById']

leadToLead21 = {
    'name':{
        'Id': 'NewSalesforceExtID__c',
        'City':'LASERCA__Home_City__c',
        'State':'LASERCA__Home_State__c',
        'PostalCode':'LASERCA__Home_Zip__c',
        'Street':'LASERCA__Home_Address__c'
    },
    'target': ['Company', 'DoNotCall', 'Email', 'FirstName', 'LASERCA__Home_Address__c', 'LASERCA__Home_City__c', 'LASERCA__Home_State__c', 'LASERCA__Home_Zip__c', 'LastName', 'MobilePhone', 'NewSalesforceExtID__c', 'Phone', 'Status', 'Description'],
    'datetime': []
}
leadStatus21 = {
    'Name': 'Status',
    'New':"Interested, Closer Appt Not Yet Set",
    'Appointment Set':"Appointment Set",
    'Appointment Sat':"Sat, Not Converted",
    'Appointment Unattended':"Did Not Sit",
    'Appointment Attended':"Sat, Not Converted",
    'Converted - Sale':"Converted - Sale",
    'Unqualified':"Not Yet Contacted",
    'Working':"Qualified & Recyclable",


    'Appt Unattended':"Did Not Sit",
    'Appt Attended':"Sat, Not Converted",

    "Interested, Closer Appt Not Yet Set":"Interested, Closer Appt Not Yet Set",
    "Cold Lead":"Cold Lead",
    "Did Not Sit":"Did Not Sit",
    "Sat, Not Converted":"Sat, Not Converted",
    "Dismissed":"Dismissed",
    "Not Yet Contacted":"Not Yet Contacted",
    "Qualified & Recyclable":"Qualified & Recyclable"

}

oppoToOppo21 = {
    'name':{
        'LeadId__c': 'NewSalesforceExtID__c',
        'CreatedDate': 'CloseDate'
    },
    'datetime': {
        'CreatedDate': 'CloseDate'
    },
    'target': ['Amount', 'CloseDate', 'LeadId__c', 'Name', 'NewSalesforceExtID__c', 'StageName']
}
oppoStage21 = {
    # 'Name': 'StageName',
    # 'Sale' : 'New Customer',
    # # 'Sale' : 'Site Survey',
    # # 'Sale' : 'Array Design',
    # # 'Sale' : 'Array Design Ready',
    # 'Good to Go' : 'Good to Go',
    # 'Permit Submitted' : 'Pre-Install Permits Submitted',
    # # 'Permits Submitted' : 'Town Permit Received',
    # # 'Permits Submitted' : 'Installation Date Confirmed',
    # 'Installed' : 'Installed',
    # # 'Installed' : 'Required Post-Install Inspection',
    # # 'In Service' : 'System Placed in Service',
    # # 'In Service' : 'Completed',
    # 'Closed Lost' : 'Closed Lost',
    # 'On Hold' : 'On Hold',
}

interactionToEvent21 = {
    'name':{
        'Id': 'NewSalesforceExtID__c',
        # 'Assigned_Employee__c': 'Assigned_To__c',
        'Cancelled__c': 'Canceled__c',
        # 'Lead__c' :'NewSalesforceLeadID__c',
        'Subject' : 'Subject__c'
    },
    'target': ['Assigned_To__c', 'Canceled__c', 'NewSalesforceExtID__c', 'Outcome__c', 'Rescheduled__c', 'ScheduledDate__c', 'Subject__c', 'lead__r.NewSalesforceExtID__c','Opportunity__r.NewSalesforceExtID__c'],
    'datetime': {
        'ActivityDateTime': 'ScheduledDate__c'
    }
}

interactionOutcome21 = {
    
}