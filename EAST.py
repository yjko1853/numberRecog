"""
# 1
from imutils.object_detection import non_max_suppression
from imutils.perspective import four_point_transform
from imutils.contours import sort_contours
import matplotlib.pyplot as plt
import imutils
import numpy as np
import requests
import pytesseract
import cv2


def plt_imshow(title='image', img=None, figsize=(8, 5)):
    plt.figure(figsize=figsize)

    if type(img) == list:
        if type(title) == list:
            titles = title
        else:
            titles = []

            for i in range(len(img)):
                titles.append(title)

        for i in range(len(img)):
            if len(img[i].shape) <= 2:
                rgbImg = cv2.cvtColor(img[i], cv2.COLOR_GRAY2RGB)
            else:
                rgbImg = cv2.cvtColor(img[i], cv2.COLOR_BGR2RGB)

            plt.subplot(1, len(img), i + 1), plt.imshow(rgbImg)
            plt.title(titles[i])
            plt.xticks([]), plt.yticks([])

        plt.show()
    else:
        if len(img.shape) < 3:
            rgbImg = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        else:
            rgbImg = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        plt.imshow(rgbImg)
        plt.title(title)
        plt.xticks([]), plt.yticks([])
        plt.show()


def decode_predictions(scores, geometry):
    (numRows, numCols) = scores.shape[2:4]
    rects = []
    confidences = []

    for y in range(0, numRows):
        scoresData = scores[0, 0, y]
        xData0 = geometry[0, 0, y]
        xData1 = geometry[0, 1, y]
        xData2 = geometry[0, 2, y]
        xData3 = geometry[0, 3, y]
        anglesData = geometry[0, 4, y]

        for x in range(0, numCols):
            if scoresData[x] < min_confidence:
                continue

            (offsetX, offsetY) = (x * 4.0, y * 4.0)

            angle = anglesData[x]
            cos = np.cos(angle)
            sin = np.sin(angle)

            h = xData0[x] + xData2[x]
            w = xData1[x] + xData3[x]

            endX = int(offsetX + (cos * xData1[x]) + (sin * xData2[x]))
            endY = int(offsetY - (sin * xData1[x]) + (cos * xData2[x]))
            startX = int(endX - w)
            startY = int(endY - h)

            rects.append((startX, startY, endX, endY))
            confidences.append(scoresData[x])

    return (rects, confidences)


layerNames = ["feature_fusion/Conv_7/Sigmoid",
              "feature_fusion/concat_3"]

# ????????? ????????? EAST text detector ?????? Load
print("[INFO] loading EAST text detector...")
net = cv2.dnn.readNet("model/frozen_east_text_detection.pb") # ????????? ???,,,,,

width = 640
height = 640
min_confidence = 0.5
padding = 0.0

url = 'https://user-images.githubusercontent.com/69428232/149087561-4803b3e0-bcb4-4f9f-a597-c362db24ff9c.jpg'

image_nparray = np.asarray(bytearray(requests.get(url).content), dtype=np.uint8)
org_image = cv2.imdecode(image_nparray, cv2.IMREAD_COLOR)

plt_imshow("Original", org_image)

orig = org_image.copy()
(origH, origW) = org_image.shape[:2]

(newW, newH) = (width, height)
rW = origW / float(newW)
rH = origH / float(newH)

org_image = cv2.resize(org_image, (newW, newH))
(H, W) = org_image.shape[:2]

blob = cv2.dnn.blobFromImage(org_image, 1.0, (W, H), (123.68, 116.78, 103.94), swapRB=True, crop=False)
net.setInput(blob)
(scores, geometry) = net.forward(layerNames)

(rects, confidences) = decode_predictions(scores, geometry)
boxes = non_max_suppression(np.array(rects), probs=confidences)

for (startX, startY, endX, endY) in boxes:
    startX = int(startX * rW)
    startY = int(startY * rH)
    endX = int(endX * rW)
    endY = int(endY * rH)

    dX = int((endX - startX) * padding)
    dY = int((endY - startY) * padding)

    startX = max(0, startX - dX)
    startY = max(0, startY - dY)
    endX = min(origW, endX + (dX * 2))
    endY = min(origH, endY + (dY * 2))

    # ?????? ??????
    roi = orig[startY:endY, startX:endX]

    config = ("-l eng --psm 4")
    text = pytesseract.image_to_string(roi, config=config)

    results.append(((startX, startY, endX, endY), text))

results = sorted(results, key=lambda r: r[0][1])

output = orig.copy()

# ?????? ??????
for ((startX, startY, endX, endY), text) in results:
    cv2.rectangle(output, (startX, startY), (endX, endY), (0, 255, 0), 5)
    cv2.putText(output, text, (startX, startY - 20), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 5)

plt_imshow("Text Detection", output, figsize=(16, 10))



"""
import results as results

