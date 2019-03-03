
import ee

def rwGenSR(aoi = None, WATER_METHOD = 'Jones2019', MAXDISTANCE = 4000, FILL_SIZE = 333, MAXDISTANCE_BRANCH_REMOVAL = 500):

    grwl = ee.FeatureCollection("users/eeProject/grwl")
    from functions_landsat import CalculateWaterAddFlagsSR
    from functions_river import ExtractRiver
    from functions_centerline_width import CalculateCenterline, CalculateOrthAngle, CalculateWidth

    # // generate function based on user choice
    def tempFUN(image, aoi = aoi):
        aoi = ee.Algorithms.If(aoi, aoi, image.geometry())
        image = image.clip(aoi)

        # // derive water mask and masks for flags
        imgOut = CalculateWaterAddFlagsSR(image, WATER_METHOD)
        # // calculate river mask
        imgOut = ExtractRiver(imgOut, grwl, MAXDISTANCE, FILL_SIZE)
        # // calculate centerline
        imgOut = CalculateCenterline(imgOut)
        # // calculate orthogonal direction of the centerline
        imgOut = CalculateOrthAngle(imgOut)
        # // export widths
        widthOut = CalculateWidth(imgOut)

        return(widthOut)

    return(tempFUN)
