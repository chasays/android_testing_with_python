#!/usr/bin/env python
# coding: utf-8
# author: Xuxiao

from uiautomator import device as d
from uiautomator import Device

# import serial
# import serial.tools.list_ports

# plist = list(serial.tools.list_ports.comports())
# serial = serial.Serial('COM15', 115200, timeout=0.001)
# print plist, serial
d = Device('ffff', adb_server_host='10.81.25.87', adb_server_port=5555)
'''
d.screen.on()

d(text="Clock").click()

d.long_click(x, y)

d.swipe(sx, sy, ex, ey, steps=10)

d.screenshot("home.png")

d.dump("hierarchy.xml")
xml = d.dump()


- text, textContains, textMatches, textStartsWith
- className, classNameMatches
- description, descriptionContains, descriptionMatches, descriptionStartsWith
- checkable, checked, clickable, longClickable
- scrollable, enabled,focusable, focused, selected
- packageName, packageNameMatches
- resourceId, resourceIdMatches
- index, instance
'''
d(text='Clock', className='android.widget.TextView')
d(className="android.widget.ListView").child(text="Bluetooth")
d(text="Google").sibling(className="android.widget.ImageView")
d(text="Wi‑Fi").right(className="android.widget.Switch").click()
d(text="Settings").exists # True if exists, else False
d.exists(text="Settings") # alias of above property.
d(text="Settings").info
d(text="Settings").click()

print 111
