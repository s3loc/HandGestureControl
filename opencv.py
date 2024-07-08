import cv2
import numpy as np
import wmi
import pyautogui


# Ekran parlaklığını ayarlamak için WMI
def set_brightness(level):
    c = wmi.WMI(namespace='wmi')
    methods = c.WmiMonitorBrightnessMethods()[0]
    methods.WmiSetBrightness(level, 0)


# Mevcut parlaklık seviyesini almak için WMI
def get_brightness():
    c = wmi.WMI(namespace='wmi')
    brightness = c.WmiMonitorBrightness()[0]
    return brightness.CurrentBrightness


# Parlaklık seviyesini kademeli olarak değiştir
def change_brightness(change):
    global current_brightness
    new_brightness = max(0, min(100, current_brightness + change))
    set_brightness(new_brightness)
    current_brightness = new_brightness


# Ses seviyesini ayarlamak için pyautogui
def change_volume(change):
    if change > 0:
        pyautogui.press('volumeup', presses=abs(change))
    elif change < 0:
        pyautogui.press('volumedown', presses=abs(change))


# VideoCapture nesnesini başlat
vid = cv2.VideoCapture(0)

# Önceki koordinatlar
prev_y = None
prev_x = None
initial_y = None
initial_x = None

# Başlangıç parlaklık seviyesi
current_brightness = get_brightness()

while True:
    ret, frame = vid.read()

    if not ret:
        break

    # Görüntüyü gri tona çevir
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (35, 35), 0)

    # İkili görüntü oluşturmak için bir eşik değeri kullan
    _, thresh = cv2.threshold(blur, 60, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Konturları bul
    contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        max_contour = max(contours, key=cv2.contourArea)

        # Konveks gövde bul ve çiz
        hull = cv2.convexHull(max_contour, returnPoints=False)
        defects = cv2.convexityDefects(max_contour, hull)

        if defects is not None:
            far_points = []
            start_points = []

            for i in range(defects.shape[0]):
                s, e, f, d = defects[i, 0]
                start = tuple(max_contour[s][0])
                end = tuple(max_contour[e][0])
                far = tuple(max_contour[f][0])

                start_points.append(start)
                far_points.append(far)

                # Parmak uçlarına kırmızı noktalar ekle
                cv2.circle(frame, start, 5, [0, 0, 255], -1)
                cv2.circle(frame, end, 5, [0, 0, 255], -1)
                cv2.circle(frame, far, 5, [0, 255, 255], -1)

                cv2.line(frame, start, end, [0, 255, 0], 2)
                cv2.line(frame, start, far, [0, 255, 0], 2)
                cv2.line(frame, end, far, [0, 255, 0], 2)

            if len(start_points) >= 2:
                start_points = sorted(start_points, key=lambda x: x[1])
                start_points_x = sorted(start_points, key=lambda x: x[0])
                if initial_y is None:
                    initial_y = start_points[0][1]
                if initial_x is None:
                    initial_x = start_points_x[0][0]

                if prev_y is not None and prev_x is not None:
                    delta_y = prev_y - start_points[0][1]
                    delta_x = prev_x - start_points_x[0][0]
                    if delta_y > 20:  # El yukarı hareket ediyor
                        change_brightness(5)  # Parlaklığı %5 artır
                    elif delta_y < -20:  # El aşağı hareket ediyor
                        change_brightness(-5)  # Parlaklığı %5 azalt
                    if delta_x > 20:  # El sola hareket ediyor
                        change_volume(-2)  # Sesi azalt
                    elif delta_x < -20:  # El sağa hareket ediyor
                        change_volume(2)  # Sesi artır

                prev_y = start_points[0][1]
                prev_x = start_points_x[0][0]

    # O anki parlaklık seviyesini ekranda göster
    cv2.putText(frame, f'Brightness: {current_brightness}%', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    # Sonucu ekranda göster
    cv2.imshow('USER', frame)

    # 'q' tuşuna basıldığında döngüyü kır
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# VideoCapture nesnesini serbest bırak
vid.release()

# Tüm OpenCV pencerelerini kapat
cv2.destroyAllWindows()
