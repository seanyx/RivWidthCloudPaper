# #!/usr/bin/env python2
# # -*- coding: utf-8 -*-
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
# Note: THIS IS A PRERELEASE VERSION (Edited on: 2019/02/18)

import ee
import numpy as np
import math
import sys

def GetCenterline(bound):
	"""clip the GRWL centerline based on the input geometry
	"""
	centerLineData = ee.FeatureCollection("users/eeProject/GRWL_summaryStats")
	cl = (ee.FeatureCollection(centerLineData).filterBounds(bound)
    .filterMetadata('lakeFlag', 'equals', 0))
	return cl

def ExtractChannel(image, centerline, bound, maxDistance, LR):
    """extract the channels from the water mask, using
    the GRWL centerline.
    LR controls whether to use a low resolution version of water to speed up the
    cumulativeCost calculation.
    """

    waterMask = image.select(['waterMask'])

    if (LR):
        waterMask = (image.select(['waterMask']).reduceResolution(
            reducer = ee.Reducer.max(),
            bestEffort = True,
            maxPixels = 64
        ))

    cost = waterMask.Not().cumulativeCost(ee.Image().toByte().paint(centerline, 1).And(waterMask), maxDistance) # only use the centerline that overlaps with the water mask

    channelMask = cost.eq(0).unmask(0).clip(bound).rename(['channelMask'])
    channel = image.select(['waterMask']).mask(channelMask).unmask(0)
    return channel

def ExtractRiver_mapVersion(image):
    """extract the river from the water mask, using the GRWL centerline.
    """
    bound = image.geometry()
    centerline = GetCenterline(bound)
    waterMask = image.select(['waterMask'])

    cost = waterMask.Not().cumulativeCost(ee.Image().toByte().paint(centerline, 15).And(waterMask), 4000) # only use the centerline that overlaps with the water mask
    channelMask = cost.eq(0).unmask(0).clip(bound).rename(['channelMask'])
    channel = image.select(['waterMask']).mask(channelMask).unmask(0)

    fill = (channel.Not()).mask(channel.Not()).connectedPixelCount(333).lt(333).unmask(0)
    river = channel.where(fill, ee.Image(1))

    return river

def hitOrMiss(image, se1, se2):
    """perform hitOrMiss transform (adapted from [citation])
    """
    e1 = image.reduceNeighborhood(ee.Reducer.min(), se1)
    e2 = image.Not().reduceNeighborhood(ee.Reducer.min(), se2)
    return e1.And(e2)

def splitKernel(kernel, value):
    """recalculate the kernel according to the given foreground value
    """
    kernel = np.array(kernel)
    result = kernel
    r = 0
    while (r < kernel.shape[0]):
        c = 0
        while (c < kernel.shape[1]):
            if kernel[r][c] == value:
                result[r][c] = 1
            else:
                result[r][c] = 0
            c = c + 1
        r = r + 1
    return result.tolist()

def Skeletonize(image, iterations, method):
    """perform skeletonization
    """

    se1w = [[2, 2, 2], [0, 1, 0], [1, 1, 1]]

    if (method == 2):
        se1w = [[2, 2, 2], [0, 1, 0], [0, 1, 0]]

    se11 = ee.Kernel.fixed(3, 3, splitKernel(se1w, 1))
    se12 = ee.Kernel.fixed(3, 3, splitKernel(se1w, 2))

    se2w = [[2, 2, 0], [2, 1, 1], [0, 1, 0]]

    if (method == 2):
        se2w = [[2, 2, 0], [2, 1, 1], [0, 1, 1]]

    se21 = ee.Kernel.fixed(3, 3, splitKernel(se2w, 1))
    se22 = ee.Kernel.fixed(3, 3, splitKernel(se2w, 2))

    result = image

    i = 0
    while (i < iterations):
        j = 0
        while (j < 4):
              result = result.subtract(hitOrMiss(result, se11, se12))
              se11 = se11.rotate(1)
              se12 = se12.rotate(1)
              result = result.subtract(hitOrMiss(result, se21, se22))
              se21 = se21.rotate(1)
              se22 = se22.rotate(1)
              j = j + 1
        i = i + 1

    return result.rename(['clRaw'])

