/* UI components*/
// design and structure adapted from:
// https://code.earthengine.google.com/31fc8040f2972e19c8b7cfc780255205
var app = {};

app.createStyles = function() {
  app.TEXTSTYLE = {
    width: '130px',
    margin: '8px 0 -3px 8px',
    fontSize: '14px',
    color: 'gray'
  };
  app.TEXTSTYLE_WORKING = {
    width: '130px',
    margin: '8px 0 -3px 8px',
    fontSize: '14px',
    color: 'green'
  };
  app.SECTION_STYLE = {
    width: '400px',
    margin: '20px 0 0 0'
  };
  app.INPUTBOX_STYLE = {
    width: '200px',
    height: '30px'
  };
  app.BUTTON_STYLE = {
    backgroundColor: 'green'
  };
};

app.createPanels = function() {
  
  app.intro = {
    panel: ui.Panel([
      ui.Label({
        value: "RivWidthCloud: Landsat",
        style: {fontWeight: 'bold', fontSize: '24px', margin: '10px 5px'}
      }),
      ui.Label('accompanying app for PAPER CITATION and license info.')
    ])
  };
  
  app.input = {
    imageID: ui.Textbox({placeholder: 'e.g. LC08_L1TP_022034_20130422_20170310_01_T1', style: app.INPUTBOX_STYLE}),
    seachDistance: ui.Textbox({placeholder: 'default: 4000 (meters)', style: app.INPUTBOX_STYLE}),
    islandSize: ui.Textbox({placeholder: 'default: 333 (pixels)', style: app.INPUTBOX_STYLE}),
    branchLength: ui.Textbox({placeholder: 'default: 300 (pixels)', style: app.INPUTBOX_STYLE}),
    exportFn: ui.Textbox({placeholder: 'default: Landsat Image ID', style: app.INPUTBOX_STYLE}),
    applyButton: ui.Button({label: 'Visualize image and generate task', style: app.BUTTON_STYLE})
  };
  
  app.input.panel = ui.Panel({
    widgets: [
      ui.Label('Main inputs', {fontWeight: 'bold'}),
      ui.Panel([ui.Label('Landsat Image ID', app.TEXTSTYLE_WORKING), app.input.imageID], ui.Panel.Layout.flow('horizontal')),
      ui.Panel([app.input.applyButton]),
      ui.Label('OPTIONAL: Change default parameters', {fontWeight: 'bold'}),
      ui.Panel([ui.Label('Max search distance', app.TEXTSTYLE_WORKING), app.input.seachDistance], ui.Panel.Layout.flow('horizontal')),
      ui.Panel([ui.Label('Max island to keep', app.TEXTSTYLE_WORKING), app.input.islandSize], ui.Panel.Layout.flow('horizontal')),
      ui.Panel([ui.Label('Max branch length to remove', app.TEXTSTYLE_WORKING), app.input.branchLength], ui.Panel.Layout.flow('horizontal')),
      ui.Panel([ui.Label('Exporting file name', app.TEXTSTYLE_WORKING), app.input.exportFn], ui.Panel.Layout.flow('horizontal'))
      ],
    style: app.SECTION_STYLE
  });
};
app.applyFunctions = function() {
  app.input.applyButton.onClick(ExportTask);
};
app.boot = function() {
  app.createStyles();
  app.createPanels();
  app.applyFunctions();
  var main = ui.Panel({
    widgets: [
      app.intro.panel,
      app.input.panel
      ],
    style: {width: '400', padding: '8px'}
  });
  ui.root.insert(0, main);
};

// main functions
var ExportTask = function() {
  // callback function for submitting task
  
  var fls = require('users/eeProject/RivWidthCloudPaper:functions_Landsat578/functions_landsat.js');
  var flsh = require('users/eeProject/RivWidthCloudPaper:functions_Landsat578/functions_highlevel.js');
  var inputID = app.input.imageID.getValue();
  var maxDistance = app.input.seachDistance.getValue();
  var islandSize = app.input.islandSize.getValue();
  var maxBranchRemoval = app.input.branchLength.getValue();
  
  // get the image with the input ID
  var img = fls.id2Img(inputID);
  
  // visualize the image
  var fmask = fls.AddFmaskSR(img).select('fmask');
  Map.clear();
  Map.centerObject(img);
  Map.addLayer(img, {bands: ['Red', 'Green', 'Blue'], min: 200, max: 2000}, "RGB", false);
  Map.addLayer(img, {bands: ['Swir1', 'Nir', 'Green'], min: 200, max: 5000}, "false color", true);
  Map.addLayer(fls.ClassifyWater(img, 'Jones2019').select('waterMask').selfMask(), {palette: ['blue']}, "Water mask", false);
  Map.addLayer(fmask.mask(fmask.gt(1)), {min: 2, max: 4, palette: ['grey', 'cyan', 'white']}, "CFmask", false);
  
  var rw = flsh.rwGenSR(null, 'Jones2019', maxDistance, islandSize, maxBranchRemoval, 'Pre-release version');
  var widths = rw(img);
  
  Export.table.toDrive({
    collection: widths.map(function(f) {return(f.setGeometry(null))}), 
    description: inputID, 
    folder: "", 
    fileNamePrefix: inputID, 
    fileFormat: "CSV"});

};

// initial program
app.boot();