## Originally copied from https://files.waveshare.com/upload/d/db/LCD1602_I2C_Module_code.zip

# -*- coding: utf-8 -*-
import time
from machine import Pin,I2C
from ulogging import uLogger

#Device I2C Arress
LCD_ADDRESS   =  (0x7c>>1)

LCD_CLEARDISPLAY = 0x01
LCD_RETURNHOME = 0x02
LCD_ENTRYMODESET = 0x04
LCD_DISPLAYCONTROL = 0x08
LCD_CURSORSHIFT = 0x10
LCD_FUNCTIONSET = 0x20
LCD_SETCGRAMADDR = 0x40
LCD_SETDDRAMADDR = 0x80

#flags for display entry mode
LCD_ENTRYRIGHT = 0x00
LCD_ENTRYLEFT = 0x02
LCD_ENTRYSHIFTINCREMENT = 0x01
LCD_ENTRYSHIFTDECREMENT = 0x00

#flags for display on/off control
LCD_DISPLAYON = 0x04
LCD_DISPLAYOFF = 0x00
LCD_CURSORON = 0x02
LCD_CURSOROFF = 0x00
LCD_BLINKON = 0x01
LCD_BLINKOFF = 0x00

#flags for display/cursor shift
LCD_DISPLAYMOVE = 0x08
LCD_CURSORMOVE = 0x00
LCD_MOVERIGHT = 0x04
LCD_MOVELEFT = 0x00

#flags for function set
LCD_8BITMODE = 0x10
LCD_4BITMODE = 0x00
LCD_2LINE = 0x08
LCD_1LINE = 0x00
LCD_5x8DOTS = 0x00


class LCD1602:
  def __init__(self, log_level: int, i2c_id: int,  i2c_sda: int, i2c_scl: int, col: int, row: int):
    self.log = uLogger("LCD1602", log_level)
    self.log.info("Init LCD1602 display driver")
    self._row = row
    self._col = col

    try:
      self.LCD1602_I2C = I2C(i2c_id, sda = i2c_sda, scl = i2c_scl ,freq = 400000)
      self._showfunction = LCD_4BITMODE | LCD_1LINE | LCD_5x8DOTS
      self.begin(self._row,self._col)
    except BaseException:
      self.log.error("Error connecting to LCD display on I2C bus. Check I2C pins and ID and that correct module (I2C address) is connected.")
      raise
        
  def command(self,cmd):
    self.LCD1602_I2C.writeto_mem(LCD_ADDRESS, 0x80, chr(cmd))

  def write(self,data):
    self.LCD1602_I2C.writeto_mem(LCD_ADDRESS, 0x40, chr(data))

  def setCursor(self,col,row):
    if(row == 0):
      col|=0x80
    else:
      col|=0xc0
    self.LCD1602_I2C.writeto(LCD_ADDRESS, bytearray([0x80,col]))

  def clear(self):
    self.command(LCD_CLEARDISPLAY)
    time.sleep(0.002)
  def printout(self,arg):
    if(isinstance(arg,int)):
      arg=str(arg)

    for x in bytearray(arg,'utf-8'):
      self.write(x)


  def display(self):
    self._showcontrol |= LCD_DISPLAYON 
    self.command(LCD_DISPLAYCONTROL | self._showcontrol)

 
  def begin(self,cols,lines):
    if (lines > 1):
        self._showfunction |= LCD_2LINE 
     
    self._numlines = lines 
    self._currline = 0 

    time.sleep(0.05)

    # Send function set command sequence
    self.command(LCD_FUNCTIONSET | self._showfunction)
    #delayMicroseconds(4500);  # wait more than 4.1ms
    time.sleep(0.005)
    # second try
    self.command(LCD_FUNCTIONSET | self._showfunction)
    #delayMicroseconds(150);
    time.sleep(0.005)
    # third go
    self.command(LCD_FUNCTIONSET | self._showfunction)
    # finally, set # lines, font size, etc.
    self.command(LCD_FUNCTIONSET | self._showfunction)
    # turn the display on with no cursor or blinking default
    self._showcontrol = LCD_DISPLAYON | LCD_CURSOROFF | LCD_BLINKOFF 
    self.display()
    # clear it off
    self.clear()
    # Initialize to default text direction (for romance languages)
    self._showmode = LCD_ENTRYLEFT | LCD_ENTRYSHIFTDECREMENT 
    # set the entry mode
    self.command(LCD_ENTRYMODESET | self._showmode)
    # backlight init