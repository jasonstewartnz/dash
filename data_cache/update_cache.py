
# Script to ensure freshness of Snowflake data - caches without needing to hit the SF instance 
# for every front-end request
# Download data - write to csv
#

from snowflake import connector
from os import getenv, path 
import pandas as pd
from datetime import timedelta, datetime
from time import sleep

DATA_FRESHNESS_INTERVAL_SECONDS = 60*60*24 # daily # 60 # 1 minute for testing #
data_location = './data/housing_data.csv'

def read_housing_data():
    assert (getenv('SNOWSQL_USER') is not None),'Cannot retrieve env variable "SNOWSQL_USER"'

    # Gets the version
    ctx = connector.connect(
        user=getenv('SNOWSQL_USER'),
        password=getenv('SNOWSQL_PASSWORD'),
        account=getenv('SNOWSQL_ACCOUNT'),
        warehouse='COMPUTE_WH',
        database='FHFA_SINGLE_FAMILY_HOME_APPRAISALS__VALUES',
        schema='cybersyn'
        )

    sql = """
    SELECT ind.level, geo_name, date, value 
    FROM cybersyn.fhfa_uad_timeseries ts
    JOIN cybersyn.fhfa_uad_attributes att ON ts.variable = att.variable
    JOIN cybersyn.fhfa_geo_index ind ON ind.id = ts.geo_id
    WHERE purpose = 'Purchase & Refinance'
        AND characteristic = ''
        AND ts.variable = 'Quarterly_Median_Appraised_Value__Purchase_&_Refinance_All_Appraisals'
    ORDER BY date
    """

    print('Importing housing data from db')
    # suppress this warning
    housing_data = pd.read_sql( sql, ctx )
    print('Housing data imported')

    return housing_data

def write_housing_data(housing_data):
    housing_data.to_csv(data_location,index=False)


if __name__ == '__main__':
    while True:

        if not path.isfile(data_location):
            print(f'Data does not exist\n')
            write_housing_data(read_housing_data())
            print(f'Data written to {data_location}')

            sleep_interval = DATA_FRESHNESS_INTERVAL_SECONDS            

        else:
            last_update_time = datetime.fromtimestamp(path.getmtime(data_location))
            # datetime.strptime( 
            print(type(last_update_time))
            print(last_update_time)
            print(f'Last updated: {last_update_time}')

            freshness = (datetime.now() - last_update_time )
            print(f'Time passed since updated: {freshness}')

            if freshness>timedelta(seconds=DATA_FRESHNESS_INTERVAL_SECONDS):

                print(f'Data needs refresh\n')
                write_housing_data(read_housing_data())
                print(f'Data written to {data_location}')

                sleep_interval = DATA_FRESHNESS_INTERVAL_SECONDS            
            else: 
                print('Housing data is fresh')
                sleep_interval = DATA_FRESHNESS_INTERVAL_SECONDS-freshness.seconds
                if sleep_interval<0:
                    sleep_interval=0

        print(f'Waiting for {timedelta(seconds=sleep_interval)}')
        sleep(sleep_interval)