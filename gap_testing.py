
# coding: utf-8

# In[9]:

# Standard Modules
import sys
import pandas as pd
import datetime
import os


# Obtain excel filename
# try:
#     filename = sys.argv[3]
# except:
filename = 'C:\\Temp\\gap_test_data.xlsx'

print filename
    


# In[10]:

def investigate(dataframe, gap, colhead):
    
    ''' Returns a list of ids that need to be investigated for 
        being separated from the rest of the peer group. '''
    
    switch = False

    investigate_list = []
    
    prev_value = 'start'

    for index, value in dataframe.iteritems():

        if  prev_value == 'start': 

            prev_value = value
            continue

        elif not switch:

            curr_value = value
            diff = curr_value - prev_value

            if abs(diff) > gap:

                investigate_list.append(index)
                switch = True

            prev_value = value

        else:
            investigate_list.append(index)

    return investigate_list


# In[11]:

# open excel file and create the dataframe
df = pd.read_excel(filename)

# columns are assumed to be in this order, with these headings
headings = {
            'A'  :  'Name',
            'B'  :  'SecId',
            'C'  :  'Morningstar Category',
            'D'  :  'Return Date (Mo-End)',
            'E'  :  'Ret 1 Mo (Mo-End)',
            'F'  :  'Ret 2 Mo (Mo-End)',
            'G'  :  'Ret 3 Mo (Mo-End)',
            'H'  :  'Ret 6 Mo (Mo-End)',
            'I'  :  'Ret 1 Yr (Mo-End)',
            'J'  :  'Ret Annlzd 2 Yr (Mo-End)',
            'K'  :  'Ret Annlzd 3 Yr (Mo-End)',
            'L'  :  'Ret Annlzd 5 Yr (Mo-End)',
            'M'  :  'Ret Annlzd 10 Yr (Mo-End)',
            'N'  :  'Ret Annlzd 15 Yr (Mo-End)'
            }

presumed_headings = [
                    'Name',
                    'SecId',
                    'Morningstar Category',
                    'Return Date (Mo-End)',
                    'Ret 1 Mo (Mo-End)',
                    'Ret 2 Mo (Mo-End)',
                    'Ret 3 Mo (Mo-End)',
                    'Ret 6 Mo (Mo-End)',
                    'Ret 1 Yr (Mo-End)',
                    'Ret Annlzd 2 Yr (Mo-End)',
                    'Ret Annlzd 3 Yr (Mo-End)',
                    'Ret Annlzd 5 Yr (Mo-End)',
                    'Ret Annlzd 10 Yr (Mo-End)',
                    'Ret Annlzd 15 Yr (Mo-End)'
                    ]

df.columns = [presumed_headings]


# In[12]:


# clean the dataset

# remove all rows without an ID
df = df[df['SecId'].notnull()]
df['str-date'] = df['Return Date (Mo-End)'].astype(str)

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

# set the SecId as the index
df = df.set_index('SecId')



# In[13]:

# retrieve all the categories in the data
all_categories = df['Morningstar Category'].unique()


# In[14]:

# test_cat = 'Australia OE Australian Cash'
# test_ret= 'Return Date (Mo-End)'

# test_sample = df[df['Morningstar Category'] == test_cat]
# # test_sample = df[df['Morningstar Category'] == test_cat, pd.notnull(df['test_ret'])]

# print test_sample


# In[20]:

# cycle over all the return columns
for column in list('EFGHIJKLMN'):

    # dictionary to hold the ids of the funds to investigate
    new_column_data = {}
    
    colhead = headings[column]
    print colhead
    
    count = len(all_categories)
    print count
    
    # cycle over all the categories in the dataset
    for category in all_categories:
        
        count -= 1
        
        if not count % 25:
            print count
     
        # create a dataframe containing only the funds in the category, with non-NA data, 
        # grab only the current return column
        returns = df[df['Morningstar Category'] == category][colhead].dropna()
             
        # if the dataset is too small, then abandon the analysis for this category over this time period
        if len(returns) < 6:
            continue

        # calculate the median and the stdev for the returns
        median = returns.median()
        stddev = returns.std()
        
        # create two new dataframes with the funds below and above the median      
        low_slice  = returns[returns < median]
        low_slice.sort(axis=0, inplace=True, ascending=False )
        high_slice  = returns[returns > median]
        high_slice.sort(axis=0, inplace=True, ascending=True )        

        # retrieve lists of the id's of the funds that need to be investigated for this return period
        investigate_low  = investigate(low_slice,  stddev, colhead)  
        investigate_high = investigate(high_slice, stddev, colhead)

        # add the investigation funds for this category to return period investigation dictionary 
        new_column_data = dict(new_column_data.items() + [(x, 'L') for x in investigate_low] + [(y, 'H') for y in investigate_high])
      
    # create a new column that highlights with an "L" or an "H" which funds need to be investigated
    df['INVESTIGATE '+colhead] = [new_column_data.get(x, '') for x in list(df.index.values)]

    
# export the results to excel
folder, name = os.path.split(filename)
now = datetime.datetime.now().strftime("%I%M%S")
output_name = os.path.join(folder, 'results_' + now + '.xlsx')
df.to_excel(output_name, sheet_name='Gap_Results')

print 'done'    


# In[ ]:



