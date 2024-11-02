#include <TinyGPS++.h>
#include <HardwareSerial.h>

#define RXPin (16)
#define TXPin (17)

static const uint32_t GPSBaud = 9600;

// The TinyGPS++ object
TinyGPSPlus gps;

// The serial connection to the GPS device
HardwareSerial ss(2);

void setup()
{
Serial.begin(115200);
ss.begin(GPSBaud, SERIAL_8N1, RXPin, TXPin, false);
Serial.println(TinyGPSPlus::libraryVersion());
}

void loop()
{

while (ss.available() > 0)
if (gps.encode(ss.read()))
displayInfo();

if (millis() > 5000 && gps.charsProcessed() < 10)
{
Serial.println(F("No GPS detected: check wiring."));
while(true);
}
}

void displayInfo()
{
Serial.print(F("Location: "));
if (gps.location.isUpdated())
{
Serial.print(gps.location.lat(), 6);
Serial.print(F(","));
Serial.print(gps.location.lng(), 6);
}
else
{
Serial.print(F("INVALID"));
}

Serial.println();
}
