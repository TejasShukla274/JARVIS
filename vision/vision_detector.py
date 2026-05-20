import cv2

from ultralytics import YOLO


# LOAD YOLO MODEL
model = YOLO("yolov8n.pt")


def detect_objects():

    # OPEN CAMERA
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():

        return []

    # CAPTURE SINGLE FRAME
    success, frame = cap.read()

    # RELEASE CAMERA IMMEDIATELY
    cap.release()

    if not success:

        return []

    # RUN YOLO DETECTION
    results = model(frame, verbose=False)

    detected_objects = []

    # GET DETECTED OBJECTS
    for result in results:

        boxes = result.boxes

        for box in boxes:

            class_id = int(box.cls[0])

            object_name = model.names[class_id]

            # AVOID DUPLICATES
            if object_name not in detected_objects:

                detected_objects.append(object_name)

    return detected_objects