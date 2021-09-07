import hashlib
import sqlite3


def readdb(db_fname, db_request) -> list:
	db = sqlite3.connect(db_fname)
	cur = db.cursor()
	try:
		cur.execute(db_request)
	except sqlite3.OperationalError as e:
		if "no such table: " in str(e):
			raise ValueError(str(e)) from None
		else:
			raise
	answer = cur.fetchall()
	db.close()
	return answer


def writedb(db_fname, db_request):
	db = sqlite3.connect(db_fname)
	cur = db.cursor()
	try:
		cur.execute(db_request)
	except sqlite3.OperationalError as e:
		if "no such table: " in str(e):
			raise ValueError(str(e)) from None
		else:
			raise
	db.commit()
	db.close()


def param_san_check(tablename, username, cipher, nbeg, nend, salt, text):
	# Checking table
	tablename_san = tablename.replace("'", "''")
	# Checking user
	if username == '' or username is None:
		raise ValueError("user name can't be empty")
	if len(username) > 50:
		raise ValueError("user name max len is 50 symbols")
	username_san = username.replace("'", "''")
	# Checking cipher
	if cipher != '':
		cipher = cipher.replace("'", "''")
		if cipher not in hashlib.algorithms_available:
			raise ValueError("Unsupported hash cipher: " + cipher)
	cipher_san = cipher
	# Checking nbeg, nend
	if cipher_san != '':
		if nbeg != '':
			nbeg_int = int(nbeg)
		else:
			nbeg_int = 1
		if nend != '':
			nend_int = int(nend)
		else:
			nend_int = 15
		if nbeg_int <= 0 or nbeg_int >= 16:
			raise ValueError("nbeg must be 1 to 15")
		if nend_int <= 0 or nend_int >= 16:
			raise ValueError("nend must be 1 to 15")
		if nbeg_int >= nend_int:
			raise ValueError("nbeg must be less than nend")
	else:
		nbeg = ''
		nend = ''
	nbeg_san = nbeg
	nend_san = nend
	# Checking salt
	if salt != '':
		salt = salt.replace("'", "''")
		if len(salt) > 16:
			raise ValueError("Max salt len is 16")
	salt_san = salt
	# Checking text
	if text != '':
		text = text.replace("'", "''")
	text_san = text
	return tablename_san, username_san, cipher_san, nbeg_san, nend_san, salt_san, text_san


def addtable(db_fname, tablename):
	writedb(
		db_fname, "CREATE TABLE IF NOT EXISTS " + tablename +
		" (name TEXT UNIQUE, cipher TEXT, nbeg INTEGER, nend INTEGER, salt TEXT, comm TEXT)")


def rmtable(db_fname, tablename):
	writedb(db_fname, "DROP TABLE " + tablename)


def mvtable(db_fname, old_name, new_name):
	writedb(db_fname, "ALTER TABLE " + old_name + " RENAME TO " + new_name)


def adduser(db_fname, table, name, cipher, nbeg, nend, salt, text):
	table, name, cipher, nbeg, nend, salt, text = param_san_check(table, name, cipher, nbeg, nend, salt, text)
	writedb(
		db_fname, "INSERT or REPLACE INTO " + table + " VALUES('" +
		name + "','" + cipher + "','" + nbeg + "','" + nend + "','" + salt + "','" + text + "')")


def rmuser(db_fname, table, name):
	table = table.replace("'", "''")
	name = name.replace("'", "''")
	writedb(db_fname, "DELETE FROM " + table + " WHERE name='" + name + "'")


def searchusers(db_fname, table, name="", cipher="", nbeg="", nend="", salt="", text=""):
	req_conditions = ""
	if name == "":
		table, name, cipher, nbeg, nend, salt, text = param_san_check(table, "dummy", cipher, nbeg, nend, salt, text)
	else:
		table, name, cipher, nbeg, nend, salt, text = param_san_check(table, name, cipher, nbeg, nend, salt, text)
		req_conditions = "name LIKE '%" + name + "%'"
	request = "SELECT * FROM " + table
	if cipher != "":
		if req_conditions != "":
			req_conditions += " AND "
		req_conditions += "cipher='" + cipher + "'"
	if nbeg != "":
		if req_conditions != "":
			req_conditions += " AND "
		req_conditions += "nbeg='" + nbeg + "'"
	if nend != "":
		if req_conditions != "":
			req_conditions += " AND "
		req_conditions += "nend='" + nend + "'"
	if salt != "":
		if req_conditions != "":
			req_conditions += " AND "
		req_conditions += "salt LIKE '%" + salt + "%'"
	if text != "":
		if req_conditions != "":
			req_conditions += " AND "
		req_conditions += "comm LIKE '%" + text + "%'"
	if req_conditions != "":
		request += " WHERE " + req_conditions
	answer = readdb(db_fname, request)
	return answer


def pwusers(db_fname, table, name) -> list:
	lines = readdb(db_fname, "SELECT * FROM " + table + " WHERE name LIKE '%" + name + "%'")
	users = []
	for line in lines:
		name = line[0]
		cipher = line[1]
		salt = line[4].replace(" #", "")
		if cipher == '':
			users.append((name, salt))
			continue
		if cipher not in hashlib.algorithms_available:
			raise ValueError("Unsupported hash cipher: " + cipher)		
		
		nbeg = int(line[2]) - 1
		nend = int(line[3])
			
		hasher = hashlib.new(cipher)
		hasher.update((name + "\n").encode("utf-8"))
		hashpart = hasher.hexdigest()
		users.append((name, hashpart[nbeg:nend] + salt))
	return users
	

def list(dbfname, table) -> list:
	if (table is None) or (table == ""):
		answer = readdb(dbfname, "SELECT name FROM sqlite_master WHERE type='table'")
	else:
		answer = readdb(dbfname, "SELECT name, comm FROM " + table)
	return answer
