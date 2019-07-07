if __name__ == '__main__':

    # import ee
    import numpy as np
    import pandas as pd
    import getopt
    import os
    from os import listdir
    import argparse
    from functions_batch import maximum_no_of_tasks


    parser = argparse.ArgumentParser(prog = 'rwc_landsat_batch.py', description = "Batch execute rwc_landsat.py for a csv files that contains Landsat image IDs and/or point locations.\
    (Example: python rwc_landsat_batch.py example_batch_input/example_batch_input.csv)")
    parser.add_argument('ID_FILE', help = 'Csv file contains at least one column (named "LANDSAT_ID")', type = str)
    parser.add_argument('-f', '--FORMAT', help = "Output file format ('csv' or 'shp'). Default: 'csv'", type = str, default = 'csv')
    parser.add_argument('-w', '--WATER_METHOD', help = "Water classification method ('Jones2019' or 'Zou2018'). Default: 'Jones2019'", type = str, default = 'Jones2019')
    parser.add_argument('-d', '--MAXDISTANCE', help = 'Default: 4000 meters', type = float, default = 4000)
    parser.add_argument('-i', '--FILL_SIZE', help = 'Default: 333 pixels', type = float, default = 333)
    parser.add_argument('-b', '--MAXDISTANCE_BRANCH_REMOVAL', help = 'Default: 500 pixels', type = float, default = 500)
    parser.add_argument('-o', '--OUTPUT_FOLDER', help = 'Any existing folder name in Google Drive. Default: root of Google Drive', type = str, default = '')
    parser.add_argument('-m', '--MAXIMUM_NO_OF_TASKS', help = 'Maximum number of tasks running simutaneously on the server. Default: 6', type = int, default = 6)
    parser.add_argument('-s', '--START_NO', help = '(Re)starting task No. Helpful when restarting an interrupted batch processing. Default: 0 (start from the beginning)', type = int, default = 0)

    group_validation = parser.add_argument_group(title = 'Batch run the RivWidthCloud in POINT mode',
    description = 'In POINT mode, the csv file needs to have addtional columns named "Point_ID", "Longitude", and "Latitude"\
    The point must locate within the bounds of the scene. \
    (Example: python rwc_landsat_batch.py example_batch_input/example_batch_input.csv -p)')

    group_validation.add_argument('-p', '--POINT', help = 'Enable the POINT mode', action = 'store_true')
    group_validation.add_argument('-r', '--BUFFER', help = 'Radius of the buffered region around the point location', type = float, default = 4000)

    args = parser.parse_args()

    ID_FILE = args.ID_FILE
    FORMAT = args.FORMAT
    WATER_METHOD = args.WATER_METHOD
    MAXDISTANCE = args.MAXDISTANCE
    FILL_SIZE = args.FILL_SIZE
    MAXDISTANCE_BRANCH_REMOVAL = args.MAXDISTANCE_BRANCH_REMOVAL
    OUTPUT_FOLDER = args.OUTPUT_FOLDER
    MAXIMUM_NO_OF_TASKS= args.MAXIMUM_NO_OF_TASKS
    START_NO = args.START_NO

    POINTMODE = args.POINT
    RADIUS = args.BUFFER

    if not POINTMODE:
        imageInfo = pd.read_csv(ID_FILE, dtype = {'LANDSAT_ID': np.unicode_})
        sceneIDList = imageInfo['LANDSAT_ID'].values.tolist()
    if POINTMODE:
        imageInfo = pd.read_csv(ID_FILE, dtype = {'Point_ID': np.unicode_, 'LANDSAT_ID': np.unicode_})
        sceneIDList = imageInfo['LANDSAT_ID'].values.tolist()
        point_IDList = imageInfo['Point_ID'].values.tolist()
        x = imageInfo['Longitude'].values.tolist()
        y = imageInfo['Latitude'].values.tolist()

    N = len(sceneIDList)

    print('')
    print('Image ID csv file is', ID_FILE)
    print('Output file format is', FORMAT)
    print('Results will be exported to', OUTPUT_FOLDER)
    print('')
    print('Number of images in the file:', N)

    for n in range(START_NO, N):

        cmdstr = 'python rwc_landsat_one_image.py ' +  sceneIDList[n] + ' -f ' + FORMAT + ' -w ' + WATER_METHOD
        cmdstr = cmdstr + ' -d ' + str(MAXDISTANCE) + ' -i ' + str(FILL_SIZE) + ' -b ' + str(MAXDISTANCE_BRANCH_REMOVAL)

        if OUTPUT_FOLDER:
            cmdstr = cmdstr + ' -o ' + OUTPUT_FOLDER

        if POINTMODE:
            cmdstr = cmdstr + ' -p -x ' + str(x[n]) + ' -y ' + str(y[n]) + ' -r ' + str(RADIUS) + ' -n ' + point_IDList[n]

        os.system(cmdstr)

        maximum_no_of_tasks(MAXIMUM_NO_OF_TASKS, 30)

        print('submitted task ', n + 1, ' of ', N)
