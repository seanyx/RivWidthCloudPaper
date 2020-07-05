import ee
import math
import numpy as np

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

def CalcDistanceMap(img, neighborhoodSize, scale):
    # // assign each river pixel with the distance (in meter) between itself and the closest non-river pixel
    imgD2 = img.focal_max(1.5, 'circle', 'pixels', 2)
    imgD1 = img.focal_max(1.5, 'circle', 'pixels', 1)
    outline = imgD2.subtract(imgD1)

    dpixel = outline.fastDistanceTransform(neighborhoodSize).sqrt()
    dmeters = dpixel.multiply(scale) #// for a given scale
    DM = dmeters.mask(dpixel.lte(neighborhoodSize).And(imgD2))

    return(DM)

def CalcGradientMap(image, gradMethod, scale):
    ## Calculate the gradient
    if (gradMethod == 1): # GEE .gradient() method
        grad = image.gradient()
        dx = grad.select(['x'])
        dy = grad.select(['y'])
        g = dx.multiply(dx).add(dy.multiply(dy)).sqrt()

    if (gradMethod == 2): # Gena's method
        k_dx = ee.Kernel.fixed(3, 3, [[ 1.0/8, 0.0, -1.0/8], [ 2.0/8, 0.0, -2.0/8], [ 1.0/8,  0.0, -1.0/8]])
        k_dy = ee.Kernel.fixed(3, 3, [[ -1.0/8, -2.0/8, -1.0/8], [ 0.0, 0.0, 0.0], [ 1.0/8, 2.0/8, 1.0/8]])
        dx = image.convolve(k_dx)
        dy = image.convolve(k_dy)
        g = dx.multiply(dx).add(dy.multiply(dy)).divide(scale.multiply(scale)).sqrt()

    if (gradMethod == 3): # RivWidth method
        k_dx = ee.Kernel.fixed(3, 1, [[-0.5, 0.0, 0.5]])
        k_dy = ee.Kernel.fixed(1, 3, [[0.5], [0.0], [-0.5]])
        dx = image.convolve(k_dx)
        dy = image.convolve(k_dy)
        g = dx.multiply(dx).add(dy.multiply(dy)).divide(scale.multiply(scale))

    return(g)

def CalcOnePixelWidthCenterline(img, GM, hGrad):
    # /***
    # calculate the 1px centerline from:
    # 1. fast distance transform of the river banks
    # 2. gradient of the distance transform, mask areas where gradient greater than a threshold hGrad
    # 3. apply skeletonization twice to get a 1px centerline
    # thresholding gradient map inspired by Pavelsky and Smith., 2008
    # ***/

    imgD2 = img.focal_max(1.5, 'circle', 'pixels', 2)
    cl = ee.Image(GM).mask(imgD2).lte(hGrad).And(img)
    # // apply skeletonization twice
    cl1px = Skeletonize(cl, 2, 1)
    return(cl1px)

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

def CleanCenterline(cl1px, maxBranchLengthToRemove, rmCorners):
    """clean the 1px centerline:
	1. remove branches
	2. remove corners to insure 1px width (optional)
    """

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
    cl1Cleaned = cl1Cleaned.updateMask(ends.Not())

    if (rmCorners):
        corners = ExtractCorners(cl1Cleaned)
        cl1Cleaned = cl1Cleaned.updateMask(corners.Not())

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