def ExtractEndpoints(CL1px):
    """calculate end points in the one pixel centerline
    """

    se1w = [[0, 0, 0], [2, 1, 2], [2, 2, 2]]

    se11 = ee.Kernel.fixed(3, 3, splitKernel(se1w, 1))
    se12 = ee.Kernel.fixed(3, 3, splitKernel(se1w, 2))

    result = CL1px

    # // the for loop removes the identified endpoints from the imput image
    i = 0
    while (i<4): # rotate kernels
        result = result.subtract(hitOrMiss(CL1px, se11, se12))
        se11 = se11.rotate(1)
        se12 = se12.rotate(1)
        i = i + 1
    endpoints = CL1px.subtract(result)
    return endpoints

def ExtractEndpointsToKeep(CL1px):
    """calculate end points in the one pixel centerline
    """

    se1w = [[1, 2, 1], [2, 1, 2], [2, 2, 2]]

    se11 = ee.Kernel.fixed(3, 3, splitKernel(se1w, 1))
    se12 = ee.Kernel.fixed(3, 3, splitKernel(se1w, 2))

    result = CL1px

    # // the for loop removes the identified endpoints from the imput image
    i = 0
    while (i<4): # rotate kernels
        result = result.subtract(hitOrMiss(CL1px, se11, se12))
        se11 = se11.rotate(1)
        se12 = se12.rotate(1)
        i = i + 1
    endpoints = CL1px.subtract(result)
    return endpoints

# def ExtractEndpoints(CL1px):
#     """calculate end points in the one pixel centerline
#     """
#
#     se1w = [[1, 1, 1], [2, 1, 2], [2, 2, 2]]
#
#     se11 = ee.Kernel.fixed(3, 3, splitKernel(se1w, 1))
#     se12 = ee.Kernel.fixed(3, 3, splitKernel(se1w, 2))
#
#     result = CL1px
#
#     # // the for loop removes the identified endpoints from the imput image
#     i = 0
#     while (i<4): # rotate kernels
#         result = result.subtract(hitOrMiss(result, se11, se12))
#         se11 = se11.rotate(1)
#         se12 = se12.rotate(1)
#         i = i + 1
#     endpoints = CL1px.subtract(result)
#     return endpoints

def ExtractCorners(CL1px):
    """calculate corners in the one pixel centerline
    """

    se1w = [[2, 2, 0], [2, 1, 1], [0, 1, 0]]

    se11 = ee.Kernel.fixed(3, 3, splitKernel(se1w, 1))
    se12 = ee.Kernel.fixed(3, 3, splitKernel(se1w, 2))

    result = CL1px
    # // the for loop removes the identified corners from the imput image

    i = 0
    while(i < 4): # rotate kernels

        result = result.subtract(hitOrMiss(result, se11, se12))

        se11 = se11.rotate(1)
        se12 = se12.rotate(1)

        i = i + 1

    cornerPoints = CL1px.subtract(result)
    return cornerPoints

def ExtractTu(CL1px):
    """calculate corners in the one pixel centerline
    """

    se1w = [[2, 1, 2], [1, 1, 1], [0, 0, 0]]

    se11 = ee.Kernel.fixed(3, 3, splitKernel(se1w, 1))
    se12 = ee.Kernel.fixed(3, 3, splitKernel(se1w, 2))

    result = CL1px
    # // the for loop removes the identified corners from the imput image

    i = 0
    while(i < 4): # rotate kernels

        result = result.subtract(hitOrMiss(result, se11, se12))

        se11 = se11.rotate(1)
        se12 = se12.rotate(1)

        i = i + 1

    tuPoints = CL1px.subtract(result)
    return tuPoints

