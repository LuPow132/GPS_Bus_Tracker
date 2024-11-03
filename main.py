#include <TinyGPS++.h>
#include <HardwareSerial.h>
#include "FS.h"
#include "SD.h"
#include "SPI.h"
#include <WiFi.h> // นำเข้าไลบรารี่ WiFi
#include <ArtronShop_LineNotify.h> // นำเข้าไลบารี่ ArtronShop_LineNotify

const char* ssid = "realme 12 5G"; // ชื่อ WiFi
const char* password = "2550172550"; // รหัสผ่าน WiFi
#define LINE_TOKEN "Q95BudUaJlzNs1eWyicvmTThCATyHiUGI4HMP6bfKzs" // LINE Token

#define RXPin (16)
#define TXPin (17)
#define SD_CS 5            // SD card Chip Select pin
#define BUTTON_PIN 12      // Button pin

#include <LiquidCrystal_I2C.h>

// set the LCD number of columns and rows
int lcdColumns = 16;
int lcdRows = 2;

String dateStr;
String timeStr;

// set LCD address, number of columns and rows
// if you don't know your display address, run an I2C scanner sketch
LiquidCrystal_I2C lcd(0x27, lcdColumns, lcdRows);  

static const uint32_t GPSBaud = 9600;

int waypoint_index = 0;
bool recording = false;    // Start with recording off
TinyGPSPlus gps;
HardwareSerial ss(2);
bool GPS_Signal = false;

double lastLat = 0.0;
double lastLng = 0.0;
int lastButtonState = HIGH;
int currentButtonState;
String currentFilename;

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

String createFilename() {
    // Retrieve date and time from GPS
    String filename = "";
    if (gps.date.isValid() && gps.time.isValid()) {
        // Format: MMDDYYYY_HHMMSS.txt
        filename += String(gps.date.month());
        filename += String(gps.date.day());
        filename += String(gps.date.year());
        filename += "_";

        int hour = gps.time.hour() + 7;  // Convert UTC to UTC+7
        if (hour >= 24) hour -= 24;      // Adjust if beyond 23 hours

        if (hour < 10) filename += "0";
        filename += String(hour);
        if (gps.time.minute() < 10) filename += "0";
        filename += String(gps.time.minute());
        if (gps.time.second() < 10) filename += "0";
        filename += String(gps.time.second());
        filename += ".txt";
    } else {
        filename = "gps_log.txt";  // Default filename if date/time not valid
    }
    return filename;
}

void setup() {
    Serial.begin(115200);
    ss.begin(GPSBaud, SERIAL_8N1, RXPin, TXPin, false);
    Serial.println(TinyGPSPlus::libraryVersion());

        // initialize LCD
    lcd.init();
    // turn on LCD backlight                      
    lcd.backlight();

    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("GPS BUS TRACKER");
    lcd.setCursor(0, 1);
    lcd.print("SETUP...");

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
    
    Serial.println();
    Serial.println("******************************************************");
    Serial.print("Connecting to ");
    Serial.println(ssid);

    WiFi.begin(ssid, password); // เริ่มต้นเชื่อมต่อ WiFi

    while (WiFi.status() != WL_CONNECTED) { // วนลูปหากยังเชื่อมต่อ WiFi ไม่สำเร็จ
      delay(500);
      Serial.print(".");
    }

    Serial.println("");
    Serial.println("WiFi connected");
    Serial.println("IP address: ");
    Serial.println(WiFi.localIP());

    LINE.begin(LINE_TOKEN); // เริ่มต้นใช้ LINE Notify

    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Wait For GPS");
    lcd.setCursor(0,1);
    lcd.print("GPS SAT COUNT:");

    while(!GPS_Signal){
      if (ss.available() > 0){
        if (gps.encode(ss.read())) {
          if(gps.satellites.value() > 5){
            GPS_Signal = true;
          }else{
            lcd.setCursor(14,1);
            lcd.print(gps.satellites.value());
            Serial.println(gps.satellites.value());
          }
        }
      }
    }
    // Initialize button
    pinMode(BUTTON_PIN, INPUT_PULLUP);
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Not Record");
    lcd.setCursor(0, 0);
    lcd.print("Press Button to");
    lcd.setCursor(0,1);
    lcd.print("start Record");
    delay(1000);
}

