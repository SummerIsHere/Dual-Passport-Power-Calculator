#! python3

# The basic structure of a request is https://www.passportindex.org/comparebyPassport.php?p1=ar&p2=ne&p3=al&p4=am
# where the p1, p2, etc are the two letter abbreviations of countries

import requests, bs4, pandas as pd, pprint, re, itertools as it, html5lib, numpy as np, datetime

# Logging
import logging

# Initialize logging
logging.basicConfig(level=logging.DEBUG
                    , filename='passport_logging.txt'
                    , format=' %(asctime)s - %(levelname)s - %(message)s')

# Generate a unique timestamp for this run in order to append to various files
a = datetime.datetime.now();
ts = a.strftime(format='%Y-%m-%d_%H%M%S')

# Get list of abbreviations and their full country names from one of the passportindex.org pages

url = 'https://www.passportindex.org/comparebyPassport.php'
logging.debug('Opening ' + url)
pagey = requests.get(url)
pagey.raise_for_status()
parsey = bs4.BeautifulSoup(pagey.text, 'html5lib')

a = parsey.select('select[id="country-selector01"] option[value]')
countries = pd.DataFrame(columns=['Country', 'Abbreviation'])
for i in a:
    countries.at[len(countries)] = [i.getText(), i.get('value').upper()]

# Save html file to disk with timestamp appended
tempFile = open('.//exports//compareByPassport_' + ts + '.html', 'w')
tempFile.write(pagey.text)
tempFile.close()
logging.debug('Saved ' + ('.//exports//compareByPassport_' + ts + '.html') + ' and closed connection')

# Remove spurious entries
countries = countries[countries.Abbreviation!='0']

#Write out a working copy
countries.to_csv(('.\\exports\\countries.csv'), index=False)
logging.debug('Wrote out working copy of countries')

# Set up an empty cross table to fill in later with visa requirements
logging.debug('Setting up empty cross table to fill in with data')
crossRef = pd.DataFrame(data=None, index=countries['Abbreviation'].copy().values,
                        columns=countries['Abbreviation'].copy().values)
crossRef.index.names = ['Destination']
crossRef.columns.names = ['Origin']

# The visa requirements table uses information embedded in the script code itself, so we will prase to get this information into a table
scripts = parsey.select('script')

# There are several script sections, find the appropriate one with some unique phrases
logging.debug('Parsing script section')
theScript = []
for i in scripts:
    if ('com_c_voa' in i.getText()):
        theScript += [i.getText()]

# There should only be one matching code section
if(len(theScript) > 1):
    raise Exception('More than one script body to parse')

# Remove new lines, and split into pieces by semicolon

code = theScript[0]
code = code.replace('\n', '')
codeList = code.split(';')


# Go through each piece and use it to populate a cross table. All should be general format of com_c_XX["YY"]=['A','B']
# Interpret this to mean that people from country YY is XX in terms of requirements for travel to countries A, B
# The alternative is that people from A, B need XX to travel to country YY.
# I looked at a couple cases on the site, it appears to be the first definition.
# Assume vf: visa free, voa: vista on arrival, eta: electronic travel authorization. Assume unlisted means visa required

for thisS in codeList:
    logging.debug('Filling in cross table, now on: ' + thisS)
    try:
        thisS = thisS.strip()
        es = thisS.split('=')
        tempDest = es[1].upper().replace('"', '').strip().split(',')
        tempOrig = es[0].upper().split('"')[1]
        tempTravReq = es[0].upper().split('"')[0].replace('[', '')
        #This is not a travel requirement, but an indicator for a country as to whether
        #the visas they issue can be e-Visas. Therefore, ignore.
        if tempTravReq == 'MC_EVISA':
            continue
    except:
        continue
    for x in [tempOrig]:
        crossRef.loc[x, x] = 'Same Country'
        for y in tempDest:
            crossRef.loc[y, x] = tempTravReq

# Any remaining missing values should be visa required

crossRef = crossRef.fillna('Visa Required')
reqs = pd.Series(crossRef.values.ravel()).unique()

crossRef = crossRef.replace('COM_C_VF', 'Visa Free')
crossRef = crossRef.replace('COM_C_VOA', 'Visa on Arrival')
crossRef = crossRef.replace('COM_C_ETA', 'Electronic Travel Authorization')

## Write out this crosstable
logging.debug('Writing out crosstable')
crossRef.to_csv(('.\\exports\\PassportIndex_' + ts + '.csv'), index=False)


assert len(crossRef.index) > 180, 'not enough countries'
assert len(crossRef.columns) > 180, 'not enough countries'

## Convert cross table to long format
logging.debug('Converting cross table to long format')
longTable = (crossRef.stack()).reset_index()
longTable = (longTable.loc[longTable['Origin'] != '0']).copy()
longTable = (longTable.loc[longTable['Destination'] != '0']).copy()
longTable.columns.values[2] = 'Visa Requirements'

longTable = (longTable.loc[longTable['Destination'] != '']).copy()
longTable = (longTable.loc[longTable['Origin'] != '']).copy()
assert (longTable.columns.values[1] == 'Origin'), 'Wrong columns'

## Write out this long table as a working copy
longTable.to_csv(('.\\exports\\PassportIndex_Long.csv'), index=False)

## Write out this long table as an archive version
longTable.to_csv(('.\\exports\\PassportIndex_Long_' + ts + '.csv'), index=False)
logging.debug('Wrote out long table')