"""
# 2

from imutils.object_detection import non_max_suppression
import numpy as np
import argparse #??????????????? ???????????? ?????? ????????? ??? ?????? ?????? ?????????
import time
import cv2

ap = argparse.ArgumentParser()
# ?????? ????????? ??????
ap.add_argument("-i", "--a-1.png", type=str, help="path to input image")
# ????????? ?????? ??????(????????? ???????????? ?????? ??????) ??????
ap.add_argument("-east", "--east", type=str, help="path to input EAST text detector")
# ??????????????? ???????????? ?????? ?????? ??? (?????????=0.5)
ap.add_argument("-c", "--min-confidence", type=float, default=0.5, help="minimum probability required to inspect a region")
# ?????? ????????? ????????? ??????
ap.add_argument("-w", "--width", type=int, default=320, help="resized image width (should be multiple of 32")
# ?????? ????????? ????????? ??????
ap.add_argument("-e", "--height", type=int, default=320, help="resized image height (should be multiple of 32")
args = vars(ap.parse_args())

# ????????? ?????? ??? ????????? ??????
image = cv2.imread("a-2.png")

orig = image.copy() # ?????? ??????
(H, W) = image.shape[:2] # ??????, ?????? ??????

(newW, newH) = (args["width"], args["height"]) # ???????????? ????????? ????????? ??????
rW = W / float(newW) # ?????? ??????????????? ????????? ??????
rH = H / float(newH)

image = cv2.resize(image, (newW, newH)) #????????? resize
(H,W) = image.shape[:2] # ??????, ?????? ??????

layerNames = [
    "feature_fusion/Conv_7/Sigmoid", # ??????????????? ????????????/???????????? ???????????? ????????? ???????????? ?????? ??????
    "feature_fusion/concat_3" # ????????? ??????/???????????? ???????????? ?????? -> ???????????? ??????????????? ?????????
]
# EAST ?????? ????????? ????????? ??????????????? ??????

print("[INFO] loading EAST text detector...")
# cv2??? ???????????? EAST??? ????????? ?????? ??????
net = cv2.dnn.readNet("frozen_east_text_detection.pb")
# blobFromImages ??? ?????? ????????? ????????? Net??? ???????????? ???????????? blob ???????????? ??????
blob = cv2.dnn.blobFromImage(image, 1.0, (W, H), (123.68, 116.78, 103.94), swapRB=True, crop=False)

net.setInput(blob) # ???????????? ???????????? EAST??? ?????? ??????
(scores, geometry) = net.forward(layerNames) # scores??? geometry??? ????????? ????????? ????????????

# print(scores.shape)
print(geometry.shape)
# ????????? ??????
(a, b, numRows, numCols) = scores.shape # ?????? ?????? ?????? ??? ?????? ???????????? ?????????
rects = [] # ???????????? ?????? ????????? ?????? ??????
confidences = [] # ??? ????????? ????????? ???????????? ????????? ???????????? ?????? ??????

for y in range(0, numRows):
    scoresData = scores[0,0,y]
    xData0 = geometry[0,0,y]
    xData1 = geometry[0,0,y]
    xData2 = geometry[0,0,y]
    xData3 = geometry[0,0,y]
    anglesData = geometry[0,4,y]

    for x in range (0, numCols):
        if scoresData[x] < args["min_confidence"]:
            continue
        (offsetX, offsetY) = (x * 4.0, y * 4.0) # ????????? ????????? ???????????? ?????? ?????? 4??? ????????? ??????

        angle = anglesData[x]
        cos = np.cos(angle)
        sin = np.sin(angle)

        h = xData0[x] + xData2[x]
        w = xData1[x] + xData3[x]

        # ?????? ??????
        endX = int(offsetX + (cos + xData1[x]) + (sin + xData2[x]))
        endY = int(offsetX - (sin + xData1[x]) + (cos + xData2[x]))
        startX = int(endX - w)
        startY = int(endY - h)

        # ?????? ??????????????? ????????? ????????? ??????
        rects.append((startX, startY, endX, endY))
        confidences.append(scoresData[x])

# NMS ?????? -> ?????? ?????? ????????? ????????? ?????? ????????? ????????? ???????????? ??? ????????? ?????? ?????? ?????? ??????

# ?????? ?????? ??????
boxes = non_max_suppression(np.array(rects), probs=confidences)

# ????????? ?????? ?????????
for (startX, startY, endX, endY) in boxes:
    startX = int(startX + rW)
    startY = int(startY + rH)
    endX = int(endX + rW)
    endY = int(endY + rH)

    cv2.rectangle(orig, (startX,startY), (endX,endY), (0, 255, 0, 2))

#????????? ??????
cv2.imshow("Text Detection", orig)
cv2.waitKey(0)

"""
"""

# 3


# Import required modules
import cv2 as cv
import math
import argparse

parser = argparse.ArgumentParser(description='Use this script to run text detection deep learning networks using OpenCV.')
# Input argument
parser.add_argument('--input', help='Path to input image or video file. Skip this argument to capture frames from a camera.')
# Model argument
parser.add_argument('--model', default="frozen_east_text_detection.pb",
                    help='Path to a binary .pb file of model contains trained weights.'
                    )
# Width argument
parser.add_argument('--width', type=int, default=320,
                    help='Preprocess input image by resizing to a specific width. It should be multiple by 32.'
                   )
# Height argument
parser.add_argument('--height',type=int, default=320,
                    help='Preprocess input image by resizing to a specific height. It should be multiple by 32.'
                   )
# Confidence threshold
parser.add_argument('--thr',type=float, default=0.5,
                    help='Confidence threshold.'
                   )
# Non-maximum suppression threshold
parser.add_argument('--nms',type=float, default=0.4,
                    help='Non-maximum suppression threshold.'
                   )

parser.add_argument('--device', default="cpu", help="Device to inference on")


args = parser.parse_args()


############ Utility functions ############
def decode(scores, geometry, scoreThresh):
    detections = []
    confidences = []

    ############ CHECK DIMENSIONS AND SHAPES OF geometry AND scores ############
    assert len(scores.shape) == 4, "Incorrect dimensions of scores"
    assert len(geometry.shape) == 4, "Incorrect dimensions of geometry"
    assert scores.shape[0] == 1, "Invalid dimensions of scores"
    assert geometry.shape[0] == 1, "Invalid dimensions of geometry"
    assert scores.shape[1] == 1, "Invalid dimensions of scores"
    assert geometry.shape[1] == 5, "Invalid dimensions of geometry"
    assert scores.shape[2] == geometry.shape[2], "Invalid dimensions of scores and geometry"
    assert scores.shape[3] == geometry.shape[3], "Invalid dimensions of scores and geometry"
    height = scores.shape[2]
    width = scores.shape[3]
    for y in range(0, height):

        # Extract data from scores
        scoresData = scores[0][0][y]
        x0_data = geometry[0][0][y]
        x1_data = geometry[0][1][y]
        x2_data = geometry[0][2][y]
        x3_data = geometry[0][3][y]
        anglesData = geometry[0][4][y]
        for x in range(0, width):
            score = scoresData[x]

            # If score is lower than threshold score, move to next x
            if(score < scoreThresh):
                continue

            # Calculate offset
            offsetX = x * 4.0
            offsetY = y * 4.0
            angle = anglesData[x]

            # Calculate cos and sin of angle
            cosA = math.cos(angle)
            sinA = math.sin(angle)
            h = x0_data[x] + x2_data[x]
            w = x1_data[x] + x3_data[x]

            # Calculate offset
            offset = ([offsetX + cosA * x1_data[x] + sinA * x2_data[x], offsetY - sinA * x1_data[x] + cosA * x2_data[x]])

            # Find points for rectangle
            p1 = (-sinA * h + offset[0], -cosA * h + offset[1])
            p3 = (-cosA * w + offset[0],  sinA * w + offset[1])
            center = (0.5*(p1[0]+p3[0]), 0.5*(p1[1]+p3[1]))
            detections.append((center, (w,h), -1*angle * 180.0 / math.pi))
            confidences.append(float(score))

    # Return detections and confidences
    return [detections, confidences]

if __name__ == "__main__":
    # Read and store arguments
    confThreshold = args.thr
    nmsThreshold = args.nms
    inpWidth = args.width
    inpHeight = args.height
    model = args.model

    # Load network
    net = cv.dnn.readNet(model)
    if args.device == "cpu":
        net.setPreferableBackend(cv.dnn.DNN_TARGET_CPU)
        print("Using CPU device")
    elif args.device == "gpu":
        net.setPreferableBackend(cv.dnn.DNN_BACKEND_CUDA)
        net.setPreferableTarget(cv.dnn.DNN_TARGET_CUDA)
        print("Using GPU device")


    # Create a new named window
    kWinName = "EAST: An Efficient and Accurate Scene Text Detector"
    cv.namedWindow(kWinName, cv.WINDOW_NORMAL)
    outputLayers = []
    outputLayers.append("feature_fusion/Conv_7/Sigmoid")
    outputLayers.append("feature_fusion/concat_3")
    print("b")
    # Open a video file or an image file or a camera stream
    cap = cv.VideoCapture(args.input if args.input else 0)

    while cv.waitKey(1) < 0:
        # Read frame
        hasFrame, frame = cap.read()
        if not hasFrame:
            cv.waitKey()
            break
        print("c")
        # Get frame height and width
        height_ = frame.shape[0]
        width_ = frame.shape[1]
        rW = width_ / float(inpWidth)
        rH = height_ / float(inpHeight)

        # Create a 4D blob from frame.
        blob = cv.dnn.blobFromImage(frame, 1.0, (inpWidth, inpHeight), (123.68, 116.78, 103.94), True, False)
        print("d")
        # Run the model
        net.setInput(blob)
        output = net.forward(outputLayers)
        t, _ = net.getPerfProfile()
        label = 'Inference time: %.2f ms' % (t * 1000.0 / cv.getTickFrequency())
        print("e")
        # Get scores and geometry
        scores = output[0]
        geometry = output[1]
        [boxes, confidences] = decode(scores, geometry, confThreshold)
        # Apply NMS
        indices = []
        indices.append(cv.dnn.NMSBoxesRotated(boxes, confidences, confThreshold, nmsThreshold))
        print("indices : ", indices)
        for i in indices:
            print(indices)
            # get 4 corners of the rotated rect
            if indices == [()]:
                break
            vertices = cv.boxPoints(boxes[i[0]])
            # scale the bounding box coordinates based on the respective ratios
            for j in range(4):
                print("g")
                vertices[j][0] *= rW
                vertices[j][1] *= rH
                print(vertices[j][0], vertices[j][1])
            for j in range(4):
                p1 = (int(vertices[j][0]), int(vertices[j][1]))
                p2 = (int(vertices[(j + 1) % 4][0]), int(vertices[(j + 1) % 4][1]))
                print(p1, p2)
                cv.line(frame, p1, p2, (0, 255, 0), 2, cv.LINE_AA)
                # cv.putText(frame, "{:.3f}".format(confidences[i[0]]), (vertices[0][0], vertices[0][1]), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1, cv.LINE_AA)

        # Put efficiency information
        cv.putText(frame, label, (0, 15), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255))

        # Display the frame
        cv.imshow(kWinName, frame)
        print("a")
"""

