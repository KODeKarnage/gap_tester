
# coding: utf-8

# Standard Modules
import sys
import pandas as pd

# eliminate annoying error message
pd.options.mode.chained_assignment = None


def error_message():
    print '--->:::'
    print '--->::: Usage:        python gap_testing.py [input file*] [output file*] [minimum^] [gap_adj^] -debug^'
    print '--->:::               * required '
    print '--->:::               ^ optional (you can only use gap_adj if you also supply a minimum'
    print '--->:::'
    print '--->::: input file:   the filename of the excel file to be tested.'
    print '--->:::               The file must be in the same folder as the script.'
    print '--->:::               col(1) - Date'
    print '--->:::               col(2) - Name'
    print '--->:::               col(3) - Category'
    print '--->:::               col(4) - Return Date'
    print '--->:::               col(5-10) - Return Periods'
    print '--->:::'
    print '--->::: output file:  the filename of the excel file to be produced. Make sure the file is not open.'
    print '--->:::               Example: test_results.xlsx'
    print '--->:::'
    print '--->::: minimum:      the minimum number of funds required in a category to run the test on that category.'
    print '--->:::               default = 6'
    print '--->:::'
    print '--->::: gap_adj:      the number of standard deviations consituting an investigatable gap.'
    print '--->:::               default = 1.0'
    print '--->:::'
    print '--->::: -debug:       add this tag if you want to export a comprehensive debug log to the export folder'
    print '--->:::               debug log is always named "gap_tester_debug.txt"'
    print '--->:::'


def investigate(dataframe, gap, colhead):
    
    ''' Returns a list of ids that need to be investigated for 
        being separated from the rest of the peer group. '''
    
    switch = False

    investigate_list = []
    
    prev_value = 'start'

    log('   -  length of recieved df:   %s' % len(dataframe))

    action_count = {}

    for index, value in dataframe.iteritems():

        if  prev_value == 'start': 

            action_count['start'] = action_count.get('start', 0) + 1

            prev_value = value
            continue

        elif not switch:

            action_count['standard'] = action_count.get('standard', 0) + 1

            curr_value = value
            diff = curr_value - prev_value

            if abs(diff) > gap * CRITICAL_SD:

                action_count['standard'] = action_count.get('standard', 0) - 1
                action_count['outlier'] = action_count.get('outlier', 0) + 1

                investigate_list.append(index)
                switch = True

            prev_value = value

        else:
            investigate_list.append(index)

            action_count['outlier'] = action_count.get('outlier', 0) + 1

    log('Counts: start= %s, standard= %s, outlier= %s' % (action_count.get('start', 0), action_count.get('standard', 0), action_count.get('outlier', 0)))

    return investigate_list


def clean(dataframe):
    
    ''' Cleans the dataset '''

    # remove all rows without an ID
    df = dataframe[dataframe['SecId'].notnull()]
    df['str-date'] = df['Return Date'].astype(str)

    # find modal return date, remove all rows without that return date
    mode_series = df['str-date']
    mode_list = list(mode_series.values)

    count_list = {}

    for x in mode_list:
        prev = count_list.get(x, 0) + 1
        count_list[x] = prev
        
    max_val = max(count_list.values())

    for k, v in count_list.iteritems():
        if v == max_val:
            mode = k
            break

    df = df[df['str-date'] == mode]
            
    del df['str-date']    

    return df


# setup extreme logging !!!!!!!!
extreme_log = []

if '-debug' in sys.argv:
    logging = True
else:
    logging = False

def log(string):

    global logging

    if logging:

        global extreme_log
        extreme_log.append(str(string))


error = False

# Obtain excel filename
try:
    filename = sys.argv[1]
    # cwd = os.getcwd()
    # filename = os.path.join(cwd, filestring)
except:
    error_message()
    sys.exit()

try:
    output = sys.argv[2]
except:
    error_message()
    sys.exit

try:
    MIN_FUNDS = float(sys.argv[3])
except:
    print '--->::: minimum not supplied, using default minimum: 6'
    MIN_FUNDS = 6
    try:
        if sys.argv[3] != '-debug':
            error=True
    except:
        pass

try:
    CRITICAL_SD = float(sys.argv[4])
