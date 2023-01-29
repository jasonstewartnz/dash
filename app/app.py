# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, html, dcc, dash_table, Output, Input
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from snowflake import connector
from os import getenv
from datetime import date, datetime



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
display_cols = ['GEO_NAME','DATE','VALUE']


@app.callback(
    Output("housing-data-table", "data"), 
    Input("geo-level-dropdown", "value"),
    Input("date-picker", "date"))
def display_geo_for_level(level,date_value):             
    # 
    print(date_value)
    date_idx = housing_data['DATE']==datetime.strptime(date_value, '%Y-%m-%d').date()
    level_idx = housing_data['LEVEL']==level

    display_idx = date_idx & level_idx

    data=housing_data.loc[display_idx,display_cols].to_dict('records')
   
    return data


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
            month_format='M-D-Y-Q',
            placeholder='Select a date',
            date=last_date
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