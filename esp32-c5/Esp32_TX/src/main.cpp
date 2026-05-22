#include <Arduino.h>
#include "WiFi.h"
#include "esp_wifi.h"

// Wi-Fi 고정 채널 (수신기와 반드시 일치해야 함)
#define WIFI_CHANNEL 1

// IEEE 802.11 표준 규격에 맞춘 가짜 'Null Function' 패킷 프레임 양식
// 데이터 내용은 비어있고, 오직 안테나가 전파를 물리적으로 쏘게 만들기 위한 껍데기입니다.
uint8_t csi_ping_packet[26] = {
    0x48, 0x00,                         // Type/Subtype: Null Function (데이터 없음)
    0x00, 0x00,                         // Duration
    0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, // Receiver Address (브로드캐스트: 주변 모든 기기가 들을 수 있게)
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // Transmitter Address (송신기 MAC 주소 - 일단 더미값)
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // BSSID (더미값)
    0x00, 0x00                          // Sequence Control
};

void setup() {
    Serial.begin(115200);
    delay(500);
    Serial.println("\n--- CSI 송신기 초기화 시작 ---");

    // 1. 와이파이를 일반 스마트폰 모드(Station)로 설정
    WiFi.mode(WIFI_STA);

    // 2. 와이파이 제어권을 가져오기 위해 무차별 수신(Promiscuous) 모드 활성화
    esp_wifi_set_promiscuous(true);

    // 3. 수신기와 약속된 주파수 채널로 고정
    esp_wifi_set_channel(WIFI_CHANNEL, WIFI_SECOND_CHAN_NONE);

    // 4. 송신기 본인의 진짜 MAC 주소를 추출하여 패킷에 심어줍니다 (수신기가 필터링할 수 있도록)
    uint8_t mac[6];
    esp_wifi_get_mac(WIFI_IF_STA, mac);
    memcpy(&csi_ping_packet[10], mac, 6); // 송신기 주소 영역에 복사
    memcpy(&csi_ping_packet[16], mac, 6); // BSSID 영역에 복사

    Serial.print("송신기 고유 MAC 주소: ");
    for (int i = 0; i < 6; i++) {
        Serial.printf("%02X", mac[i]);
        if (i < 5) Serial.print(":");
    }
    Serial.println("\nCSI 패킷 송신 준비 완료.");
}

void loop() {
    // esp_wifi_80211_tx : 안테나 하드웨어로 원시 패킷 패킷을 직접 강제 방출하는 함수
    // 매개변수: (패킷배열주소, 패킷길이, 비동기여부)
    esp_err_t err = esp_wifi_80211_tx(WIFI_IF_STA, csi_ping_packet, sizeof(csi_ping_packet), false);

    if (err == ESP_OK) {
        Serial.println("[송신] CSI 핑 패킷 방출 성공 (0.1초 주기)");
    } else {
        Serial.printf("[에러] 패킷 송신 실패코드: %d\n", err);
    }

    // 0.1초 대기 (초당 10번 방출)
    delay(100); 
}