from pad4pi import rpi_gpio
import sqlite3
import sys
import pyfingerprint
import I2C_LCD_driver
from time import *
import datetime
import hashlib
from pyfingerprint import PyFingerprint
import calendar
import time

###connceting to the lcd driver
mylcd = I2C_LCD_driver.lcd()

pressed_keys =''
pin="12345"
fun = ''
yer = ''
code = ''
cors_type = ''
branch = ''
last = ''
roll_id = ''
r = ''

def finger():
	## Search for a finger
	##

	## Tries to initialize the sensor
	try:
		f = PyFingerprint('/dev/serial0', 9600, 0xFFFFFFFF, 0x00000000)

		if ( f.verifyPassword() == False ):
			raise ValueError('The given fingerprint sensor password is wrong!')
			startChoice()
	except Exception as e:
		print('The fingerprint sensor could not be initialized!')
		print('Exception message: ' + str(e))
		startChoice()

	## Gets some sensor information
	print('Currently used templates: ' + str(f.getTemplateCount()))

	## Tries to search the finger and calculate hash
	try:
		mylcd.lcd_clear()
		mylcd.lcd_display_string('Waiting for finger..',2)

		## Wait that finger is read
		while ( f.readImage() == False ):
			pass

		## Converts read image to characteristics and stores it in charbuffer 1
		f.convertImage(0x01)

		## Searchs template
		result = f.searchTemplate()

		positionNumber = result[0]
		accuracyScore = result[1]

		if ( positionNumber == -1 ):
			mylcd.lcd_clear()
			mylcd.lcd_display_string('No match found!')
			sleep(2)
			mylcd.lcd_clear()
			startChoice()
		else:
			mylcd.lcd_clear()
			today_name = datetime.date.today()
			if (calendar.day_name[today_name.weekday()] != 'Sunday') and (calendar.day_name[today_name.weekday()] != 'Saturday'):
				## Generating TIME VALUES
				now = datetime.datetime.now()
				my_time_string_10 = "10:30:00"
				my_time_string_12 = "12:30:00"
				my_time_string_13 = "13:29:59"
				my_time_string_14 = "14:30:00"
				my_time_string_16 = "16:00:01"
				time_10 = datetime.datetime.strptime(my_time_string_10, "%H:%M:%S")
				time_12 = datetime.datetime.strptime(my_time_string_12, "%H:%M:%S")
				time_13 = datetime.datetime.strptime(my_time_string_13, "%H:%M:%S")
				time_14 = datetime.datetime.strptime(my_time_string_14, "%H:%M:%S")
				time_16 = datetime.datetime.strptime(my_time_string_16, "%H:%M:%S")

				# I am supposing that the date must be the same as now
				time_10 = now.replace(hour=time_10.time().hour, minute=time_10.time().minute, second=time_10.time().second, microsecond=0)
				time_12 = now.replace(hour=time_12.time().hour, minute=time_12.time().minute, second=time_12.time().second, microsecond=0)
				time_13 = now.replace(hour=time_13.time().hour, minute=time_13.time().minute, second=time_13.time().second, microsecond=0)
				time_14 = now.replace(hour=time_14.time().hour, minute=time_14.time().minute, second=time_14.time().second, microsecond=0)
				time_16 = now.replace(hour=time_16.time().hour, minute=time_16.time().minute, second=time_16.time().second, microsecond=0)

				print('Found template at position #' + str(positionNumber))
				mylcd.lcd_display_string('PLEASE WAIT',2,3)

				## Create Hash Value for finger
				##

				## Loads the found template to charbuffer 1
				f.loadTemplate(positionNumber, 0x01)

				## Downloads the characteristics of template loaded in charbuffer 1
				characterics = str(f.downloadCharacteristics(0x01)).encode('utf-8')
				val_hash = hashlib.sha256(characterics).hexdigest()
				## Hashes characteristics of template
				print('SHA-2 hash of template: ' + val_hash)

				## GETTING INFORMATION FROM DATABASE
				conn = sqlite3.connect('/home/pi/attendance/app.db')
				curs = conn.cursor()
				db_val = curs.execute('SELECT rollnum, hashval from finger_store where hashval in (values(?))', [val_hash])
				for row in db_val:
					ext_id = row[0]
					mylcd.lcd_clear()
					mylcd.lcd_display_string("YOUR ID NUMBER:",2,2)
					mylcd.lcd_display_string(ext_id,3,3)
					sleep(2)
					mylcd.lcd_clear()
				conn.commit()
				conn.close()

				con = sqlite3.connect('/home/pi/attendance/app.db')
				curs2 = con.cursor()
				curs2.execute('SELECT date from attendance where (date, rollnum) in (values(?, ?))', (datetime.date.today(), ext_id))
				d = curs2.fetchone()
				con.close()

				if d == None:
					con = sqlite3.connect('/home/pi/attendance/app.db')
					c = con.cursor()
					c.execute('INSERT INTO attendance (rollnum,date) values(?, ?)',(ext_id, datetime.date.today()))
					con.commit()
					con.close()
				## GETTING INFORMATION FROM DATABASE
				con = sqlite3.connect('/home/pi/attendance/app.db')
				curs2 = con.cursor()
				curs2.execute('SELECT status,statusexit,statusnoon,statusnoonexit from attendance where (date, rollnum) in (values(?, ?))', (datetime.date.today(), ext_id))
				row = curs2.fetchall()
				for all in row:
					status1 = all[0]
					status2 = all[1]
					status3 = all[2]
					status4 = all[3]
				con.close()

				if status1 == 'absent':
					if now < time_10:
						con = sqlite3.connect('/home/pi/attendance/app.db')
						c = con.cursor()
						c.execute('UPDATE attendance Set status = ? where (rollnum, date) in (values(?, ?))',('present', ext_id, datetime.date.today()))
						con.commit()
						con.close()
						mylcd.lcd_display_string("Attendance Success for",1)
						mylcd.lcd_display_string(" this Morining",2)
						sleep(2)
						mylcd.lcd_clear()
						mylcd.lcd_display_string("Dont forgot to ",1)
						mylcd.lcd_display_string("comeback after 12:30 PM",2)
						sleep(2)
						mylcd.lcd_clear()
					elif (now >= time_10) and (now <= time_13):
						mylcd.lcd_display_string("Sorry, You are Late today",1)
						sleep(2)
						mylcd.lcd_clear()
						mylcd.lcd_display_string("Come Afternoon ",2)
						mylcd.lcd_display_string("or Tomorrow",3)
						sleep(2)
						mylcd.lcd_clear()
					elif now > time_13:
						if status3 == 'absent':
							if now <= time_14:
								con = sqlite3.connect('/home/pi/attendance/app.db')
								c = con.cursor()
								c.execute('UPDATE attendance Set statusnoon = ? where (rollnum, date) in (values(?, ?))',('present',ext_id,datetime.date.today()))
								con.commit()
								con.close()
								mylcd.lcd_display_string("Attendance Success ",1)
								mylcd.lcd_display_string("for this Afternoon",2)
								sleep(2)
								mylcd.lcd_clear()
								mylcd.lcd_display_string("Dont forgot to  ",1)
								mylcd.lcd_display_string("comeback after",2)
								mylcd.lcd_display_string("04:00 PM ",3)
								sleep(3)
								mylcd.lcd_clear()
							elif now > time_14:
								mylcd.lcd_display_string("Sorry, You are Late",2)
								sleep(2)
								mylcd.lcd_clear()
								mylcd.lcd_display_string("Please Come Early ",1)
								mylcd.lcd_display_string("Tomorrow",2,2)
								sleep(2)
								mylcd.lcd_clear()
						elif status3 == 'present':
							if now < time_16:
								mylcd.lcd_display_string("You're leaving Early",1)
								mylcd.lcd_display_string("Please come back",2)
								mylcd.lcd_display_string("after 4 PM",3)
								sleep(3)
								mylcd.lcd_clear()
							elif now >= time_16:
								if status4 == 'present':
									mylcd.lcd_display_string("Thought you were",1)
									mylcd.lcd_display_string("already in your home!",2)
									sleep(2)
									mylcd.lcd_clear()
								else:
									con = sqlite3.connect('/home/pi/attendance/app.db')
									c = con.cursor()
									c.execute('UPDATE attendance Set statusnoonexit = ? where (rollnum, date) in (values(?, ?))',('present',ext_id,datetime.date.today()))
									con.commit()
									con.close()
									mylcd.lcd_display_string("Attendance Success,",2)
									mylcd.lcd_display_string(" Happy Day!",3,2)
									sleep(2)
									mylcd.lcd_clear()
				elif status1 == 'present':
					if now < time_12:
						mylcd.lcd_display_string("Not the time to",2)
						mylcd.lcd_display_string("leave",3,2)
						sleep(2)
						mylcd.lcd_clear()
					elif (now >= time_12) and (now <= time_13):
						con = sqlite3.connect('/home/pi/attendance/app.db')
						c = con.cursor()
						c.execute('UPDATE attendance Set statusexit = ? where (rollnum, date) in (values(?, ?))',('present',ext_id,datetime.date.today()))
						con.commit()
						con.close()
						mylcd.lcd_display_string("Attendance Success",1)
						mylcd.lcd_display_string("Now Go and",2,2)
						mylcd.lcd_display_string("have your LUNCH :)",3)
						sleep(3)
						mylcd.lcd_clear()
					elif now > time_13:
						if status3 == 'absent':
							if now <= time_14:
								con = sqlite3.connect('/home/pi/attendance/app.db')
								c = con.cursor()
								c.execute('UPDATE attendance Set statusnoon = ? where (rollnum, date) in (values(?, ?))',('present',ext_id,datetime.date.today()))
								con.commit()
								con.close()
								mylcd.lcd_display_string("Attendance Success ",1)
								mylcd.lcd_display_string("for this Afternoon",2)
								sleep(2)
								mylcd.lcd_clear()
								mylcd.lcd_display_string("Dont forgot to  ",1)
								mylcd.lcd_display_string("comeback after",2)
								mylcd.lcd_display_string("04:00 PM ",3)
								sleep(3)
								mylcd.lcd_clear()
							elif now > time_14:
								mylcd.lcd_display_string("Sorry, You are Late",2)
								sleep(2)
								mylcd.lcd_clear()
								mylcd.lcd_display_string("Please Come Early ",1)
								mylcd.lcd_display_string("Tomorrow",2,2)
								sleep(2)
								mylcd.lcd_clear()
						elif status3 == 'present':
							if now < time_16:
								mylcd.lcd_display_string("You're leaving Early",1)
								mylcd.lcd_display_string("Please come back",2)
								mylcd.lcd_display_string("after 4 PM",3)
								sleep(3)
								mylcd.lcd_clear()
							elif now >= time_16:
								if status4 == 'present':
									mylcd.lcd_display_string("Thought you were",1)
									mylcd.lcd_display_string("already in your home!",2)
									sleep(2)
									mylcd.lcd_clear()
								else:
									con = sqlite3.connect('/home/pi/attendance/app.db')
									c = con.cursor()
									c.execute('UPDATE attendance Set statusnoonexit = ? where (rollnum, date) in (values(?, ?))',('present',ext_id,datetime.date.today()))
									con.commit()
									con.close()
									mylcd.lcd_display_string("Attendance Success,",2)
									mylcd.lcd_display_string(" Happy Day!",3,2)
									sleep(2)
									mylcd.lcd_clear()
			else:
				mylcd.lcd_clear()
				mylcd.lcd_display_string('Today is a holiday',1)
				sleep(2)
				mylcd.lcd_display_string('So no ATTENDANCE',2)
				sleep(2)
				mylcd.lcd_display_string('........ENJOY.......',3)
				sleep(2)
			startChoice()
	except Exception as e:
		print('Operation failed!')
		print('Exception message: ' + str(e))
		startChoice()

