from flask import Flask, render_template, Response, request, jsonify
from ultralytics import YOLO
import cv2
import os
import time

app = Flask(__name__)

model = YOLO("yolov8n.pt")

camera = cv2.VideoCapture(0)

detected_objects = []

def generate_frames():
    global detected_objects
    while True:
        success, frame = camera.read()
        if not success:
            break

        results = model(frame)
        detected_objects = []

        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                label = model.names[cls_id]
                detected_objects.append(label)

        annotated_frame = results[0].plot()

        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video')
def video():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/detect', methods=['POST'])
def detect():
    pattern = request.json.get("pattern")
    if pattern in detected_objects:
        return jsonify({"match": True})
    return jsonify({"match": False})


@app.route('/capture', methods=['POST'])
def capture():
    success, frame = camera.read()
    if success:
        filename = f"static/captured/capture_{int(time.time())}.jpg"
        cv2.imwrite(filename, frame)
        return jsonify({"saved": filename})
    return jsonify({"saved": None})


if __name__ == '__main__':
    app.run(debug=True)