def OnePixelCenterline(img, FDTneighborhoodSize, gradMethod, hGrad, scale):
    """calculate the 1px centerline from:
	1. fast distance transform of the river banks
	2. gradient of the distance transform, mask areas where gradient greater than a threshold hGrad
	3. thin twice to get a 1px centerline
    """

    ## calculate the river banks
    imgD2 = img.focal_max(1.5, 'circle', 'pixels', 2)
    imgD1 = img.focal_max(1.5, 'circle', 'pixels', 1)
    outline = imgD2.subtract(imgD1)

    dpixel = outline.fastDistanceTransform(FDTneighborhoodSize).sqrt()
    dmeters = dpixel.multiply(scale) # for a given scale
    DM = dmeters.mask(dmeters.lte(FDTneighborhoodSize * scale).And(imgD2))

    ## Calculate the gradient
    if (gradMethod == 1): # GEE .gradient() method
        grad = DM.gradient()
        dx = grad.select('x')
        dy = grad.select('y')
        g = dx.multiply(dx).add(dy.multiply(dy)).sqrt()

    if (gradMethod == 2): # Gena's method
        k_dx = ee.Kernel.fixed(3, 3, [[ 1.0/8, 0.0, -1.0/8], [ 2.0/8, 0.0, -2.0/8], [ 1.0/8,  0.0, -1.0/8]])
        k_dy = ee.Kernel.fixed(3, 3, [[ -1.0/8, -2.0/8, -1.0/8], [ 0.0, 0.0, 0.0], [ 1.0/8, 2.0/8, 1.0/8]])
        dx = DM.convolve(k_dx)
        dy = DM.convolve(k_dy)
        g = dx.multiply(dx).add(dy.multiply(dy)).divide(scale * scale).sqrt()

    if (gradMethod == 3): # RivWidth method
        k_dx = ee.Kernel.fixed(3, 1, [[-0.5, 0.0, 0.5]])
        k_dy = ee.Kernel.fixed(1, 3, [[0.5], [0.0], [-0.5]])
        dx = DM.convolve(k_dx)
        dy = DM.convolve(k_dy)
        g = dx.multiply(dx).add(dy.multiply(dy)).divide(scale * scale)

    cl = g.mask(imgD2).lte(hGrad).And(img)

    ## skeletonization
    cl1px = Skeletonize(cl, 2, 1)

    return cl1px.addBands(DM)

def CleanCenterline(cl1px, maxBranchLengthToRemove, rmCorners):
    """clean the 1px centerline:
	1. remove branches
	2. remove corners to insure 1px width (optional)
    """

    # tu = ExtractTu(cl1px)
    # cl1px = cl1px.updateMask(tu.Not())

    ## find the number of connecting pixels (8-connectivity)
    nearbyPoints = (cl1px.mask(cl1px).reduceNeighborhood(
        reducer = ee.Reducer.count(),
        kernel = ee.Kernel.circle(1.5),
        skipMasked = True))

	## define ends
    endsByNeighbors = nearbyPoints.lte(2)

	## define joint points
    joints = nearbyPoints.gte(4)


    costMap = (cl1px.mask(cl1px).updateMask(joints.Not()).cumulativeCost(
        source = endsByNeighbors.mask(endsByNeighbors),
        maxDistance = maxBranchLengthToRemove,
        geodeticDistance = True))

    branchMask = costMap.gte(0).unmask(0)
    cl1Cleaned = cl1px.updateMask(branchMask.Not()) # mask short branches;

    ends = ExtractEndpoints(cl1Cleaned)

    endsToKeep = ExtractEndpointsToKeep(cl1Cleaned)

    cl1Cleaned = cl1Cleaned.updateMask(ends.Not().Or(endsToKeep))
    # cl1Cleaned = cl1Cleaned.subtract(ends).add(endsToKeep)

    if (rmCorners):
        corners = ExtractCorners(cl1Cleaned)
        cl1Cleaned = cl1Cleaned.updateMask(corners.Not())
        # cl1Cleaned = cl1Cleaned.subtract(corners)

    return cl1Cleaned


def CalculateAngle(clCleaned):
    """calculate the orthogonal direction of each pixel of the centerline
    """

    w3 = (ee.Kernel.fixed(9, 9, [
    [135.0, 126.9, 116.6, 104.0, 90.0, 76.0, 63.4, 53.1, 45.0],
    [143.1, 0.0,	0.0,	0.0,	0.0,	0.0,	0.0,	0.0, 36.9],
    [153.4, 0.0,	0.0,	0.0,	0.0,	0.0,	0.0,	0.0, 26.6],
    [166.0, 0.0,	0.0,	0.0,	0.0,	0.0,	0.0,	0.0, 14.0],
    [180.0, 0.0,	0.0,	0.0,	0.0,	0.0,	0.0,	0.0, 1e-5],
    [194.0, 0.0,	0.0,	0.0,	0.0,	0.0,	0.0,	0.0, 346.0],
    [206.6, 0.0,	0.0,	0.0,	0.0,	0.0,	0.0,	0.0, 333.4],
    [216.9, 0.0,	0.0,	0.0,	0.0,	0.0,	0.0,	0.0, 323.1],
    [225.0, 233.1,  243.4,  256.0,  270.0,  284.0,  296.6,  306.9, 315.0]]))

    combinedReducer = ee.Reducer.sum().combine(ee.Reducer.count(), None, True)

    clAngle = (clCleaned.mask(clCleaned)
        .rename(['clCleaned'])
        .reduceNeighborhood(
        reducer = combinedReducer,
        kernel = w3,
        inputWeight = 'kernel',
        skipMasked = True))

	## mask calculating when there are more than two inputs into the angle calculation
    clAngleNorm = (clAngle
        .select('clCleaned_sum')
        .divide(clAngle.select('clCleaned_count'))
        .mask(clAngle.select('clCleaned_count').gt(2).Not()))

	## if only one input into the angle calculation, rotate it by 90 degrees to get the orthogonal
    clAngleNorm = (clAngleNorm
        .where(clAngle.select('clCleaned_count').eq(1), clAngleNorm.add(ee.Image(90))))

    return clAngleNorm.rename(['orthDegree'])

