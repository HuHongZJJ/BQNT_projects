import pandas as pd
import numpy as np
import ipywidgets as widgets
from collections import OrderedDict
from ipydatagrid import DataGrid,TextRenderer, Expr
import bql
from logger import ApplicationLogger
from constants import STATES
from bqplot import ColorScale, OrdinalScale, LinearScale, OrdinalColorScale

class Application:
    """ 
    Parameters
    ----------

    """

    def __init__(self,
                 bq,
                 ud_main_group_values
                 ):
        self._bq=bq
        self._ud_main_group_values=ud_main_group_values
        self._logger=ApplicationLogger()
        self._spinner=self._build_spinner()
        self._build_app()
        
    
                      
    def _build_spinner(self, color='slategray',textcolor='slategray'):
        
        """Build the spinner: will show when refreshing the data """
        return widgets.HTML("""
                <h5 style="color:{textcolor};">Updating...</h>
                <i class="fa fa-spinner fa-spin fa-fw" style="color:{color};"></i>
                """.format(color=color,textcolor=textcolor),
                layout=widgets.Layout(padding='0px 0px 40px 0px',
                                min_width='180px',
                                width='180px',
                                height='30px',
                                min_height='30px',
                                overflow_x='hidden',
                                overflow_y='hidden'))     
    def _build_app(self):
        
        """Build the app """
        self.widgets = OrderedDict()
        
        self._build_control_panel()
        self._build_display_panel()
        
        self.app =widgets.VBox( [self.widgets['control_panel_box'],self.widgets['display_panel_box'],self._logger.get_widget()])

    
    def _reload_main_group_cde( self,evt):
        self._logger.log_message('Reload UD_MAIN_GROUP CDE')
        self.widgets['control_panel_box_ud_main_group_reload_spinner'].children=[self._spinner]
        try:
            bq=self._bq
            cde_item = bq.data._cde('UD_MAIN_GROUP', fill='prev')

            bql_universe =bq.univ.filter( bq.univ.fundsuniv(['active','primary']),cde_item!= bql.NA)

            bql_request = bql.Request(bql_universe, {'UD_MAIN_GROUP':bq.data.id().group(cde_item).count()['Value']},
                                      with_params = dict(fill='prev', mode='cached')
                             )
            bql_response = bq.execute(bql_request)
            self._ud_main_group_values =list(bql_response[0].df().index)
            self.widgets['control_panel_box_ud_main_group_value'].options=self._ud_main_group_values
            self._logger.log_message('Done')
        
        except Exception as e :
            self._logger.log_message('Issue when retrieving the data :{}'.format(str(e)),color ='red')
        self.widgets['control_panel_box_ud_main_group_reload_spinner'].children=[] 
    def _build_control_panel(self):
        
        """Construct the control panel."""
        self.widgets['control_panel_box']= widgets.Tab([])
        self.widgets['control_panel_box'].set_title(0,'Control')
        self.widgets['control_panel_box_minimum_capital_label']=widgets.HTML('Minimum Market Cap $MM')
        self.widgets['control_panel_box_minimum_capital_value']=widgets.IntText(0 , layout ={'width':'66px'})
        self.widgets['control_panel_box_ud_main_group_label']=widgets.HTML('UD_MAIN_GROUP')
        self.widgets['control_panel_box_ud_main_group_value']=widgets.Dropdown(options=self._ud_main_group_values,layout={'width':'190px'})
        self.widgets['control_panel_box_ud_main_group_reload']=widgets.Button(description='Reload Main Group', button_style='warning', layout={'width':'150px'})
        self.widgets['control_panel_box_ud_main_group_reload'].on_click(self._reload_main_group_cde)
        self.widgets['control_panel_box_ud_main_group_reload_spinner']=widgets.VBox([])
        self.widgets['control_panel_box_refresh']= widgets.Button(description='Refresh', button_style='success', layout={'width':'150px'})
        self.widgets['control_panel_box_refresh'].on_click(self._refresh_data)
        self.widgets['control_panel_box'].children= [
            widgets.VBox([
                widgets.HBox([ 
                            self.widgets['control_panel_box_minimum_capital_label'],
                            self.widgets['control_panel_box_minimum_capital_value'],
                            self.widgets['control_panel_box_ud_main_group_label'],
                            self.widgets['control_panel_box_ud_main_group_value'],
                            self.widgets['control_panel_box_ud_main_group_reload'],
                            self.widgets['control_panel_box_ud_main_group_reload_spinner']
                             ]),
                self.widgets['control_panel_box_refresh']
                ])
        ]
    
    def _build_display_panel(self):
        """Build Display Panel  and its components """
        self.widgets['display_panel_box']=widgets.VBox([])
        self.widgets['display_panel_spinner']=widgets.HBox([])
        
        self.widgets['display_panel_box'].children=[ ]
        
    def _find_middle(self, input_list):
        middle = float(len(input_list))/2
        if middle % 2 != 0:
            return input_list[int(middle - .5)]
        else:
            return (input_list[int(middle)] + input_list[int(middle-1)])/2
        
    def _build_datagrid(self,data,column_size=200) :

        """
        Builds a DataGrid component for vizualisation
        """
        # specify widths for individual columns using their names as keys
       
        col_widths = {'key': 100,
              'name': 200,
              'ud_main_group': 200,
               'ud_sub_group':200}
        
        renderers = {
            'DATE': TextRenderer(format='%Y-%m-%d', format_type='time'),
            'score':TextRenderer(format='.2f', background_color = ColorScale(min =  min(data["score"]), max = max(data["score"])), scheme = "RdYlGn", text_color = 'black'),
            'price': TextRenderer(format='$.2f', text_color = 'White'),
            'trailing 1q performance':TextRenderer(format='.2%', background_color = ColorScale(min =  min(data["trailing 1q performance"]), mid = 0, max = max(data["trailing 1q performance"]), dtype = "percentile"), scheme = "RdGn", text_color = 'black'),
            'div indicated':TextRenderer(format='.2f', background_color = ColorScale(min =  min(data["div indicated"]), mid = self._find_middle(data["div indicated"]), max = max(data["div indicated"])), scheme = "RdYlGn", text_color = 'black'),
            '12-month yield':TextRenderer(format='.2%', background_color = ColorScale(min =  min(data["12-month yield"]), mid = self._find_middle(data["12-month yield"]),  max = max(data["12-month yield"]), dtype = "percentile"), scheme = "RdYlGn", text_color = 'black'),
            '3-year dividend growth':TextRenderer(format='.2%', background_color = ColorScale(min =  min(data["3-year dividend growth"]),mid = 0, max = max(data["3-year dividend growth"]), dtype = "percentile"), scheme = "RdGn", text_color = 'white'),
            'current premium/ discount':TextRenderer(format='.2%', background_color = ColorScale(min =  min(data["current premium/ discount"]), mid = 0, max = max(data["current premium/ discount"]), dtype = "percentile"), scheme = "GnRd", text_color = 'black'),
            '1-year Zscore NAV premium':TextRenderer(format='.2f', background_color = ColorScale(min =  min(data["1-year Zscore NAV premium"]), mid = 0, max = max(data["1-year Zscore NAV premium"])), scheme = "GnRd", text_color = 'black'),
            '90-day Zscore':TextRenderer(format='.2f', background_color = ColorScale(min =  min(data["90-day Zscore"]), mid  = 0, max = max(data["90-day Zscore"])), scheme = "GnRd", text_color = 'black'),
            '5-year NAV std':TextRenderer(format='.2%', background_color = ColorScale(min =  min(data["5-year NAV std"]), mid = self._find_middle(data["5-year NAV std"]) ,max = max(data["5-year NAV std"]), dtype = "percentile"), scheme = "GnYlRd", text_color = "black"),
            "max drawdown":TextRenderer(format='.2%', background_color = ColorScale(min =  min(data["max drawdown"]), max = max(data["max drawdown"]), dtype = "percentile"), scheme = "RdWt", text_color = 'black'),
            '5-year NAV return':TextRenderer(format='.2%', background_color = ColorScale(min =  min(data["5-year NAV return"]), mid = 0, max = max(data["5-year NAV return"]), dtype = "percentile"), scheme = "RdGn", text_color = "white"),
            'current market cap (millions)':TextRenderer(format='$.2f'),
            'assuming 400k trade':TextRenderer(format='.2%')
        }
        
        return DataGrid(dataframe=data,
                        base_column_size=column_size, 
                        selection_mode='cell'
                        ,renderers=renderers,
                        column_widths=col_widths,    
                            )     

    def _refresh_data(self,btn):
        self.widgets['display_panel_box'].children=[self._spinner]
        try:
            self._pull_data()
            self.widgets['display_panel_box'].children=[self.widgets['display_panel_grid']]
        except Exception as e :
            self._logger.log_message('Issue when retrieving the data :{}'.format(str(e)),color ='red')
            self.widgets['display_panel_box'].children=[]
    

        
    def _pull_data(self):
        
        """
        Get all data via BQL
        """
        bq=self._bq
        self._logger.log_message('Pulling Bql Data')
        bql_ud_main_group=self.widgets['control_panel_box_ud_main_group_value'].value
        bql_mkt='{}m'.format(self.widgets['control_panel_box_minimum_capital_value'].value)
        bql_states=STATES        
        bql_divindicated = bq.func.last(bq.func.dropna(bq.data.cash_divs(dates = bq.func.range("-3y","0d"))))*12 / bq.data.px_last()
        bql_navpremium = ((bq.data.px_last() / bq.data.fund_net_asset_val()) - 1)
        bql_percentile_divindicated = bql.let("percentile_divindicated", bq.func.ungroup(bq.func.cut(bq.func.group(bql_divindicated, bq.data._cde('UD_SUB_GROUP')["value"]), 100)))
        bql_percentile_navpremium = bql.let("percentile_navpremium", bq.func.ungroup(bq.func.cut(bq.func.group(bql_navpremium, bq.data._cde('UD_SUB_GROUP')["value"]), 100)))
        bql_score = bql.let("score", (bql_percentile_divindicated["value"] + (100 - bql_percentile_navpremium)))
        bql_item1 = bq.func.groupsort(bq.data.name()["value"], sortby=bql_score["value"], by=bq.data._cde('UD_SUB_GROUP')["value"])['Value']
        bql_price=bq.data.px_last()
        bql_trailing_1q_performance = (bq.data.px_last()/bq.data.px_last(dates = "-3m")) - 1
        bql_12m_yield  = bq.data.dividend_yield(fill = "prev")
        bql_3yr_div_growth = bq.data.is_regular_cash_dividend_per_sh()/bq.data.cash_divs(dates = "-3y") - 1
        bql_1YR_Zscore_navpremium = bq.func.last(bq.func.zscore(bq.func.dropna(bq.func.rolling(bql_navpremium, iterationdates = bq.func.range("-1y","0d")))))
        bql_90days_Zscore_navpremium = bq.func.last(bq.func.zscore(bq.func.dropna(bq.func.rolling(bql_navpremium, iterationdates = bq.func.range("-90d","0d")))))
        bql_5year_nav_std = bq.func.std(bq.func.diff(bq.data.fund_net_asset_val(start ="-5y", end = "0d")))/100
        bql_max_drawdown = bq.data.max_drawdown()
        bql_5year_nav_return = bq.data.fund_net_asset_val()/bq.data.fund_net_asset_val(dates = "-5y") - 1
        bql_cur_mkt_cap = bq.data.cur_mkt_cap()/1000000
        bql_assume_400k_trade = (400000/((bq.func.avg(bq.data.px_volume(dates = bq.func.range('-6m',"0d"))))*bql_price))
        #bql_cost_score = 
        cde_main_group=bq.data._cde('UD_MAIN_GROUP')["value"]
        cde_sub_group=bq.data._cde('UD_SUB_GROUP')["value"]
        bql_items = {
            'name':bql_item1,
            'CDE sub group': cde_sub_group,
            'score':bql_score["value"],
            'price':bql_price['value'],
            'trailing 1q performance':bql_trailing_1q_performance["value"],
            "div indicated":bql_divindicated["value"],
            "12-month yield":bql_12m_yield["value"],
            "3-year dividend growth": bql_3yr_div_growth["value"],
            "current premium/ discount": bql_navpremium['value'],
            "1-year Zscore NAV premium": bql_1YR_Zscore_navpremium["value"],
            "90-day Zscore":bql_90days_Zscore_navpremium["value"],
            "5-year NAV std": bql_5year_nav_std["value"],
            "max drawdown": bql_max_drawdown["value"],
            "5-year NAV return": bql_5year_nav_return["value"],
            "current market cap (millions)": bql_cur_mkt_cap["value"],
            "assuming 400k trade": bql_assume_400k_trade["value"]               
        }
        bql_universe = bq.univ.filter(
            bq.univ.fundsuniv(['Active', 'Primary']),
            bq.func.and_(bq.data.fund_typ() == 'Closed-End Fund', bq.data.fund_geo_focus() == 'U.S.').or_(bq.func.in_(bq.data.fund_geo_focus(), bql_states)).and_(bq.data.cur_mkt_cap() >= bql_mkt).and_(cde_main_group == bql_ud_main_group))

        bql_request = bql.Request(bql_universe, bql_items, with_params = dict(fill='prev', mode='cached'))
        
        self._logger.log_message(bql_request)
        
        bql_response = bq.execute(bql_request)
        data=pd.concat([x.df() for x in bql_response],axis=1,sort=True)
        self._all_data=data
        self._logger.log_message('Pulling Data Finished')
        self.widgets['display_panel_grid']=self._build_datagrid(data)
                                                                        
        


