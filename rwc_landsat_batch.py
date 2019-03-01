if __name__ == '__main__':

    # import ee
    import numpy as np
    import pandas as pd
    import getopt
    import os
    from os import listdir
    import argparse
    from functions import maximum_no_of_tasks

    ## default values
    localGoogleDriveDir = '/Users/yangxiao/Google_Drive/'

    parser = argparse.ArgumentParser(prog = 'rwc_landsat_batch.py', description = "Batch execute rwc_landsat.py for a csv files that contains scene IDs and/or site locations")
    parser.add_argument('ID_FILE', help = 'csv file contains column LANDSAT_ID, site_no, lon, and lat', type = str)
    parser.add_argument('-f', '--FORMAT', help = "output file format,  much be one or  any combination of 'csv', 'shp'", type = str, default = 'CSV')
    parser.add_argument('-d', '--MAXDISTANCE', help = '', type = str, default = '4000')
    parser.add_argument('-i', '--FILL_SIZE', help = '', type = str, default = '333')
    parser.add_argument('-b', '--MAXDISTANCE_BRANCH_REMOVAL', help = '', type = str, default = '500')
    parser.add_argument('-o', '--OUTPUT_FOLDER', help = 'any existing folder name in Google Drive to store the output file, defaults to the root of Google Drive', type = str, default = ' ')
    parser.add_argument('-m', '--MAXIMUM_NO_OF_TASKS', help = 'maximum number of tasks running on server', type = int, default = 6)
    parser.add_argument('-s', '--START_NO', help = 'starting task no', type = int, default = 0)

    args = parser.parse_args()

    ID_FILE = args.ID_FILE
    FORMAT = args.FORMAT
    MAXDISTANCE = args.MAXDISTANCE
    FILL_SIZE = args.FILL_SIZE
    MAXDISTANCE_BRANCH_REMOVAL = args.MAXDISTANCE_BRANCH_REMOVAL
    OUTPUT_FOLDER = args.OUTPUT_FOLDER
    MAXIMUM_NO_OF_TASKS= args.MAXIMUM_NO_OF_TASKS
    START_NO = args.START_NO

    siteInfo = pd.read_csv(ID_FILE, dtype = {'site_no': np.unicode_})
    sceneIDList = siteInfo['LANDSAT_ID'].values.tolist()
    site_no = siteInfo['site_no'].values.tolist()
    x = siteInfo['lon'].values.tolist()
    y = siteInfo['lat'].values.tolist()
    N = len(sceneIDList)

    print('')
    print('scene ID csv file is', ID_FILE)
    print('output file format is', FORMAT)
    print('results will be exported to', OUTPUT_FOLDER)
    print('')
    print('number of unfinished scenes in the file:', N)

    for n in range(START_NO, N):

        maximum_no_of_tasks(MAXIMUM_NO_OF_TASKS, 45)

        cmdstr = 'python rwc_landsat.py ' +  sceneIDList[n] + ' -f ' + FORMAT + ' -o ' + OUTPUT_FOLDER + ' '
        cmdstr = cmdstr + ' -d ' + MAXDISTANCE + ' -i ' + FILL_SIZE + ' -b ' + MAXDISTANCE_BRANCH_REMOVAL + ' '
        cmdstr = cmdstr + ' -v -x ' + str(x[n]) + ' -y ' + str(y[n]) + ' -n ' + site_no[n]

        print(cmdstr)

        os.system(cmdstr)

        print('submitted task ', n + 1, ' of ', N)