def GetWidth(clAngleNorm, riverWithCloud, endInfo, MD, crs, bound, scale, sceneID, note):
    """calculate the width of the river at each centerline pixel, measured according to the orthgonal direction of the river
    """
    def GetXsectionEnds(f):
        xc = ee.Number(f.get('x'))
        yc = ee.Number(f.get('y'))
        orthRad = ee.Number(f.get('angle')).divide(180).multiply(math.pi)

        width = ee.Number(f.get('toBankDistance')).multiply(1.3)
        cosRad = width.multiply(orthRad.cos())
        sinRad = width.multiply(orthRad.sin())
        p1 = ee.Geometry.Point([xc.add(cosRad), yc.add(sinRad)], crs)
        p2 = ee.Geometry.Point([xc.subtract(cosRad), yc.subtract(sinRad)], crs)

        xlEnds = (ee.Feature(ee.Geometry.MultiPoint([p1, p2]).buffer(30), {
            'xc': xc,
            'yc': yc,
            'lon': f.get('lon'),
            'lat': f.get('lat'),
            'orthRad': orthRad,
            'MLength': width.multiply(2),
            'p1': p1,
            'p2': p2,
            'crs': crs,
            'sceneID': sceneID,
            'note': note
            }))

        return xlEnds

    def SwitchGeometry(f):
        return (f
        .setGeometry(ee.Geometry.LineString([f.get('p1'), f.get('p2')]).buffer(30))
        .set('p1', None).set('p2', None)) # remove p1 and p2

    ## convert centerline image to a list. prepare for map function
    clPoints = (clAngleNorm.rename(['angle'])
    	.addBands(ee.Image.pixelCoordinates(crs))
        .addBands(ee.Image.pixelLonLat().rename(['lon', 'lat']))
        .addBands(MD.rename(['toBankDistance']))
        .sample(
            region = bound,
            scale = scale,
            projection = None,
            factor = 1,
            dropNulls = True
        ))

	## calculate the cross-section lines, returning a featureCollection
    xsectionsEnds = clPoints.map(GetXsectionEnds)

	## calculate the flags at the xsection line end points
    endStat = (endInfo.reduceRegions(
        collection = xsectionsEnds,
        reducer = ee.Reducer.anyNonZero(), # test endpoints type
        scale = scale,
        crs = crs))

	## calculate the width of the river and other flags along the xsection lines
    xsections1 = endStat.map(SwitchGeometry)
    combinedReducer = ee.Reducer.mean().combine(ee.Reducer.stdDev(), None, True)
    xsections = (riverWithCloud.reduceRegions(
        collection = xsections1,
        reducer = combinedReducer,
        scale = scale,
        crs = crs))

    return xsections

def RemoveGeometry(f):
    """remove the geometry of a feature
    """
    return ee.Feature(f).setGeometry(None)

def maximum_no_of_tasks(MaxNActive, waitingPeriod):
	"""maintain a maximum number of active tasks
	"""
	import time
	import ee
	ee.Initialize()

	time.sleep(10)
	## initialize submitting jobs
	ts = list(ee.batch.Task.list())

	NActive = 0
	for task in ts:
		if ('RUNNING' in str(task) or 'READY' in str(task)):
			NActive += 1
	## wait if the number of current active tasks reach the maximum number
	## defined in MaxNActive
	while (NActive >= MaxNActive):
		time.sleep(waitingPeriod) # if reach or over maximum no. of active tasks, wait for 2min and check again
		ts = list(ee.batch.Task.list())
		NActive = 0
		for task in ts:
			if ('RUNNING' in str(task) or 'READY' in str(task)):
				NActive += 1
	return()
