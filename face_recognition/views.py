from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
import cv2
#from .serializers import RecognitionResultSerializer, RegisterSerializer, RecognitionRequestSerializer
from django.utils.six import BytesIO
from rest_framework.parsers import JSONParser
from django.http import HttpResponse
import json
import cv2
import numpy as np
from django.core.files.storage import get_storage_class
from django.core.files.base import ContentFile
from PIL import Image
import io
from face_algorithm.face_id import getRep, calcCossimilarity, addFaceVec
from django.conf import settings
from .my_serializers import RecognitionResultSerializer, RegisterSerializer, RecognitionRequestSerializer
from .models import Info
# Create your views here.


class FaceRecognition(APIView):

    def post(self, request, format=None):

        if len(settings.CANDIDATE) == 0:
            return Response({"detail":"No face in database!"})

        serializer = RecognitionRequestSerializer(data=self.request.data)

        data = serializer.valid_data
        imgArr = data["picture"]
        boundingbox = data["boundingbox"]
        threshold = data["threshold"]

        print("img:", imgArr.shape)
        print("bdbox:", boundingbox)
        print("threshold:", threshold)
        try:
            resultId, similarity = calcCossimilarity(imgArr, settings.CANDIDATE)
        except:
            return Response({"detail": "recognition failed!"})
        print("resultId:", resultId)
        print("similarity:", similarity)
        if similarity >= threshold:
            info = Info.objects.get(ID=resultId)
            ID = info.ID
            name = info.name
            resImgPath = info.imgPath
            resSerializer = RecognitionResultSerializer(resImgPath, ID, name, similarity, True)
            return Response(resSerializer.valid_data)
        else:
            #resSerializer = RecognitionResultSerializer(None, similarity, False)
            return Response({"detail": "no result!"})


class Register(APIView):

    def post(self, request, format=None):

        serializer = RegisterSerializer(data=self.request.data)

        data = serializer.valid_data
        imgArr = data["picture"]
        del data["picture"]
        del data["boundingbox"]
        data["imgPath"] = settings.IMAGEPATH+str(data["ID"])+".jpg"
        try:
            Info.objects.create(**data)
        except:
           return Response({"detail": "Database Info saved Error!"})

        cv2.imwrite(data["imgPath"], imgArr)

        # 生成特征向量并存储
        addFaceVec(imgArr, data["ID"])

        return Response({"detail": "new face has been saved!"})