def GetWidth(clAngleNorm, segmentInfo, endInfo, DM, crs, bound, scale, sceneID, note):
    """calculate the width of the river at each centerline pixel, measured according to the orthgonal direction of the river
    """
    def GetXsectionEnds(f):
        xc = ee.Number(f.get('x'))
        yc = ee.Number(f.get('y'))
        orthRad = ee.Number(f.get('angle')).divide(180).multiply(math.pi)

        width = ee.Number(f.get('toBankDistance')).multiply(1.5)
        cosRad = width.multiply(orthRad.cos())
        sinRad = width.multiply(orthRad.sin())
        p1 = ee.Geometry.Point([xc.add(cosRad), yc.add(sinRad)], crs)
        p2 = ee.Geometry.Point([xc.subtract(cosRad), yc.subtract(sinRad)], crs)

        xlEnds = (ee.Feature(ee.Geometry.MultiPoint([p1, p2]).buffer(30), {
            'xc': xc,
            'yc': yc,
            'longitude': f.get('lon'),
            'latitude': f.get('lat'),
            'orthogonalDirection': orthRad,
            'MLength': width.multiply(2),
            'p1': p1,
            'p2': p2,
            'crs': crs,
            'image_id': sceneID,
            'note': note
            }))

        return xlEnds

    def SwitchGeometry(f):
        return (f
        .setGeometry(ee.Geometry.LineString(coords = [f.get('p1'), f.get('p2')], proj = crs, geodesic = False))
        .set('p1', None).set('p2', None)) # remove p1 and p2

    ## convert centerline image to a list. prepare for map function
    clPoints = (clAngleNorm.rename(['angle'])
    	.addBands(ee.Image.pixelCoordinates(crs))
        .addBands(ee.Image.pixelLonLat().rename(['lon', 'lat']))
        .addBands(DM.rename(['toBankDistance']))
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
        reducer = ee.Reducer.anyNonZero().combine(ee.Reducer.count(), None, True), # test endpoints type
        scale = scale,
        crs = crs))

	## calculate the width of the river and other flags along the xsection lines
    xsections1 = endStat.map(SwitchGeometry)
    combinedReducer = ee.Reducer.mean()
    xsections = (segmentInfo.reduceRegions(
        collection = xsections1,
        reducer = combinedReducer,
        scale = scale,
        crs = crs))

    return xsections

def CalculateCenterline(imgIn):

    crs = imgIn.get('crs')
    scale = ee.Number(imgIn.get('scale'))
    riverMask = imgIn.select(['riverMask'])

    distM = CalcDistanceMap(riverMask, 256, scale)
    gradM = CalcGradientMap(distM, 2, scale)
    cl1 = CalcOnePixelWidthCenterline(riverMask, gradM, 0.9)
    cl1Cleaned1 = CleanCenterline(cl1, 300, True)
    cl1px = CleanCenterline(cl1Cleaned1, 300, False)

    imgOut = (imgIn
    .addBands(cl1px.rename(['cleanedCL']))
    .addBands(cl1.rename(['rawCL']))
    .addBands(gradM.rename(['gradientMap']))
    .addBands(distM.rename(['distanceMap'])))

    return(imgOut)

def CalculateOrthAngle(imgIn):
    cl1px = imgIn.select(['cleanedCL'])
    angle = CalculateAngle(cl1px)
    imgOut = imgIn.addBands(angle)
    return(imgOut)

def prepExport(f):
    f = (f.set({
        'width': ee.Number(f.get('MLength')).multiply(f.get('channelMask')),
        'endsInWater': ee.Number(f.get('any')).eq(1),
        'endsOverEdge': ee.Number(f.get('count')).lt(2)}))

    fOut = (ee.Feature(ee.Geometry.Point([f.get('longitude'), f.get('latitude')]), {})
    .copyProperties(f, None, ['any', 'count', 'MLength', 'xc', 'yc', 'channelMask']))
    return(fOut)

def CalculateWidth(imgIn):
    crs = imgIn.get('crs')
    scale = imgIn.get('scale')
    imgId = imgIn.get('image_id')
    bound = imgIn.select(['riverMask']).geometry()
    angle = imgIn.select(['orthDegree'])
    dem = ee.Image("users/eeProject/MERIT")
    infoEnds = imgIn.select(['riverMask'])
    infoExport = (imgIn.select('channelMask')
    .addBands(imgIn.select('^flag.*'))
    .addBands(dem.rename(['flag_elevation'])))
    dm = imgIn.select(['distanceMap'])

    widths = GetWidth(angle, infoExport, infoEnds, dm, crs, bound, scale, imgId, '').map(prepExport)

    return(widths)
