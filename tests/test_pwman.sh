#!/usr/bin/env bash

CMDNAME="../src/pwman --db-fname ./test.db"

countPassed=0
countFailed=0

function calcStats() {
	if [[ $1 -eq 0 ]]; then
		countPassed=$(($countPassed + 1))
	else
		countFailed=$(($countFailed + 1))
	fi
}

function printReport() {
	echo "Tests passed: " $countPassed
	echo "Tests failed: " $countFailed
	if [[ $countFailed -eq 0 ]]; then
		echo "Case passed."
		exit 0
	else
		echo "Case failed"
		exit 1
	fi
}
function test_add() {
	rm -f test.db
	sqlite3 test.db "CREATE TABLE mytesttable (name TEXT UNIQUE, cipher TEXT, nbeg INTEGER, nend INTEGER, salt TEXT, comm TEXT)"
	$CMDNAME add -t mytesttable -n vasya > /dev/null
	sqlite3 test.db "SELECT name FROM mytesttable" | grep vasya > /dev/null
	if [[ $? -ne 0 ]]; then
		echo "Test adduser failed."
		return 1
	fi
	return 0
}

function test_rm() {
	echo "Not implemented"
	return 1
}

function test_list() {
	rm -f test.db
	sqlite3 test.db "CREATE TABLE mytesttable (name TEXT UNIQUE, cipher TEXT, nbeg INTEGER, nend INTEGER, salt TEXT, comm TEXT)"
	$CMDNAME add -t mytesttable -n vasya > /dev/null
	$CMDNAME add -t mytesttable -n petya > /dev/null
	$CMDNAME add -t mytesttable -n sammuel > /dev/null
	sqlite3 test.db "SELECT name FROM mytesttable" | sort > ./tmp.users
	diff -q ./tmp.users ./test_pwman_test_list.users > /dev/null
	if [[ $? -eq 0 ]]; then
		return 0
	else
		echo "Test list failed."
		return 1
	fi
}

test_add
calcStats $?

test_rm
calcStats $?

test_list
calcStats $?

printReport
