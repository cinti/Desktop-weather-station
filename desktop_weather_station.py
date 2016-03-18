from Adafruit_BME280 import *
from Adafruit_LED_Backpack import BicolorMatrix8x8
import datetime, math, time, RPi.GPIO as io, smbus

grid = BicolorMatrix8x8.BicolorMatrix8x8()
sensor = BME280(mode=BME280_OSAMPLE_8)
io.setmode(io.BCM)

metric_switch=4
io.setup(metric_switch, io.IN, pull_up_down = io.PUD_DOWN) 


##  Plots a spiral on screen when less than eight periods of record are available.

def display_spiral():
    spiral=[0,1,2,3,4,5,6,7,15,23,31,39,47,55,63,62,61,60,59,58,57,49,41,33,25,17,18,19,20,21,29,37,45,44,43,35]
    grid.clear()
    for n in range(len(spiral)-1):
        time.sleep(0.1)
        grid.set_pixel(int(spiral[n]/8), spiral[n]%8, 1)
        grid.write_display()
    time.sleep(0.1)
    grid.set_pixel(int(spiral[len(spiral)-1]/8), spiral[len(spiral)-1]%8, 2)
    grid.write_display()
    time.sleep(.5)
    for n in range(len(spiral)-1):
        time.sleep(0.1)
        grid.set_pixel(int(spiral[len(spiral)-2-n]/8), spiral[len(spiral)-2-n]%8, 0)
        grid.write_display()
    return


##  Plot relative change in barometric pressure over the last eight recording periods.
    
def display_trend(array,orientation,plot_speed):
    minimum_value=min(array)
    maximum_value=max(array)
    pressure_change=maximum_value-minimum_value
    if pressure_change>150: warning_level=2
    elif pressure_change>100: warning_level=3
    else: warning_level=1
    if maximum_value-minimum_value>0.0:
        scale=7.0/(max(array)-minimum_value)
    else:
        minimum_value-=3
        scale=1.0
    for i in range(len(array)):
        col = max(0,min(7,7-int(scale*(array[i]-minimum_value)+0.5)))
        row = i
        if orientation==0:
            first=row
            second=col
        elif orientation==1:
            first=col
            second=7-row
        elif orientation==2:
            first=7-row
            second=7-col
        else:
            first=7-col
            second=row
        if i == len(array)-1:
            for i in range(3):
                grid.set_pixel(first,second,warning_level)
                grid.write_display()
                time.sleep(2*plot_speed)
                grid.set_pixel(first,second,0)
                grid.write_display()
                time.sleep(2*plot_speed)      
            grid.set_pixel(first,second,warning_level)
            grid.write_display()
        else:
            grid.set_pixel(first,second,1)
            grid.write_display()
        time.sleep(plot_speed)
    return

 
##  Displays passed character string on Adafruit 8x8 bicolor LED (with backpack).
##  Color is an ineger (1=green, 2=red, 3=orange).  Array symbol holds fonts for all
##  Alphanumeric ASCII characters and some symbols.    

