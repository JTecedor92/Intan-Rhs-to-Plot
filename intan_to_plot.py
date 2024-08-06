import tkinter as tk
from tkinter import filedialog
import os
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import time
from intanutil.header import (read_header,
                              header_to_result)
from intanutil.data import (calculate_data_size,
                            read_all_data_blocks,
                            check_end_of_file,
                            parse_data,
                            data_to_result)
from intanutil.filter import apply_notch_filter



def read_data(filename):
    """Reads Intan Technologies RHS2000 data file generated by acquisition
    software (IntanRHX, or legacy Stimulation/Recording Controller software).

    Data are returned in a dictionary, for future extensibility.
    """
    # Start measuring how long this read takes.
    tic = time.time()
    print(filename)
    # Open file for reading.
    with open(filename, 'rb') as fid:

        # Read header and summarize its contents to console.
        header = read_header(fid)

        # Calculate how much data is present and summarize to console.
        data_present, filesize, num_blocks, num_samples = (
            calculate_data_size(header, filename, fid))

        # If .rhs file contains data, read all present data blocks into 'data'
        # dict, and verify the amount of data read.
        print('FINISHED HEADER')
        if data_present:
            data = read_all_data_blocks(header, num_samples, num_blocks, fid)
            check_end_of_file(filesize, fid)

    # Save information in 'header' to 'result' dict.
    result = {}
    header_to_result(header, result)

    # If .rhs file contains data, parse data into readable forms and, if
    # necessary, apply the same notch filter that was active during recording.
    if data_present:
        parse_data(header, data)
        #apply_notch_filter(header, data)

        # Save recorded data in 'data' to 'result' dict.
        data_to_result(header, data, result)

    # Otherwise (.rhs file is just a header for One File Per Signal Type or
    # One File Per Channel data formats, in which actual data is saved in
    # separate .dat files), just return data as an empty list.
    else:
        data = []

    # Report how long read took.
    print('Done!  Elapsed time: {0:0.1f} seconds'.format(time.time() - tic))

    # Return 'result' dict.
    return result



def list_rhs_files(directory):
    """
    Lists all files in the given directory that end with the .rhs extension.

    Args:
    directory (str): The path to the directory where to look for files.

    Returns:
    list: A list of file names that end with .rhs
    """
    # List to hold file names
    rhs_files = []

    # Check if the directory exists
    if not os.path.exists(directory):
        print("The specified directory does not have Intan .rhs files.")
        return []

    # Loop through each file in the directory
    for filename in os.listdir(directory):
        # Check if the file ends with .rhs
        if filename.endswith('.rhs'):
            rhs_files.append(filename)

    return sorted(rhs_files)



# New function to handle the main folder processing
def process_main_folder(folder_path, channel, stimbool):
    rhs_folders_path=[]
    x = []
    y = []
    rhs_folders=list_rhs_files(folder_path)
    for rhs_folder in rhs_folders:
        rhs_folders_path.append(os.path.join(folder_path, rhs_folder))
    concatenated_signal,concatenated_time,concatenated_stim=Concatenate(rhs_folders_path, stimbool)

    # Transpose the list of signals to align with concatenated_time
    transposed_signals = list(zip(*concatenated_signal))
    data = [ [time] + list(signals) for time, signals in zip(concatenated_time, transposed_signals)]
    stim = concatenated_stim
    for i in data:
        x.append(i[0:1])
        y.append(i[channel:(channel + 1)])
        
    print('Data collected')
    return x, y, stim
    


def Concatenate(rhs_folders, stimbool):
    concatenated_signal = None
    concatenated_time= None
    concatenated_stim = None
    for file_name in sorted(rhs_folders):
        rhs_data = read_data(file_name)  # Assuming this returns a dict with necessary data
        # Concatenate data across files
        if concatenated_signal is None:
            concatenated_signal = rhs_data['amplifier_data']
            concatenated_time=rhs_data['t']
            if stimbool:
                concatenated_stim = rhs_data['board_dig_out_data']

            #concatenated_board_dig_in_data = rhs_data['board_dig_in_data']
        else:
            concatenated_signal = np.concatenate((concatenated_signal, rhs_data['amplifier_data']), axis=1)
            concatenated_time = np.concatenate((concatenated_time, rhs_data['t']))
            if stimbool:
                concatenated_time = np.concatenate((concatenated_stim, rhs_data['board_dig_out_data']))

    print('All files read and concatinated')
    return concatenated_signal,concatenated_time,concatenated_stim


