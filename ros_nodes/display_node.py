#!/usr/bin/env python3
import rospy
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
import cv2
import json
import threading
from flask import Flask, Response, render_template_string, jsonify

bridge = CvBridge()
latest_frame = None
latest_result = None
captured_frame = None
capture_pub = None
# 카메라 영상, 검출 결과 저장할 변수 초기화

app = Flask(__name__)

led_colors = {
    "gold_screw":   (0, 255, 0),    # 초록
    "silver_screw": (0, 0, 255),    # 빨강
    "gold_nail":    (0, 255, 255),  # 노랑
}
# 나사 종류별 색깔 딕셔너리

def image_callback(msg):
    global latest_frame
    latest_frame = bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
# 카메라 토픽에서 이미지 받을 때마다 ROS 메세지 OpenCV 이미지로 변환

def result_callback(msg):
    global latest_result, captured_frame
    latest_result = json.loads(msg.data)
    # 검출 결과 오면 현재 프레임에 박스 그려서 저장
    if latest_frame is not None:
        frame = latest_frame.copy()
        counts = latest_result["counts"].split(',')
        gold_screw = int(counts[0])
        silver_screw = int(counts[1])
        gold_nail = int(counts[2])
        total = gold_screw + silver_screw + gold_nail

        current_detections = {
            "gold_screw": gold_screw,
            "silver_screw": silver_screw,
            "gold_nail": gold_nail
        }

        for box in latest_result["boxes"]:
            x1, y1, x2, y2 = box["x1"], box["y1"], box["x2"], box["y2"]
            class_name = box["class_name"]
            confidence = box["confidence"]
            color = led_colors[class_name]
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            text = f"{class_name} {confidence*100:.0f}%"
            cv2.putText(frame, text, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        cv2.putText(frame, f"Total: {total}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        captured_frame = frame
# 검출 결과 토픽 받을 때마다 JSON 문자열을 딕셔너리로 변환

def generate_stream():
    # 실시간 영상 스트리밍
    while True:
        if latest_frame is not None:
            display = cv2.resize(latest_frame, (640, 480))
            ret, buffer = cv2.imencode('.jpg', display)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/video')
def video():
    return Response(generate_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
# 실시간 영상 스트리밍

@app.route('/capture', methods=['POST'])
def capture():
    global capture_pub
    if capture_pub is not None:
        capture_pub.publish("capture")
        # 촬영 요청 토픽 발행
    return jsonify({"status": "ok"})

@app.route('/result_image')
def result_image():
    # 촬영된 결과 이미지 반환
    if captured_frame is not None:
        display = cv2.resize(captured_frame, (640, 480))
        ret, buffer = cv2.imencode('.jpg', display)
        return Response(buffer.tobytes(), mimetype='image/jpeg')
    return '', 204

@app.route('/result_data')
def result_data():
    # 검출 결과 데이터 반환
    if latest_result is not None:
        counts = latest_result["counts"].split(',')
        return jsonify({
            "gold_screw": int(counts[0]),
            "silver_screw": int(counts[1]),
            "gold_nail": int(counts[2]),
            "total": int(counts[0]) + int(counts[1]) + int(counts[2])
        })
    return jsonify({"gold_screw": 0, "silver_screw": 0, "gold_nail": 0, "total": 0})

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>🔩 Screw Detection</title>
    <style>
        body { background: #1a1a1a; color: white; font-family: Arial; 
               display: flex; flex-direction: column; align-items: center; padding: 20px; }
        h1 { color: #f0c040; }
        .container { display: flex; gap: 20px; }
        .box { background: #2a2a2a; border-radius: 10px; padding: 15px; }
        img { border-radius: 8px; width: 400px; }
        button { background: #f0c040; color: black; border: none; 
                 padding: 15px 40px; font-size: 18px; border-radius: 8px; 
                 cursor: pointer; margin-top: 15px; font-weight: bold; }
        button:hover { background: #e0b030; }
        button:disabled { background: #888; cursor: not-allowed; }
        .result { margin-top: 15px; }
        .item { display: flex; align-items: center; gap: 10px; margin: 8px 0; font-size: 16px; }
        .circle { width: 20px; height: 20px; border-radius: 50%; }
        .green  { background: #00ff00; }
        .red    { background: #ff0000; }
        .yellow { background: #ffff00; }
        .gray   { background: #555; }
        .total  { font-size: 20px; font-weight: bold; margin-top: 10px; color: #f0c040; }
    </style>
</head>
<body>
    <h1>🔩 Screw Detection</h1>
    <div class="container">
        <div class="box">
            <p>실시간 영상</p>
            <img src="/video" id="stream">
            <br>
            <button id="btn" onclick="capture()">📸 촬영 및 검출</button>
        </div>
        <div class="box">
            <p>검출 결과</p>
            <img src="" id="result_img" style="display:none">
            <div class="result" id="result_data">
                <div class="item">
                    <div class="circle gray"></div> 대기 중...
                </div>
            </div>
        </div>
    </div>

    <script>
        function capture() {
            const btn = document.getElementById('btn');
            btn.disabled = true;
            btn.innerText = '검출 중...';

            // 촬영 요청 전송
            fetch('/capture', {method: 'POST'})
                .then(() => {
                    // 2초 후 결과 가져오기
                    setTimeout(() => {
                        fetch('/result_data')
                            .then(r => r.json())
                            .then(data => {
                                // 결과 이미지 표시
                                document.getElementById('result_img').src = '/result_image?' + Date.now();
                                document.getElementById('result_img').style.display = 'block';

                                // 결과 데이터 표시
                                let html = '';
                                html += `<div class="item"><div class="circle ${data.gold_screw > 0 ? 'green' : 'gray'}"></div> gold_screw: ${data.gold_screw}개</div>`;
                                html += `<div class="item"><div class="circle ${data.silver_screw > 0 ? 'red' : 'gray'}"></div> silver_screw: ${data.silver_screw}개</div>`;
                                html += `<div class="item"><div class="circle ${data.gold_nail > 0 ? 'yellow' : 'gray'}"></div> gold_nail: ${data.gold_nail}개</div>`;
                                html += `<div class="total">Total: ${data.total}개</div>`;
                                document.getElementById('result_data').innerHTML = html;

                                btn.disabled = false;
                                btn.innerText = '📸 촬영 및 검출';
                            });
                    }, 2000);
                });
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)
# 메인 페이지

def main():
    global capture_pub
    rospy.init_node('display_node')
    rospy.Subscriber('/camera/image', Image, image_callback)
    # /camera/image 토픽 구독
    rospy.Subscriber('/detection/result', String, result_callback)
    # /detection/result 토픽 구독
    capture_pub = rospy.Publisher('/capture/request', String, queue_size=1)
    # 촬영 요청 토픽 발행자
    rospy.loginfo("화면 노드 시작!")

    # Flask 별도 스레드로 실행
    flask_thread = threading.Thread(
        target=lambda: app.run(host='0.0.0.0', port=5000, threaded=True))
    flask_thread.daemon = True
    flask_thread.start()

    rospy.spin()
    # 노드 실행 유지

if __name__ == '__main__':
    main()
