#!/usr/bin/env python3
from sys import path
from shutil import copyfile
import unittest

import maketestdb

path.append("../")
import src.libpwman as libpwman
	

class FunctionalTestsTables(unittest.TestCase):
	testDBFname = "test.db"
	
	def setUp(self):
		copyfile("test.db.original", self.testDBFname)
	
	def test_addtable(self):
		libpwman.addtable(self.testDBFname, "mytest_table")
		libpwman.addtable(self.testDBFname, "mytest_table")
		tlist = libpwman.list(self.testDBFname, None)
		self.assertEqual(tlist, [('test_table',), ("mytest_table",)])
		
	def test_mvtable(self):
		libpwman.mvtable(self.testDBFname, "test_table", "иваси")
		tlist = libpwman.list(self.testDBFname, None)
		self.assertEqual(tlist, [("иваси",)])
		try:
			libpwman.mvtable(self.testDBFname, "table1", "table2")
		except ValueError as e:
			self.assertEqual(str(e), "no such table: table1")
			
	def test_rmtable(self):
		libpwman.rmtable(self.testDBFname, "test_table")
		tlist = libpwman.list(self.testDBFname, None)
		self.assertEqual(tlist, [])
		# test remove nonexisted table
		try:
			libpwman.rmtable(self.testDBFname, "test_table")
		except ValueError as e:
			self.assertEqual(str(e), "no such table: test_table")
	
	def test_list_wotable(self):
		tlist = libpwman.list(self.testDBFname, None)
		self.assertEqual(tlist, [("test_table",)])
		tlist = libpwman.list(self.testDBFname, "")
		self.assertEqual(tlist, [("test_table",)])


class TestIntFun(unittest.TestCase):
	def test_param_san_check(self):
		ref_array = (
			("Basic test", "test_table", "Sam", "sha256", "1", "12", "lalala", "test user",
				("test_table", "Sam", "sha256", "1", "12", "lalala", "test user")),
			("Quotes test", "test_table", "S'am", "sha256", "1", "12", "lalala", "test user",
				("test_table", "S''am", "sha256", "1", "12", "lalala", "test user")),
			("Russian test", "test_table", "Иван Болконский", "sha256", "1", "12", "иванъ", "тест на русский",
				("test_table", "Иван Болконский", "sha256", "1", "12", "иванъ", "тест на русский")),
			("Special symbols test", "test table", "S'am", "sha256", "1", "12", "la#@_ la", "t#$&_-()=+':%/\"*,.est user",
				("test table", "S''am", "sha256", "1", "12", "la#@_ la", "t#$&_-()=+'':%/\"*,.est user")),
			)
		for ref_data in ref_array:
			with self.subTest(name=ref_data[0]):
				test_data = libpwman.param_san_check(*ref_data[1:-1])
				self.assertEqual(test_data, ref_data[-1])
	
	def test_param_san_check_exceptions(self):
		long_name = ''.join("aaaaaa" for i in range(10))
		ref_array = (
			("Name too long", "test_table", long_name, "sha256", "1", "12", "lalala",
				"test user", "user name max len is 50 symbols"),
			("Name is empty", "test_table", "", "sha256", "1", "12", "lalala",
				"test user", "user name can't be empty"),
			("Wrong cipher", "test_table", "Igor", "rare soviet cipher", "1", "12", "lalala",
				"test user", "Unsupported hash cipher: rare soviet cipher"),
			("nbeg not num", "test_table", "Sandy", "sha256", "bla", "1", "lalala",
				"test user", "invalid literal for int() with base 10: 'bla'"),
			("nend not num", "test_table", "Sandy", "sha256", "3", "tra", "lalala",
				"test user", "invalid literal for int() with base 10: 'tra'"),
			("nbeg > nend", "test_table", "Sandy", "sha256", "10", "1", "lalala",
				"test user", "nbeg must be less than nend"),
			("nbeg < 0", "test_table", "Sandy", "sha256", "-1", "1", "lalala", "test user", "nbeg must be 1 to 15"),
			("nbeg > 15", "test_table", "Sandy", "sha256", "25", "27", "lalala", "test user", "nbeg must be 1 to 15"),
			("nend < 0", "test_table", "Sandy", "sha256", "10", "-1", "lalala", "test user", "nend must be 1 to 15"),
			("nend > 15", "test_table", "Sandy", "sha256", "10", "25", "lalala", "test user", "nend must be 1 to 15"),
			("salt > 15", "test_table", "Sandy", "sha256", "10", "11", long_name, "test user", "Max salt len is 16")
		)
		for ref_data in ref_array:
			with self.subTest(Name=ref_data[0]):
				try:
					libpwman.param_san_check(*ref_data[1:-1])
				except ValueError as e:
					self.assertEqual(str(e), ref_data[-1])
	

