'''
Collect temperature and light intensity data
Facilitate connection between physical sensors and data display
'''
import time
import board
import analogio
import math

# set display to show either ADC output representative integer or the voltage that it represents
INT_MODE = 0
VOLT_MODE = 1

TEMPERATURE_MODE = 2
mode_thermistor = 2

mode_photoresistor = 0


# always 0xff (in hex) according to: https://learn.adafruit.com/
# circuitpython-basics-analog-inputs-and-outputs/analog-to-digital-converter-inputs
ADC_HIGH = 65535

# set up thermistor as analog input over analog pin A0 (on GPIO pin 26)
thermistor_pin = board.A0
thermistor = analogio.AnalogIn(thermistor_pin)

# set up photoresistor as analog input over analog pin A0 (on GPIO pin 26)
photoresistor_pin = board.A1
photoresistor = analogio.AnalogIn(photoresistor_pin)

# show reference voltage (logic high, 3.3V) and the corresponding analog integer value
ADC_REF = thermistor.reference_voltage
print("ADC reference voltage: {}".format(ADC_REF))
print("ADC high voltage integer value: {}".format(ADC_HIGH))

# show reference voltage (logic high, 3.3V) and the corresponding analog integer value
ADC_REF = photoresistor.reference_voltage
print("ADC reference voltage: {}".format(ADC_REF))
print("ADC high voltage integer value: {}".format(ADC_HIGH))


# convert ADC input value back to voltage
def adc_to_voltage(adc_value):
    return  ADC_REF * (float(adc_value)/float(ADC_HIGH))

def adc_to_temperature(adc_value):
    a = math.log(adc_value/10000)
    b = a/3950
    c = b + 1/(25+273.15)
    T = c**(-1)
    return T-273.15

# take readings
while True:
    # read adc value and print
    if mode_thermistor == INT_MODE:
        print('Thermistor value', (thermistor.value,))
    # convert to voltage
    elif mode_thermistor == VOLT_MODE:
        print('Thermistor value', (adc_to_voltage(thermistor.value),))
    else:
        print('Thermistor value', (adc_to_temperature(thermistor.value),))

    # read adc value and print
    if mode_photoresistor == INT_MODE:
        print('Photoresistor value', (photoresistor.value,))
    # convert to voltage
    else:
        print('Photoresistor value', (adc_to_voltage(photoresistor.value),))

    time.sleep(0.5)