##Enroll
def enroll():
	global roll_id
	print(roll_id)
	r = roll_id
	print("Roll is: ",r)
	## GETTING INFORMATION FROM DATABASE
	conn = sqlite3.connect('/home/pi/attendance/app.db')
	curs = conn.cursor()
	db_val = curs.execute('SELECT rollnum from finger_store where rollnum in (values(?))', [r])
	coun = (len(list(db_val)))
	print(coun)
	if coun >= 1:
		mylcd.lcd_clear()
		mylcd.lcd_display_string('ID Number Already',1)
		mylcd.lcd_display_string('Taken',2,2)
		sleep(2)
		conn.commit()
		conn.close()
		startChoice()
	else:
		conn.commit()
		conn.close()
		## Enrolls new finger
		##

		## Tries to initialize the sensor
		try:
			f = PyFingerprint('/dev/serial0', 9600, 0xFFFFFFFF, 0x00000000)

			if ( f.verifyPassword() == False ):
				mylcd.lcd_clear()
				mylcd.lcd_display_string('Contact Admin',1)
				sleep(2)
				raise ValueError('The given fingerprint sensor password is wrong!')
				
		except Exception as e:
			mylcd.lcd_clear()
			mylcd.lcd_display_string('Contact Admin',1)
			sleep(2)
			print('The fingerprint sensor could not be initialized!')
			print('Exception message: ' + str(e))
			startChoice()

		## Gets some sensor information
		mylcd.lcd_clear()
		mylcd.lcd_display_string('Currently used',1)
		mylcd.lcd_display_string('templates: ',2)
		mylcd.lcd_display_string(str(f.getTemplateCount()),2,13)
		sleep(2)
		print('Currently used templates: ' + str(f.getTemplateCount()))

		## Tries to enroll new finger
		try:
			mylcd.lcd_clear()
			mylcd.lcd_display_string('Waiting for Finger',2,2)

			## Wait that finger is read
			while ( f.readImage() == False ):
				pass

			## Converts read image to characteristics and stores it in charbuffer 1
			f.convertImage(0x01)

			## Checks if finger is already enrolled
			result = f.searchTemplate()
			positionNumber = result[0]

			if ( positionNumber >= 0 ):
				mylcd.lcd_clear()
				mylcd.lcd_display_string('Template already',1)
				mylcd.lcd_display_string('exists at  ',2)
				mylcd.lcd_display_string('position # ',3)
				mylcd.lcd_display_string(str(positionNumber),3,13)
				sleep(3)
				print('Template already exists at position #' + str(positionNumber))
				startChoice()
			else:
				mylcd.lcd_clear()
				mylcd.lcd_display_string('Remove finger...',2,2)
				print('Remove finger...')
				time.sleep(2)
				
				mylcd.lcd_clear()
				mylcd.lcd_display_string('Waiting for same',2)
				mylcd.lcd_display_string(' finger again',3)
				print('Waiting for same finger again...')

				## Wait that finger is read again
				while ( f.readImage() == False ):
					pass

				## Converts read image to characteristics and stores it in charbuffer 2
				f.convertImage(0x02)

				## Compares the charbuffers
				if ( f.compareCharacteristics() == 0 ):
					mylcd.lcd_clear()
					mylcd.lcd_display_string('Fingers not matched',2)
					sleep(2)
					raise Exception('Fingers do not match')
				## Creates a template
				f.createTemplate()

				## Saves template at new position number
				positionNumber = f.storeTemplate()
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
				mylcd.lcd_clear()
				mylcd.lcd_display_string('Finger enrolled',2)
				mylcd.lcd_display_string('Successfully!',3,2)
				sleep(2)
				print('New template position #' + str(positionNumber))
				startChoice()
			
		except Exception as e:
			print('Operation failed!')
			print('Exception message: ' + str(e))
			startChoice()
		