except:
    print '--->::: gap_adj not supplied, using default: 1.0'
    CRITICAL_SD = 1.0
    try:
        if sys.argv[4] != '-debug':
            error=True
    except:
        pass

if error:
    error_message()



log('input file:  %s ' % filename)     
log('output file:   %s' % output)   
log('MIN_FUNDS:  %s' % MIN_FUNDS)
log('CRITICAL_SD:  %s' % CRITICAL_SD)

print '--->::: Starting Analysis'

# open excel file and create the dataframe
df = pd.read_excel(filename)

# columns are assumed to be in this order
presumed_headings = [
                    'Name',
                    'SecId',
                    'Morningstar Category',
                    'Return Date',
                    'Ret_0',
                    'Ret_2',
                    'Ret_1',
                    'Ret_3',
                    'Ret_4',
                    'Ret_5',
                    'Ret_6',
                    'Ret_7',
                    'Ret_8',
                    'Ret_9',
                    ]

df.columns = [presumed_headings]

# clean the dataframe
df = clean(df)

# set the SecId as the index
df = df.set_index('SecId')

# retrieve all the categories in the data
all_categories = df['Morningstar Category'].unique()

log('all_categories:   %s ' % all_categories)

# cycle over all the return columns
for column in presumed_headings[4:]:

    log('#' * 120)

    # dictionary to hold the ids of the funds to investigate
    new_column_data = {}
    
    print '--->::: Processing Column %s' % column

    print '--->:::     %s returns in column' % len(df[column].dropna())
    
    # cycle over all the categories in the dataset
    for category in all_categories:

        log('column:   %s, category:   %s' % (column, category))

        # create a dataframe containing only the funds in the category, with non-NA data, 
        # grab only the current return column
        returns = df[df['Morningstar Category'] == category][column].dropna()
           
        # if the dataset is too small, then abandon the analysis for this category over this time period
        count_of_returns = len(returns)

        log('Count of returns:   %s' % count_of_returns)

        if count_of_returns < MIN_FUNDS:
            log('too few returns, skipping category')
            continue

        # calculate the median and the stdev for the returns
        median = returns.median()
        stddev = returns.std()

        log('Median:   %s' % median)
        log('Stddev:   %s' % stddev)
        
        # create two new dataframes with the funds below and above the median      
        low_slice  = returns[returns < median]

        log('count of low slice:   %s' % len(low_slice))

        low_slice.sort(axis=0, inplace=True, ascending=False )

        log('count of low slice after sort:   %s' % len(low_slice))
        
        high_slice  = returns[returns > median]

        log('count of high slice:   %s' % len(high_slice))

        high_slice.sort(axis=0, inplace=True, ascending=True )

        log('count of high slice after sort:   %s' % len(high_slice))

        # retrieve lists of the id's of the funds that need to be investigated for this return period
        log('investigating low slice')
        investigate_low  = investigate(low_slice,  stddev, column)  
        log('length of investigate_low:   %s' % len(investigate_low))

        log('investigating low slice')
        investigate_high = investigate(high_slice, stddev, column)
        log('length of investigate_high:   %s' % len(investigate_high))

        # add the investigation funds for this category to return period investigation dictionary 
        new_column_data = dict(new_column_data.items() + [(x, 'L') for x in investigate_low] + [(y, 'H') for y in investigate_high])

        log('length of new_column_data:   %s' % len(new_column_data))
      
    # create a new column that highlights with an "L" or an "H" which funds need to be investigated
    df['INV '+column] = [new_column_data.get(x, '') for x in list(df.index.values)]

    
# export the results to excel
# folder, name = os.path.split(filename)
# now = datetime.datetime.now().strftime("%I%M%S")
# output_name = os.path.join(folder, 'results_' + now + '.xlsx')

print '--->::: Exporting to Excel'

df.to_excel(output, sheet_name='Gap_Results')

print '--->::: Analysis and Export Complete! :::<---'    

# output the log list to a debug_log file.
if logging:

    print '--->::: Dumping debug log'

    # debug_series = pd.Series(extreme_log)

    # debug_df = pd.DataFrame({"Debug Log":debug_series})

    # debug_df.to_excel('Debug_log', sheet_name="Debug")

    with open("gap_tester_debug.txt", 'w') as f:
        lines = '\n'.join(extreme_log)
        f.writelines(lines)

    print '--->::: Debug log pinched off :::<---'    