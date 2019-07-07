/* functions to extract river mask */
exports.GetCenterline = function(clDataset, bound) {
  // filter the GRWL centerline based on area of interest
  var cl = clDataset.filterBounds(bound); 
  return(cl);
};
exports.ExtractChannel = function(image, centerline, maxDistance) {
  // extract the channel water bodies from the water mask, based on connectivity to the reference centerline.
  var connectedToCl = image.not().cumulativeCost({
    source: ee.Image().toByte().paint(centerline, 1).and(image), // only use the centerline that overlaps with the water mask
    maxDistance: maxDistance,
    geodeticDistance: false
  }).eq(0);

  var channel = image.updateMask(connectedToCl).unmask(0).updateMask(image.gte(0)).rename(['channelMask']);
  return channel;
};
exports.RemoveIsland = function(channel, FILL_SIZE) {
  /* fill in island as water if the size (number of pixels) of the island is smaller than FILL_SIZE */
  var fill = channel.not().selfMask().connectedPixelCount(FILL_SIZE).lt(FILL_SIZE);
  var river = channel.where(fill, ee.Image(1)).rename(['riverMask']);
  return(river);
};

exports.ExtractRiver = function(imgIn, clData, maxDist, minIslandRemoval) {
  
  var waterMask = imgIn.select('waterMask');
  var bound = waterMask.geometry();
  var cl = exports.GetCenterline(clData, bound);
  var channelMask = exports.ExtractChannel(waterMask, cl, maxDist);
  var riverMask = exports.RemoveIsland(channelMask, minIslandRemoval);
  return(imgIn.addBands(channelMask).addBands(riverMask));
};