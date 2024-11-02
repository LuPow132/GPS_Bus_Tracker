#include <TinyGPS++.h>
#include <HardwareSerial.h>
#include "FS.h"
#include "SD.h"
#include "SPI.h"

#define RXPin (16)
#define TXPin (17)
#define SD_CS 5  // Set SD card Chip Select pin

static const uint32_t GPSBaud = 9600;

int waypoint_index = 0;
TinyGPSPlus gps;
HardwareSerial ss(2);

double lastLat = 0.0;
double lastLng = 0.0;

void appendFile(fs::FS &fs, const char *path, const char *message) {
    File file = fs.open(path, FILE_APPEND);
    if (!file) {
        Serial.println("Failed to open file for appending");
        return;
    }
    if (file.print(message)) {
        Serial.println("Message appended to SD card");
    } else {
        Serial.println("Append to SD card failed");
    }
    file.close();
}

void setup() {
    Serial.begin(115200);
    ss.begin(GPSBaud, SERIAL_8N1, RXPin, TXPin, false);
    Serial.println(TinyGPSPlus::libraryVersion());

    // Initialize SD card
    if (!SD.begin(SD_CS)) {
        Serial.println("Card Mount Failed");
        return;
    }
    uint8_t cardType = SD.cardType();
    if (cardType == CARD_NONE) {
        Serial.println("No SD card attached");
        return;
    }

    Serial.println("SD Card initialized.");
    delay(1000);
    Serial.println("waypoint,lat,lng,time");

    // Write headers to SD card
    appendFile(SD, "/gps_log.txt", "waypoint,lat,lng,time\n");
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

                    // Prepare data string for both Serial and SD card
                    String dataString = String(waypoint_index) + "," +
                                        String(currentLat, 6) + "," +
                                        String(currentLng, 6) + ",";

                    int hour = gps.time.hour() + 7;  // Convert UTC to UTC+7
                    if (hour >= 24) hour -= 24;      // Adjust if beyond 23 hours

                    // Append formatted time to data string
                    if (hour < 10) dataString += "0";
                    dataString += String(hour) + ":";
                    if (gps.time.minute() < 10) dataString += "0";
                    dataString += String(gps.time.minute()) + ":";
                    if (gps.time.second() < 10) dataString += "0";
                    dataString += String(gps.time.second()) + "\n";

                    // Print to Serial
                    Serial.print(dataString);

                    // Write to SD card
                    appendFile(SD, "/gps_log.txt", dataString.c_str());

                    // Update last known location
                    lastLat = currentLat;
                    lastLng = currentLng;
                }
            }
        }
    }

    if (millis() > 5000 && gps.charsProcessed() < 10) {
        Serial.println(F("No GPS detected: check wiring."));
        while (true);
    }
}
