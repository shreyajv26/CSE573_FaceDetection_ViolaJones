# -*- coding: utf-8 -*-
"""FaceDetection.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1LZT88ocf4yJAokSxL8AsX03VucDoK9oD
"""

import numpy as np

def integralOf(image):
    #_integral = image
    #for i in range(image.ndim):
    #   _integral = _integral.cumsum(axis=i)    
    #return _integral
    integral_im = np.zeros(image.shape)
    t = np.zeros(image.shape)
    for y in range(len(image)):
        for x in range(len(image[y])):
            t[y][x] = t[y-1][x] + image[y][x] if y-1 >= 0 else image[y][x]
            integral_im[y][x] = integral_im[y][x-1]+t[y][x] if x-1 >= 0 else t[y][x]
    return integral_im

def haarFeaturesOf(height, width):
    initial_rectangle_width = 1
    initial_rectangle_height = 1

    haarLike = []

    for r_width in range(initial_rectangle_width, width + 1):
        for r_height in range(initial_rectangle_height, height + 1):
            x = 0
            while x + r_width < width:
                y = 0
                while y + r_height < height:
                    current = {"x": x, "y": y, "w": r_width, "h": r_height}
                    right1 = {"x": x + r_width, "y": y, "w": r_width, "h": r_height}
                    
                    # current:light, right1:dark
                    if x + 2*r_width < width:
                        haarLike.append({"light": [current], "dark": [right1]})

                    # current:light, right1:dark, right2:light
                    if x + 3*r_width < width:
                        right2 = {"x": x + 2*r_width, "y": y, "w": r_width, "h": r_height}
                        haarLike.append({"light": [current, right2], "dark": [right1]})

                    # current:dark, bottom1:light
                    if y + 2*r_height < height:
                        bottom1 = {"x": x, "y": y + r_height, "w": r_width, "h": r_height}
                        haarLike.append({"light": [bottom1], "dark": [current]})

                    # current:dark, right1:light, bottom1:light, bottom1right1:dark
                    if x + 2*r_width < width and y + 2*height < height:
                        bottom1right1 = {"x": x + r_width, "y": y + r_height, "w": r_width, "h": r_height}
                        haarLike.append({"light": [right1, bottom1], "dark": [bottom1right1, current]})

                    # current:light , bottom1:dark, bottom2:light
                    if y + 3*r_height < height:
                        bottom2 = {"x": x, "y": y + 2*r_height, "w" : r_width, "h" : r_height}
                        haarLike.append({"light": [current, bottom2], "dark":[bottom1]})
                    y += 1
                x += 1

    return haarLike

def getFeatureValue(integral_image, rect):
    return integral_image[rect["y"]][rect["x"]] + integral_image[rect["y"] + rect["h"]][rect["x"]+rect["w"]] - integral_image[rect["y"]+rect["h"]][rect["x"]] - integral_image[rect["y"]][rect["x"]+rect["w"]]

def applyFeaturesToData(features, data):
    all_features = np.zeros((len(features), len(data)))
    for i, feature in enumerate(features):
        feature_value = lambda integral_image: sum([getFeatureValue(integral_image, r) for r in feature["dark"]]) - sum([getFeatureValue(integral_image, r) for r in feature["light"]])
        all_features[i] = list(map(lambda d: feature_value(d[0]), data))
    return all_features

import math

def weak_training(applied_features, labels, haar_like_features, weights):
  pos_wt = 0;
  neg_wt = 0;

  for i in range(len(labels)):
    if labels[i] == 1:
      pos_wt += weights[i]
    else:
      neg_wt += weights[i]
  classifiers = list()
  n_features = applied_features.shape[0]
  for i, feature in enumerate(applied_features):
    applied_feature = sorted(zip(weights, feature, labels), key=lambda x: x[1])
    pos_seen, neg_seen = 0, 0
    pos_weights, neg_weights = 0, 0
    min_error, best_feature, best_threshold, best_polarity = float('inf'), None, None, None
    for w, f, label in applied_feature:
        error = min(neg_weights + pos_wt - pos_weights, pos_weights + neg_wt - neg_weights)
        if error < min_error:
            min_error = error
            best_feature = haar_like_features[i]
            best_threshold = f
            best_polarity = 1 if pos_seen > neg_seen else -1
        if label == 1:
            pos_seen += 1
            pos_weights += w
        else:
            neg_seen += 1
            neg_weights += w
    clf = {"feature":best_feature, "theta": best_threshold, "polarity":best_polarity}
    classifiers.append(clf)
  return classifiers

def weak_classify(classifier, data):
  feature = sum([getFeatureValue(data, r) for r in classifier["feature"]["dark"]]) - sum([getFeatureValue(data, r) for r in classifier["feature"]["light"]])
  if classifier["polarity"]*feature < classifier["polarity"]*classifier["theta"]:
    return 1
  else:
    return 0