## Start for Enrollment Process

def pwd():
	global fun
	fun = fun.replace(fun,'password')
	mylcd.lcd_clear()
	mylcd.lcd_display_string('Enter Password',2)
	print('Enter Password')
	
def passWord(key):
	global pressed_keys
	global pin
	if key=='#':
		print(pressed_keys)
		if pressed_keys == pin:
			clear_keys()
			year()
		else:
			mylcd.lcd_clear()
			mylcd.lcd_display_string('Wrong Password',2)
			print('Wrong Password')
			sleep(2)
			startChoice()
	else:
		pressed_keys += key
		
def year():
	global fun
	fun = fun.replace(fun,'year')
	mylcd.lcd_clear()
	mylcd.lcd_display_string('Enter last 2 digits',1)
	mylcd.lcd_display_string('of Joining Year',2)
	print('Enter last two digits of Joining year')

def yearJoin(key):
	global pressed_keys
	global yer
	if key=='#':
		if len(pressed_keys) != 2:
			clear_keys()
			mylcd.lcd_clear()
			mylcd.lcd_display_string('Sorry, Enter Only',1)
			mylcd.lcd_display_string(' 2 DIGIT Number',2)
			print("Enter only 2 DIGIT Number")
			sleep(2)
			year()
		else:
			yer = pressed_keys
			clear_keys()
			ccode()
	else:
		pressed_keys += key	
		
