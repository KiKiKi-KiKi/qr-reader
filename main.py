from flask import Flask, Response
from pyzbar import pyzbar
from picamera.array import PiRGBArray
from picamera import PiCamera
from datetime import datetime

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
                  mimetype = 'multipart/x-mixed-replace; boundary=frame')

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
    print(type(obj.type), type(obj.data))
    draw_qr_data_by_text( frame, obj )

  qrNum = len(decoded_objs)
  if (qrNum > 0):
    draw_qr_code_num(frame, len(decoded_objs))
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
              (122,197,197), 4)

'''
認識したQRコードのデータを表示
cv2.putText
http://labs.eecs.tottori-u.ac.jp/sd/Member/oyamada/OpenCV/html/py_tutorials/py_gui/py_drawing_functions/py_drawing_functions.html#id8
'''
def draw_qr_data_by_text(frame, obj):
  fontType = cv2.FONT_HERSHEY_SIMPLEX
  qrType = str(obj.type)
  qrData = str(obj.data)
  left, top, width, height = obj.rect
  cv2.putText(frame, '{0}: {1}'.format(qrType, qrData), (left, top + 50), fontType, 2, (0, 255, 0), 3, cv2.LINE_AA)

def draw_qr_code_num(frame, num):
  fontType = cv2.FONT_HERSHEY_SIMPLEX
  text = 'Detected QR cordes: {0}'.format(str(num))
  cv2.putText(frame, text, (int(640/2), 100), fontType, 2, (0, 255, 0), 3, cv2.LINE_AA)

# Flaskサーバーを立ち上げる
if __name__ == '__main__':
  app.run(host="0.0.0.0", debug=False, threaded=True)
