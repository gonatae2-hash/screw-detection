#!/usr/bin/env python3
import rospy
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
import cv2
import numpy as np
from ultralytics import YOLO
import tflite_runtime.interpreter as tflite
import json
bridge = CvBridge()
yolo_model = YOLO("/home/kwantae/catkin_ws/src/screw_detection/scripts/best.pt")
interpreter = tflite.Interpreter(model_path="/home/kwantae/catkin_ws/src/screw_detection/scripts/model_unquant.tflite")
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
labels = ["gold_screw", "silver_screw", "gold_nail"]
pub = None
frame_count = 0
capture_requested = False  # 촬영 요청 플래그
# 전역변수 선언
def capture_callback(msg):
    global capture_requested
    capture_requested = True
# /capture/request 토픽 받으면 촬영 요청 플래그 True로 설정
def image_callback(msg):
    global frame_count, capture_requested
    frame_count += 1
    if not capture_requested:
        return
    # 촬영 요청 없으면 건너뜀
    if frame_count % 3 != 0:
        return
    # 3프레임마다 1번 처리
    capture_requested = False
    # 요청 처리 후 초기화
    frame = bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
    results = yolo_model.predict(frame, conf=0.5, imgsz=320, verbose=False)
    detections = {"gold_screw": 0, "silver_screw": 0, "gold_nail": 0}
    boxes_info = []
    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            roi = frame[y1:y2, x1:x2]
            if roi.size == 0:
                continue
            roi_resized = cv2.resize(roi, (224, 224))
            roi_rgb = cv2.cvtColor(roi_resized, cv2.COLOR_BGR2RGB)
            roi_array = np.asarray(roi_rgb, dtype=np.float32)
            roi_array = (roi_array / 127.5) - 1
            roi_array = np.expand_dims(roi_array, axis=0)
            interpreter.set_tensor(input_details[0]['index'], roi_array)
            interpreter.invoke()
            prediction = interpreter.get_tensor(output_details[0]['index'])
            class_idx = np.argmax(prediction)
            class_name = labels[class_idx]
            confidence = float(prediction[0][class_idx])
            detections[class_name] += 1
            boxes_info.append({
                "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                "class_name": class_name,
                "confidence": confidence
            })
    result = {
        "counts": f"{detections['gold_screw']},{detections['silver_screw']},{detections['gold_nail']}",
        "boxes": boxes_info
    }
    pub.publish(json.dumps(result))
def main():
    global pub
    rospy.init_node('detection_node')
    pub = rospy.Publisher('/detection/result', String, queue_size=1)
    rospy.Subscriber('/camera/image', Image, image_callback)
    rospy.Subscriber('/capture/request', String, capture_callback)
    # 촬영 요청 토픽 구독
    rospy.loginfo("검출 노드 시작!")
    rospy.spin()
if __name__ == '__main__':
    main()
