import data_reader
import numpy as np
import pandas as pd

def get_indifference_point_staircase(choices,delay):
    if len(choices[~choices.ss_chosen])==0:
        ip = 0
    elif len(choices[choices.ss_chosen])==0:
        ip = 1
    else:
        ip = (choices[choices.ss_chosen].amount_ratio.min()
                + choices[~choices.ss_chosen].amount_ratio.max())/2
    return ip

def get_indiff_point_sc(choices_sc):
    indiff_points = (choices_sc.groupby(['subj_id', 'll_delay'])
                     .apply(lambda c: get_indifference_point_staircase(c, c.iloc[0].ll_delay))
                     .rename('indiff_point'))
    return indiff_points

def get_delta_staircase(choices_sc):
    indiff_points = get_indiff_point_sc(choices_sc)
    choices_sc = choices_sc.join(indiff_points, on=['subj_id', 'll_delay'])
    choices_sc['delta'] = abs(choices_sc['amount_ratio'] - choices_sc['indiff_point'])
    choices_sc['log_delta'] = np.log(choices_sc['delta'])
    choices_sc['delta_quartile'] = pd.cut(choices_sc.delta,
                                        choices_sc.delta.quantile([0, 0.25, 0.5, 0.75, 1]),
                                        labels=[1, 2, 3, 4])
    return choices_sc

def get_k(indiff_points):
    delays = indiff_points.index.get_level_values('ll_delay').values
    delays = delays/max(delays)
    values = indiff_points.values
    
    # This calculates k-value based on AUC under original discounting curve
    k = 1 - ((delays[1:] - delays[:-1]) * (values[:-1] + values[1:]) / 2).sum()
    
    # We might as well check AUC under the discounting curve with log-scaled delay

    return k


#data_path = '../data/'
data_path = 'C:/Users/Arkady/Google Drive/data/beyond_the_reach'

dr = data_reader.DataReader()
choices, dynamics = dr.read_data(data_path)

index = ['subj_id', 'task', 'trial_no']

choices.reset_index(drop=False, inplace=True)

# TODO: current RT 
#exclude based on RT:
choices = choices[((choices.RT > 1) & (choices.RT < 5 )& (choices.task =='mouse' )) | ((choices.RT > 2) & (choices.RT < 7 )& (choices.task =='walking'))]
choices.set_index(index, inplace=True, drop=True)
dynamics[~dynamics.isin(choices)].dropna()

#drop backwards:
choices = choices[~np.isfinite(choices['first_backwards'])]
dynamics[~dynamics.isin(choices)].dropna()

#drop slowdowns:
#TODO: discuss how to.



#drop depending on k-values:
ip = get_indiff_point_sc(choices)
k_values = ip.groupby('subj_id').apply(get_k)

subj_to_exclude = []

for i, v in k_values.items():
    if (v < 2) | (v >98):
        subj_to_exclude.append(i)

choices.reset_index(drop=False, inplace=True)

choices[~choices['subj_id'].isin(subj_to_exclude)]
dynamics[~dynamics.isin(choices)].dropna()





