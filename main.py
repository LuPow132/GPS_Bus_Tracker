#include <TinyGPS++.h>
#include <HardwareSerial.h>

#define RXPin (16)
#define TXPin (17)

#include "FS.h"
#include "SD.h"
#include "SPI.h"

static const uint32_t GPSBaud = 9600;

int waypoint_index = 0;
TinyGPSPlus gps;
HardwareSerial ss(2);

double lastLat = 0.0;
double lastLng = 0.0;

void setup() {
    Serial.begin(115200);
    ss.begin(GPSBaud, SERIAL_8N1, RXPin, TXPin, false);
    Serial.println(TinyGPSPlus::libraryVersion());
    delay(1000);
    Serial.println("waypoint,lat,lng,time");
}

void loop() {
    while (ss.available() > 0) {
        if (gps.encode(ss.read())) {
            if (gps.location.isUpdated()) {
                double currentLat = gps.location.lat();
                double currentLng = gps.location.lng();

                // Only print if location has changed
                if (currentLat != lastLat || currentLng != lastLng) {
                    waypoint_index += 1;
                    Serial.print(waypoint_index);
                    Serial.print(F(","));
                    Serial.print(currentLat, 6);
                    Serial.print(F(","));
                    Serial.print(currentLng, 6);
                    Serial.print(F(","));

                    int hour = gps.time.hour() + 7;  // Convert UTC to UTC+7
                    if (hour >= 24) hour -= 24;      // Adjust if beyond 23 hours

                    if (hour < 10) Serial.print(F("0"));
                    Serial.print(hour);
                    Serial.print(F(":"));
                    if (gps.time.minute() < 10) Serial.print(F("0"));
                    Serial.print(gps.time.minute());
                    Serial.print(F(":"));
                    if (gps.time.second() < 10) Serial.print(F("0"));
                    Serial.print(gps.time.second());
                    Serial.println();

                    // Update last known location
                    lastLat = currentLat;
                    lastLng = currentLng;
                }
            }
        }
    }

    if (millis() > 5000 && gps.charsProcessed() < 10) {
        Serial.println(F("No GPS detected: check wiring."));
        while(true);
    }
}