def ccode():
	global fun
	fun = fun.replace(fun,'code')
	mylcd.lcd_clear()
	mylcd.lcd_display_string('ENTER NUMBER OF ',1)
	mylcd.lcd_display_string(' COLLEGE CODE',2)
	print('Enter number of college code')
	
def colCode(key):
	global pressed_keys
	global code
	if key=='#':
		colCodeDict = {'1':'4H','2':'8Q','3':'8P','4':'2F','5':'E8','6':'2G','7':'HN','8':'HM','9':'70','10':'AK','11':'G2','12':'HP',
					'13':'2H','14':'H0','15':'JP','16':'3K','17':'8R','18':'5K','19':'2K','20':'F3','21':'2M','22':'2N','23':'P1','24':'2Q',
					'25':'2P','26':'2R','27':'8T','28':'2T','29':'FH','30':'HQ','31':'5M','32':'9X','33':'AT','34':'F2','35':'2J','36':'2U',
					'37':'3A','38':'F8','39':'8U','40':'3C','41':'74','42':'F5','43':'3D','44':'3E','45':'9Y','46':'3H','47':'BC','48':'3F',
					'49':'3G','50':'EH','51':'3J','52':'8W','53':'F4','54':'8X','55':'69','56':'72','57':'L4','58':'3M','59':'HR','60':'KB',
					'61':'F1','62':'71','63':'8Y','64':'3N','65':'73','66':'G1','67':'R6','68':'3P','69':'8Z','70':'K2','71':'09','72':'3Q',
					'73':'3R','74':'3T','75':'K5','76':'HT','77':'KF','78':'X5','79':'JM','80':'3U','81':'4A','82':'9A','83':'4E','84':'F6',
					'85':'9B','86':'W5','87':'9C','88':'4C','89':'JN','90':'12','91':'75','92':'38','93':'G8','94':'9D','95':'4F','96':'F7',
					'97':'G0','98':'BF','99':'KH','100':'78','101':'9E','102':'BG','103':'9F','104':'9G','105':'9H','106':'4G','107':'G3','108':'BM',
					'109':'AM','110':'4J','111':'4K','112':'HU','113':'L2','114':'BP','115':'9J','116':'4M','117':'9K','118':'4N','119':'4P','0':'00'
					}
		if pressed_keys in colCodeDict:
			code = colCodeDict[pressed_keys]
			clear_keys()
			cType()
		else:
			clear_keys()
			mylcd.lcd_clear()
			mylcd.lcd_display_string('WRONG NUMBER ENTERED',1)
			print("Wrong Number Entered")
			sleep(2)
			ccode()
			
	else:
		pressed_keys += key

