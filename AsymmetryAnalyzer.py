import numpy as np
import matplotlib.pyplot as plt
from EyeAnalyzer import EyeState

# define facial area
# MID_LINE = [9, 8, 168, 6, 197, 195, 5, 4, 1, 0, 11, 12, 13, 14, 15, 16, 17]
MID_LINE = [9, 4]
EYE_CENTER = [468, 473]
UP_EYELID = [470, 475]
DOWN_EYELID = [472, 477]
CHEEK_BONE = [50, 280]
MOUTH_CORNER = [61, 291]

class AsymmetryAnalyzer:
    def __init__(self) -> None:
        self.score_recorder = []

    def get_vec(self, idx1, idx2, face_landmarks):
        point1 = (face_landmarks[idx1].x, face_landmarks[idx1].y)
        point2 = (face_landmarks[idx2].x, face_landmarks[idx2].y)
        vec = np.array(point2) - np.array(point1)
        return vec

    def cal_vertical_vec(self, face_landmarks):
        # x = []
        # y = []
        # for idx in MID_LINE:
        #     x.append(face_landmarks[idx].x)
        #     y.append(face_landmarks[idx].y)
        # x = np.array(x)
        # y = np.array(y)
        # slope, intercept = np.polyfit(x, y, 1)
        # point1 = (x[0], slope * x[0] + intercept)
        # point2 = (x[-1], slope * x[-1] + intercept)
        # vertical_vec = np.array(point2) - np.array(point1)
        point1 = (face_landmarks[MID_LINE[0]].x, face_landmarks[MID_LINE[0]].y)
        point2 = (face_landmarks[MID_LINE[1]].x, face_landmarks[MID_LINE[1]].y)
        vertical_vec = np.array(point2) - np.array(point1)
        return vertical_vec

    def record(self, face_landmarks, eyeState):
        if eyeState == EyeState.WINK_DETECTED:
            self.score_recorder.append(0)
            return 0
        else:
            horizontal_vec = []
            horizontal_vec.append(self.get_vec(EYE_CENTER[0], EYE_CENTER[1], face_landmarks))
            # horizontal_vec.append(self.get_vec(UP_EYELID[0], UP_EYELID[1], face_landmarks))
            # horizontal_vec.append(self.get_vec(DOWN_EYELID[0], DOWN_EYELID[1], face_landmarks))
            # horizontal_vec.append(self.get_vec(CHEEK_BONE[0], CHEEK_BONE[1], face_landmarks))
            horizontal_vec.append(self.get_vec(MOUTH_CORNER[0], MOUTH_CORNER[1], face_landmarks))
            vertical_vec = self.cal_vertical_vec(face_landmarks)
            score = 0
            for vec in horizontal_vec:
                score += abs(np.dot(vec, vertical_vec) / (np.linalg.norm(vec) * np.linalg.norm(vertical_vec)))
            self.score_recorder.append(score)
            return score


    def draw(self, save_path=None):
        score_recorder = np.array(self.score_recorder)
        plt.figure(figsize=(15, 10))
        plt.plot(score_recorder, label='Asymmetry Score')
        plt.xticks(np.arange(0, len(score_recorder), 100))
        plt.yticks(np.arange(0, 1, 0.1))
        if save_path:
            plt.savefig(save_path)
        else:
            plt.show()
        plt.close()

    
    def analyze(self):
        avg_score = np.mean([score for score in self.score_recorder if score != 0])
        return avg_score