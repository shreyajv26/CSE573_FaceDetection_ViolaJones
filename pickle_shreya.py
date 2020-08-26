import cv2
import os
import sys
import glob
import numpy as np
import random as rand
import matplotlib.pyplot as plt
import pickle
import time

test_images = './test_images/*.jpg'

#https://www.quora.com/How-can-I-read-multiple-images-in-Python-presented-in-a-folder
images = glob.glob(test_images)
files = []
for i in images:
    img = cv2.imread(i)
    files.append(img)
print(len(files))

#https://stackoverflow.com/questions/25104618/pickling-an-image-object
with open("training_images.pkl",'wb') as file:
    pickle.dump(images,file)
    
with open("training_images.pkl",'rb') as file:
    loaded_open = pickle.load(file)
    print(len(loaded_open))
    
    
def calculate_integralImage(image):
    
    rows = image.shape[0]
    columns = image.shape[1]
    
    #defining np array for integral images with all zeros
    #https://en.wikipedia.org/wiki/Summed-area_table
    #https://www.codeproject.com/Articles/441226/Haar-feature-Object-Detection-in-Csharp
    
    integral_image = np.zeros((rows,columns))
    integral_image[0][0] = img[0][0]
    
    #calculate ii(x-1,y)
    for r in range(1,rows):
        integral_image[r][0] = integral_image[r-1][0] + img[r][0]
    
    #calculate ii(x,y-1)
    for c in range(1,columns):
        integral_image[0][c] = integral_image[0][c-1] + img[0][c]
    
    #calculate final
    for r in range(1,rows):
        for c in range(1,columns):
            integral_image[c][r] = (integral_image[c-1][r]+integral_image[c][r-1]-integral_image[c-1][r-1]) + (img[c][r])

class Rectangle:
    # constructor
    #https://www.javatpoint.com/python-constructors
    
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    
    # Return the sum of all pixels inside a rectangle for a specific integral image
    def compute_sum(self, integralImg, scale, x, y):
        
        x = self.x
        y = self.y
        width  = self.width
        height = self.height
        
        one   = integralImg[y][x]
        two   = integralImg[y][x+width]
        three = integralImg[y+height][x]
        four  = integralImg[y+height][x+width]
        
        desiredSum = (one + four) - (two + three)
        print(desiredSum)
        return desiredSum
    