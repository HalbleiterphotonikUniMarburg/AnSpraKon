# coding=utf-8
# AnSpraKon, reads 7-Segment-Displays and reads the result out loud.
# Copyright (C) 2018  Matthias Axel Kröll ansprakon@makroell.de
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>
import argparse
import call_nanotts
import cv2
import feat_detector
import image_preprocessor
import opencv_webcam_multithread
import result_processor
import roi_cutter
import sdnotify
import ssocr
import sys


class Ansprakon:
    def __init__(self, args):
        # cam setup
        self._cam_index = args.cam
        self._cam = opencv_webcam_multithread.WebcamVideoStream(src=self._cam_index).start()
        self._device_id = args.device
        self._final_result = args.final
        self._speak_on_button = args.button
        self._mute = args.mute

        # flags for nanoTTS
        self._nanotts_options = ["-v", args.language,
                                 "--speed", args.speed,
                                 "--pitch", args.pitch,
                                 "--volume", args.volume]
        # rpi GPIO setup
        self._on_pi = args.rpi
        if self._on_pi:
            # noinspection PyPep8Naming
            import RPi.GPIO as gpio
            self._gpio_pin = args.gpiopin
            gpio.setmode(gpio.BOARD)
            gpio.setwarnings(False)
            gpio.setup(self._gpio_pin, gpio.IN, pull_up_down=gpio.PUD_UP)
            gpio.add_event_detect(self._gpio_pin, gpio.FALLING, callback=self.gpio_callback, bouncetime=200)

        # storage for processing steps
        self._min_buffer_length = args.buffer[0]
        self._min_result_count = args.buffer[1]
        self._grabbed_image = None
        self._preprocessed_image = None
        self._rois_cut = None
        self._rois_processed = None
        self._results_processed = None
        self._result_buffer = []
        self._last_spoken = None

        # setup systemd communication
        self._sdnotify = sdnotify.SystemdNotifier()
        self._sdnotify.notify("READY=1")
        if not self._mute:
            call_nanotts.call_nanotts(self._nanotts_options)

    @property
    def sdnotify(self):
        return self._sdnotify

    def gpio_callback(self, channel):
        """
Callback for the GPIO-Event detection thread, calls nanoTTS if results exist.
        :param channel:
        """
        if len(self._result_buffer) >= 2:
            call_nanotts.call_nanotts(self._nanotts_options, max(set(self._result_buffer),
                                                                 key=self._result_buffer.count))

    def get_frame(self):
        """
Grabs an image from the cam thread, retries recursively on failing, to workaround cam issues.
        """
        try:
            self._grabbed_image = self._cam.read()
        except cv2.error as e:
            print(e)
            self.get_frame()

    # getattr() is used with the modules of the processing steps, this allows for modularization and avoids cluttering
    # This way allows having all device in one branch, instead of branching for every device and it allows device
    #  selection via flag

    def preprocess_image(self):
        """
Processes an Image with the methods defined for the device in image_preprocessor.py.
        """
        self._preprocessed_image = getattr(image_preprocessor, "image_device_" + self._device_id)(self._grabbed_image)

    def cut_rois(self):
        """
Cuts out Rois and perform additional processing as specified in roi_cutter.py.
Stores rois in _rois_processed as list of lists [[ocr-rois], [feat-rois]].
        """
        self._rois_cut = getattr(roi_cutter, "roi_device_" + self._device_id)(self._preprocessed_image)

    def run_ssocr(self):
        """
Calls ssocr with the options matching the device, specified in ssocr.py and stores the result in _rois_processed[0].
        """
        self._rois_processed = getattr(ssocr, "ssocr_device_" + self._device_id)(self._rois_cut)
        self._rois_cut[0] = self._rois_processed[0]

    def detect_feat(self):
        """
Detect features of the device as specified in feat_detector.py, if the device has features.
        """
        if len(self._rois_cut[1]) > 1:
            self._rois_processed = getattr(feat_detector, "feat_detect_device_" + self._device_id)(self._rois_cut)

    def process_result(self):
        """
Processes the results of ssocr.py and feat_detector.py as specified in result_processor.py.
        """
        self._results_processed = getattr(result_processor,
                                          "process_results_device_" + self._device_id)(self._rois_processed)
        if self._results_processed is not None:
            self._result_buffer.append(self._results_processed)
        # scrub result buffer if needed
        if len(self._result_buffer) > 30:
            self._result_buffer = self._result_buffer[-15:]

        print(self._results_processed)

    def speak_result(self):
        """
Speaks the result with call_nanotts if speaking is not by button and the result was not spoken max 3 read before.
Or if it is final result device, speake the result if it was read at least 5 times before.
        """

        # don't speak if muted via flag
        if self._mute:
            return print("Muted.", self._results_processed)

        # for speak on change devices
        if not self._speak_on_button and not self._final_result and self._results_processed is not None:
            if self._results_processed not in self._result_buffer[-3:-1] \
                    and self._results_processed != self._last_spoken:
                call_nanotts.call_nanotts(self._nanotts_options, self._results_processed)
                self._last_spoken = self._results_processed
                self.sdnotify.notify("Spoke: " + self._results_processed)

        # for final result devices
        if self._final_result and not self._speak_on_button and self._results_processed is not None:
            if len(self._result_buffer) >= self._min_buffer_length:
                if self._result_buffer[0:-1].count(self._results_processed) >= self._min_result_count \
                        and self._results_processed != self._last_spoken:
                    call_nanotts.call_nanotts(self._nanotts_options, self._results_processed)
                    self._last_spoken = self._results_processed
                    self.sdnotify.notify("Spoke: " + self._results_processed)

        else:
            print("Did not Speak.")


