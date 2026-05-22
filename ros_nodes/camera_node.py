#!/usr/bin/env python3
import rospy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
bridge = CvBridge()
def main():
    rospy.init_node('camera_node')
    pub = rospy.Publisher('/camera/image', Image, queue_size=1)
    # 최신 프레임 1개만 유지
    rate = rospy.Rate(10)
    # select() timout에러 발생 1초에 프레임 전송 횟수 10회
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    # V4L2 방식 강제 지정 (안정적) 
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    cap.set(cv2.CAP_PROP_FPS, 15)
    # 카메라 반응속도가 느려서 해상도 낮춤
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    # 버퍼 1로 설정(버퍼가 크면 오래된 프레임이 쌓여 지연된 영상이 나옴)
    
    if not cap.isOpened():
        rospy.logerr("카메라를 찾을 수 없습니다!")
        return
    # 카메라 연결 실패시 에러 출력
    
    rospy.loginfo("카메라 노드 시작!")
    
    while not rospy.is_shutdown():
    # ROS 작동중 계속 반복
        ret, frame = cap.read()
        # ret(읽기 성공 여부 True/False), frame(실제 이미지 데이터)
        if not ret:
        # 읽기 실패시
            rospy.logwarn("프레임 읽기 실패, 재연결 시도...")
            cap.release()
            # 기존 연결 끊기
            cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
            # 재 연결
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
            cap.set(cv2.CAP_PROP_FPS, 15)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            continue
            # 프레임 읽기 실패시 카메라 재연결 시도
        msg = bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        # OpenCV 이미지를 ROS 메세지 형식으로 변환
        pub.publish(msg)
        # 변환된 이미지 /camera/image 토픽으로 발행
        rate.sleep()
    
    cap.release()
if __name__ == '__main__':
    main()
