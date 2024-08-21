import os
import mediapipe as mp
from mediapipe import solutions
from mediapipe.framework.formats import landmark_pb2
import numpy as np
import cv2
import math
import time
from detect.EyeAnalyzer import EyeAnalyzer, EyeState
from detect.MouthAnalyzer import MouthAnalyzer, MouseState
from detect.AsymmetryAnalyzer import AsymmetryAnalyzer


# Mediapipe的画图函数
def draw_landmarks_on_image(rgb_image, face_landmarks):
    mp_draw = mp.solutions.drawing_utils
    mp_draw_styles = mp.solutions.drawing_styles
    annotated_image = np.copy(rgb_image)
    # Draw the face landmarks.
    face_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
    face_landmarks_proto.landmark.extend([
        landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) for landmark in face_landmarks
    ])
    # Style and Points
    solutions.drawing_utils.draw_landmarks(
        image=annotated_image,
        landmark_list=face_landmarks_proto,
        landmark_drawing_spec=mp_draw.DrawingSpec(color=(0, 0, 255), thickness=1, circle_radius=0))

    return annotated_image


def process_face_landmarks(face_landmarks):
    left_eye = [33, 246, 161, 160, 159, 158, 157, 173, 133, 155, 154, 153, 145, 144, 163, 7, 33]
    right_eye = [263, 466, 388, 387, 386, 385, 384, 398, 362, 382, 381, 380, 374, 373, 390, 249]
    mouth = [61, 291]
    eye_center = [468, 473]
    mid = [9, 8, 168, 6, 197, 195, 5, 4, 1, 19, 2, 164, 0, 11, 12, 13, 14, 15, 16, 17, 18, 200]
    processed_face_landmarks = []
    for idx in left_eye:
        processed_face_landmarks.append(face_landmarks[idx])
    for idx in right_eye:
        processed_face_landmarks.append(face_landmarks[idx])
    for idx in mouth:
        processed_face_landmarks.append(face_landmarks[idx])
    for idx in eye_center:
        processed_face_landmarks.append(face_landmarks[idx])
    for idx in mid:
        processed_face_landmarks.append(face_landmarks[idx])
    return processed_face_landmarks


def detect(video_path, debug=False):
    BaseOptions = mp.tasks.BaseOptions
    FaceLandmarker = mp.tasks.vision.FaceLandmarker
    FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
    VisionRunningMode = mp.tasks.vision.RunningMode

    # Create a face landmarker instance with the video mode:
    model_path = 'detect/face_landmarker.task'
    options = FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=model_path),
        running_mode=VisionRunningMode.VIDEO)

    with FaceLandmarker.create_from_options(options) as landmarker:
        # 打开视频文件
        cap = cv2.VideoCapture(video_path)

        # 获取视频的帧率和总帧数
        fps = math.floor(cap.get(cv2.CAP_PROP_FPS))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        h, w = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)), int(
            cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        resolution = (w, h)

        eyeAnalyzer = EyeAnalyzer(fps=fps)
        mouthAnalyzer = MouthAnalyzer(fps=fps)
        asymmetryAnalyzer = AsymmetryAnalyzer()

        print(f"Video FPS: {fps}")
        print(f"Total Frames: {total_frames}")
        print(f"Video Resolution: {w}x{h}")

        n = 1
        # 读取并显示每一帧
        while cap.isOpened():
            ret, frame = cap.read()

            # 检查是否成功读取帧
            if not ret:
                break

            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
            face_landmarker_result = landmarker.detect_for_video(
                mp_image, math.floor(n * 1000 / fps))
            face_landmarks = face_landmarker_result.face_landmarks[0]

            processed_face_landmarks = process_face_landmarks(face_landmarks)
            # annotated_image = draw_landmarks_on_image(frame, face_landmarks)
            annotated_image = draw_landmarks_on_image(frame, processed_face_landmarks)

            # 检测眼睛
            eyeState, left_eye_ratio, right_eye_ratio = eyeAnalyzer.record(face_landmarks=face_landmarks, n=n)

            # 检测嘴角
            mouthState, mouth_ratio = mouthAnalyzer.record(face_landmarks=face_landmarks, n=n, eyeState=eyeState)

            # 计算脸部不对称
            score = asymmetryAnalyzer.record(face_landmarks=face_landmarks, eyeState=eyeState)

            # dbug mode, show the video frame by frame
            if debug:
                cv2.putText(annotated_image, f"Frame: {n}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                cv2.putText(annotated_image, f"Left Eye: {left_eye_ratio}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                cv2.putText(annotated_image, f"Right Eye: {right_eye_ratio}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                cv2.putText(annotated_image, f"Score: {score}", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                if eyeState == EyeState.WINK_DETECTED:
                    cv2.putText(annotated_image, "Wink Detected", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                cv2.putText(annotated_image, f"Mouth Ratio: {mouth_ratio}", (10, 180), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                if mouthState == MouseState.SMILE:
                    cv2.putText(annotated_image, "Smile Detected", (10, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

                cv2.imshow('Video Frame', annotated_image)

                # time.sleep(0.1)

                # break
                # 按 'q' 键退出循环
                if cv2.waitKey(30) & 0xFF == ord('q'):
                    break

            # 下一帧
            n += 1

        # 释放资源
        cap.release()
        cv2.destroyAllWindows()

    return fps, resolution, eyeAnalyzer, mouthAnalyzer, asymmetryAnalyzer