def main():
    root = tk.Tk()
    root.attributes('-topmost', True)  # Display the dialog in the foreground.
    root.iconify()  # Hide the little window.
    mpl.rcParams['toolbar'] = 'None'
    plt.figure(figsize=(10,14))

    print('\nFigure type (full/partition)')
    plottype = input()

    if plottype == 'full':
        print('\nNumber of plots:')
        plotnum = int(input())
        if plotnum > 1:
            print('Number of rows:')
            rownum = int(input())
            print('Number of columns:')
            colnum = int(input())
        else:
            rownum = 1
            colnum = 1
        
        if plotnum <= (rownum*colnum):
            print('\nLayout mapped')
        else:
            print('\nFaulty layout')
            quit()

        plotid = 0
        for _ in range(plotnum):
            plotid += 1
            plt.subplot(rownum, colnum, plotid)

            print('\nPlot ' + str(plotid))
            print('Number of Channels:')
            numch = int(input())

            for _ in range(numch):
                folder_path = filedialog.askdirectory(title="Select the main folder")
                print('\nFolder selected')

                print('Channel:')
                channel = int(input())

                print('Color:')
                color = input()

                print('Stim (y/n):')
                st = input()
                if st == 'y':
                    stimbool = True
                    kind = 'stim'
                    print('Stim Channel 1 Info (name, µA, color):')
                    stimchannel1 = input()
                    stimv1 = input()
                    stimcolor1 = input()
                    print('Stim Channel 2 Info (name, µA, color):')
                    stimchannel2 = input()
                    stimv2 = input()
                    stimcolor2 = input()
                else:
                    stimbool = False
                    kind = 'baseline'

                if channel >= 43:
                    loc = 'B-0' + str(channel - 33)
                elif channel >= 33:
                    loc = 'B-00' + str(channel - 33)
                elif channel >= 11:
                    loc = 'A-0' + str(channel - 1)
                else:
                    loc = 'A-00' + str(channel - 1)
    
                if folder_path:
                    x, y, stim = process_main_folder(folder_path, channel, stimbool)
                    plt.plot(x, y, color=color, label='Channel ' + loc + ' (' + kind + ')')

                    if stimbool:
                        z = stim*1
                        z = z.tolist()
                        c1 = 0
                        for i in z:
                            c2 = 0
                            indexes=[]
                            for elem in range(0, len(i)):
                                if i[elem] == 1:
                                    indexes.append(elem)
                            for j in indexes:
                                if c1 == 0 and c2 == 0:
                                    plt.vlines(x = x[j], color=stimcolor1, label=stimchannel1 + ' (' + stimv1 + 'µA)', ymin = -50, ymax = 50)
                                elif c1 == 0 and c2 > 0:
                                    plt.vlines(x = x[j], color=stimcolor1, ymin = -50, ymax = 50)
                                elif c1 > 0 and c2 == 0:
                                    plt.vlines(x = x[j], color=stimcolor2, label=stimchannel2 + ' (' + stimv2 + 'µA)', ymin = -50, ymax = 50)
                                else:
                                    plt.vlines(x = x[j], color=stimcolor2, ymin = -50, ymax = 50)
                                c2 += 1
                            c1 += 1
                    print('Plotting...')

            if numch > 1:
                print('\nTitle:')
                title = input()
                print('Min Seconds:')
            else:
                title = 'Intan recording: Channel ' + loc
                print('\nMin Seconds:')
            minlim = int(input())
            print('Max Seconds:')
            maxlim = int(input())
            print('Range:')
            yrange = int(input())

            plt.title(title)
            plt.xlabel('Time (s)')
            plt.xlim(minlim, maxlim)
            plt.ylabel('Signal (µV)')
            plt.ylim(-1*yrange, yrange)
            plt.grid(True)
            plt.legend(loc='upper left')
    
    elif plottype == 'partition':
        folder_path = filedialog.askdirectory(title="Select the main folder")
        print('\nFolder selected')

        print('Channel:')
        channel = int(input())

        print('Title:')
        title = input()

        print('Range:')
        yrange = int(input())

        print('Color:')
        color = input()

        print('Stim channel (1-2):')
        stimloc = int(input())
        if stimloc == 1:
            stimindex = 0
        elif stimloc == 2:
            stimindex = 1
        else:
            print('\nStim channel not found')
            quit()
        
        if folder_path:
            stimbool = True
            x, y, stim = process_main_folder(folder_path, channel, stimbool)
            z = stim.tolist()
            i = z[stimindex]
            plots = []
            plotcount = 0
            elem = 0
            while elem < len(i):
                if i[elem] == 1:
                    plots.append(elem)
                    elem += 30
                    plotcount += 1
                else:
                    elem += 1

            if plotcount < 5:
                colcount = plotcount
                rowcount = 1
            else:
                colcount = 5
                rowcount = int(colcount / 5)
                if rowcount % 5 != 0:
                    rowcount += 1

            plt.title(title)
            ax = plt.gca()
            ax.set_frame_on(False)
            ax.axis('off')
            for k in plots:
                plt.subplot(rowcount, colcount, plots.index(k) + 1)
                plt.plot(x, y, color=color)
                plt.xlabel('Time (s)')
                plt.xlim(float(x[k][0].item()) - 1, float(x[k][0].item()) + 3)
                plt.ylabel('Signal (µV)')
                plt.ylim(-1*yrange, yrange)
                plt.grid(True)          

    else:
        print('\nNot a valid figure type')
        quit()

    root.destroy()
    print('\n Plot completed')
    plt.tight_layout(h_pad=2)
    plt.show()
    
if __name__ == "__main__":
    folder_path=main()
    
    
    