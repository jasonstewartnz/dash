# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, html, dcc, dash_table, Output, Input
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from snowflake import connector
from os import getenv



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
display_cols = ['GEO_NAME','DATE','VALUE']


@app.callback(
    Output("housing-data-table", "data"), 
    Input("geo-level-dropdown", "value"))
def display_geo_for_level(level):     
    
    data=housing_data.loc[housing_data['LEVEL']==level,display_cols].to_dict('records')
   
    return data


app.layout = html.Div(children=[
    html.H1(children='Housing indexes!'),
    
    html.Div(children='''
        Dash: A web application framework for your housing data.
    '''),

    html.Div([
        dcc.Dropdown(levels, 'Select Level', id='geo-level-dropdown'),
        html.Div(id='dd-output-container')
    ]),

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