def main():
    """
Setup argument parser and then run the processing loop.
    """
    license_info = """
        AnSpraKon  Copyright (C) 2018  Matthias Axel Kröll
        This program comes with ABSOLUTELY NO WARRANTY; 
        This is free software, and you are welcome to redistribute it under certain conditions; 
        """
    print(license_info)

    parser = argparse.ArgumentParser(description="read 7-segment displays and read out the result")
    parser.add_argument("device", help="enter the ID of the device to use")
    parser.add_argument("-b", "--button", help="speak on button press", action="store_true")
    parser.add_argument("-m", "--mute", help="don't speak", action="store_true")
    parser.add_argument("-f", "--final", help="device which displays a final result", action="store_true")
    parser.add_argument("-r", "--rpi", help="run on rpi", action="store_true")
    parser.add_argument("-g", "--gpiopin", help="set the GPIO pin", default=11, type=int)
    parser.add_argument("-c", "--cam", help="set the device index of the cam to use", default=0, type=int)
    parser.add_argument("-s", "--speed", help="set speed of the voice", default="1.4", metavar="<0.2-5.0>")
    parser.add_argument("-p", "--pitch", help="set the pitch of the voice", default="0.8", metavar="<0.5-2.0>")
    parser.add_argument("-v", "--volume", help="set the volume of the voice", default="1", metavar="<0.0-5.0>")
    parser.add_argument("-l", "--language", help="set the language of the voice", default="de-DE",
                        choices=["en-US", "en-GB", "de-DE", "es-ES", "fr-FR", "it-IT"])
    parser.add_argument("-q", "--buffer",
                        help="min. bufferlength and min. result count to be the finalresult",
                        default=[8, 6], type=int, nargs="+")

    parser.add_argument("--version", action="version", version="%(AnSpraKon)s 2.0 ")
    parser.add_argument("--show-w", help="Show warranty details of the GPL", action="store_true")
    parser.add_argument("--show-c", help="Show redistribution conditions of the GPL", action="store_true")

    args = parser.parse_args()

    ansprakon = Ansprakon(args)

    while True:
        # try:
        ansprakon.get_frame()
        ansprakon.preprocess_image()
        ansprakon.cut_rois()
        ansprakon.run_ssocr()
        ansprakon.detect_feat()
        ansprakon.process_result()
        ansprakon.speak_result()
        ansprakon.sdnotify.notify("WATCHDOG=1")
        # except:
        #     print("Unexpected error:", sys.exc_info()[0])


if __name__ == "__main__":
    main()
