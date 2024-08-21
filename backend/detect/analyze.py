import os
import openai
import json
import time

openai.api_key = os.getenv("OPENAI_API_KEY")


def get_chat_response(messages):
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0
    )
    # print(response)
    return response.choices[0].message.content


def read_message_from_file(file_path):
    with open(file_path, "r") as file:
        return file.read()


def read_sampling_data(file_path):
    with open(file_path, "r") as file:
        res = [float(line.strip()) for line in file.readlines()]
    if len(res) > 400:
        return res[0:400]
    else:
        return res


def get_patient_info(folder_path):
    patient_info = {}
    l_eye_samples = read_sampling_data(folder_path + "l_eye_samples.txt")
    r_eye_samples = read_sampling_data(folder_path + "r_eye_samples.txt")
    mouth_samples = read_sampling_data(folder_path + "mouth_samples.txt")
    patient_info["left_eye_ratio"] = l_eye_samples
    patient_info["right_eye_ratio"] = r_eye_samples
    patient_info["mouth_dis_ratio"] = mouth_samples
    return patient_info


def grade(patient_info):
    global system_message
    messages = [
        {'role': 'system', 'content': system_message},
        {'role': 'user', 'content': str(patient_info)}
    ]
    ans = get_chat_response(messages)
    # print(ans)
    ans = json.loads(ans)
    return ans["level"]


def compare(patient_info1, patient_info2):
    global system_message
    message = {
        "patientA": patient_info1,
        "patientB": patient_info2
    }
    messages = [
        {'role': 'system', 'content': system_message},
        {'role': 'user', 'content': str(message)}
    ]
    ans = get_chat_response(messages)
    # print(ans)
    ans = json.loads(ans)
    return ">" if ans["severe_patient"] == "A" else "<"



data_folder = "output/"

# method 1
# system_message = read_message_from_file("prompts/1/v0.txt")
# patient = "10"
# patient_info = get_patient_info(data_folder + patient + "/")
# result = grade(patient_info)
# print(result)


# method 1 batch
# system_message = read_message_from_file("prompts/1/v0.txt")
# for i in range(0, 5):
#     patient = str(i)
#     patient_info = get_patient_info(data_folder + patient + "/")
#     result = grade(patient_info)
#     print(str(i) + " " + str(result))

#     time.sleep(1)



# method 2
# system_message = read_message_from_file("prompts/2/v1.txt")
# patientA = "10"
# patientB = "0"
# patient_info1 = get_patient_info(data_folder + patientA + "/")
# patient_info2 = get_patient_info(data_folder + patientB + "/")
# result = compare(patient_info1, patient_info2)
# print(result)


# method 2 batch
# 
# for i in range(5, 10):
#     for j in range(0, 17):
#         patientA = str(i)
#         patientB = str(j)
#         patient_info1 = get_patient_info(data_folder + patientA + "/")
#         patient_info2 = get_patient_info(data_folder + patientB + "/")
#         result = compare(patient_info1, patient_info2)
#         print(str(i) + " " + result + " " + str(j))

#         time.sleep(1)
