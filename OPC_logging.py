#! /usr/bin/python
import opc
import usbiss
import serial
from time import sleep
import time
import os
import sys
#from sht_sensor import Sht
home_dir = "/home/pi"

                       
#first make sure there is a home data directory
#might want to check the permissions too
data_dir = os.path.join(home_dir, "data")
if not os.path.exists(data_dir):
    try:
        os.makedirs(data_dir)
    except OSError:
        print "couldn't make home data directory"
        exit()
print("Sleeping 2 mins to ensure the fan is on")
sleep(120)
#Setup the USB connection 
spi = usbiss.USBISS("/dev/ttyACM0", 'spi', spi_mode=2, freq=500000)

# initiate the opc class -- this constructor is changed from David's
# original in order to give the OPC more time to set up before being
# asked about its firmware as it sometimes chokes -- (SPI feature)
alpha = opc.OPCN2(spi)


print "Attempting to turn on the OPC"
i=0
OPC_on=alpha.on()
if not OPC_on:
    print "OPC did not power up. Waiting 5 minutes seconds and trying again"
    sleep (300)
    print "Attempting to turn on the OPC"
    OPC_on=alpha.on()
    
else:
    print "OPC powered up OK"

print "Waiting 10 seconds for system to stabilize"
sleep(10)

# Read the info
print "Reading the information string"
print alpha.read_info_string()
#Construct a header string for the .csv file
PM_header = "PM1, PM2.5, PM10, bin0, bin1, bin2, bin3, bin4, bin5, bin6, bin7, bin8, bin9, bin10, bin11, bin12, bin13, bin14, bin15\n"
time_header = "Date, SysTime,"
#HT_header = "Temp, RH, Dewpoint,"
#GPS_header = "GPS_UTC, LatDeg, LatMin, Hemi, LonMin, LonDeg, Hemi,"
#column_headers = GPS_header+time_header+HT_header+PM_header
column_headers=time_header+PM_header

# Read the OPC data, temp and humidity, GPS data and the present time
i = 0
try:
    while True:
        try:
            # Read SHT75 temp, humidity and dewpoint
            #sht = Sht(48, 44)
            #Temp = sht.read_t()
            #RH = sht.read_rh()
            #DewP = sht.read_dew_point()
            #EnvString = str(Temp) + "," + str(RH) + "," + str(DewP)
            

#            #Get the time and date
            now=time.gmtime()
            timestring = str(now.tm_year)+"/"+str(now.tm_mon)+"/"+str(now.tm_mday)+","+str(now.tm_hour)+":"+str(now.tm_min)

#           Get location from GPS string
            #GPS_array = GPS_read()
            #timeUTC = GPS_array[1][:-8]+':'+GPS_array[1][-8:-6]+':'+GPS_array[1][-6:-4]
            #latDeg = GPS_array[3][:-7]
            #latMin = GPS_array[3][-7:]
            #latHem = GPS_array[4]
            #lonDeg = GPS_array[5][:-7]
            #lonMin = GPS_array[5][-7:]
            #lonHem = GPS_array[6]
            #knots = GPS_array[7]
            
            #GPSstring = str(timeUTC)+","+str(latDeg)+","+str(latMin)+","+str(latHem)+","+str(lonDeg)+","+str(lonMin)+","+str(lonHem)
        
            
#           Build up a datastring for the CSV file
            try:
                hist = alpha.histogram()
            except Exception as err:
                print("histogram failed to initialize")
                alpha = opc.OPCN2(spi)
                print "Attempting to turn on the OPC"
                OPC_on=alpha.on()
                if not OPC_on:
                    print "OPC did not power up. Waiting 5 minutes seconds and trying again"
                    sleep (300)
                    print "Attempting to turn on the OPC"
                    OPC_on=alpha.on()
                else:
                    print "OPC powered up OK"
                    print "Waiting 10 seconds for system to stabilize"
                    sleep(10)
                
            datastring = str(hist['PM1']) +"," + str(hist['PM2.5'])+ "," + str(hist['PM10']) + \
            str(hist['Bin 1']) + "," + str(hist['Bin 2']) + "," + str(hist['Bin 3']) + "," + str(hist['Bin 4']) + "," + \
            str(hist['Bin 5']) + "," + str(hist['Bin 6']) + "," + str(hist['Bin 7']) + "," + str( hist['Bin 8']) + "," + \
            str(hist['Bin 9']) + "," + str(hist['Bin 10']) + "," + str(hist['Bin 11']) + "," + str(hist['Bin 12']) + "," + \
            str(hist['Bin 13']) + "," + str(hist['Bin 14']) + "," + str(hist['Bin 15'])

            #outstring = GPSstring+","+timestring + "," + EnvString +"," + datastring + "\n"
            outstring=timestring+","+datastring+"\n"
            # clear the screen
#            sys.stderr.write("\x1b[2J\x1b[H")
            print column_headers
            print outstring
            # So we now have our datastrings
            # now to see what the present directory and file should be
            # note that the general scheme is to make a new  directory for each day
            # and inside that directory make a new file for each hours data.
            # First find out what the directory for this day and hour should be
            d=time.localtime()
            date=d.tm_mday
            hour=d.tm_hour
            minute = d.tm_min
            second = d.tm_sec
            
            # So the directory+file name should be of the form ~/data/day/hour.csv
            # Check if datafile exists; if not instantiate it and write the column headers
            dir_name = os.path.join(data_dir,"Day" + str(date))
            if not os.path.exists(dir_name):
                try:
                    os.makedirs(dir_name)
                except OSError:
                    print "couldn't make data directory"
                    print "Turning off the OPC and exiting"
                    print ("OFF: {0}".format(alpha.off()))
                    exit()
            os.chdir(dir_name)

            # Test if it the first opening and if so write the headers
            # Also if it is the first opening email the last one 
            # Priyanka note: this needs improvement to cope with change of the month
            outfile = "OPC_Data_hour_"+str(hour)+".csv"
            try:
                if not os.path.exists(outfile):
                    f = open(outfile,'w')
                    f.write(column_headers)
                    # calculate the last one and email it
                    if not hour == 1:
                        last_file = "OPC_Data_hour_"+str(hour-1)+".csv"
                        last_dir = os.path.join(data_dir,"Day" + str(date))
                    else:
                        last_file = "OPC_Data_hour_"+str(23)+".csv"
                        last_dir = os.path.join(data_dir,"Day" + str(date-1))
                    transfer_file = os.path.join(last_dir,last_file)
                    print "\nFile to be transferred is  "
                    print  transfer_file
                    #send_msg(transfer_file)
                else:
                    f = open(outfile,'a+')
            except OSError:
                print "Couldn't open data file"
                print "Turning off the OPC and exiting"
                print ("OFF: {0}".format(alpha.off()))
                exit()
            f.write(outstring)
            f.close()
            sleep(20)
            i += 1
        except Exception as err:
            print ("{0}".format(err))

except KeyboardInterrupt:
    alpha.off()

# Turn the OPC OFF
f.close()
print ("Turning off the OPC")
print ("OFF: {0}".format(alpha.off()))
