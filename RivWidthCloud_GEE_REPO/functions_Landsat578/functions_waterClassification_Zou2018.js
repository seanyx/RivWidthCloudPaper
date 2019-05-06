// Calculate water mask according to Zou et al., 2018
// https://www.pnas.org/content/pnas/suppl/2018/03/20/1719275115.DCSupplemental/pnas.1719275115.sapp.pdf

var Ndvi = function(image) {
  // calculate normalized difference vegetation index
  var ndvi = image.normalizedDifference(['Nir', 'Red']).rename('ndvi');
  return(ndvi);
};
var Evi = function(image) {
  // calculate the enhanced vegetation index
  var evi = image.expression('2.5 * (Nir - Red) / (1 + Nir + 6 * Red - 7.5 * Blue)', {
    'Nir': image.select(['Nir']),
    'Red': image.select(['Red']),
    'Blue': image.select(['Blue'])
    });
  return(evi.rename(['evi']));
};
var Mndwi = function(image) {
  // calculate modified normalized difference water index
  var mndwi = image.normalizedDifference(['Green', 'Swir1']).rename('mndwi');
  return(mndwi);
};

exports.ClassifyWaterZou2018 = function(image) {
  
  var mndwi = Mndwi(image);
  var ndvi = Ndvi(image);
  var evi = Evi(image);
  var water = (mndwi.gt(ndvi).or(mndwi.gt(evi))).and(evi.lt(0.1)); 
  
  return(water.rename(['waterMask']));
};