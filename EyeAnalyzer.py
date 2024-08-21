import numpy as np
import matplotlib.pyplot as plt
import enum

LEFT_UP_CONTOURS = [161, 160, 159, 158, 157]
LEFT_DOWN_CONTOURS = [163, 144, 145, 153, 154]

RIGHT_UP_CONTOURS = [384, 385, 386, 387, 388]
RIGHT_DOWN_CONTOURS = [381, 380, 374, 373, 390]

UNNORMAL_THRESHOLD = 0.7

WINK_DETECTED_THRESHOLD = 0.5

EYE_TWITCH_THRESHOLD = 0.06

class EyeState(enum.Enum):
    NORMAL = 0
    UNNORMAL = 1
    WINK_DETECTED = 2


class EyeAnalyzer:
    def __init__(self, fps=60):
        self.ratio_recorder = [(1, 1)]
        self.frame_state = EyeState.NORMAL
        self.n_left_eye_distance = 0
        self.n_right_eye_distance = 0
        self.fps = fps
        self.MOST_FRAME_PER_TWITCH = self.fps // 3

    def get_distance(self, face_landmarks):
        left_eye_up = np.mean([face_landmarks[idx].y for idx in LEFT_UP_CONTOURS], axis=0)
        left_eye_down = np.mean([face_landmarks[idx].y for idx in LEFT_DOWN_CONTOURS], axis=0)
        right_eye_up = np.mean([face_landmarks[idx].y for idx in RIGHT_UP_CONTOURS], axis=0)
        right_eye_down = np.mean([face_landmarks[idx].y for idx in RIGHT_DOWN_CONTOURS], axis=0)
        left_eye_distance = left_eye_down - left_eye_up
        right_eye_distance = right_eye_down - right_eye_up
        return left_eye_distance, right_eye_distance

    def record(self, face_landmarks, n):
        self.frame_state = EyeState.NORMAL

        # 检测眨眼
        left_eye_distance, right_eye_distance = self.get_distance(
            face_landmarks)

        if n == 1:
            self.n_left_eye_distance = left_eye_distance
            self.n_right_eye_distance = right_eye_distance

        left_eye_ratio = left_eye_distance / self.n_left_eye_distance
        right_eye_ratio = right_eye_distance / self.n_right_eye_distance

        if left_eye_ratio < WINK_DETECTED_THRESHOLD or right_eye_ratio < WINK_DETECTED_THRESHOLD:
            self.frame_state = EyeState.WINK_DETECTED
        elif left_eye_ratio < UNNORMAL_THRESHOLD or right_eye_ratio < UNNORMAL_THRESHOLD:
            self.frame_state = EyeState.UNNORMAL

        # 记录眼睛比例
        if self.frame_state == EyeState.WINK_DETECTED:
            self.ratio_recorder.append((WINK_DETECTED_THRESHOLD, WINK_DETECTED_THRESHOLD))
        else:
            self.ratio_recorder.append((left_eye_ratio, right_eye_ratio))

        # 更新眼睛平均距离
        if self.frame_state == EyeState.NORMAL:
            self.n_left_eye_distance = (
                self.n_right_eye_distance * (n - 1) + left_eye_distance) / n
            self.n_right_eye_distance = (
                self.n_right_eye_distance * (n - 1) + right_eye_distance) / n

        return self.frame_state, left_eye_ratio, right_eye_ratio

    def draw(self, save_path=None):
        eye_ratio_recorder = np.array(self.ratio_recorder)
        plt.figure(figsize=(15, 10))
        plt.plot(eye_ratio_recorder[:, 0], label='Left Eye')
        plt.plot(eye_ratio_recorder[:, 1], label='Right Eye')
        plt.xticks(np.arange(0, len(eye_ratio_recorder), 100))
        plt.legend()
        if save_path:
            plt.savefig(save_path)
            plt.close()
        else:
            plt.show()

        # 保存到excel文件中
        import pandas as pd
        df = pd.DataFrame(eye_ratio_recorder, columns=['Left Eye', 'Right Eye'])
        df.to_excel('eye_ratio_recorder.xlsx', index=False)

    def sampling(self, sample_rate):
        return [eye_ratio[0] for eye_ratio in self.ratio_recorder[::sample_rate]], [eye_ratio[1] for eye_ratio in self.ratio_recorder[::sample_rate]]

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
                value = (extremes[i][1] + extremes[i + 1][1] + extremes[i + 2][1]) / 3
                attribute = extremes[i][2]
                filtered_extremes.append((extremes[i][0], value, attribute))
                i += 3
            else:
                filtered_extremes.append(extremes[i])
                i += 1

        return filtered_extremes

    def analyze(self):
        extremes_left = self.find_local_extremes(
            [eye_ratio[0] for eye_ratio in self.ratio_recorder])
        extremes_right = self.find_local_extremes(
            [eye_ratio[1] for eye_ratio in self.ratio_recorder])

        eye_twitch_recorder = []

        for i in range(1, len(extremes_left) - 1):
            if extremes_left[i][2] == 'Local Minimum':
                # find the left extreme of the current extreme
                if i > 2 and extremes_left[i][0] - extremes_left[i-3][0] < self.MOST_FRAME_PER_TWITCH:
                    extreme_left = extremes_left[i-1] if extremes_left[i - 1][1] >= extremes_left[i-3][1] else extremes_left[i-3]
                else:
                    extreme_left = extremes_left[i-1]
                # find the right extreme of the current extreme
                if i < len(extremes_left) - 3 and extremes_left[i+3][0] - extremes_left[i][0] < self.MOST_FRAME_PER_TWITCH:
                    extreme_right = extremes_left[i+1] if extremes_left[i + 1][1] >= extremes_left[i+3][1] else extremes_left[i+3]
                else:
                    extreme_right = extremes_left[i+1]
                if extremes_left[i][0] - extreme_left[0] > self.MOST_FRAME_PER_TWITCH or extreme_right[0] - extremes_left[i][0] > self.MOST_FRAME_PER_TWITCH:
                    continue
                if extreme_left[1] + extreme_right[1] - 2 * extremes_left[i][1] >= 2 * EYE_TWITCH_THRESHOLD:
                    twitch_range = (extreme_left[1] + extreme_right[1] - 2 * extremes_left[i][1]) / 2
                    eye_twitch_recorder.append({
                        'eye': 'left',
                        'frame': extremes_left[i][0],
                        'range': twitch_range
                    })

        for i in range(1, len(extremes_right) - 1):
            if extremes_right[i][2] == 'Local Minimum':
                # find the left extreme of the current extreme
                if i > 2 and extremes_right[i][0] - extremes_right[i-3][0] < self.MOST_FRAME_PER_TWITCH:
                    extreme_left = extremes_right[i-1] if extremes_right[i - 1][1] >= extremes_right[i-3][1] else extremes_right[i-3]
                else:
                    extreme_left = extremes_right[i-1]
                # find the right extreme of the current extreme
                if i < len(extremes_right) - 3 and extremes_right[i+3][0] - extremes_right[i][0] < self.MOST_FRAME_PER_TWITCH:
                    extreme_right = extremes_right[i+1] if extremes_right[i + 1][1] >= extremes_right[i+3][1] else extremes_right[i+3]
                else:
                    extreme_right = extremes_right[i+1]
                if extremes_right[i][0] - extreme_left[0] > self.MOST_FRAME_PER_TWITCH or extreme_right[0] - extremes_right[i][0] > self.MOST_FRAME_PER_TWITCH:
                    continue
                if extreme_left[1] + extreme_right[1] - 2 * extremes_right[i][1] >= 2 * EYE_TWITCH_THRESHOLD:
                    twitch_range = (extreme_left[1] + extreme_right[1] - 2 * extremes_right[i][1]) / 2
                    eye_twitch_recorder.append({
                        'eye': 'right',
                        'frame': extremes_right[i][0],
                        'range': twitch_range
                    })

        filtered_eye_twitch_recorder = []
        for eye_twitch in eye_twitch_recorder:
            # 过滤掉幅度较小的眼睛抽搐
            if eye_twitch['range'] < EYE_TWITCH_THRESHOLD / 2:
                continue
            # 过滤掉幅度极大的眼睛抽搐
            if eye_twitch['range'] > 0.17:
                continue
            # 过滤掉双眼在短时间内同时抽搐
            find_another_eye_twitch = False
            for another_eye_twitch in eye_twitch_recorder:
                if another_eye_twitch['eye'] != eye_twitch['eye'] and abs(another_eye_twitch['frame'] - eye_twitch['frame']) < 10:
                    find_another_eye_twitch = True
                    break
            if find_another_eye_twitch:
                continue
            # 符合条件的眼睛抽搐
            filtered_eye_twitch_recorder.append(eye_twitch)

        return filtered_eye_twitch_recorder
