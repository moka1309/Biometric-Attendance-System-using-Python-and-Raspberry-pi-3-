#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PyFingerprint
Copyright (C) 2015 Bastian Raschke <bastian.raschke@posteo.de>
All rights reserved.

"""
from flask import Flask, session, redirect, url_for, escape, request, render_template, flash
import sqlite3
import sys
import pyfingerprint
import I2C_LCD_driver
import time
import hashlib
from pyfingerprint import PyFingerprint


## Enrolls new finger
##

## Tries to initialize the sensor
try:
	f = PyFingerprint('/dev/serial0', 9600, 0xFFFFFFFF, 0x00000000)

	if ( f.verifyPassword() == False ):
		raise ValueError('The given fingerprint sensor password is wrong!')

except Exception as e:
	print('The fingerprint sensor could not be initialized!')
	print('Exception message: ' + str(e))
	exit(1)

## Gets some sensor information
print('Currently used templates: ' + str(f.getTemplateCount()))

## Tries to enroll new finger
try:
	print('Waiting for finger...')

	## Wait that finger is read
	while ( f.readImage() == False ):
		pass

	## Converts read image to characteristics and stores it in charbuffer 1
	f.convertImage(0x01)

	## Checks if finger is already enrolled
	result = f.searchTemplate()
	positionNumber = result[0]

	if ( positionNumber >= 0 ):
		print('Template already exists at position #' + str(positionNumber))
		exit(0)

	print('Remove finger...')
	time.sleep(2)

	print('Waiting for same finger again...')

	## Wait that finger is read again
	while ( f.readImage() == False ):
		pass

	## Converts read image to characteristics and stores it in charbuffer 2
	f.convertImage(0x02)

	## Compares the charbuffers
	if ( f.compareCharacteristics() == 0 ):
		raise Exception('Fingers do not match')

	## Creates a template
	f.createTemplate()

	## Saves template at new position number
	positionNumber = f.storeTemplate()

	r = raw_input("Enter Roll Number: ")
	## Loads the found template to charbuffer 1
	f.loadTemplate(positionNumber, 0x01)

	## Downloads the characteristics of template loaded in charbuffer 1
	characterics = str(f.downloadCharacteristics(0x01)).encode('utf-8')

	## Hashes characteristics of template
	cre_hash = hashlib.sha256(characterics).hexdigest()
	conn = sqlite3.connect('/home/pi/attendance/app.db')
	curs = conn.cursor()
	curs.execute('INSERT INTO finger_store(rollnum, hashval, id) values(?, ?, ?)',(r, cre_hash, positionNumber))
	conn.commit()
	conn.close()
	print('Finger enrolled successfully!')
	print('New template position #' + str(positionNumber))

except Exception as e:
	print('Operation failed!')
	print('Exception message: ' + str(e))
	exit(1)
