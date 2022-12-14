import cv2
import numpy as np
from threading import Thread
import HandTrackingModule as htm
import json
import matplotlib.pyplot as plt
import matplotlib as mpl

samples = 100
start = False
path = "GesturesFiles/"


def find_distances(lmList):
    """
    Calculates all the distances between all the 21 nodes
    :param lmList: matrix of coordinates for each node
    :return: matrix of distances 21x21
    """
    distMatrix = np.zeros([len(lmList), len(lmList)], dtype='float')
    palmSize = ((lmList[0][1] - lmList[9][1]) ** 2 + (lmList[0][2] - lmList[9][2]) ** 2) ** (1. / 2.)
    for row in range(0, len(lmList)):
        for column in range(0, len(lmList)):
            distMatrix[row][column] = (((lmList[row][1] - lmList[column][1]) ** 2 +
                                        (lmList[row][2] - lmList[column][2]) ** 2) ** (1. / 2.)) / palmSize
    return distMatrix


def calculate_average(samplesList):
    """
    Calculates the average of the samples detected in "samples" number of detections
    :param samplesList: list of samples, for each sample a matrix of distances 21x21
    :return: the matrix of distances resulted from the avg operation
    """
    if len(samplesList) > 0:
        sumG = samplesList[0]
        for i in range(1, len(samplesList)):
            sumG = np.add(sumG, samplesList[i])
        avg = sumG/len(samplesList)
        return avg
    else:
        return -1


def save_in_file(letterGestureAVG, letterName):
    """
    Saves in a file the result of the avg operation for a specific letter given from letterName
    :param letterGestureAVG: a 21x21 matrix of distances resulted from the avg operation
    :param letterName: the name of the letter we are storing
    :return: None
    """
    print('Saving in json')

    # Serializing json
    json_object = json.dumps(letterGestureAVG.tolist())

    # Writing to sample.json
    with open(path + letterName.upper() + ".json", "w+") as outfile:
        outfile.write(json_object)
        outfile.close()


def bgr_to_rgb(image):
    """
    Converts a BGR image into RBG
    :param image: the BGR image
    :return: the same image but in RGB
    """
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def handle_close(event, cap):
    """
    Handles the close event of the Matplotlib window by closing the camera capture
    :param event: the close event
    :param cap: the VideoCapture object to be closed
    """
    cap.release()


def start_c():
    """
    Thread that asks the user to insert S to start the storing
    """
    prompt = 'Press S when Ready --> '
    name = input(prompt)
    if name == 's' or name == 'S':
        global start
        start = True
    else:
        start_c()


def store_gestures(_letter):
    """
    Method to store data linked to a specific gesture
    """
    mpl.use('TkAgg')

    # init the camera
    cap = cv2.VideoCapture(0)

    # enable Matplotlib interactive mode
    plt.ion()

    # create a figure to be updated
    fig = plt.figure()

    # intercept the window's close event to call the handle_close() function
    fig.canvas.mpl_connect("close_event", lambda event: handle_close(event, cap))

    # prep a variable for the first run
    img = None

    # prep detector + init unknownGestureSamples list
    detector = htm.HandDetector()
    unknown_gesture_samples = []

    # flags
    i = 0
    averageFlag = True

    # Throw a thread that controls the start of the calculating
    t = Thread(target=start_c)
    t.start()

    while cap.isOpened():
        success, frame = cap.read()
        frame = cv2.flip(frame, 1)

        frame = detector.find_hands(frame)
        RightHand = detector.right_hand(frame)  # False = Left Hand;   True = Right Hand
        lmList = detector.find_position(frame, draw=False)

        if len(lmList) != 0 and RightHand is False:  # if a only left hand is detected
            if start is True:
                if i < samples:
                    cv2.putText(frame, 'Storing ' + _letter.upper(), (2, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5,
                                (0, 0, 125), 3, cv2.LINE_AA)
                    unknown_gesture_sample = find_distances(lmList)  # save the sample
                    unknown_gesture_samples.append(unknown_gesture_sample)  # add the sample to the list of samples
                    i = i + 1
                else:
                    if averageFlag is True:
                        res = calculate_average(unknown_gesture_samples)  # calculate the average
                        save_in_file(res, letter)  # save the result into a file
                        averageFlag = False
                    else:
                        return
        elif RightHand is True:
            cv2.putText(frame, "Remove your Right Hand", (2, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 125), 2,
                        cv2.LINE_AA)

        if img is None:
            # convert it in RBG (for Matplotlib)
            img = plt.imshow(bgr_to_rgb(frame))
            plt.axis("off")  # hide axis, ticks, ...
            plt.title("Store Gestures")

            # show the plot!
            plt.show()
        else:
            # set the current frame as the data to show
            img.set_data(bgr_to_rgb(frame))

            # update the figure associated to the shown plot
            fig.canvas.draw()
            fig.canvas.flush_events()
            plt.pause(1 / 30)


if __name__ == "__main__":
    try:
        prompt = 'Which Letter? --> '
        letter = input(prompt)
        store_gestures(letter)
    except KeyboardInterrupt:
        exit(0)
