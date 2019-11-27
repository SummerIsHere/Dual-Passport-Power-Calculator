# DualPassportPower

## What is this?

Arton Capital's [Passport Index](https://www.passportindex.org/) is an interactive tool that displays and ranks passports of the world and is frequently updated with visa requirements and waivers. The code in this repository extracts data from the site and calculates similar measures for all combinations of two and three passports. It grew out of my curiosity about which two and which three passports would together give the greatest range of visa free travel options.

## File Organization

###CalculatePassportPower.py
This is Python code that extracts data from passportindex.org and calculates the number of countries each pair and triad of passports can travel to visa-free, or with a electronic travel authorization or visa upon arrival.

###RankPassportCombinations.py
This python code imports data processed by CalculatePassportPower.py and calculates misc scores (see below)

###Folder: exports
Whenever the code is run, it save several files with a timestamp appended

1. Dual Passport Power Scores.csv
   This is the table you want to look at to determine which passport combinations have the greatest power, in terms of
   1. maxScore: The number of destination countries the passport combo can travel to without a visa, with a visa on arrival, or with an electronic travel authorization.
   2. HDIScore: Multiply population by the Human Development Index (HDI) for each destination country, then sum them all up.
   3. PopScore: Sum up all the population for all the destination countries.
   4. GDPScore: Sum up the nominal GDP for all the destination countries (values are latest available when I pulled, which means the year are around 2010 to 2015).
   
2. compareByPassport.html

   The webpage from which data is extracted
3. PassportIndex.csv

   Visa requirements crosstable extracted from webpage
4. PassportIndex_Long.csv

   The above crosstable "melted" or unpivoted into "long" format
5. DualPowerTable.csv (may be compressed as zip due to size)

   A table with the passport power of combinations of two origin passports for each destination country. This takes a while to calculate so it is important to save periodically.


###Folder: website snapshots
Contains misc information from the Passprt Index that informs the calculations.

###Folder: support tables
Contains country information about Gross Domestic Product (GDP), Human Development Index (HDI), and population.

