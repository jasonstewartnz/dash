# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, html, dcc, dash_table, Output, Input
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from snowflake import connector
from os import getenv
from datetime import date, datetime, timedelta



def import_housing_data():
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

    housing_data = pd.read_sql( sql, ctx )

    return housing_data

def gen_geo_table():
    data=housing_data.to_dict('records'),
    columns=[{'name':col,'id':col} for col in display_cols],
    style_cell=dict(textAlign='left'),
    style_header=dict(backgroundColor="paleturquoise"),
    style_data=dict(backgroundColor="lavender")       

## Initialize
app = Dash(__name__)

housing_data = import_housing_data()
levels = housing_data['LEVEL'].unique()
last_date = housing_data['DATE'].max()
first_date = housing_data['DATE'].min()
dates_in_range = [first_date + timedelta(days=x) for x in range((last_date-first_date).days + 1)]
disable_dates = [date.strftime('%Y-%m-%d') for date in dates_in_range if date not in housing_data['DATE'].values]
display_cols = ['GEO_NAME','DATE','VALUE']


@app.callback(
    Output("housing-data-table", "data"), 
    Input("geo-level-dropdown", "value"),
    Input("date-picker", "date"))
def display_geo_for_level(level,date_value):             
    # 
    print(f'Last date found {date_value}')
    date_idx = housing_data['DATE']==datetime.strptime(date_value, '%Y-%m-%d').date()
    level_idx = housing_data['LEVEL']==level

    display_idx = date_idx & level_idx

    display_data=housing_data.loc[display_idx,display_cols]
    if display_data.shape[0]==0:
        # numpy.repeat
        display_data = pd.DataFrame(data=[['<No data to display>','<No data to display>','<No data to display>']],columns=display_cols)        
   
    return display_data.to_dict('records')


app.layout = html.Div(children=[
    html.H1(children='Housing indexes!'),
    
    html.Div(children='''
        A web application framework for your housing price data.
    '''),

    html.Div([
        dcc.Dropdown(levels, placeholder='State', id='geo-level-dropdown'),
        html.Div(id='dd-output-container')
    ]),

    html.Div([
        dcc.DatePickerSingle(
            id='date-picker',
            month_format='M-D-Y',
            placeholder='M-D-Y',
            date=last_date,
            min_date_allowed=first_date.strftime('%Y-%m-%d'),
            max_date_allowed=last_date.strftime('%Y-%m-%d'),
            disabled_days=disable_dates
        )]
    ),

    dash_table.DataTable(
        id='housing-data-table', 
        columns=[{'name':col,'id':col} for col in display_cols],
        style_cell=dict(textAlign='left'),
        style_header=dict(backgroundColor="paleturquoise"),
        style_data=dict(backgroundColor="lavender")            
    )

])


# .loc[housing_data['LEVEL']==levels,display_cols]





if __name__ == '__main__':
    # app.run_server(debug=True)
    app.run_server(host='0.0.0.0',debug=True, port=8050)