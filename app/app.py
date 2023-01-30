# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, html, dcc, dash_table, Output, Input
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from snowflake import connector
from os import getenv
from datetime import date, datetime, timedelta
import dash_bootstrap_components as dbc
import warnings


def import_housing_data():
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
# transform for state-level time series
housing_data_state_level = housing_data.loc[housing_data['LEVEL']=='State',:].pivot_table(index='DATE',columns='GEO_NAME',values='VALUE')

# National Summary
us_idx = (housing_data['GEO_NAME']=='United States') & \
    (housing_data['LEVEL']=='Country') & \
    (housing_data['DATE']==last_date)
us_latest = housing_data.loc[us_idx,'VALUE'].values[0]
us_summary_card = dbc.Card(
    dbc.CardBody(
        [
            html.H4("US Overall:", id="card-title"),
            html.H2(f'{round(us_latest)}', id="card-value"),
            html.P(f"Value for US overall on {last_date}", id="card-description")
        ]
    )
)

# state data
default_selected_states = ['California']
state_list = [state for state in housing_data_state_level.columns]

print('Housing data imported')

@app.callback(
    Output("housing-data-table", "data"), 
    Input("geo-level-dropdown", "value"),
    Input("date-picker", "date"),
    Input("order-by-dropdown", "value"))
def display_geo_for_level(level,date_value,order_by):
    # 
    print(f'Last date found {date_value}')
    date_idx = housing_data['DATE']==datetime.strptime(date_value, '%Y-%m-%d').date()
    level_idx = housing_data['LEVEL']==level

    display_idx = date_idx & level_idx

    display_data=housing_data.loc[display_idx,display_cols]
    if display_data.shape[0]==0:
        # numpy.repeat
        display_data = pd.DataFrame(data=[['<No data to display>','<No data to display>','<No data to display>']],columns=display_cols)
    else: 
        display_data.sort_values(order_by,inplace=True)
   
    return display_data.to_dict('records')

@app.callback(
    Output('geo-value-time-series-chart','figure'),
    Input('state-select-list', 'value'),
)
def plot_state_data(selected_states):

    selected_idx = housing_data_state_level.columns.isin(selected_states)
    hd_selected_states = housing_data_state_level.loc[:,selected_idx]

    fig = px.line( hd_selected_states )

    return fig

app.layout = html.Div(
    className="app-header",
    children=[
    html.H1(children='Housing indexes!', className="app-header--title"),
    
    html.Div(children='''
        A web application framework for your housing price data.
    '''),    

    dcc.Markdown('''
        #### Housing Index Data
        Housing index values by geography shown on a given date
    '''
    ),
    
    dbc.Row([
        dbc.Col(html.Div("")), 
        dbc.Col(us_summary_card), 
        dbc.Col(html.Div("")),
    ]),
    dbc.Row([
        dcc.Tabs(
            id="housing-tabs",         
            className='data-tab-collection',
            children=[        
            dcc.Tab(            
                label='Housing Index table', 
                className="data-tab",
                children=html.Div([
                    dcc.Dropdown(levels, placeholder='State', id='geo-level-dropdown'),
                    html.Div(id='dd-output-container'),            
                    html.Div([

                        'Select date: ',

                        dcc.DatePickerSingle(
                            id='date-picker',
                            month_format='M-D-Y',
                            placeholder='M-D-Y',
                            date=last_date,
                            min_date_allowed=first_date.strftime('%Y-%m-%d'),
                            max_date_allowed=last_date.strftime('%Y-%m-%d'),
                            disabled_days=disable_dates
                        ),

                        'Order by',

                        dcc.Dropdown(['GEO_NAME','VALUE'], 
                            placeholder='Order By', 
                            id='order-by-dropdown',
                            value='GEO_NAME',
                            style={'width': '200px'},
                            ),

                        dash_table.DataTable(
                            id='housing-data-table', 
                            columns=[{'name':col,'id':col} for col in display_cols],
                        )
                    ],
                    className='data-tab-div'
                    ),
                ])
            ),
            dcc.Tab(
                label='State History Comparer', 
                className="data-tab",
                children=html.Div([
                    html.H3('Value over time for series'),

                    html.Div([
                        dcc.Dropdown(state_list, default_selected_states, 
                            multi=True,
                            id='state-select-list')
                    ]),

                    dcc.Graph(
                        id='geo-value-time-series-chart',
                                        
                        figure=plot_state_data(default_selected_states)
                    )
                ],
                className='data-tab-div'
                ),
            )
        ]),
    ])
])


if __name__ == '__main__':
    # app.run_server(debug=True)
    app.run_server(host='0.0.0.0',debug=True, port=8050)