def cType():
	global fun
	fun = fun.replace(fun,'type')
	mylcd.lcd_clear()
	mylcd.lcd_display_string('CHOOSE COURSE TYPE',1)
	mylcd.lcd_display_string('1. DAY TIME',2)
	mylcd.lcd_display_string('2.LATERAL ENTRY',3)
	print('Choose Course Type')
	print('1.Day Time')
	print('2.Lateral Entey')

def courseType(key):
	global pressed_keys
	global cors_type
	if key=='#':
		if pressed_keys == '1':
			cors_type = '1'
			clear_keys()
			branch()
		elif pressed_keys == '2':
			cors_type = '5'
			clear_keys()
			branch()
		else:
			clear_keys()
			mylcd.lcd_clear()
			mylcd.lcd_display_string('CHOOSE CORECT NUMBER',1)
			print('Choose correct number')
			sleep(2)
			cType()
	else:
		pressed_keys += key

def branch():
	global fun
	fun = fun.replace(fun,'branch')
	mylcd.lcd_clear()
	mylcd.lcd_display_string('  CHOOSE BRANCH',1)
	mylcd.lcd_display_string('1.BTech 2.MTech ',2)
	mylcd.lcd_display_string('3.MBA 4.MCA 5.BPhar',3)
	mylcd.lcd_display_string('6.MPharm 7.Pharm.D',4)
	print('Choose Branch')
	print('1.BTech 2.MTech 3.MBA\n4.MCA 5.BPhar 6.MPharm 7.Pharm.D')