void loop() {
    // Check button press to toggle recording
    int buttonState = digitalRead(BUTTON_PIN);
    if (buttonState == LOW && lastButtonState == HIGH) {
        recording = !recording;
        delay(50); // Debounce delay
        while (digitalRead(BUTTON_PIN) == LOW) {
            delay(10);  // Wait until button is released
        }

        if (recording) {
            Serial.println("Recording started");

            // Generate a new filename based on current date and time
            currentFilename = "/" + createFilename();
            Serial.print("Logging to file: ");
            Serial.println(currentFilename);

            // Write headers to the new file
            appendFile(SD, currentFilename.c_str(), "waypoint,lat,lng,time\n");
        } else {
            lcd.setCursor(0, 0);
            lcd.print("Not Record");
            lcd.setCursor(0, 0);
            lcd.print("Press Button to");
            lcd.setCursor(0,1);
            lcd.print("start Record");
        }
    }
    lastButtonState = buttonState;

    // If not recording, skip GPS data processing
    if (!recording) return;

    // Process GPS data
    while (ss.available() > 0) {
        if (gps.encode(ss.read())) {
            if (gps.location.isUpdated()) {
                double currentLat = gps.location.lat();
                double currentLng = gps.location.lng();

                // Only print if location has changed
                if (currentLat != lastLat || currentLng != lastLng) {
                    waypoint_index += 1;
                    lcd.clear();
                    if(waypoint_index % 10 == 0){
                      String latitude = String(gps.location.lat(), 6);
                      String longitude = String(gps.location.lng(), 6);
                      String googleMapLink = "https://www.google.com/maps/place/" + latitude + "," + longitude;

                      if (LINE.send(googleMapLink)) {  // ถ้าส่งข้อความ "รถโดนขโมย" ไปที่ LINE สำเร็จ
                        Serial.println("Send notify successful"); // ส่งข้อความ "Send notify successful" ไปที่ Serial Monitor
                      } else { // ถ้าส่งไม่สำเร็จ
                        Serial.printf("Send notify fail. check your token (code: %d)\n", LINE.status_code); // ส่งข้อความ "Send notify fail" ไปที่ Serial Monitor
                      }
                    }
                    if(waypoint_index % 10 <= 5){
                      if (gps.date.isValid()) {
                        dateStr = String(gps.date.month()) + "/" + 
                                  String(gps.date.day()) + "/" + 
                                  String(gps.date.year());
                      } else {
                        dateStr = "INVALID";
                      }

                      if (gps.time.isValid()) {
                        int hour = gps.time.hour();
                        int minute = gps.time.minute();
                        int second = gps.time.second();
                        int centisecond = gps.time.centisecond();

                        // Format time with leading zeroes
                        timeStr = (hour < 10 ? "0" : "") + String(hour) + ":" +
                                  (minute < 10 ? "0" : "") + String(minute) + ":" +
                                  (second < 10 ? "0" : "") + String(second) + "." +
                                  (centisecond < 10 ? "0" : "") + String(centisecond);
                      } else {
                        timeStr = "INVALID";
                      }
                      lcd.setCursor(0,0);
                      lcd.print(dateStr);
                      lcd.setCursor(0,1);
                      lcd.print(timeStr);
                    }else{
                      lcd.setCursor(0,0);
                      lcd.print(gps.location.lat(), 5);
                      lcd.setCursor(0,1);
                      lcd.print(gps.location.lng(), 5);
                    }

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

                    // Write to the dynamically created file on SD card
                    appendFile(SD, currentFilename.c_str(), dataString.c_str());

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
