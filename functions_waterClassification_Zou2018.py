import ee

def Ndvi(image):
    # // calculate ndvi
    ndvi = image.normalizedDifference(['Nir', 'Red']).rename('ndvi')
    return ndvi

def Evi(image):
    # calculate the enhanced vegetation index
    evi = image.expression('2.5 * (Nir - Red) / (1 + Nir + 6 * Red - 7.5 * Blue)', {
    'Nir': image.select(['Nir']),
    'Red': image.select(['Red']),
    'Blue': image.select(['Blue'])
    })
    return evi.rename(['evi'])

def Mndwi(image):
    # calculate mndwi
    mndwi = image.normalizedDifference(['Green', 'Swir1']).rename('mndwi')
    return mndwi

def ClassifyWaterZou2018(image):
    mndwi = Mndwi(image)
    ndvi = Ndvi(image)
    evi = Evi(image)

    water = (mndwi.gt(ndvi).Or(mndwi.gt(evi))).And(evi.lt(0.1))
    return(water.rename(['waterMask']))
