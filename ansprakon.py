# coding=utf-8
import subprocess
import image_preprocessor
import ssocr
import roi_cutter
import result_processor
import feat_detector
import opencv_webcam_multithread
import cv2
import time
import gc
import bottleneck
gc.enable()

# check if running on an RPi by trying to import the RPi.GPIO library. If this fails, we are usually not on an RPi.
# ID of the device to read.
device_id = 7

video_src = 0  # index of the video source

# NanoTTS Options
lang = "de-DE"
volume = 0
rate = 0  # speed of the reading
pitch = 0

# create cam stream object
cam = opencv_webcam_multithread.WebcamVideoStream(src=video_src)


def grab_image():
    """
Creates new cv VideoCapture object. Reads a frame and releases the VideoCapture Device.
    :return: The frame which was read as cv2 MAT format.
    """
    img = None
    try:
        img = cam.read()
    except cv2.error as e:
        print(e)
        grab_image()
    return img


def preprocess_image(img):
    """
Processes an Image with the methods defined for the device in image_preprocessor.py
    :param img: image to process as cv2 MAT format
    :return: processed image
    """
    return getattr(image_preprocessor, "image_device_" + str(device_id))(img)


def cut_roi(img):
    """
Cuts out Rois and returns ocr-rois and feat-rois as
    :param img:
    :return: list of list [[ocr_rois],[feat_rois]]
    """
    return getattr(roi_cutter, "roi_device_" + str(device_id))(img)


def detect_feat(rois):
    """
Detect feat in the
    :param rois:
    :return:
    """
    return getattr(feat_detector, "feat_detect_device_" + str(device_id))(rois)


def run_ssocr(rois):
    """
Sets the ssocr flags matching to the given device id
    :param rois:
    """
    return getattr(ssocr, "ssocr_device_" + str(device_id))(rois)


def process_result(ocr_results):
    """

    :param ocr_results:
    :return:
    """
    return getattr(result_processor, "process_results_device_" + str(device_id))(ocr_results)


def speak_ocr_results(speak_text="Ansprakon bereit."):
    """
Calls nanoTTS in an subprocess. nanoTTS parses text to pico.
-l de-DE flag sets the language to german.
Volume & Speed & Pitch control with flags is possible, see man nanoTTS
    :param speak_text: this is the String from the ocr
    """
    global speak
    if speak:
        try:
            subprocess.call(["nanotts-git", "-v", lang, speak_text], stdout=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            print("Error code {} while speaking, output: {}".format(e.returncode, e.output))
    else:
        print("Not Speaking")
        pass


# boolean to hold the speaking again flag
speak = True
# variable to store last ocr string
text = ""


def ocr_and_speak():
    """
Read ssocr call into "new_text" and determine if the same text was read as in the last iteration.
Also speak the last text again  if "speak_again = True" was set.
    """
    global new_text
    new_text = process_result(
        run_ssocr(
            detect_feat(
                cut_roi(
                    preprocess_image(
                        grab_image()
                    )
                )
            )
        )
    )

    # flat_list = [item for sublist in new_text for item in sublist]
    # for text in flat_list:
    #     speak_ocr_results(text)

    # print(flat_list)


# Say "Ansprakon bereit" 1x time, to get audio feedback that the pi booted and AnSpraKon is running.
# speak_ocr_results()


def main():
    """

    """
    # read_counter = 0
    while True:
        ocr_and_speak()
        # read_counter += 1
        # print(read_counter, time.process_time(), gc.get_count(), gc.get_stats(), gc.get_debug())




if __name__ == "__main__":
    cam.start()
    main()
    cam.stop()
