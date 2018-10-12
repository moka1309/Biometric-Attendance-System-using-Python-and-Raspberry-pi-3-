#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PyFingerprint
Copyright (C) 2015 Bastian Raschke <bastian.raschke@posteo.de>
All rights reserved.

"""

from pyfingerprint import PyFingerprint


## Deletes a finger from sensor
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

## Tries to delete the template of the finger
try:
    positionNumber = input('Please enter the template position you want to delete: ')
    positionNumber = int(positionNumber)

    if ( f.deleteTemplate(positionNumber) == True ):
        print('Template deleted!')

except Exception as e:
    print('Operation failed!')
    print('Exception message: ' + str(e))
    exit(1)
