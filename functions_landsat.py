import ee

def merge_collections_std_bandnames_collection1tier1_sr():
    """merge landsat 5, 7, 8 collection 1 tier 1 SR imageCollections and standardize band names
    """
    ## standardize band names
    bn8 = ['B1', 'B2', 'B3', 'B4', 'B6', 'pixel_qa', 'B5', 'B7']
    bn7 = ['B1', 'B1', 'B2', 'B3', 'B5', 'pixel_qa', 'B4', 'B7']
    bn5 = ['B1', 'B1', 'B2', 'B3', 'B5', 'pixel_qa', 'B4', 'B7']
    bns = ['uBlue', 'Blue', 'Green', 'Red', 'Swir1', 'BQA', 'Nir', 'Swir2']

    # create a merged collection from landsat 5, 7, and 8
    ls5 = ee.ImageCollection("LANDSAT/LT05/C01/T1_SR").select(bn5, bns)

    ls7 = (ee.ImageCollection("LANDSAT/LE07/C01/T1_SR")
           .filterDate('1999-04-15', '2003-05-30')
           .select(bn7, bns))

    ls8 = ee.ImageCollection("LANDSAT/LC08/C01/T1_SR").select(bn8, bns)

    merged = ls5.merge(ls7).merge(ls8)

    return(merged)

def id2Img(id):
    return(ee.Image(merge_collections_std_bandnames_collection1tier1_sr()
    .filterMetadata('LANDSAT_ID', 'equals', id)
    .first()))

def Unpack(bitBand, startingBit, bitWidth):
    # unpacking bit bands
    # see: https://groups.google.com/forum/#!starred/google-earth-engine-developers/iSV4LwzIW7A
    return (ee.Image(bitBand)
            .rightShift(startingBit)
            .bitwiseAnd(ee.Number(2).pow(ee.Number(bitWidth)).subtract(ee.Number(1)).int()))
def UnpackAllSR(bitBand):
    # apply Unpack function for multiple pixel qualities
    bitInfoSR = {
    'Cloud': [5, 1],
    'CloudShadow': [3, 1],
    'SnowIce': [4, 1],
    'Water': [2, 1]
    }
    unpackedImage = ee.Image.cat([Unpack(bitBand, bitInfoSR[key][0], bitInfoSR[key][1]).rename([key]) for key in bitInfoSR])
    return unpackedImage
def AddFmaskSR(image):
    # // add fmask as a separate band to the input image
    temp = UnpackAllSR(image.select(['BQA']))

    fmask = (temp.select(['Water']).rename(['fmask'])
    .where(temp.select(['SnowIce']), ee.Image(3))
    .where(temp.select(['CloudShadow']), ee.Image(2))
    .where(temp.select(['Cloud']), ee.Image(4))
    .mask(temp.select(['Cloud']).gte(0)))

    return image.addBands(fmask)

def CalcHillShadowSR(image):
    dem = ee.Image("users/eeProject/MERIT").clip(image.geometry().buffer(9000).bounds())
    SOLAR_AZIMUTH_ANGLE = ee.Number(image.get('SOLAR_AZIMUTH_ANGLE'))
    SOLAR_ZENITH_ANGLE = ee.Number(image.get('SOLAR_ZENITH_ANGLE'))

    return(ee.Terrain.hillShadow(dem, SOLAR_AZIMUTH_ANGLE, SOLAR_ZENITH_ANGLE, 100, True)
    .reproject("EPSG:4326", None, 90).rename(['hillshadow']))

# /* functions to classify water (default) */
def ClassifyWater(imgIn, method = 'Jones2019'):

    if method == 'Jones2019':
        from functions_waterClassification_Jones2019 import ClassifyWaterJones2019
        return(ClassifyWaterJones2019(imgIn))
    elif method == 'Zou2018':
        from functions_waterClassification_Zou2018 import ClassifyWaterZou2018
        return(ClassifyWaterZou2018(imgIn))

# /* water function */
def CalculateWaterAddFlagsSR(imgIn, waterMethod = 'Jones2019'):
    # waterMethod = typeof waterMethod !== 'undefined' ? waterMethod : 'Jones2019';

    fmask = AddFmaskSR(imgIn).select(['fmask'])

    fmaskUnpacked = (fmask.eq(4).rename('flag_cloud')
    .addBands(fmask.eq(2).rename('flag_cldShadow'))
    .addBands(fmask.eq(3).rename('flag_snowIce'))
    .addBands(fmask.eq(1).rename('flag_water')))

    water = ClassifyWater(imgIn, waterMethod).where(fmask.gte(2), ee.Image.constant(0))
    hillshadow = CalcHillShadowSR(imgIn).Not().rename(['flag_hillshadow'])

    imgOut = (ee.Image(water.addBands(fmask).addBands(hillshadow).addBands(fmaskUnpacked)
    .setMulti({
        'image_id': imgIn.get('LANDSAT_ID'),
        'timestamp': imgIn.get('system:time_start'),
        'scale': imgIn.projection().nominalScale(),
        'crs': imgIn.projection().crs()
    })))

    return(imgOut)