## Calculate single passport power
## Passport Power for an origin country
## 1 point for each destination country that a origin passport holder can visit visa free, with a visa on arrival, or electronic travel authorization
logging.debug('Calculating single passport power')
powerTable = longTable.copy()
powerTable = powerTable.replace('Visa Required', '0')
powerTable = powerTable.replace('Visa Free', '1')
powerTable = powerTable.replace('Visa on Arrival', '1')
powerTable = powerTable.replace('Electronic Travel Authorization', '1')
powerTable = powerTable.replace('Same Country', '1')

## Calculate dual passport power. For each pair or origin countries and destination, select the highest number e.g. least restrictive requirement
logging.debug('Calculating dual passport power')
# Create country combinations
c = it.combinations(longTable['Origin'].copy().unique(), 2)
c = list(c)

dualPowerTable = pd.DataFrame(columns=['Destination', 'Origin1', 'Origin2', 'maxScore'])
# dualPowerSum = pd.DataFrame(columns=['Origin1','Origin2','maxScore'])
for i in c:
    first = (powerTable.copy()).loc[powerTable['Origin'] == i[0]]
    second = (powerTable.copy()).loc[powerTable['Origin'] == i[1]]
    logging.debug('First: ' + i[0] + ' , Second: ' + i[1])
    first.rename(columns={'Origin': 'Origin1'}, inplace=True)
    first.rename(columns={'Visa Requirements': 'Visa Requirements1'}, inplace=True)
    second.rename(columns={'Origin': 'Origin2'}, inplace=True)
    second.rename(columns={'Visa Requirements': 'Visa Requirements2'}, inplace=True)
    first.reset_index(drop=True, inplace=True)
    second.reset_index(drop=True, inplace=True)
    result = pd.merge(left=first, right=second, how='left', on='Destination')
    maxScore = result.loc[:, ['Visa Requirements1', 'Visa Requirements2']].apply(np.max, axis=1).astype(float)
    result.loc[:, 'maxScore'] = maxScore
    a = result
    dualPowerTable = dualPowerTable.append(a, ignore_index=True)

#Write out a working copy
logging.debug('Writing out dual power table')
dualPowerTable.to_csv(('.\\exports\\DualPowerTable.csv'),index=False)

#Write out an archive version
dualPowerTable.to_csv(('.\\exports\\DualPowerTable_'+ts+'.csv'),index=False)

logging.debug('Finished writing out dual power table')

# By origin country combinations, sum up passport power for comparison
#dualPowerTable = dualPowerTable.loc[:,['Origin1','Origin2','maxScore']]
#dualPowerSum = dualPowerTable.groupby(['Origin1','Origin2']).sum()
#dualPowerSum.to_csv(('.\\exports\\DualPowerSum_'+ts+'.csv'),index=False)

## Calculate triad passport power
logging.debug('Start triad passport power calculation')
# Create country combinations
c = it.combinations(longTable['Origin'].copy().unique(), 3)
c = list(c)

triadPowerTable = pd.DataFrame(columns=['Destination', 'Origin1', 'Origin2', 'Origin3', 'maxScore'])
for i in c:
    first = (powerTable.copy()).loc[powerTable['Origin'] == i[0]]
    second = (powerTable.copy()).loc[powerTable['Origin'] == i[1]]
    third = (powerTable.copy()).loc[powerTable['Origin'] == i[2]]
    logging.debug('First: ' + i[0] + ', Second: ' + i[1] + ', Third: ' + i[2])
    first.rename(columns={'Origin': 'Origin1'}, inplace=True)
    first.rename(columns={'Visa Requirements': 'Visa Requirements1'}, inplace=True)

    second.rename(columns={'Origin': 'Origin2'}, inplace=True)
    second.rename(columns={'Visa Requirements': 'Visa Requirements2'}, inplace=True)

    third.rename(columns={'Origin': 'Origin3'}, inplace=True)
    third.rename(columns={'Visa Requirements': 'Visa Requirements3'}, inplace=True)

    first.reset_index(drop=True, inplace=True)
    second.reset_index(drop=True, inplace=True)
    third.reset_index(drop=True, inplace=True)

    result = pd.merge(left=first, right=second, how='left', on='Destination')
    result = pd.merge(left=result, right=third, how='left', on='Destination')

    maxScore = result.loc[:, ['Visa Requirements1', 'Visa Requirements2', 'Visa Requirements3']].apply(np.max, axis=1)
    result.loc[:, 'maxScore'] = maxScore
    newSection = result.loc[:, ['Destination', 'Origin1', 'Origin2', 'Origin3', 'maxScore']]
    triadPowerTable = triadPowerTable.append(newSection, ignore_index=True)

# Write out triadPowerTable working copy
triadPowerTable.to_csv(('.\\exports\\TriadPowerTable.csv'), index=False)

# Write out triadPowerTable archive version
triadPowerTable.to_csv(('.\\exports\\TriadPowerTable_' + ts + '.csv'), index=False)

logging.debug('Wrote out triad power table')

# By origin country combinations, sum up passport power for comparison
#triadPowerSum = triadPowerTable.groupby(['Origin1','Origin2','Origin3']).sum()
#triadPowerSum.to_csv(('.\\exports\\TriadPowerSum_'+ts+'.csv'),index=False)
