# Raw data

This folder contains the original, unmodified dataset files downloaded from the UCI Machine Learning Repository.

## Source

- Dataset: Apartment for Rent Classified
- URL: https://archive.ics.uci.edu/dataset/555/apartment
- Dataset ID: 555
- Geographic coverage: United States
- Data period: 2019

## Import in python


    from ucimlrepo import fetch_ucirepo 
    # fetch dataset 
    apartment_for_rent_classified = fetch_ucirepo(id=555) 
    
    # data (as pandas dataframes) 
    X = apartment_for_rent_classified.data.features 
    y = apartment_for_rent_classified.data.targets 
    
    # metadata 
    print(apartment_for_rent_classified.metadata) 
    
    # variable information 
    print(apartment_for_rent_classified.variables) 


## Files and version used

Record the exact archive/version downloaded by the team and list the filenames below.

- Dataset version: **[Fill in: 10K or 100K]**
- Download date: **[Fill in date]**
- Original filenames: **[List filenames]**

## Data handling

Keep the source files unchanged in this folder. Do not remove rows, rename columns, impute missing values or otherwise preprocess the raw data here. Store any cleaned or transformed data in a separate processed-data folder.
