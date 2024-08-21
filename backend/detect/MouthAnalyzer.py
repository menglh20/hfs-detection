import numpy as np
import matplotlib.pyplot as plt
import enum
from detect.EyeAnalyzer import EyeState

LEFT_MOUTH_CORNER = [61, 185, 146]
RIGHT_MOUTH_CORNER = [291, 409, 375]

SMILE_DETECTED_THRESHOLD = 1.05

MOUTH_TWITCH_THRESHOLD = 0.017

class MouseState(enum.Enum):
    NORMAL = 0
    UNNORMAL = 1
    SMILE = 2


class MouthAnalyzer:
    def __init__(self, fps=60):
        self.dis_ratio_recorder = []
        self.eye_state_recorder = []
        self.n_dis = 0
        self.fps = fps
        self.MOST_FRAME_PER_TWITCH = self.fps // 3

    def get_pos(self, face_landmarks):
        l_pos = np.mean([face_landmarks[idx].x for idx in LEFT_MOUTH_CORNER], axis=0), np.mean([face_landmarks[idx].y for idx in LEFT_MOUTH_CORNER], axis=0)
        r_pos = np.mean([face_landmarks[idx].x for idx in RIGHT_MOUTH_CORNER], axis=0), np.mean([face_landmarks[idx].y for idx in RIGHT_MOUTH_CORNER], axis=0)
        return l_pos, r_pos

    def record(self, face_landmarks, n, eyeState):
        mouthState = MouseState.NORMAL
        self.eye_state_recorder.append(eyeState)

        l_pos, r_pos = self.get_pos(face_landmarks)

        dis = np.sqrt((l_pos[0] - r_pos[0]) ** 2 + (l_pos[1] - r_pos[1]) ** 2)
        if n == 1:
            ratio = 1
        else:
            ratio = dis / self.n_dis

        if ratio > SMILE_DETECTED_THRESHOLD:
            mouthState = MouseState.SMILE
            ratio = SMILE_DETECTED_THRESHOLD

        if mouthState == MouseState.NORMAL:
            self.n_dis = (self.n_dis * (n - 1) + dis) / n

        self.dis_ratio_recorder.append(ratio)

        return mouthState, ratio

    def draw(self, save_path=None):
        dis_ratio_recorder = np.array(self.dis_ratio_recorder)
        # eye_state_recorder = np.array([0.95 if eye_etate == EyeState.WINK_DETECTED else 1 for eye_etate in self.eye_state_recorder])
        plt.figure(figsize=(15, 10))
        plt.plot(dis_ratio_recorder, label='Mouth Dis Ratio')
        # plt.plot(eye_state_recorder, label='Eye State')
        plt.xticks(np.arange(0, len(dis_ratio_recorder), 100))
        plt.yticks(np.arange(0.9, 1.1, 0.01))
        plt.legend()
        if save_path:
            plt.savefig(save_path)
            plt.close()
        else:
            plt.show()

    def sampling(self, sample_rate):
        return self.dis_ratio_recorder[::sample_rate]


    def find_local_extremes(self, sequence):
        extremes = []
        n = len(sequence)

        if n < 3:
            return extremes

        for i in range(1, n - 1):
            if sequence[i] > sequence[i - 1] and sequence[i] > sequence[i + 1]:
                extremes.append((i, sequence[i], 'Local Maximum'))
            elif sequence[i] < sequence[i - 1] and sequence[i] < sequence[i + 1]:
                extremes.append((i, sequence[i], 'Local Minimum'))

        # 如果有三个极值点的index相邻，其中中间的极值点与左右两边的极值点属性不同
        # 那么将其视为一个极值点，极值点的值为三个极值点的平均值，极值点的属性为左右两边极值点的属性
        filtered_extremes = []
        i = 0
        while i < len(extremes):
            if i < len(extremes) - 2 and extremes[i + 1][0] - extremes[i][0] == 1 and extremes[i + 2][0] - extremes[i + 1][0] == 1:
                value = (extremes[i][1] + extremes[i + 1] [1] + extremes[i + 2][1]) / 3
                attribute = extremes[i][2]
                filtered_extremes.append((extremes[i][0], value, attribute))
                i += 3
            else:
                filtered_extremes.append(extremes[i])
                i += 1

        return filtered_extremes

    def analyze(self):
        extremes = self.find_local_extremes(self.dis_ratio_recorder)

        mouth_twitch_recorder = []

        for i in range(1, len(extremes) - 1):
            if extremes[i][2] == 'Local Maximum':
                # find the left extreme of the current extreme
                if i > 2 and extremes[i][0] - extremes[i-3][0] < self.MOST_FRAME_PER_TWITCH:
                    extreme_left = extremes[i-1] if extremes[i-1][1] <= extremes[i-3][1] else extremes[i-3] 
                else:
                    extreme_left = extremes[i-1]
                # find the right extreme of the current extreme
                if i < len(extremes) - 3 and extremes[i+3][0] - extremes[i][0] < self.MOST_FRAME_PER_TWITCH:
                    extreme_right = extremes[i+1] if extremes[i+1][1] <= extremes[i+3][1] else extremes[i+3]
                else:
                    extreme_right = extremes[i+1]
                if extremes[i][0] - extreme_left[0] > self.MOST_FRAME_PER_TWITCH or extreme_right[0] - extremes[i][0] > self.MOST_FRAME_PER_TWITCH:
                    continue
                if 2 * extremes[i][1] - extreme_left[1] - extreme_right[1] >= 2 * MOUTH_TWITCH_THRESHOLD:
                    twitch_range = (2 * extremes[i][1] - extreme_left[1] - extreme_right[1]) / 2
                    if self.eye_state_recorder[extremes[i][0]] != EyeState.WINK_DETECTED:
                        mouth_twitch_recorder.append({
                            'frame': extremes[i][0],
                            'range': twitch_range
                        })

        return mouth_twitch_recorder