class FunctionalTestsUsers(unittest.TestCase):
	testDBFname = "test.db"
	
	def setUp(self):
		copyfile("test.db.original", self.testDBFname)
		
	def test_adduser(self):
		# Check error if table doesnt exist
		try:
			libpwman.adduser(self.testDBFname, "mytest_table", "Sandy o'Neil", "sha256", "1", "10", "lalala", "test user")
		except ValueError as e:
			self.assertEqual(str(e), "no such table: mytest_table")
		libpwman.adduser(
			self.testDBFname,
			"test_table", "Sandy o'Shean", "sha256", "1", "10", "lal_a la ", "test user's attenti@n")
		test_list = libpwman.readdb(self.testDBFname, "SELECT name FROM test_table WHERE name = 'Sandy o''Shean'")
		self.assertEqual(test_list, [("Sandy o'Shean",)])
	
	def test_rmuser(self):
		users = libpwman.readdb(self.testDBFname, "SELECT name FROM test_table")
		for user in users:
			with self.subTest(Name="Remove user " + user[0]):
				ref_list = libpwman.readdb(self.testDBFname, "SELECT name FROM test_table")
				ref_list.sort()
				libpwman.rmuser(self.testDBFname, "test_table", user[0])
				test_list = libpwman.readdb(self.testDBFname, "SELECT name FROM test_table")
				test_list.append(user)
				test_list.sort()
				self.assertEqual(test_list, ref_list)
		# Remove nonexistent user
		libpwman.rmuser(self.testDBFname, "test_table", "noMandy")
	
	def test_searchusers(self):
		ref_line = list(libpwman.readdb(self.testDBFname, "SELECT * FROM test_table WHERE comm='searchtest'")[0])
		ref_array = (
			("search by name",		self.testDBFname, "test_table",	ref_line[0],	"",			"",				"",				"",			""),
			("search by cipher",	self.testDBFname, "test_table",	"",			ref_line[1],	"",				"",				"",			""),
			("search by nbeg",		self.testDBFname, "test_table",	"",			ref_line[1],	str(ref_line[2]),	"",				"",			""),
			("search by nend",		self.testDBFname, "test_table",	"",			ref_line[1],	"",				str(ref_line[3]),	"",			""),
			("search by salt",		self.testDBFname, "test_table",	"",			"",			"",				"",				ref_line[4],	""),
			("search by text",		self.testDBFname, "test_table",	"",			"",			"",				"",				"",			ref_line[5])
		)
		for ref_data in ref_array:
			with self.subTest(Name=ref_data[0]):
				test_data = libpwman.searchusers(*ref_data[1:])
				self.assertEqual(list(test_data[0]), ref_line)
	
	def test_pwusers(self):
		# test password with hash
		test_list = libpwman.pwusers(self.testDBFname, "test_table", "John@Smith")
		self.assertEqual(test_list, [('1John@Smith.com', '983be4d4233'), ('2John@Smith.com', '5793dace86e')])
		# test password without hash
		libpwman.adduser(self.testDBFname, "test_table", "Mandy1", "", "", "", "mysalt", "pwissalt")
		libpwman.adduser(self.testDBFname, "test_table", "Mandy2", "", "", "", "mysaly", "pwissalt")
		test_list = libpwman.pwusers(self.testDBFname, "test_table", "Mandy")
		self.assertEqual(test_list, [('Mandy1', 'mysalt'), ('Mandy2', 'mysaly')])
		# nonexist user
		test_list = libpwman.pwusers(self.testDBFname, "test_table", "Abdullah")
		self.assertEqual(test_list, [])
		
	def test_list_withtable(self):
		ref_list = libpwman.readdb(self.testDBFname, "SELECT name, comm FROM test_table")
		test_list = libpwman.list(self.testDBFname, "test_table")
		self.assertEqual(test_list, ref_list)
		try:
			libpwman.list(self.testDBFname, "nonexist")
		except ValueError as e:
			self.assertEqual(str(e), "no such table: nonexist")
	

if __name__ == "__main__":
	maketestdb.make_test_db()
	maketestdb.print_test_db()
	unittest.main(verbosity=2)
