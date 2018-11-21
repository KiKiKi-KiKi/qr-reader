from flask import Flask, Response
from pyzbar import pyzbar
from picamera.array import PiRGBArray
from picamera import PiCamera
from detetime import datetime

import numpy as np
import cv2
import time

# camera object
cam = PiCamera()
cam.resolution = (640, 480)
cam.framerate = 32

rawCapture = PiRGBArray( cam, size=(630, 480) )
time.sleep( 0.5 )

# Flask webサーバーインスタンス
app = Flask( __name__ )

'''
Picameraの映像をMotion JPEGとしてブラウザから確認できるようにするためのエンドポイントを作成
'''
# @ ... デコレータ
@app.route('/stream')
def stream():
  return Response(gen(),
                  minetype = 'multipart/x-mixed-replace; boundary=frame')

def gen():
  while True:
    frame = get_frame()
    # http://ailaby.com/yield/
    yield (b'--frame\r\n'
           b'Content-Type: image\r\n\r\n' + frame + b'\r\n\r\n')

'''
Picameraからフレームを読み込み、QR認識とその位置を描画
'''
def get_frame():
  cam.capture(rawCapture, format="bgr", use_video_port=True)
  frame = rawCapture.array
  process_frame(frame)
  ret, jpeg = cv2.imencode('.jpg', frame)
  rawCapture.truncate(0)

  return jpeg.tobytes()

'''
取得したフレームを使ってQR認識と認識したポジションの描画
'''
def process_frame(frame):
  decoded_objs = decode(frame)
  draw_positions(frame, decoded_objs)

'''
Pyzbarライブラリを使って実際にQRを認識
'''
def decode(frame):
  decoded_objs = pyzbar.decode(frame, scan_locations=True)
  for obj in decoded_objs:
    print(datetime.now().strftime('%H:%M:%S.%f'))
    print('Type: ', obj.type)
    print('Data: ', obj.data)

  return decoded_objs

'''
認識したQRコードの位置をフレームに描画
'''
def draw_positions(frame, decoded_objs):
  for decoded_obj in decoded_objs:
    left, top, width, height = decoded_obj.rect
    frame = cv2.rectangle(frame,
              (left, top),
              (left + width, height + top),
              (0, 255, 0), 2)

# Flaskサーバーを立ち上げる
if __name__ == '__main__':
  app.run(host="0.0.0.0", debug=False, threaded=True)
