/* functions to load Landsat 4-5 data*/
exports.merge_collections_std_bandnames_collection1tier1_sr = function() {
  // merge landsat 5, 7, 8 collection 1 tier 1 imageCollections and standardize band names

  // refer and define standard band names
  var bn8 = ['B1', 'B2', 'B3', 'B4', 'B6', 'pixel_qa', 'B5', 'B7'];
  var bn7 = ['B1', 'B1', 'B2', 'B3', 'B5', 'pixel_qa', 'B4', 'B7'];
  var bn5 = ['B1', 'B1', 'B2', 'B3', 'B5', 'pixel_qa', 'B4', 'B7'];
  var bns = ['uBlue', 'Blue', 'Green', 'Red', 'Swir1', 'BQA', 'Nir', 'Swir2'];

  // create a merged collection from landsat 5, 7, and 8
  var ls5 = ee.ImageCollection("LANDSAT/LT05/C01/T1_SR").select(bn5, bns);
  var ls7 = (ee.ImageCollection("LANDSAT/LE07/C01/T1_SR")
  .filterDate('1999-04-15', '2003-05-30') // exclude LE7 images that affected by failure of Scan Line Corrector (SLC)
  .select(bn7, bns));
  var ls8 = ee.ImageCollection("LANDSAT/LC08/C01/T1_SR").select(bn8, bns);
  var merged = ls5.merge(ls7).merge(ls8);

  return(merged);
};

exports.id2Img = function(id) {
  return(ee.Image(exports.merge_collections_std_bandnames_collection1tier1_sr()
  .filterMetadata('LANDSAT_ID', 'equals', id)
  .first()));
};

/* functions to add quality band (Fmask and hillshade) */
var Unpack = function(qualityBand, startingBit, bitWidth) {
  // unpacking bit information from the quality band given the bit position and width
  // see: https://groups.google.com/forum/#!starred/google-earth-engine-developers/iSV4LwzIW7A
  return(qualityBand
  .rightShift(startingBit)
  .bitwiseAnd(ee.Number(2).pow(bitWidth).subtract(1).int()));
};
var UnpackAllSR = function(bitBand) {
  // apply Unpack function for multiple pixel qualities
  var bitInfoSR = {
    'Cloud': [5, 1],
    'CloudShadow': [3, 1],
    'SnowIce': [4, 1],
    'Water': [2, 1]
  };
  var unpackedImage = ee.Image();
  for (var key in bitInfoSR) {
    unpackedImage = ee.Image.cat(
      unpackedImage, Unpack(bitBand, bitInfoSR[key][0], bitInfoSR[key][1])
      .rename(key));
  }
  return(unpackedImage.select(Object.keys(bitInfoSR)));
};
exports.AddFmaskSR = function(image) {
  // add fmask as a separate band to the input image
  var temp = UnpackAllSR(image.select(['BQA']));

  // construct the fmask
  var fmask = (temp.select(['Water']).rename(['fmask'])
  .where(temp.select(['SnowIce']), ee.Image(3))
  .where(temp.select(['CloudShadow']), ee.Image(2))
  .where(temp.select(['Cloud']), ee.Image(4)))
  .mask(temp.select(['Cloud']).gte(0)); // mask the fmask so that it has the same footprint as the quality (BQA) band

  return(image.addBands(fmask));
};

exports.CalcHillShadowSR = function(image) {
  var dem = ee.Image("users/eeProject/MERIT").clip(image.geometry().buffer(9000).bounds());
  var SOLAR_AZIMUTH_ANGLE = ee.Number(image.get('SOLAR_AZIMUTH_ANGLE'));
  var SOLAR_ZENITH_ANGLE = ee.Number(image.get('SOLAR_ZENITH_ANGLE'));
  return(ee.Terrain.hillShadow(dem, SOLAR_AZIMUTH_ANGLE, SOLAR_ZENITH_ANGLE, 100, true).rename(['hillshadow']));
};


/* functions to classify water (default) */
exports.ClassifyWater = function(imgIn, method) {

  if (method == 'Jones2019') {
    var waterJones2019 = require('users/eeProject/RivWidthCloudPaper:functions_Landsat578/functions_waterClassification_Jones2019.js');
    return(waterJones2019.ClassifyWaterJones2019(imgIn));
  } else if (method == 'Zou2018') {
    var waterZou2018 = require('users/eeProject/RivWidthCloudPaper:functions_Landsat578/functions_waterClassification_Zou2018.js');
    return(waterZou2018.ClassifyWaterZou2018(imgIn));
  }
};

/* water function */
exports.CalculateWaterAddFlagsSR = function(imgIn, waterMethod) {

  waterMethod = typeof waterMethod !== 'undefined' ? waterMethod : 'Jones2019';

  var fmask = exports.AddFmaskSR(imgIn).select(['fmask']);

  var fmaskUnpacked = fmask.eq(4).rename('flag_cloud')
  .addBands(fmask.eq(2).rename('flag_cldShadow'))
  .addBands(fmask.eq(3).rename('flag_snowIce'))
  .addBands(fmask.eq(1).rename('flag_water'));

  var water = exports.ClassifyWater(imgIn, waterMethod)
  .where(fmask.gte(2), ee.Image.constant(0));
  var hillshadow = exports.CalcHillShadowSR(imgIn).not().rename(['flag_hillshadow']);
  var imgOut = ee.Image(water.addBands(fmask).addBands(hillshadow).addBands(fmaskUnpacked)
  .setMulti({
    'image_id': imgIn.get('LANDSAT_ID'),
    'timestamp': imgIn.get('system:time_start'),
    'scale': imgIn.projection().nominalScale(),
    'crs': imgIn.projection().crs()
  }));
  return(imgOut);
};
