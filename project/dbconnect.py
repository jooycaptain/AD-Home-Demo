import MySQLdb

def connection():
	conn = MySQLdb.connect(host="arraydesign.c6ffm4eevbwx.us-east-1.rds.amazonaws.com",
				user = "admin",
				passwd = "Levelsolar1",
				db = "ADDATA")
	c = conn.cursor()
	return c, conn
