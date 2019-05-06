/* water test functions for determing DSWE
see https://github.com/USGS-EROS/espa-surface-water-extent/blob/master/dswe/algorithm-description.md
*/
var Mndwi = function(image) {
  return(image.normalizedDifference(['Green', 'Swir1']).rename('mndwi'));
};
var Mbsrv = function(image) {
  return(image.select(['Green']).add(image.select(['Red'])).rename('mbsrv'));
};
var Mbsrn = function(image) {
  return(image.select(['Nir']).add(image.select(['Swir1'])).rename('mbsrn'));
};
var Ndvi = function(image) {
  return(image.normalizedDifference(['Nir', 'Red']).rename('ndvi'));
};
var Awesh = function(image) {
  return(image
  .expression('Blue + 2.5 * Green + (-1.5) * mbsrn + (-0.25) * Swir2', {
    'Blue': image.select(['Blue']),
    'Green': image.select(['Green']),
    'mbsrn': Mbsrn(image).select(['mbsrn']),
    'Swir2': image.select(['Swir2'])
  }));
};

var Dswe = function(i) {
  var mndwi = Mndwi(i);
  var mbsrv = Mbsrv(i);
  var mbsrn = Mbsrn(i);
  var awesh = Awesh(i);
  var swir1 = i.select(['Swir1']);
  var nir = i.select(['Nir']);
  var ndvi = Ndvi(i);
  var blue = i.select(['Blue']);
  var swir2 = i.select(['Swir2']);
  
  
  var t1 = mndwi.gt(0.124);
  var t2 = mbsrv.gt(mbsrn);
  var t3 = awesh.gt(0);
  var t4 = mndwi.gt(-0.44)
  .and(swir1.lt(900))
  .and(nir.lt(1500))
  .and(ndvi.lt(0.7));
  var t5 = mndwi.gt(-0.5)
  .and(blue.lt(1000))
  .and(swir1.lt(3000))
  .and(swir2.lt(1000))
  .and(nir.lt(2500));
  
  var t = t1.add(t2.multiply(10)).add(t3.multiply(100)).add(t4.multiply(1000)).add(t5.multiply(10000));
  
  var noWater = t.eq(0)
  .or(t.eq(1))
  .or(t.eq(10))
  .or(t.eq(100))
  .or(t.eq(1000));
  var hWater = t.eq(1111)
  .or(t.eq(10111))
  .or(t.eq(11011))
  .or(t.eq(11101))
  .or(t.eq(11110))
  .or(t.eq(11111));
  var mWater = t.eq(111)
  .or(t.eq(1011))
  .or(t.eq(1101))
  .or(t.eq(1110))
  .or(t.eq(10011))
  .or(t.eq(10101))
  .or(t.eq(10110))
  .or(t.eq(11001))
  .or(t.eq(11010))
  .or(t.eq(11100));
  var pWetland = t.eq(11000);
  var lWater = t.eq(11)
  .or(t.eq(101))
  .or(t.eq(110))
  .or(t.eq(1001))
  .or(t.eq(1010))
  .or(t.eq(1100))
  .or(t.eq(10000))
  .or(t.eq(10001))
  .or(t.eq(10010))
  .or(t.eq(10100));
  
  var iDswe = noWater.multiply(0)
  .add(hWater.multiply(1))
  .add(mWater.multiply(2))
  .add(pWetland.multiply(3))
  .add(lWater.multiply(4));
  
  return(iDswe.rename('dswe'));
};

exports.ClassifyWaterJones2019 = function(img) {
  var dswe = Dswe(img);
  var waterMask = dswe.eq(1).or(dswe.eq(2)).rename(['waterMask']);
  return(waterMask);
};