def scroll_display(input_string,color,orientation,stream_delay):
    ring_pointer=0
    insert_point=7
    ring_pointer=insert_point
    string_pointer=-1

    display_ring=[[0 for row in range(8)] for col in range(16)]
    symbols=[[6,21,30,34,35,36,37,38,39,46,53],[6,20,27,34,35,36,37,38,39,43,52],[6,12,19,20,21,26,28,30,36,44,52,60],[6,12,20,28,36,42,44,46,51,52,53,60],
            [8,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,64],[6],[6],[6],[6],[6],[6],
            [6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6,],[2,2,10,18,26,34,50],[6],[6],[6,4,10,11,12,13,14,18,26,27,28,29,30,38,42,43,44,45,46,52],[6,2,3,10,11,14,21,28,35,42,45,46,53,54],
            [6],[6],[3,3,10,18,26,34,42,51],[3,2,11,19,27,35,43,50],[6],[6,12,20,26,27,28,29,30,36,44],[4,52,59],[5,27,28,29],[4,51],[7,15,22,29,36,43,50],[6,3,4,5,10,14,18,22,26,30,34,38,42,46,51,52,53],
            [4,4,11,12,18,20,28,36,44,52],[6,3,4,5,10,14,18,22,29,36,43,50,51,52,53,54],[6,3,4,5,10,14,22,28,29,38,42,46,51,52,53],[6,5,12,13,19,21,26,29,34,35,36,37,38,45,53],[6,2,3,4,5,6,10,18,19,20,21,30,38,42,46,51,52,53],
            [6,3,4,5,10,14,18,26,27,28,29,34,38,42,46,51,52,53],[6,2,3,4,5,6,14,21,28,36,44,52],[6,3,4,5,10,14,18,22,27,28,29,34,38,42,46,51,52,53],[6,3,4,5,10,14,18,22,27,28,29,30,38,42,46,51,52,53],[4,11,43],[6],
            [6,20,27,34,43,52],[6,19,20,21,35,36,37,],[6,19,28,37,44,51],[6,3,4,10,13,21,28,35,51],[6,3,4,5,10,11,12,14,18,20,21,22,26,28,29,30,35,36,37],[6,3,4,5,10,14,18,22,26,27,28,29,30,34,38,42,46,50,54],
            [6,2,3,4,5,10,14,18,22,26,27,28,29,34,38,42,46,50,51,52,53],[6,3,4,5,10,14,18,26,34,42,46,51,52,53],[6,2,3,4,5,10,14,18,22,26,30,34,38,42,46,50,51,52,53],[6,2,3,4,5,6,10,18,26,27,28,29,34,42,50,51,52,53,54],
            [6,2,3,4,5,6,10,18,26,27,28,29,34,42,50],[6,3,4,5,10,18,26,34,36,37,38,42,46,51,52,53,],[6,2,6,10,14,18,22,26,27,28,29,30,34,38,42,46,50,54],[4,2,3,4,11,19,27,35,43,50,51,52],[6,6,14,22,30,34,38,42,46,51,52,53],
            [6,2,6,10,13,18,20,26,27,34,36,42,45,50,54],[6,2,10,18,26,34,42,50,51,52,53,54],[6,2,6,10,11,13,14,18,20,22,26,30,34,38,42,46,50,54,],[6,2,6,10,14,18,19,22,26,28,30,34,37,38,42,46,50,54],
            [6,3,4,5,10,14,18,22,26,30,34,38,42,46,51,52,53],[6,2,3,4,5,10,14,18,22,26,30,34,35,36,37,42,50],[6,3,4,5,10,14,18,22,26,30,34,36,38,42,45,46,51,52,53,54],[6,2,3,4,5,10,14,18,22,26,30,34,35,36,37,42,46,50,54],
            [6,3,4,5,10,14,18,27,28,29,38,42,46,51,52,53],[6,2,3,4,5,6,12,20,28,36,44,52,],[6,2,6,10,14,18,22,26,30,34,38,42,46,51,52,53],[6,2,6,10,14,18,22,26,30,34,38,43,45,52],
            [6,2,6,10,14,18,20,22,26,28,30,34,36,38,42,44,46,51,53],[6,2,6,10,14,19,21,28,35,37,42,46,50,54],[6,2,6,10,14,18,22,27,29,36,44,52],[6,2,3,4,5,6,14,21,28,35,42,50,51,52,53,54,],[6],[6],[6],[6],[6],[6],
            [5,19,20,29,35,36,37,42,45,51,52,53],[5,2,10,18,26,27,28,34,37,42,45,50,51,52,],[5,19,20,26,29,34,42,51,52,53],[5,5,13,19,20,21,26,29,34,37,42,45,51,52,53],[5,19,20,26,29,34,35,36,37,42,51,52,53],
            [4,4,11,18,19,20,27,35,43,51],[5,19,20,26,29,34,37,43,44,45,53,58,59,60],[5,2,10,18,26,27,28,34,37,42,45,50,53],[4,3,18,19,27,35,43,50,51,52],[4,4,19,20,28,36,44,50,52,59],[5,2,10,18,21,26,28,34,35,42,44,50,53],
            [4,2,3,11,19,27,35,43,50,51,52],[6,18,19,20,21,26,28,30,34,36,38,42,44,46,50,52,54],[5,18,19,20,26,29,34,37,42,45,50,53],[5,19,20,26,29,34,37,42,45,51,52],[5,18,19,20,26,29,34,37,42,43,44,50,58],
            [5,19,20,21,26,29,34,37,43,44,45,53,61],[5,18,20,27,29,35,43,51],[5,19,20,21,26,35,36,45,50,51,52],[5,3,11,18,19,20,27,35,43,45,52],[5,18,21,26,29,34,37,42,45,51,52,53],[5,18,21,26,29,34,37,42,44,50,51],
            [6,18,20,22,26,28,30,34,36,38,42,44,46,51,53],[6,18,21,26,29,35,36,42,45,50,53],[5,18,21,26,29,34,37,43,44,45,53,58,59,60],[5,18,19,20,21,29,36,43,50,51,52,53],[6],[6],[6],[6],[6],
            [6,12,13,14,19,26,27,28,29,35,42,43,44,45,51,60,61,62],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],[6],
            [6],[6],[6],[6],[6],[6],[6],[6],[5,3,4,10,13,18,21,27,28]]

    while ring_pointer > -1:
        if ring_pointer == insert_point:
            string_pointer += 1
            if string_pointer < len(input_string):
                character = input_string[string_pointer]
                ring_pointer = insert_point + symbols[ord(character)-1][0]
                for turn_on in symbols[ord(character)-1][1:len(symbols[ord(character)-1])]:
                    display_ring[turn_on%8+insert_point][int(turn_on/8)]=color
                    
        for row in range(15):
            for col in range(8):
                display_ring[row][col]=display_ring[row+1][col]
        for col in range(8):
            display_ring[15][col]=0
        ring_pointer -= 1
        
        for row in range(8):
            for col in range(8):
                if orientation==0:
                    first=row
                    second=col
                elif orientation==1:
                    first=col
                    second=7-row
                elif orientation==2:
                    first=7-row
                    second=7-col
                else:
                    first=7-col
                    second=row
                grid.set_pixel(first,second,display_ring[row][col])
        grid.write_display()
        time.sleep(stream_delay)