def get_best_weak_classifier(data, weak_classifiers, weights):
  res_cls = None
  res_acc = None
  res_error = float('inf')
  for cls in weak_classifiers:
    error, accuracy = 0, []
    for d, w in zip(data, weights):
      prediction = weak_classify(cls, d[0])
      d_acc = abs(prediction - d[1])
      accuracy.append(d_acc)
      error += w * d_acc
    error = error / len(data)
    if error < res_error:
        res_cls, res_error, res_acc = cls, error, accuracy
  beta = res_error/(1-res_error)
  for i in range(len(res_acc)):
    weights[i] = weights[i] * (beta ** (1 - res_acc[i]))
  alpha = math.log(1.0/beta)
  print('alpha', alpha)
  return beta, alpha, weights, res_cls

def classify(classifiers, img, alphas):
  score = 0
  ii = integralOf(img)
  for alpha, clf in zip(alphas, classifiers):
      score += alpha * weak_classify(clf, ii)
  return 1 if score >= 0.5 * sum(alphas) else 0

import cv2
import numpy as np
from glob import glob

num_classifiers = 5
classifiers = list()
alphas = list()

positive_image_path = "train/faces/*.pgm"
negative_image_path = "train/nonfaces/*.pgm"

training_set = []

for _f in glob(positive_image_path):
    training_set.append((cv2.imread(_f, cv2.IMREAD_GRAYSCALE), 1))

for _f in glob(negative_image_path):
    training_set.append((cv2.imread(_f, cv2.IMREAD_GRAYSCALE), 0))

len_positive = len(glob(positive_image_path))
len_negative = len(glob(negative_image_path))
print(len_positive, len_negative)
training_set_integrals = []
weights = np.zeros(len(training_set))
labels = np.zeros(len(training_set))

for i, example in enumerate(training_set):
    training_set_integrals.append((integralOf(example[0]), example[1]))
    x = len_positive if example[1] == 1 else len_negative
    weights[i] = 1.0 / (2 * x)
    labels[i] = example[1]

img_height, img_width = training_set_integrals[0][0].shape
print(img_height, img_width)
print('calculating HAAR')
haar_like_features = haarFeaturesOf(img_height, img_width)  
applied_features = applyFeaturesToData(haar_like_features, training_set_integrals)

print(weights)

for c in range(num_classifiers):
  #update weights
  weights = weights/np.linalg.norm(weights)
  #get weak classifiers 
  weak_classifiers = weak_training(applied_features, labels, haar_like_features, weights)
  print(weak_classifiers[0])
  #choose best weak classifier
  beta, alpha, weights, cls = get_best_weak_classifier(training_set_integrals, weak_classifiers, weights)
  #add to list of final classifiers
  classifiers.append(cls)
  alphas.append(alpha)

print(alphas)

#classify using final classifiers
def crop(img, xmin, xmax, ymin, ymax):
    """Crops a given image."""
    if len(img) < xmax:
        print('WARNING')
    patch = img[xmin: xmax]
    patch = [row[ymin: ymax] for row in patch]
    print(patch)
    return patch

from google.colab.patches import cv2_imshow

positive_image_path = "train/faces/*.pgm"
negative_image_path = "train/nonfaces/*.pgm"
test_images = []

for _f in glob(positive_image_path):
    test_images.append(cv2.imread(_f, cv2.IMREAD_GRAYSCALE))

test_images_non_face_path = "train/faces/*.jpg";

for _f in glob(negative_image_path):
    test_images.append(cv2.imread(_f, cv2.IMREAD_GRAYSCALE))

json_list = []
for im in range(len(test_images)):
  img = test_images[im]
  print("im",im)
  for i in range(0,len(img)-23):
        for j in range(0,len(img[0])-23):
          extracted=img[i:i+24,j:j+24]
          res=classify(classifiers,extracted,alphas)
          if res == 1:
            print ("Face found")
            print ("i"+str(i))
            print ("j"+str(j))

import json

json_list = [] #each element is a dictionary, {"iname": "1.jpg", "bbox": [1, 2, 3 ,5]}

element_1 = {"iname": "1.jpg", "bbox": [i, j, 24, 24]} #first element in json file
element_2 = {"iname": "1.jpg", "bbox": [10, 20, 30, 40]} #second element in json file
element_3 = {"iname": "2.jpg", "bbox": [100, 120, 35, 45]} #third element in json file

#add element to list
json_list.append(element_1)
json_list.append(element_2)
json_list.append(element_3)

#the result json file name
output_json = "results.json"
#dump json_list to result.json
with open(output_json, 'w') as f:
    json.dump(json_list, f)

import json
positive_image_path = "train/faces/*.pgm"
negative_image_path = "train/nonfaces/*.pgm"
test_images = []

for _f in glob(positive_image_path):
    test_images.append(cv2.imread(_f, cv2.IMREAD_GRAYSCALE))

test_images_non_face_path = "train/faces/*.jpg";

for _f in glob(negative_image_path):
    test_images.append(cv2.imread(_f, cv2.IMREAD_GRAYSCALE))

json_list = []
for im in range(len(test_images)):
  img = test_images[im]
  for i in range(0,len(img)-23):
        for j in range(0,len(img[0])-23):
          extracted=img[i:i+24,j:j+24]
          res=classify(classifiers,extracted,alphas)
          if res == 1:
            element = {"iname":"im"+str(im), "bbox": [i, j, 24, 24]}
            print(element)
            json_list.append(element)
#the result json file name
output_json = "results.json"
#dump json_list to result.json
with open(output_json, 'w') as f:
    json.dump(json_list, f)