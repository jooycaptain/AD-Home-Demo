# AD-Home
http://adhome.levelsolar.com

# Demo Login
Email: demo@demo.com
Password: demo

# Intro
This is the first App I built with Python Flask, MySQL and with the server set up on Amazon AWS. Maintained and designed by meself so it might not be very well structured. 


# Highlights
* **box.py**

Self maintain and token refresh with Box OAuth2 to create customized folder structure.

* **pmatrix.py**

Algorithm triggered by user actions across the web app. Log records into SQL database and visulize the performance into a matix @ http://adhome.levelsolar.com/matrix.

* **crontab.py**

Batch files run recursively to do certain tasks including getting and populating PDFs from Box, verifying data intagrity and process exception, generating daily reports and sending out email alert.

* **sf1212.py**

Another bach file works as a phase 1 new Salesforce Lightning integration by maintaining and synchronizing two Salesforce instances through its Bulk API. 