# 4
"""
from imutils.object_detection import non_max_suppression
from imutils.perspective import four_point_transform
from imutils.contours import sort_contours
import matplotlib.pyplot as plt
import imutils
import numpy as np
import requests
import pytesseract
import cv2
"""
from PIL import Image
import pytesseract
"""
pytesseract.pytesseract.tesseract_cmd = R'C:\Program Files\Tesseract-OCR\tesseract'

# str = pytesseract.image_to_string(Image.open('C:/Users/yjko/PycharmProjects/numberRecog/a-2.png'), lang='Hangul')


def plt_imshow(title='image', img=None, figsize=(8, 5)):
    plt.figure(figsize=figsize)

    if type(img) == list:
        if type(title) == list:
            titles = title
        else:
            titles = []

            for i in range(len(img)):
                titles.append(title)

        for i in range(len(img)):
            if len(img[i].shape) <= 2:
                rgbImg = cv2.cvtColor(img[i], cv2.COLOR_GRAY2RGB)
            else:
                rgbImg = cv2.cvtColor(img[i], cv2.COLOR_BGR2RGB)

            plt.subplot(1, len(img), i + 1), plt.imshow(rgbImg)
            plt.title(titles[i])
            plt.xticks([]), plt.yticks([])

        plt.show()
    else:
        if len(img.shape) < 3:
            rgbImg = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        else:
            rgbImg = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        plt.imshow(rgbImg)
        plt.title(title)
        plt.xticks([]), plt.yticks([])
        plt.show()


def decode_predictions(scores, geometry):
    (numRows, numCols) = scores.shape[2:4]
    rects = []
    confidences = []

    for y in range(0, numRows):
        scoresData = scores[0, 0, y]
        xData0 = geometry[0, 0, y]
        xData1 = geometry[0, 1, y]
        xData2 = geometry[0, 2, y]
        xData3 = geometry[0, 3, y]
        anglesData = geometry[0, 4, y]

        for x in range(0, numCols):
            if scoresData[x] < min_confidence:
                continue

            (offsetX, offsetY) = (x * 4.0, y * 4.0)

            angle = anglesData[x]
            cos = np.cos(angle)
            sin = np.sin(angle)

            h = xData0[x] + xData2[x]
            w = xData1[x] + xData3[x]

            endX = int(offsetX + (cos * xData1[x]) + (sin * xData2[x]))
            endY = int(offsetY - (sin * xData1[x]) + (cos * xData2[x]))
            startX = int(endX - w)
            startY = int(endY - h)

            rects.append((startX, startY, endX, endY))
            confidences.append(scoresData[x])

    return (rects, confidences)


layerNames = ["feature_fusion/Conv_7/Sigmoid",
              "feature_fusion/concat_3"]

# ????????? ????????? EAST text detector ?????? Load
print("[INFO] loading EAST text detector...")
net = cv2.dnn.readNet("frozen_east_text_detection.pb")


width = 640
height = 640
min_confidence = 0.5
padding = 0.0

url = 'https://user-images.githubusercontent.com/69428232/149087561-4803b3e0-bcb4-4f9f-a597-c362db24ff9c.jpg'

image_nparray = np.asarray(bytearray(requests.get(url).content), dtype=np.uint8)
org_image = cv2.imdecode(image_nparray, cv2.IMREAD_COLOR)

plt_imshow("Original", org_image)

orig = org_image.copy()
(origH, origW) = org_image.shape[:2]

(newW, newH) = (width, height)
rW = origW / float(newW)
rH = origH / float(newH)

org_image = cv2.resize(org_image, (newW, newH))
(H, W) = org_image.shape[:2]

blob = cv2.dnn.blobFromImage(org_image, 1.0, (W, H), (123.68, 116.78, 103.94), swapRB=True, crop=False)
net.setInput(blob)
(scores, geometry) = net.forward(layerNames)

(rects, confidences) = decode_predictions(scores, geometry)
boxes = non_max_suppression(np.array(rects), probs=confidences)

for (startX, startY, endX, endY) in boxes:
    startX = int(startX * rW)
    startY = int(startY * rH)
    endX = int(endX * rW)
    endY = int(endY * rH)

    dX = int((endX - startX) * padding)
    dY = int((endY - startY) * padding)

    startX = max(0, startX - dX)
    startY = max(0, startY - dY)
    endX = min(origW, endX + (dX * 2))
    endY = min(origH, endY + (dY * 2))

    # ?????? ??????
    roi = orig[startY:endY, startX:endX]

    config = ("-l eng --psm 4")

    print("aaaaaaaaaaaaa")
    text = pytesseract.image_to_string(roi, config=config)
    print("bbbbbbbbb")
    results = []
    results.append(((startX, startY, endX, endY), text))

results = sorted(results, key=lambda r: r[0][1])

output = orig.copy()

# ?????? ??????
for ((startX, startY, endX, endY), text) in results:
    cv2.rectangle(output, (startX, startY), (endX, endY), (0, 255, 0), 5)
    cv2.putText(output, text, (startX, startY - 20), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 5)

plt_imshow("Text Detection", output, figsize=(16, 10))


"""
"""
# 5
import tensorflow as tf

def build_model(self):
    print("building model...")
    self.init_placeholders()
    self.build_cnn()
    self.build_rnn()

def build_cnn(self):
    with tf.variable_scope('cnn'):
        self.conv1 = activation(conv2d(self.inputs, 64, name='conv1'))
        self.pool1 = activation(conv2d(self.conv1, 64, strides=[2, 2], name='pool1'))
        self.conv2 = activation(conv2d(self.pool1, 128, name='conv2'))
        self.pool2 = activation(conv2d(self.conv2, 128, strides=[2, 2], name='pool2'))
...
        self.conv7 = activation(conv2d(self.pool4, 512, name='conv7'))
        shape = self.conv7.get_shape().as_list()
        reshape_inputs = tf.reshape(conv7, [self.batch_size, -1, shape[2] * shape[3]])
        inputs_dense = Dense(self.hidden_units, dtype=self.dtype, name = 'inputs_dense')
        self.cnn_out = inputs_dense(reshape_inputs)

def build_rnn(self):
    self.rnn_inputs = self.cnn_out
    cells_fw = [cell_type(self.hidden_units)
        for _ in range(self.depth)]
    cells_bw = [cell_type(self.hidden_units)
        for _ in range(self.depth)]
    rnn_outputs, _, _ =
        tf.contrib.rnn.stack_bidirectional_dynamic_rnn(
            cells_fw = cells_fw,
            cells_bw = cells_bw,
            inputs = self.rnn_inputs,
            dtype = self.dtype,
            scope='rnn1'
        )
    # Reshape [batch * width, hidden*2]
    rnn_out_reshaped = tf.reshape(rnn_outputs, [-1, self.hidden_units * 2])
    rnn_logits = tf.layers.dense(
        inputs = rnn_out_reshaped,
        units = self.num_classes,
    )
    rnn_logits_reshaped = tf.reshape(rnn_logits,
        [self.batch_size, -1, self.num_classes])
    if self.mode == 'train':
        self.time_major_out = tf.transpose(
            rnn_logits_reshaped, [1, 0, 2], name='time_major')
        self.ctc_loss = tf.nn.ctc_loss(
            self.targets,
            self.time_major_out,
            self.seq_len,
        )
        self.loss = tf.reduce_mean(self.ctc_loss)
        self.init_optimizer()

"""

