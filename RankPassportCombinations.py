#! python3

import pandas as pd, pprint, re, itertools as it, numpy as np, datetime

## Create rankings
dual = pd.read_csv('.\\exports\\DualPowerTable.csv');
info = pd.read_csv('.\\support tables\Pop HDI GDP.csv');
countries = pd.read_csv('.\\exports\countries.csv');

combo = pd.merge(left=dual, right=countries, how="left", left_on="Destination", right_on="Abbreviation");
combo = pd.merge(left=combo, right=info, how="left", left_on="Country", right_on="Country", indicator=True);

assert len(combo.loc[combo._merge!='both'])==0, 'not all countries matched';

## These various scores determine the "reach" of a passport duo in terms of the combined GDP, population, or HDI*population of all the destination countries that can be entered visa free, visa on arrival, or electronic travel authorization.
combo['PopScore'] = combo.maxScore * (combo['2015 Population (World Bank or CIA Factbook)'].astype(float));
combo['HDIScore'] = combo.maxScore * (combo['Human Development Index (2014) (UN or World Bank)'].astype(float))* (combo['2015 Population (World Bank or CIA Factbook)'].astype(float));
combo['GDPScore'] = combo.maxScore * (combo['GDP Nominal ($US, latest avail) (World Bank or Wikipedia)'].astype(float));

#Clean up table and add country names
combo = combo[['Origin1','Origin2','maxScore','PopScore','HDIScore','GDPScore']];
comboSum = (combo.groupby(['Origin1','Origin2']).sum()).reset_index();
comboSum = pd.merge(left=comboSum, right=countries, how="left",left_on="Origin1", right_on="Abbreviation");
comboSum = pd.merge(left=comboSum, right=countries, how="left",left_on="Origin2", right_on="Abbreviation");

comboSum = comboSum[['Country_x','Country_y', 'maxScore', 'PopScore', 'HDIScore', 'GDPScore']];

comboSum.to_csv('.\\exports\\Dual Passport Power Scores.csv',index=False);

