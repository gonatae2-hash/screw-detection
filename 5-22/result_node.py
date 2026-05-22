#!/usr/bin/env python3
import rospy
from std_msgs.msg import String
import serial
import time
import json
# arduino 시리얼 통신 연결
arduino = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
# VMware에서 아두이노 USB연결 포트
time.sleep(2)
# 아두이노 연결 안정화 대기 (2초)
def result_callback(msg):
    data = json.loads(msg.data)
    # /detection/result 토픽에서 데이터 받을 때마다 호출
    counts = data["counts"].split(',')
    # detection_node.py로 부터 counts ="2,1,0" 문자열로 받음
    # result_node에서 받아서 ["2","1","0"] 으로 분리 (문자열을 쪼개서 리스트로 변환)
    gold_screw = int(counts[0])     # 2
    silver_screw = int(counts[1])   # 1
    gold_nail = int(counts[2])      # 0
    total = gold_screw + silver_screw + gold_nail
    # 2 + 1 + 0 =3    
    # /detection/result 토픽에서 개수 받아서
    led1 = '1' if silver_screw > 0 else '0' # 0보다 크면 '1'(LED켜기)/ 이하일떄 (LED 끄기)
    led2 = '1' if gold_screw > 0 else '0'
    led3 = '1' if gold_nail > 0 else '0'
    cmd = f"{led1} {led2} {led3}\n" # "0 1 0\n"식의 문자열 만들어서 아두이노에 전송
    arduino.write(cmd.encode())     # .encode()문자열을 아두이노가 읽을 수 있는 바이트 형식으로 변환
    rospy.loginfo(f"gold_screw: {gold_screw} | silver_screw: {silver_screw} | gold_nail: {gold_nail} | Total: {total}")
    # 터미널에 나사 종류별 개수, 총 개수 출력
def main():
    rospy.init_node('result_node')
    # result_node로 ROS 노드 등록
    rospy.Subscriber('/detection/result', String, result_callback)
    # /detection/result 토픽 구독
    rospy.loginfo("결과 노드 시작!")
    rospy.spin()
    arduino.close()
    # 노드 종료 시 아두이노 종료
if __name__ == '__main__':
    main()
