import sys
import os
import mediapipe as mp
from mediapipe import solutions
from mediapipe.framework.formats import landmark_pb2
import numpy as np
import cv2
import math
import time
from EyeAnalyzer import EyeAnalyzer, EyeState
from MouthAnalyzer import MouthAnalyzer, MouseState
from AsymmetryAnalyzer import AsymmetryAnalyzer


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
    left_eye = [33, 246, 161, 160, 159, 158, 157,
                173, 133, 155, 154, 153, 145, 144, 163, 7, 33]
    right_eye = [263, 466, 388, 387, 386, 385, 384, 398, 362, 382, 381, 380, 374, 373, 390, 249]
    mouth = [61, 291, 185, 146, 409, 375]
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
    model_path = 'face_landmarker.task'
    options = FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=model_path),
        running_mode=VisionRunningMode.VIDEO)

    with FaceLandmarker.create_from_options(options) as landmarker:
        # 打开视频文件
        cap = cv2.VideoCapture(video_path)

        # 获取视频的帧率和总帧数
        fps = math.floor(cap.get(cv2.CAP_PROP_FPS))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        h, w = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)), int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))

        eyeAnalyzer = EyeAnalyzer(fps=fps)
        mouthAnalyzer = MouthAnalyzer(fps=fps)
        asymmetryAnalyzer = AsymmetryAnalyzer()

        print(f"Video FPS: {fps}")
        print(f"Total Frames: {total_frames}")
        print(f"Video Resolution: {w}x{h}")

        n = 1
        start_t = time.time()
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

                # time.sleep(0.01)

                # break
                # 按 'q' 键退出循环
                if cv2.waitKey(30) & 0xFF == ord('q'):
                    break

            # 下一帧
            n += 1

        end_t = time.time()
        processed_fps = n / (end_t - start_t)
        print(f"Processed FPS: {processed_fps}")

        # 释放资源
        cap.release()
        cv2.destroyAllWindows()

    return fps, eyeAnalyzer, mouthAnalyzer, asymmetryAnalyzer


# 写入文件
def write2file(file_path, contents):
    file = open(file_path, "w")
    for content in contents:
        v = round(content, 4)
        file.write(str(v) + "\n")
    file.close()

try:
    MODE = sys.argv[1]
except:
    MODE = "batch"

if MODE == "s" or MODE == "single" or MODE == "S" or MODE == "SINGLE":
    # SINGLE
    sample_rate = 1
    # video_path = "../data/processed/T0/9.mp4"
    video_path = "backend/media/1.mp4"
    fps, eyeAnalyzer, mouthAnalyzer, asymmetryAnalyzer = detect(video_path, debug=False)

    eyeAnalyzer.draw(save_path="temp/eye_twitch.png")
    mouthAnalyzer.draw(save_path="temp/mouth_twitch.png")

    eye_twitches = eyeAnalyzer.analyze()
    eye_file = open("temp/eye_twitch.txt", "w")
    for eye_twitch in eye_twitches:
        t = eye_twitch['frame']
        r = round(eye_twitch['range'], 4)
        eye_file.write("At " + str(t) + " frame: " + eye_twitch['eye'] + " eyelid twitch, range " + str(r) + "\n")
    eye_file.close()

    mouth_twitches = mouthAnalyzer.analyze()
    mouth_file = open("temp/mouth_twitch.txt", "w")
    for mouth_twitch in mouth_twitches:
        t = mouth_twitch['frame']
        r = round(mouth_twitch['range'], 4)
        mouth_file.write("At " + str(t) + " frame: mouth twitch, range " + str(r) + "\n")
    mouth_file.close()
elif MODE == "batch":
    # BATCH
    sample_rate = 1
    count = []
    video_folder = "../data/processed/T0/"
    output_folder = "output/"
    videos = os.listdir(video_folder)
    for video in videos:
        video_path = video_folder + video
        video_name = video.split(".")[0]

        print(f"Processing video: {video_path}")
        try:
            fps, eyeAnalyzer, mouthAnalyzer, asymmetryAnalyzer = detect(video_path)

            save_path = output_folder + video_name + "/"
            try:
                os.mkdir(output_folder + video_name)
            except:
                pass

            eyeAnalyzer.draw(save_path=save_path + "eye_twitch.png")
            mouthAnalyzer.draw(save_path=save_path + "mouth_twitch.png")

            avg_eye_twitch_range = 0
            max_eye_twitch_range = 0

            eye_twitches = eyeAnalyzer.analyze()
            eye_file = open(save_path + "eye_twitch.txt", "w")
            for eye_twitch in eye_twitches:
                t = round(eye_twitch['frame'] / fps, 2)
                r = round(eye_twitch['range'], 4)
                avg_eye_twitch_range += r
                max_eye_twitch_range = max(max_eye_twitch_range, r)
                eye_file.write("At " + str(t) + "s: " + eye_twitch['eye'] + " eye twitch, range " + str(r) + "\n")
            eye_file.close()

            if len(eye_twitches) > 0:
                avg_eye_twitch_range /= len(eye_twitches)
            avg_eye_twitch_range = round(avg_eye_twitch_range, 4)

            avg_mouth_twitch_range = 0
            max_mouth_twitch_range = 0

            mouth_twitches = mouthAnalyzer.analyze()
            mouth_file = open(save_path + "mouth_twitch.txt", "w")
            for mouth_twitch in mouth_twitches:
                t = round(mouth_twitch['frame'] / fps, 2)
                r = round(mouth_twitch['range'], 4)
                avg_mouth_twitch_range += r
                max_mouth_twitch_range = max(max_mouth_twitch_range, r)
                mouth_file.write("At " + str(t) + "s: mouth twitch, range " + str(r) + "\n")
            mouth_file.close()

            if len(mouth_twitches) > 0:
                avg_mouth_twitch_range /= len(mouth_twitches)
            avg_mouth_twitch_range = round(avg_mouth_twitch_range, 4)

            asymetry_score = asymmetryAnalyzer.analyze()
            asymetry_score = round(asymetry_score, 4)
            asymetry_file = open(save_path + "asymetry_score.txt", "w")
            asymetry_file.write(f"Asymetry Score: {asymetry_score}")
            asymetry_file.close()

            count.append({
                "video": video,
                "eye_twitches": len(eye_twitches),
                "mouth_twitches": len(mouth_twitches),
                "avg_eye_twitch_range": avg_eye_twitch_range,
                "max_eye_twitch_range": max_eye_twitch_range,
                "avg_mouth_twitch_range": avg_mouth_twitch_range,
                "max_mouth_twitch_range": max_mouth_twitch_range,
                "asymetry_score": asymetry_score
            })

            # l_eye_samples, r_eye_samples = eyeAnalyzer.sampling(sample_rate=sample_rate)
            # mouth_samples = mouthAnalyzer.sampling(sample_rate=sample_rate)
            # write2file(save_path + "l_eye_samples.txt", l_eye_samples)
            # write2file(save_path + "r_eye_samples.txt", r_eye_samples)
            # write2file(save_path + "mouth_samples.txt", mouth_samples)

            print(f"Video {video_path} processed successfully.")
        except Exception as e:
            print(f"Error processing video {video_path}: {e}")

    count_file = open(output_folder + "count.txt", "w")
    for c in count:
        count_file.write(
            f"{c['video']} {c['eye_twitches']} {c['mouth_twitches']} {c['avg_eye_twitch_range']} {c['max_eye_twitch_range']} {c['avg_mouth_twitch_range']} {c['max_mouth_twitch_range']} {c['asymetry_score']}\n")
    count_file.close()
else:
    print("Invalid mode.")
