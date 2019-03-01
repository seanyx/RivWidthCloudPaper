# /*
# MIT License
#
# Copyright (c) [2018] [Xiao Yang]
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# Original Author:  Xiao Yang, UNC Chapel Hill, United States
# Contact: yangxiao@live.unc.edu
# Contributing Authors:
# Tamlin Pavelsky, UNC Chapel Hill, United States
# George Allen, Texas A&M, United States
# Genna Dontchyts, Deltares, NL
#
# NOTE: THIS IS A PRERELEASE VERSION (Edited on: 2019/02/18)
# */

# /* functions to extract river mask */
import ee

def GetCenterline(clDataset, bound):
    # // filter the GRWL centerline based on area of interest
    cl = clDataset.filterBounds(bound)
    return(cl)

def ExtractChannel(image, centerline, maxDistance):
    # // extract the channel water bodies from the water mask, based on connectivity to the reference centerline.
    connectedToCl = (image.Not().cumulativeCost(
        source = ee.Image().toByte().paint(centerline, 1).And(image), #// only use the centerline that overlaps with the water mask
        maxDistance = maxDistance,
        geodeticDistance = False).eq(0))

    channel = image.updateMask(connectedToCl).unmask(0).updateMask(image.gte(0)).rename(['channelMask'])
    return(channel)

def RemoveIsland(channel, FILL_SIZE):
    # /* fill in island as water if the size (number of pixels) of the island is smaller than FILL_SIZE */
    fill = channel.Not().selfMask().connectedPixelCount(FILL_SIZE).lt(FILL_SIZE)
    river = channel.where(fill, ee.Image(1)).rename(['riverMask'])
    return(river)

def ExtractRiver(imgIn, clData, maxDist, minIslandRemoval):
    waterMask = imgIn.select(['waterMask'])
    bound = waterMask.geometry()
    cl = GetCenterline(clData, bound)
    channelMask = ExtractChannel(waterMask, cl, maxDist)
    riverMask = RemoveIsland(channelMask, minIslandRemoval)
    return(imgIn.addBands(channelMask).addBands(riverMask))
