# 나사 분류 및 검출 시스템

## 프로젝트 개요
카메라로 나사를 촬영하여 종류를 분류하고 Arduino LED로 결과를 출력하는 시스템

## 시스템 구조
카메라 → YOLO(나사 위치 검출) → Teachable Machine(종류 분류) → 결과 출력
→ Arduino LED 제어
→ Flask 웹앱 표시

## 사용 기술
- **AI**: YOLOv8, Teachable Machine (MobileNet)
- **프레임워크**: ROS Noetic, Flask
- **라이브러리**: OpenCV, TFLite
- **하드웨어**: Arduino UNO, USB 카메라
- **개발 환경**: Ubuntu 20.04 (VMware), Python 3

## 나사 종류
| 종류 | LED 색상 |
|------|---------|
| gold_screw | 🟢 초록 |
| silver_screw | 🔴 빨강 |
| gold_nail | 🟡 노랑 |

## ROS 노드 구조
camera_node → detection_node → result_node (Arduino LED)
→ display_node (Flask 웹앱)

## 진행 상황
- [x] YOLOv8 나사 위치 검출
- [x] Teachable Machine 종류 분류
- [x] ROS 노드 4개 구성
- [x] Arduino LED 연동
- [x] Flask 웹앱 (실시간 영상 + 촬영 버튼)
- [ ] YOLO 3클래스 재학습 (종류까지 검출)

## 한계 및 개선 방향
- YOLO에서 bbox생성 teachable machine로 넘겨받을때 사진 내 나사 픽셀이 너무작음
  teachable machine 제거하고 YOLO에서 나사검출 및 나사 종류 검출 추가 예정 
