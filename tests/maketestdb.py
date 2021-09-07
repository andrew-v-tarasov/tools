import sqlite3
from os import path, remove

fName = "test.db.original"


def writedb(db_fname, db_request):
	db_handle = sqlite3.connect(db_fname)
	cur = db_handle.cursor()
	cur.execute(db_request)
	db_handle.commit()
	db_handle.close()
	

def make_test_db():
	if path.isfile(fName):
		remove(fName)
	writedb(
		fName, "CREATE TABLE test_table  (name TEXT UNIQUE, cipher TEXT,"
		"nbeg INTEGER, nend INTEGER, salt TEXT, comm TEXT)")
	writedb(fName, "INSERT INTO test_table VALUES('1John@Smith.com', 'sha256', '3', '13', '', '')")
	writedb(fName, "INSERT INTO test_table VALUES('2John@Smith.com', 'sha256', '3', '13', '', '')")
	writedb(fName, "INSERT INTO test_table VALUES('Sam o''Connor', '', '', '', 'immortal', 'creature')")
	writedb(fName, "INSERT INTO test_table VALUES('Ян Ван Эйк', 'md5', '4', '8', '#''%', 'searchtest')")
	writedb(fName, "INSERT INTO test_table VALUES('Sandra', '', '', '', '', '')")
	writedb(fName, "INSERT INTO test_table VALUES('Mandra', '', '', '', '', '')")
	

def print_test_db():
	db_handle = sqlite3.connect(fName)
	cur = db_handle.cursor()
	cur.execute("SELECT * FROM test_table")
	for line in cur.fetchall():
		print(line)
		

if __name__ == "__main__":
	make_test_db()
	print_test_db()
	