def chooseBranch(key):
	global pressed_keys
	global branch
	if key=='#':
		if pressed_keys == '1':
			branch = 'A'
			clear_keys()
			las()
		elif pressed_keys == '2':
			branch = 'D'
			clear_keys()
			las()
		elif pressed_keys == '3':
			branch = 'E'
			clear_keys()
			las()
		elif pressed_keys == '4':
			branch = 'F'
			clear_keys()
			las()
		elif pressed_keys == '5':
			branch = 'R'
			clear_keys()
			las()
		elif pressed_keys == '6':
			branch = 'S'
			clear_keys()
			las()
		elif pressed_keys == '7':
			branch = 'T'
			clear_keys()
			las()
		else:
			clear_keys()
			mylcd.lcd_clear()
			mylcd.lcd_display_string('CHOOSE CORRECT NUMBER',1)
			print('Choose correct number')
			sleep(2)
			branch()
	else:
		pressed_keys += key

def las():
	global fun
	fun = fun.replace(fun,'last')
	mylcd.lcd_clear()
	mylcd.lcd_display_string('Enter Last Four',1)
	mylcd.lcd_display_string('Numbers of ID',2)
	print('Enter last four numbers of ID')

def lastFour(key):
	global pressed_keys
	global last
	if key=='#':
		if len(pressed_keys) == 4:
			last = pressed_keys
			clear_keys()
			conform()
		else:
			clear_keys()
			mylcd.lcd_clear()
			mylcd.lcd_display_string('Sorry,ENTER EXACTLY ',1)
			mylcd.lcd_display_string('FOUR NUMBERS',2,2)
			print('Enter exactly 4 numbers')
			sleep(2)
			las()
	else:
		pressed_keys += key