# * * * * * MAIN LOOP * * * * *

##  Check that display LED matrix and BME280 are attached via I2C

try:
    smbus.SMBus(1).read_byte_data(119,1)
    try:
        smbus.SMBus(1).read_byte_data(112,1)
        grid.begin()
        go=True
    except IOError,e:
        print "BiColor LED not found at I2C address 119.  Please check connection."
        go=False
except IOError,e:
    print "BME280 not found at I2C address 119.  Please check connection."

if go:

##  Inittializes variables

    LED_orientation=3                                                                                           #I M P O R T A N T: Determines display orientation on LED matrix
    scroll_speed=0.07                                                                                            #I M P O R T A N T: Display scroll speed
    record_time=900                                                                                             #I M P O R T A N T: Time in seconds between recording output (900 is 15 minutes)
    average_temperature=0.0                                                                                     #Holds sums temperatures to calculate average temperature per recording cycle 
    average_pressure=0.0                                                                                        #Holds sums pressures to calculate average pressure per recording cycle
    average_relative_humidity=0.0                                                                               #Holds sums relative_humidity to calculate average relative_humidity per recording cycle
    previous_pressure=sensor.read_pressure()                                                                    #Read pressure from Adafruit BME280 in Pascals
    pressure_array=[previous_pressure,previous_pressure,previous_pressure,                                      #Initialize array to hold pressure over last eight record periods (current pressure used as temporary place holder.
                    previous_pressure,previous_pressure,previous_pressure,
                    previous_pressure,previous_pressure]
    count=0                                                                                                     #Number of temperature and pressures added to average_temperature and average_pressure
    time_in_cycle=time.time()                                                                                   #Time at which current recording cycle was entered
    start_time=datetime.datetime.now()
## CHANGE /home/pi/barometer_output/ TO PATH APPROPRIATE FOR YOUR RASPBERRY PI ! ! !
    output_file='/home/pi/barometer_output/meteorology_output_'+start_time.strftime('%y%m%d%H%M%S')+'.csv'
    start_time=time.time()                                                                                      #Recycled variable to hold time at which the entire program started
    f=open(output_file,'w')
    f.write(output_file+'\n')
    f.close()


##  Colors for Adafruit bicolor LED matrix

    green=1
    orange=3
    red=2

    while go:
        try:
            read_sensors = True
            while read_sensors:
                try:
                    temperature = sensor.read_temperature()                                                     #Read temperature from Adafruit BME280
                    pressure = sensor.read_pressure()                                                           #Read pressure from Adafruit BME280 in Pascals
                    relative_humidity = sensor.read_humidity()                                                  #Read relative humidity from Adafruit BME280 in %
                    read_sensors = False
                except IOError:
                    read_sensors = True
            show_metric = io.input(metric_switch)
            scroll_display(datetime.datetime.now().strftime('%H:%M') + 
                           datetime.datetime.now().strftime(' %m-%d-%y'),1,LED_orientation,scroll_speed)        #Read and display time and date
            if show_metric:
                scroll_display('{0:.1f}'.format(temperature)+chr(176)+'C',orange,LED_orientation,scroll_speed)  #Display temperature (Centigrade)
            else:
                scroll_display('{0:.1f}'.format(1.8*temperature+32)+chr(176)+'F',
                               orange,LED_orientation,scroll_speed)                                             #Display temperature (Farenheit)
            if relative_humidity > 40 and relative_humidity < 60: color=green
            else: color=red
            scroll_display('{0:.0f}'.format(relative_humidity)+'% ',color,LED_orientation,scroll_speed)         #Display relative humidity (%)
            current_time=time.time()
            if current_time-time_in_cycle>=record_time:                                                         #Determine and record average temperature and pressure if record_time has elapsed since last output
                time_in_cycle=current_time
                f=open(output_file,'a')
                f.write(datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S')+','+
                        str(average_temperature/max(1,count))+','+
                        str(average_pressure/max(1,count))+','+
                        str(average_relative_humidity/max(1,count))+'\n')
                f.close()
                previous_pressure=average_pressure/max(1,count)


##  "Push down" the record stack, deleting oldest record and enter latest pressure average to record 

                for i in range(7):
                    pressure_array[i]=pressure_array[i+1]
                pressure_array[7]=previous_pressure


##  Reset variables
                               
                count=0
                average_temperature=0.0
                average_pressure=0.0
                average_relative_humidity=0.0
            else:
                count+=1
                average_temperature+=temperature
                average_pressure+=pressure
                average_relative_humidity+=relative_humidity
            if current_time-start_time > 8*record_time:                                                         #If the pressure record array is fully populated, display trend
                display_trend(pressure_array,LED_orientation,0.1)
            else:
                display_spiral()
            time.sleep(1)
        except KeyboardInterrupt:
            go =False
            grid.clear()
            grid.write_display()
