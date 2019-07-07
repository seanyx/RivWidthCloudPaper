# /* water test functions for determing DSWE
# see https://github.com/USGS-EROS/espa-surface-water-extent/blob/master/dswe/algorithm-description.md
# */
import ee

def Mndwi(image):
    return(image.normalizedDifference(['Green', 'Swir1']).rename('mndwi'))

def Mbsrv(image):
    return(image.select(['Green']).add(image.select(['Red'])).rename('mbsrv'))

def Mbsrn(image):
    return(image.select(['Nir']).add(image.select(['Swir1'])).rename('mbsrn'))

def Ndvi(image):
    return(image.normalizedDifference(['Nir', 'Red']).rename('ndvi'))

def Awesh(image):
    return(image.expression('Blue + 2.5 * Green + (-1.5) * mbsrn + (-0.25) * Swir2', {
    'Blue': image.select(['Blue']),
    'Green': image.select(['Green']),
    'mbsrn': Mbsrn(image).select(['mbsrn']),
    'Swir2': image.select(['Swir2'])}))

def Dswe(i):
    mndwi = Mndwi(i)
    mbsrv = Mbsrv(i)
    mbsrn = Mbsrn(i)
    awesh = Awesh(i)
    swir1 = i.select(['Swir1'])
    nir = i.select(['Nir'])
    ndvi = Ndvi(i)
    blue = i.select(['Blue'])
    swir2 = i.select(['Swir2'])

    t1 = mndwi.gt(0.124)
    t2 = mbsrv.gt(mbsrn)
    t3 = awesh.gt(0)
    t4 = (mndwi.gt(-0.44)
    .And(swir1.lt(900))
    .And(nir.lt(1500))
    .And(ndvi.lt(0.7)))
    t5 = (mndwi.gt(-0.5)
    .And(blue.lt(1000))
    .And(swir1.lt(3000))
    .And(swir2.lt(1000))
    .And(nir.lt(2500)))

    t = t1.add(t2.multiply(10)).add(t3.multiply(100)).add(t4.multiply(1000)).add(t5.multiply(10000))

    noWater = (t.eq(0)
    .Or(t.eq(1))
    .Or(t.eq(10))
    .Or(t.eq(100))
    .Or(t.eq(1000)))
    hWater = (t.eq(1111)
    .Or(t.eq(10111))
    .Or(t.eq(11011))
    .Or(t.eq(11101))
    .Or(t.eq(11110))
    .Or(t.eq(11111)))
    mWater = (t.eq(111)
    .Or(t.eq(1011))
    .Or(t.eq(1101))
    .Or(t.eq(1110))
    .Or(t.eq(10011))
    .Or(t.eq(10101))
    .Or(t.eq(10110))
    .Or(t.eq(11001))
    .Or(t.eq(11010))
    .Or(t.eq(11100)))
    pWetland = t.eq(11000)
    lWater = (t.eq(11)
    .Or(t.eq(101))
    .Or(t.eq(110))
    .Or(t.eq(1001))
    .Or(t.eq(1010))
    .Or(t.eq(1100))
    .Or(t.eq(10000))
    .Or(t.eq(10001))
    .Or(t.eq(10010))
    .Or(t.eq(10100)))

    iDswe = (noWater.multiply(0)
    .add(hWater.multiply(1))
    .add(mWater.multiply(2))
    .add(pWetland.multiply(3))
    .add(lWater.multiply(4)))

    return(iDswe.rename(['dswe']))

def ClassifyWaterJones2019(img):
    dswe = Dswe(img)
    waterMask = dswe.eq(1).Or(dswe.eq(2)).rename(['waterMask'])
    return(waterMask)
