/* high-level image functions*/

var AssignDefault = function(x, dv) {
  return(typeof x !== 'undefined' ? x : dv);
};

exports.rwGenSR = function(aoi, WATER_METHOD, MAXDISTANCE, FILL_SIZE, MAXDISTANCE_BRANCH_REMOVAL) {
   
  // assign default values
  WATER_METHOD = AssignDefault(WATER_METHOD, 'Jones2019');
  MAXDISTANCE = AssignDefault(MAXDISTANCE, 4000);
  FILL_SIZE = AssignDefault(FILL_SIZE, 333);
  MAXDISTANCE_BRANCH_REMOVAL = AssignDefault(MAXDISTANCE_BRANCH_REMOVAL, 500);
  aoi = AssignDefault(aoi, null);
  
  
  var grwl = ee.FeatureCollection("users/eeProject/grwl");
  var lsFun = require('users/eeProject/RivWidthCloudPaper:functions_Landsat578/functions_landsat.js');
  var riverFun = require('users/eeProject/RivWidthCloudPaper:functions_river.js');
  var clWidthFun = require('users/eeProject/RivWidthCloudPaper:functions_centerline_width.js');
  
  // generate function based on user choice
  var tempFUN = function(image) {
    
    aoi = ee.Algorithms.If(aoi, aoi, image.geometry());
    image = image.clip(aoi);
    
    // derive water mask and masks for flags
    var imgOut = lsFun.CalculateWaterAddFlagsSR(image, WATER_METHOD);
    // calculate river mask
    imgOut = riverFun.ExtractRiver(imgOut, grwl, MAXDISTANCE, FILL_SIZE);
    // calculate centerline
    imgOut = clWidthFun.CalculateCenterline(imgOut);
    // calculate orthogonal direction of the centerline
    imgOut = clWidthFun.CalculateOrthAngle(imgOut);
    // export widths
    var widthOut = clWidthFun.CalculateWidth(imgOut);
    
    return(widthOut);
  };
  
  return(tempFUN);
};