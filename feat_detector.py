# coding=utf-8
# This file is part of AnSpraKon.
#
#     AnSpraKon is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     AnSpraKon is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with AnSpraKon.  If not, see <http://www.gnu.org/licenses/>.
import cv2


def feat_detect_device_0(feat_rois):
    """
    Dummy Device
    :param feat_rois:
    :return:
    """
    counter = 0
    for _ in feat_rois[1]:
        feat_rois[1][counter] = True
        counter += 1
    return feat_rois


def feat_detect_device_1(feat_rois):
    """
BASETECH thermometer
    :param feat_rois:
    :return:
    """
    return feat_rois


def feat_detect_device_2(feat_rois):
    """
ADE humanscale
    :param feat_rois:
    :return:
    """
    return feat_rois


def feat_detect_device_3(feat_rois):
    """
beurer humanscale
    :param feat_rois:
    :return:
    """
    return feat_rois


def feat_detect_device_4(feat_rois):
    """
NONAME indoor/outdoor thermometer
    :param feat_rois:
    :return:
    """
    # check if mean is not white to detemine if feature is present
    for i in range(len(feat_rois[1])):
        feat_rois[1][i] = True if cv2.mean(feat_rois[1][i])[0] <= 240 else False

    # print(feat_rois[1])
    return feat_rois


def feat_detect_device_5(feat_rois):
    """
GREEN alarm/radio
    :param feat_rois:
    :return:
    """
    return feat_rois


def feat_detect_device_6(feat_rois):
    """
NONAME thermo-hygro
    :param feat_rois:
    :return:
    """
    # check if mean is not white to detemine if feature is present
    for i in range(len(feat_rois[1])):
        feat_rois[1][i] = True if cv2.mean(feat_rois[1][i])[0] <= 240 else False

    # print(feat_rois[1])
    return feat_rois


def feat_detect_device_7(feat_rois):
    """
GREEN alarm/radio
    :param feat_rois:
    :return:
    """

    return feat_rois


def feat_detect_device_8(feat_rois):
    """
IDR alarm/radio
    :param feat_rois:
    :return:
    """
    for i in range(len(feat_rois[1])):
        feat_rois[1][i] = True if cv2.mean(feat_rois[1][i])[0] <= 240 else False

    print(feat_rois[1])
    return feat_rois



def feat_detect_device_9(feat_rois):
    """
Schneider Microwave
    :param feat_rois:
    :return:
    """

    # check if mean is not white to detemine if feature is present
    for i in range(len(feat_rois[1])):
        feat_rois[1][i] = True if cv2.mean(feat_rois[1][i])[0] <= 240 else False

    print(feat_rois[1])
    return feat_rois


def feat_detect_device_11(feat_rois):
    """
SEVERIN Microwave
    :param feat_rois:
    :return:
    """

    # check if mean is not white to detemine if feature is present
    for i in range(len(feat_rois[1])):
        feat_rois[1][i] = True if cv2.mean(feat_rois[1][i])[0] <= 240 else False

    print(feat_rois[1])
    return feat_rois


def feat_detect_device_12(feat_rois):
    """
Bloodpressure
    :param feat_rois:
    :return:
    """
    return feat_rois
