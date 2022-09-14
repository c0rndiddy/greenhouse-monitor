'''
Publish sensor light intensity and temperature data to Adafruit IO Dashboard using MQTT.
'''
# SPDX-FileCopyrightText: Brent Rubell for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
from microcontroller import cpu
import board
import busio
from digitalio import DigitalInOut
from adafruit_esp32spi import adafruit_esp32spi
from adafruit_esp32spi import adafruit_esp32spi_wifimanager
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_io.adafruit_io import IO_MQTT

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

# set up thermistor as analog input over analog pin A0
thermistor_pin = board.A0
thermistor = analogio.AnalogIn(thermistor_pin)

# set up photoresistor as analog input over analog pin A1
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
    c = b + 1/(50+273.15)
    T = c**(-1)
    return T-273.15


# Define callback functions which will be called when certain events happen.
# pylint: disable=unused-argument
def connected(client):
    # Connected function will be called when the client is connected to Adafruit IO.
    print("Connected to Adafruit IO! ")

def subscribe(client, userdata, topic, granted_qos):
    # This method is called when the client subscribes to a new feed.
    print("Subscribed to {0} with QOS level {1}".format(topic, granted_qos))

# pylint: disable=unused-argument
def disconnected(client):
    # Disconnected function will be called when the client disconnects.
    print("Disconnected from Adafruit IO!")


# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

# Set up SPI pins
esp32_cs = DigitalInOut(board.CS1)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)

# Connect RP2040 to the WiFi module's ESP32 chip via SPI, then connect to WiFi
spi = busio.SPI(board.SCK1, board.MOSI1, board.MISO1)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)
wifi = adafruit_esp32spi_wifimanager.ESPSPI_WiFiManager(esp, secrets)

# Connect to WiFi
print("Connecting to WiFi...")
wifi.connect()
print("Connected!")

# Initialize MQTT interface with the esp interface
MQTT.set_socket(socket, esp)

# Initialize a new MQTT Client object
mqtt_client = MQTT.MQTT(
    broker="io.adafruit.com",
    port=secrets["port"],
    username=secrets["aio_username"],
    password=secrets["aio_key"],
)

# Initialize an Adafruit IO MQTT Client
io = IO_MQTT(mqtt_client)

# Connect the callback methods defined above to Adafruit IO
io.on_connect = connected
io.on_disconnect = disconnected
io.on_subscribe = subscribe

'''
# Set up a callback for the feed
io.add_feed_callback("thermistor", on_thermistor_msg)
io.add_feed_callback("photoresistor", on_photoresistor_msg)
'''

# Connect to Adafruit IO
print("Connecting to Adafruit IO...")
io.connect()



prv_refresh_time = 0.0
while True:
    # Poll for incoming messages
    try:
        io.loop()
    except (ValueError, RuntimeError) as e:
        print("Failed to get data, retrying\n", e)
        wifi.reset()
        io.reconnect()
        continue

    # Send a new thermistor and photoresistor reading to IO every 30 seconds
    if (time.monotonic() - prv_refresh_time) > 5:
        # take the thermistor value
        thermistor_new = adc_to_temperature(thermistor.value)
        #thermistor_new = str(thermistor_new)[:5]
        print("Thermistor value is %s degrees C" % thermistor_new)

        # publish it to io
        print("Publishing %s to temperature feed..." % thermistor_new)
        io.publish("thermistor", thermistor_new)
        print("Published!")

        # take the photoresistor value
        photoresistor_new = photoresistor.value
        #photoresistor_new = str(photoresistor_new)[:5]
        print("Photoresistor value is %s lux" % photoresistor_new)
        # publish it to io
        print("Publishing %s to light intensity feed..." % photoresistor_new)
        io.publish("photoresistor", photoresistor_new)
        print("Published!")

        prv_refresh_time = time.monotonic()
