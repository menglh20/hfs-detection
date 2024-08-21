from django.shortcuts import render
from detect.Detect import detect
from common.models import Result, User
from django.http import JsonResponse
import datetime
import time

# Create your views here.


def detection(request):
    if request.method == "POST":
        name = request.POST.get("name")
        video = request.FILES.get("video")

        if not User.objects.filter(name=name).exists():
            return JsonResponse({
                "code": 400,
                "message": "User does not exist"
            })

        if not video.name.endswith(".mp4"):
            return JsonResponse({
                "code": 400,
                "message": "Invalid file format"
            })

        start_t = time.time()

        current_time = datetime.datetime.now()
        current_time = current_time.strftime("%Y.%m.%d %H:%M:%S")
        save_name = current_time.replace(".", "").replace(":", "")

        save_path = f"media/{name}_{save_name}.mp4"

        with open(save_path, "wb+") as f:
            for chunk in video.chunks():
                f.write(chunk)

        record = Result(name=name, result=0, detail="", comment="检测中", save_path=save_path, time=current_time)
        record.save()

        try:
            fps, resolution, eyeAnalyzer, mouthAnalyzer, asymmetryAnalyzer = detect(save_path, debug=False)
            result = 0
            detail = ""
            comment = ""

            eye_twitches = eyeAnalyzer.analyze()
            mouth_twitches = mouthAnalyzer.analyze()


            detail += "检测到嘴角抽搐次数: " + str(len(mouth_twitches)) + "\n"
            avg_eye_twitch_range = 0
            avg_mouth_twitch_range = 0
            for eye_twitch in eye_twitches:
                t = round(eye_twitch['frame'] / fps, 2)
                r = round(eye_twitch['range'], 4)
                # detail += "At " + str(t) + "s: " + eye_twitch['eye'] + " eye twitch, range " + str(r) + "\n"
                avg_eye_twitch_range += r
            for mouth_twitch in mouth_twitches:
                t = round(mouth_twitch['frame'] / fps, 2)
                r = round(mouth_twitch['range'], 4)
                # detail += "At " + str(t) + "s: mouth twitch, range " + str(r) + "\n"
                avg_mouth_twitch_range += r
            if len(eye_twitches) > 0:
                avg_eye_twitch_range /= len(eye_twitches)
                detail += "检测到眼角抽搐次数: " + str(len(eye_twitches)) + "\n"
                detail += "平均眼角抽搐幅度: " + str(round(avg_eye_twitch_range, 4)) + "\n"
            else:
                detail += "未检测到眼角抽搐\n"
            if len(mouth_twitches) > 0:
                avg_mouth_twitch_range /= len(mouth_twitches)
                detail += "平均嘴角抽搐幅度: " + str(round(avg_mouth_twitch_range, 4)) + "\n"
            else:
                detail += "未检测到嘴角抽搐\n"
            # detail += "未检测到颈扩肌抽搐\n"
            # detail += "细化定级:第二级严重程度\n"

            if len(mouth_twitches) > 0:
                result = 2
            elif len(eye_twitches) > 0:
                result = 1
            else:
                result = 0
            
            if len(eye_twitches) <= 1:
                result = 0
                comment = "检测完成,未发现相关症状"
            elif len(eye_twitches) > 1 and len(mouth_twitches) == 0:
                result = 1
                comment = "检测完成,眼角有不自然抽搐"
            elif len(mouth_twitches) > 0:
                result = 2
                comment = "检测完成,眼角和嘴角均有不自然抽搐"

            record.result = result
            record.detail = detail
            record.comment = comment
            record.save()

            end_t = time.time()

            return JsonResponse({
                "code": 200,
                "time": round(end_t - start_t, 2),
                "fps": fps,
                "resolution": resolution,
                "result": result,
                "detail": detail,
                "comment": comment,
            })
        except Exception as e:
            print(str(e))
            if "list index out of range" in str(e):
                record.comment = "未检测到人脸"
                record.save()
            else:
                record.comment = "检测失败"
                record.save()
            return JsonResponse({
                "code": 500,
                "message": str(e)
            })
    else:
        return JsonResponse({
            "code": 400,
            "message": "Invalid request"
        })


def history(request):
    if request.method == "POST":
        name = request.POST.get("name")
        print(name)
        page = int(request.POST.get("page", 1))

        if not User.objects.filter(name=name).exists():
            return JsonResponse({
                "code": 400,
                "message": "User does not exist"
            })

        results = Result.objects.filter(name=name).order_by("-time")
        total = results.count()
        results = results[(page - 1) * 10:page * 10]

        return JsonResponse({
            "code": 200,
            "total": total,
            "page": page,
            "results": [{
                "id": result.id,
                "result": result.result,
                "time": result.time,
                "detail": result.detail,
                "comment": result.comment
            } for result in results]
        })
    else:
        return JsonResponse({
            "code": 400,
            "message": "Invalid request"
        })


def clear(request):
    if request.method == "POST":
        Result.objects.all().delete()
        return JsonResponse({
            "code": 200,
            "message": "Clear success"
        })