def conform():
	global fun
	global roll_id
	fun = fun.replace(fun,'conform')
	roll_id = yer+code+cors_type+branch+last
	mylcd.lcd_clear()
	mylcd.lcd_display_string('  Check Your ID  ',1)
	mylcd.lcd_display_string('1 : Confirm ',3,2)
	mylcd.lcd_display_string('2 : Cancel',4,2)
	mylcd.lcd_display_string(roll_id,2,2)
	print('Check Your ID ')
	print(roll_id)
	print('1 : Confirm')
	print('2 : Cancel')

def conformation(key):
	global pressed_keys
	global roll_id
	global yer
	global code
	global cors_type
	global branch
	global last
	if key=='#':
		if pressed_keys == '1':
			clear_keys()
			enroll()
		elif pressed_keys == '2':
			yer = yer.replace(yer,'')
			code = code.replace(code,'')
			cors_type = cors_type.replace(cors_type,'')
			branch = branch.replace(branch,'')
			last = last.replace(last,'')
			roll_id = roll_id.replace(roll_id,'')
			startChoice()
		else:
			clear_keys()
			mylcd.lcd_clear()
			mylcd.lcd_display_string(' Wrong Key Pressed',1)
			print('Wrong Key Pressed')
			sleep(2)
			conform()
	else:
		pressed_keys += key

## End of Enroll/ 

# Setup Keypad
KEYPAD = [
        ["1","2","3","A"],
        ["4","5","6","B"],
        ["7","8","9","C"],
        ["*","0","#","D"]
]

# same as calling: factory.create_4_by_4_keypad, still we put here fyi:
ROW_PINS = [16, 20, 21, 5] # BCM numbering; Board numbering is: 7,8,10,11 (see pinout.xyz/)
COL_PINS = [6, 13, 19, 26] # BCM numbering; Board numbering is: 12,13,15,16 (see pinout.xyz/)

factory = rpi_gpio.KeypadFactory()

# Try keypad = factory.create_4_by_3_keypad() or 
# Try keypad = factory.create_4_by_4_keypad() #for reasonable defaults
# or define your own:
keypad = factory.create_keypad(keypad=KEYPAD, row_pins=ROW_PINS, col_pins=COL_PINS)

#function to clear string
def clear_keys():
	global pressed_keys
	pressed_keys = pressed_keys.replace(pressed_keys,'')
	
#change store key function to do something on submission of a certain key that indicated send, will use pound for example.
def store_key(key):
	global pressed_keys
	global paass
	print(fun)
	if key=='#':
		#im printing but you should do whatever it is you intend to do with the sequence of keys.
		print(pressed_keys)
		if (pressed_keys=="1"):
			finger()
			startChoice()
		elif (pressed_keys=="2"):
			clear_keys()
			pwd()
		else:
			mylcd.lcd_clear()
			mylcd.lcd_display_string('Sorry, Choose Again',2)
			sleep(2)
			startChoice()
		

	else:
		pressed_keys += key
		

def startChoice():	
	global fun
	clear_keys()
	mylcd.lcd_clear()
	mylcd.lcd_display_string('Press Button',1)
	mylcd.lcd_display_string('1. Attendance',2)
	mylcd.lcd_display_string('2. Registration',3)
	fun = fun.replace(fun,'storekey')
## initializing Programming by calling the Start function
startChoice()

# store_key will be called each time a keypad button is pressed
def keyHandler(key):
	if fun == 'storekey':
		store_key(key)
	elif fun == 'password':
		passWord(key)
	elif fun == 'year':
		yearJoin(key)
	elif fun == 'code':
		colCode(key)
	elif fun == 'type':
		courseType(key)
	elif fun == 'branch':
		chooseBranch(key)
	elif fun == 'last':
		lastFour(key)
	elif fun == 'conform':
		conformation(key)
keypad.registerKeyPressHandler(keyHandler)

try:
	while(True):
		time.sleep(0.2)
except:
	keypad.cleanup()
