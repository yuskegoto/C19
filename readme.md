# COVID-19 daily infections indicator
C19はその名が示唆する通り、新型コロナウィルスの日々の感染者数を知らせるデバイスです。ニュースのようにむやみに危機感をあおらず、日常に溶け込むインテリアとして、さりげなく注意を促すものを身近に置きたくて製作しました。C19 is, as it's name suggests, an indicator for daily COVID-19 infections in Tokyo. I wanted to have an interior object that subtly suggests awareness, rather than stressing my self too much from daily Corona-related newses.

デバイスは毎時Webにアクセスし、一昨日の東京での感染者数を取得してきています。感染者数に応じてステッパーモーターを駆動し、真鍮の重りの位置によって大まかな感染者数を知らせます。The device accesses to the web every hour, fetches the number of daily infections in Tokyo. The brass weight hanging from the device is controlled by a small stepper motor, roughly indicates the daily infections by it's height.

今回はMicroPythonがどれだけ使えるか評価するため、コーディングはすべてMicroPythonにて行い、新型コロナウィルスの感染者数はhttps://github.com/ryo-ma/covid19-japan-web-apiより取得しています。ただし現在使っているAPIでは更新が1日遅れになるため、別のAPIに今後変更するかもしれません。 To evaluate the MicroPython, this project was completely coded by MicroPython. Daily infections number is fetched from https://github.com/ryo-ma/covid19-japan-web-api. However I might change the API in the future because current API only returns the number two days old.

![Front](https://raw.githubusercontent.com/yuskegoto/C19/master/pics/front.jpeg)

## 構成機器 Components：
- M5StackBasic
- ProtoModule
- A4988 Stepper Driver
- 28BYJ-48 Stepper Motor

## 開発環境 Development Environment：
- MicroPython esp32-idf3-20191220-v1.12.bin
- Pymakr on VSCode

## API end point
https://github.com/ryo-ma/covid19-japan-web-api

## TFT driver
I borrowed this simple ILI9341 driver from here, however this URL is no longer available...
Had to modify display orientation 
https://bitbucket.org/thesheep/micropython-ili9341/src/default/ili9341.py

## To access Wifi
Additionally you need to add wifi.ini file with SSID,PASS formatted text to connect wifi.