# 6
"""
def CRNN(input_shape, num_classes, prediction_only=False, gru=False):
    
    CRNN architecture.

    # Arguments
        input_shape: Shape of the input image, (256, 32, 1).
        num_classes: Number of characters in alphabet, including CTC blank.

    # References
        https://arxiv.org/abs/1507.05717
    

    act = 'relu'

    # KERAS API??? ????????? ?????? ??????
    x = image_input = Input(shape=input_shape, name='image_input')

    x = Conv2D(64, (3, 3), strides=(1, 1), activation=act, padding='same', name='conv1_1')(x)
    x = MaxPool2D(pool_size=(2, 2), strides=(2, 2), name='pool1', padding='same')(x)

    x = Conv2D(128, (3, 3), strides=(1, 1), activation=act, padding='same', name='conv2_1')(x)
    x = MaxPool2D(pool_size=(2, 2), strides=(2, 2), name='pool2', padding='same')(x)

    x = Conv2D(256, (3, 3), strides=(1, 1), activation=act, padding='same', name='conv3_1')(x)
    x = Conv2D(256, (3, 3), strides=(1, 1), activation=act, padding='same', name='conv3_2')(x)
    x = MaxPool2D(pool_size=(2, 2), strides=(1, 2), name='pool3', padding='same')(x)

    x = Conv2D(512, (3, 3), strides=(1, 1), activation=act, padding='same', name='conv4_1')(x)
    x = BatchNormalization(name='batchnorm1')(x)

    x = Conv2D(512, (3, 3), strides=(1, 1), activation=act, padding='same', name='conv5_1')(x)
    x = BatchNormalization(name='batchnorm2')(x)
    x = MaxPool2D(pool_size=(2, 2), strides=(1, 2), name='pool5', padding='valid')(x)

    x = Conv2D(512, (2, 2), strides=(1, 1), activation=act, padding='valid', name='conv6_1')(x)
    x = Reshape((-1, 512))(x)

    if gru:
        x = Bidirectional(GRU(256, return_sequences=True))(x)
        x = Bidirectional(GRU(256, return_sequences=True))(x)

    else:
        x = Bidirectional(LSTM(256, return_sequences=True))(x)
        x = Bidirectional(LSTM(256, return_sequences=True))(x)

    x = Dense(num_classes, name='dense1')(x)

    # output??? softmax????????? ???????????? ??????????????? ???????????? ?????????.
    x = y_pred = Activation('softmax', name='softmax')(x)

    # ????????? ?????? : Model(input, output)
    model_pred = Model(image_input, x)

    # train??????????????? preiction ????????? output??? softmax activation??? ????????? ???
    if prediction_only:
        return model_pred

    # ?????? ?????????
    max_string_len = int(y_pred.shape[1])

    # CTC LOSS ?????? ??????
    def ctc_lambda_func(args):
        labels, y_pred, input_length, label_length = args
        return K.ctc_batch_cost(labels, y_pred, input_length, label_length)

    # CTC LOSS??? ???????????? ???????????? INPUT ??????
    labels = Input(name='label_input', shape=[max_string_len], dtype='float32')
    input_length = Input(name='input_length', shape=[1], dtype='int64')
    label_length = Input(name='label_length', shape=[1], dtype='int64')

    # Lambda??? ???????????? ctc loss ?????????
    ctc_loss = Lambda(ctc_lambda_func, output_shape=(1,), name='ctc')([labels, y_pred, input_length, label_length])

    # ?????? ??????????????? ????????? 4????????????, ???????????? ctc loss ???
    model_train = Model(inputs=[image_input, labels, input_length, label_length], outputs=ctc_loss)

    return model_train, model_pred

"""