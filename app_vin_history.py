import math
import yaml
import pandas as pd
import numpy as np
from bokeh.models import Span, LabelSet, CategoricalColorMapper, TapTool, GMapPlot, GMapOptions, DataRange1d, PanTool, WheelZoomTool, ColumnDataSource
from bokeh.layouts import column, layout
from bokeh.plotting import figure
from bokeh.themes import Theme
from bokeh.models.glyphs import Circle
from bokeh.models.widgets import RadioButtonGroup, Div, DataTable,DateFormatter, TableColumn, NumberFormatter
from bokeh.models.ranges import FactorRange
# from bokeh.models.widgets.inputs import Slider
# Local imports
import load_data
import bokeh_plots

# disable pandas chained warning
pd.options.mode.chained_assignment = None
pd.set_option('display.max_colwidth', -1)
pd.options.display.max_columns = 999




# Utility function
def bokeh_time(dtstr):
    return pd.to_datetime(dtstr).value / 1e6

def modify_doc(doc):
    global current_dtc
    global current_part
    current_part = ""
    def update_part(selected=None):
        global current_part
        global text_narrative
        if len(cds.selected['1d']['indices']) > 0:
            ind = cds.selected['1d']['indices'][0]
            part = claims_vin.loc[ind, 'PART_NUMBER']
            #print(part)
            #print(current_part)
            if current_part is not part:
                # slider_parts_dtcstopped.value = 0
                data_qna = load_data.load_qna(vin, part)
                #print(data_qna)
                if data_qna.shape[0] > 0:
                    data_qna = data_qna[["Narrative Complaint", "Cause", "Correction"]]
                    # print(data_qna.to_html().replace('class="dataframe"','class="table"',1))
                    text_narrative.text = data_qna.to_html().replace('class="dataframe"', 'class="table table-hover"',
                                                                     1)
                else:
                    text_narrative.text = ""
        else:
            part = claims_vin.loc[0, 'PART_NUMBER']
        data_parts_dtcstopped_counts_selected = data_parts_dtcstopped_counts.loc[
            (data_parts_dtcstopped_counts["PART_NUMBER"] == part) & (data_parts_dtcstopped_counts["1_top"] >= slider_parts_dtcstopped.value)].reset_index()
        #print(data_parts_dtcstopped_counts_selected)
        global plot_dtcstopped_part
        #print(data_parts_dtcstopped_counts_selected.shape[0])
        if data_parts_dtcstopped_counts_selected.shape[0]>0:
            plot_dtcstopped_part.x_range.factors = data_parts_dtcstopped_counts_selected['DTC_FULL'].tolist()
            source_bar_parts.data = source_bar_parts.from_df(data_parts_dtcstopped_counts_selected)
            # slider_parts_dtcstopped.end = data_parts_dtcstopped_counts_selected["1_top"].max()
        else:
            #print("test")
            source_bar_parts.data = source_bar_parts.from_df(pd.DataFrame(columns=data_parts_dtcstopped_counts_selected.columns))
            # slider_parts_dtcstopped.end = 1
        #text_part_information.text = "Selected part: " + parts_vin[part_selection_button.active] + "<br /> Additional information: <br />" + str(data_parts_info.loc[data_parts_info.PART_NUMBER == parts_vin[part_selection_button.active],['SMLC.Name']])
        #print(parts_vin[part_selection_button.active])


        plot_dtcstopped_part.title.text = "DTCs stopped/continued after exchange of " + part
        current_part = part

    def update_dtc(dtc, selected=None):
        # print(new)
        # print(new['1d']['indices'][0])
        global current_dtc
        global data_dtcs_dtcstopped_counts
        if dtc is not current_dtc:
            slider_dtcs_dtcstopped.value = 0
            data_dtcs_dtcstopped_counts = calc_counts(load_data.load_dtc_labeled_dtc(dtc))
        current_dtc = dtc
        plot_dtcstopped_dtc.title.text = "Parts successfully resolving " + dtc
        #print(load_data.load_dtc_labeled_dtc(dtc))
        data_dtcs_dtcstopped_counts_selected = data_dtcs_dtcstopped_counts.loc[
            (data_dtcs_dtcstopped_counts["DTC_FULL"] == dtc) & (data_dtcs_dtcstopped_counts["1_top"] >= slider_dtcs_dtcstopped.value)].reset_index()

        plot_dtcstopped_dtc.x_range.factors = data_dtcs_dtcstopped_counts_selected['PART_NUMBER'].tolist()
        source_bar_dtcs.data = source_bar_dtcs.from_df(data_dtcs_dtcstopped_counts_selected)
        slider_dtcs_dtcstopped.end = data_dtcs_dtcstopped_counts_selected["1_top"].max()

    def update_all():
        update_part()
        global current_dtc
        current_dtc="none"
        update_dtc(dtcs_vin[0])

    # print(doc.session_context.request.arguments)
    vin = doc.session_context.request.arguments['VIN'][0]
    # print(vin)
    data_vin = load_data.load_vin_labeled(vin)
    # Set up data for choosing part
    parts_vin = data_vin.PART_NUMBER.dropna().unique().tolist()

    # Getting stopped part data for all the parts associated with the vin
    data_parts = load_data.load_part_labeled(parts_vin)
    data_parts_info = load_data.load_part_info(parts_vin)
    # print(data_parts)
    dtcs_vin = data_vin.DTC_FULL.dropna().unique().tolist()

    data_ewt = load_data.load_ewt(vin)

    #data_dtcs = data_vin
    #data_dtcs = load_data.load_dtc_labeled(dtcs_vin)

    ####################################################################################################################
    ####################################################################################################################

    # Convert Date data into bokeh intepretable format
    data_vin['DTC_DATE'] = pd.to_datetime(data_vin['EVENT_OCCURRED']).dt.date

    plot_history = figure(x_axis_type="datetime", y_range=sorted(set(data_vin['DTC_FULL'])),tools='pan,wheel_zoom,box_zoom',
                          title="Vehicle history")
    # We're getting data from the given dataframe
    source_history = ColumnDataSource(data=data_vin)
    bokeh_plots.scatter_with_hover(source_history, 'DTC_DATE', 'DTC_FULL', plot_history,
                                   cols=['ECU', 'EVENT_OCCURRED', 'DTC_FULL', 'FAULT_NAME', 'LAMP_NAME',
                                         'ODO_MILES', 'DTC_PART_NUMBER', 'SW_VERSION', 'DIAGNOSTIC',
                                         'DTC_STOPPED'])

    # Set up data for labeling the parts
    data_ewt = data_ewt.rename(columns={"PART NO" : "PART_NUMBER","REPAIR-DT" : "REPAIR_DT"})
    claims_vin = data_ewt.merge(data_parts_info,how='left',on="PART_NUMBER")
    claims_vin['PRAS'] = [load_data.load_pras(vin, x).append(pd.DataFrame([['NaN']],columns=['ROOT CAUSE CATEGORY']),ignore_index=True).values[0,0] for x in claims_vin["PART_NUMBER"]]
    #print(claims_vin)
    #claims_vin = claims_vin.replace(np.nan,0,regex=True)
    #print(claims_vin)
    claims_vin_2 = data_vin[["RELATED_CLAIM", "PART_NUMBER", "REPAIR_DT"]]
    claims_vin_2.drop_duplicates(inplace=True)
    claims_vin_2.dropna(inplace=True)
    claims_vin_2['WORKSHOP_DT'] = [bokeh_time(x) for x in pd.to_datetime(claims_vin_2['REPAIR_DT']).dt.date]
    claims_vin['REPAIR_DT'] = pd.to_datetime(claims_vin['REPAIR_DT']).dt.date
    #print(claims_vin)
    #print(type(claims_vin.loc[0,"REPAIR_DATE"]))
    # Extracting the different repair dates
    single_dates_sample_vin = pd.DataFrame(columns=claims_vin_2.columns)

    # Grouping of repairs on the same date
    multiple_claims = claims_vin_2.groupby(["REPAIR_DT"]).size()
    #print(multiple_claims)
    # Setting up claims related to multiple parts
    for index, row in claims_vin_2.iterrows():
        parts_in_claim = multiple_claims[row['REPAIR_DT']]
        if parts_in_claim > 1:
            repair = single_dates_sample_vin.loc[single_dates_sample_vin["REPAIR_DT"] == row['REPAIR_DT']]
            if len(repair.index) != 0:
                # appending multiple parts to one date
                single_dates_sample_vin["PART_NUMBER"].loc[repair.index] = single_dates_sample_vin["PART_NUMBER"].loc[
                                                                               repair.index].astype(str) + "," + row[
                                                                               'PART_NUMBER']
                #if row["CONTI_PART"] == 1:
                #    single_dates_sample_vin["CONTI_PART"].loc[repair.index] = 1
            else:
                single_dates_sample_vin = single_dates_sample_vin.append(row)
        else:
            single_dates_sample_vin = single_dates_sample_vin.append(row)

    # Setting up Bokeh data source for labels
    #print(single_dates_sample_vin)
    cds_data = single_dates_sample_vin.reset_index()
    #print(cds_data)
    #cds_data = cds_data.merge(data_parts_info,how='inner',on="PART_NUMBER")
    cds = ColumnDataSource(data=claims_vin)
    #print(cds_data)
    labels = LabelSet(x='REPAIR_DT', y=1, text='PART_NUMBER', level='glyph',
                      source=ColumnDataSource(single_dates_sample_vin), render_mode='canvas', angle=90, angle_units="deg", text_font_size="8pt",
                      text_color='#7f7f7f')

    for index, row in single_dates_sample_vin.iterrows():
        # x axis position of vertical lines
        date = bokeh_time(row['REPAIR_DT'])
        # Vertical line
        span = Span(location=date, dimension='height', line_dash='dashed', line_color= '#7f7f7f')
        # Add vertical lines to plot
        plot_history.add_layout(span)

    # Add label to lines
    plot_history.add_layout(labels)

    # Add clickable bubbles to labels
    #colors = brewer["Spectral"][3]

    color_mapper = CategoricalColorMapper(factors=[0, 1], palette=['#1d9b8e', '#ffa51d'])
    #color_mapper = CategoricalColorMapper(palette="Viridis8")
    glyph = Circle(x='REPAIR_DT', fill_color={'field': 'CONTI_PART', 'transform': color_mapper}, y=0.5, size=30,
                   name="parts", fill_alpha=0.8, line_alpha = 0)


    plot_history.add_glyph(cds, glyph)

    ####################################################################################################################
    ####################################################################################################################
    def calc_counts(data):
        res = data.pivot_table(index=['PART_NUMBER', 'DTC_FULL'], columns='DTC_STOPPED',
                                                            fill_value=0, values='EVENT_OCCURRED', aggfunc='count')
        res = res.reset_index()


        if len(res.columns.values)==3:

            if 0 in res.columns.values:
                res['1'] = 0
            else:
                res['0'] = 0

        res = res.rename(columns={1:'1',0 : '0'})
        res['1_top'] = res['1'] + res['0']
        return(res)


    # Add barplot for DTC stopped wrt parts
    #data_parts_dtcstopped_counts = data_parts.pivot_table(index=['PART_NUMBER', 'DTC_FULL'], columns='DTC_STOPPED',
    #                                                      fill_value=0, values='EVENT_OCCURRED', aggfunc='count')
    #data_parts_dtcstopped_counts = data_parts_dtcstopped_counts.reset_index()
    #data_parts_dtcstopped_counts.columns = ['PART_NUMBER', 'DTC_FULL', '0', '1']
    #data_parts_dtcstopped_counts['1_top'] = data_parts_dtcstopped_counts['1'] + data_parts_dtcstopped_counts['0']
    # print(data_parts_dtcstopped_counts)
    #print(data_parts)
    data_parts_dtcstopped_counts = calc_counts(data_parts)
    #print(data_parts_dtcstopped_counts)
    # slider_parts_dtcstopped = Slider(start=0,
    #                                  end=data_parts_dtcstopped_counts["1_top"].max(), value=0, step=1, title="Cut off",
    #                                  orientation="vertical",width=200)
    #data_parts_dtcstopped_counts = data_parts_dtcstopped_counts.loc[data_parts_dtcstopped_counts["1_top"] > 30]

    data_parts_dtcstopped_counts_selected = data_parts_dtcstopped_counts.loc[
        (data_parts_dtcstopped_counts["PART_NUMBER"] == parts_vin[0])]

    source_bar_parts = ColumnDataSource(data_parts_dtcstopped_counts_selected)

    # plot_dtcstopped_part = Bar(source_bar_parts,values='count',stack='DTC_STOPPED', label='DTC_FULL')
    global plot_dtcstopped_part
    plot_dtcstopped_part = figure(title="DTCs stopped/continued after exchange of selected part",
                                  x_range=FactorRange(
                                      factors=list(data_parts_dtcstopped_counts_selected.DTC_FULL)),
                                  tools='pan,wheel_zoom,box_zoom')

    plot_dtcstopped_part.vbar(source=source_bar_parts, x='DTC_FULL', top="1_top", bottom="0", width=0.5,
                              fill_color="#ffbe5b", line_alpha=0, legend="DTC Stopped")
    plot_dtcstopped_part.vbar(source=source_bar_parts, x='DTC_FULL', top="0", bottom=0, width=0.5,fill_color="#ff9900",
                              line_alpha=0,legend="DTC Continued")

    # plot_dtcstopped_part.add_layout(labels)


    ####################################################################################################################
    ####################################################################################################################


    cols = ['DTC_STOPPED','PART_NUMBER','DTC_FULL','0','1','1_top']
    data_dtcs_dtcstopped_counts = pd.DataFrame(columns=cols)
    # Add barplot for DTC stopped wrt dtcs


    # print(data_dtcs_dtcstopped_counts)

    #data_dtcs_dtcstopped_counts = data_dtcs_dtcstopped_counts.loc[data_dtcs_dtcstopped_counts["1_top"] > 10]

    data_dtcs_dtcstopped_counts_selected = data_dtcs_dtcstopped_counts.loc[
        (data_dtcs_dtcstopped_counts["DTC_FULL"] == dtcs_vin[0])]
    slider_dtcs_dtcstopped = Slider(start=0, end=data_dtcs_dtcstopped_counts_selected["1_top"].max(), value=0, step=1,
                                    title="Cut off",
                                    orientation="vertical")

    source_bar_dtcs = ColumnDataSource(data_dtcs_dtcstopped_counts_selected)

    # plot_dtcstopped_part = Bar(source_bar_dtcs,values='count',stack='DTC_STOPPED', label='DTC_FULL')
    global plot_dtcstopped_dtc
    plot_dtcstopped_dtc = figure(title="Parts successfully resolving selected DTC", x_range=FactorRange(
        factors=list(data_dtcs_dtcstopped_counts_selected.PART_NUMBER)),
                                 tools='pan,wheel_zoom,box_zoom')


    plot_dtcstopped_dtc.vbar(source=source_bar_dtcs, x='PART_NUMBER', top="1_top", bottom="0", width=0.5,fill_color="#ffbe5b",
                             line_alpha=0, legend="DTC stopped")
    plot_dtcstopped_dtc.vbar(source=source_bar_dtcs, x='PART_NUMBER', top="0", bottom=0, width=0.5,
                             fill_color="#ff9900",
                             line_alpha=0, legend="DTC continued")



    ####################################################################################################################
    ####################################################################################################################


    map_options = GMapOptions(lat=data_vin.loc[0, 'LADITUDE'], lng=data_vin.loc[0, 'LONGITUDE'], map_type="roadmap",
                              zoom=11)
    plot_map_dtc = GMapPlot(x_range=DataRange1d(), y_range=DataRange1d(), map_options=map_options, width=900)
    plot_map_dtc.api_key = "AIzaSyD_umaiKlb4bcN2EGcH5Pe04CXgzloU58g"

    # source_map_dtc = ColumnDataSource(data_vin)
    plot_map_dtc_points = Circle(x='LONGITUDE', y='LADITUDE', size=15, fill_color='#ff9900',
                                 line_color=None)
    plot_map_dtc.add_glyph(source_history, plot_map_dtc_points)
    plot_map_dtc.add_tools(PanTool(), WheelZoomTool())

    ###############################
    ### Interactions ##############
    ###############################

    # Additional interaction to dtcs

    taptool_history_dtc = TapTool()

    def dtc_selection_change(attr, old, new):
        if len(new['1d']['indices']) > 0:
            ind = new['1d']['indices'][0]
            dtc = data_vin.loc[ind, 'DTC_FULL']
            #print(dtc)
            update_dtc(dtc)

    source_history.on_change('selected', dtc_selection_change)

    plot_history.add_tools(taptool_history_dtc)



    # Adding buttons for choosing part




    part_selection_button = RadioButtonGroup(labels=parts_vin, active=0,width=700)

    def part_selection_button_change(attrname, old, new):
        part = parts_vin[part_selection_button.active]
        #print(part)
        ind = [i for i,x in enumerate(cds_data['PART_NUMBER']) if part in x][0]
        global button_changed
        button_changed = True
        cds.selected = {'0d': {'glyph': None, 'get_view': {}, 'indices': []}, '1d': {'indices': [ind]}, '2d': {'indices': {}}}
        update_part()


    part_selection_button.on_change('active', part_selection_button_change)

    global button_changed
    button_changed = False

    def part_selection_bubble_change(attrname, old, new):
        #print(new)
        global button_changed
        if (len(new['1d']['indices']) > 0) and not button_changed:

            ind = new['1d']['indices'][0]
            part = claims_vin.loc[ind, 'PART_NUMBER']
            #print("test")
            #part_selection_button.active = [i for i, x in enumerate(parts_vin) if x in part][0]
            update_part()
            #print(dtc)

        #button_changed= False



    cds.on_change('selected', part_selection_bubble_change)


    # Changing cut-off value

    def part_slider_change(attr,old,new):
        update_part()

    # slider_parts_dtcstopped.on_change('value',part_slider_change)

    def dtc_slider_change(attr,old,new):
        #print(type(source_bar_dtcs.data["DTC_FULL"].values[0]))
        update_dtc(current_dtc)
    slider_dtcs_dtcstopped.on_change('value',dtc_slider_change)

    ####################################################################################################################
    ####################################################################################################################

    # Adding textbased information

    vin_info = load_data.load_single_dtc(vin)

    text_vehicle_information = Div(
        text="""<h3><span style="color: #ff9900;"><strong>VIN</strong></span><strong>""" + vin_info.VIN8[0] +
             """ &nbsp;<span style="color: #ff9900;">Engine</span></strong><strong>""" + vin_info.ENG[0] +
             """ &nbsp;</strong><strong><span style="color: #ff9900;">Transmission</span></strong><strong>""" + vin_info.TRANS[0] +
             """ &nbsp;<span style="color: #ff9900;">Body</span></strong><strong>""" + vin_info.BODY[0] + """</strong></h3><h3><strong>""" +
             """ &nbsp;</strong><strong><span style="color: #ff9900;">MY</span></strong><strong>""" + str(vin_info.MY[0]) +
             """ &nbsp;</strong><strong><span style="color: #ff9900;">Model</span></strong><strong>""" + vin_info.MODEL[0] +
             """ &nbsp;</strong><strong><span style="color: #ff9900;">Plant</span></strong><strong>""" + vin_info.loc[0,"PLANT NAME"] + """</strong></h3><h3><strong>""" +
             """ &nbsp;</strong><strong><span style="color: #ff9900;">BuiltDate</span></strong><strong>""" + vin_info.BUILT_DATE[0] +
             """ &nbsp;</strong><strong><span style="color: #ff9900;">SoldDate</span>""" + vin_info.SOLD_DATE[0] +
             """ &nbsp;</strong><strong><span style="color: #ff9900;">SalesType</span>""" + vin_info.SALES_TYPE_DES[0] +
             """</strong></h3>""",
        width=1000)
    text_interesting_vins = Div(text="Interesting VINs to search for: GC303533, HR591701, HR512841, HR526221, HR511073, HR501257, HC633427, HR516718," +
             "Boring VINS: GC300412,GC300423", width=1000)
    #print(cds.column_names)
    columns = [
        TableColumn(field="REPAIR_DT", title="Repair Date", formatter=DateFormatter(format='mm/dd/yy'),width=120),
        TableColumn(field="PART_NUMBER", title="Part Number",width=130),
        TableColumn(field="AMOUNT(USD)", title="Amount (USD)",formatter=NumberFormatter(format='$0,0.00'),width=130),
        TableColumn(field="MLG", title="Mileage",formatter=NumberFormatter(format='0,0'),width=80),
        TableColumn(field="LCC.Name", title="LCC Name", width=360),
        TableColumn(field="LCC", title="LCC", width=60),
        TableColumn(field="SMLC.Name", title="SMLC Name", width=300),
        TableColumn(field="SMLC", title="SMLC", width=80),
        TableColumn(field="CLAIM", title="Claim", width=80),
        TableColumn(field="PRAS", title="PRAS", width=50),
    ]
    text_case_information = DataTable(source=cds,columns=columns,width=1000,editable=True)
    text_dtc_information = Div(text="Selected DTC: " + dtcs_vin[0])
    global text_narrative
    text_narrative = Div(text="",width=1700)
    #SELECT * FROM `qna` WHERE `VINLAST8`="HR512841" AND `PART_NUMBER`="6EV02PD2AE"

    ####################################################################################################################
    ####################################################################################################################

    def style_my_plots(fig):
        fig.background_fill_color = "white"  # "#f8f8f8"
        fig.xaxis.major_label_orientation = math.pi / 2
        fig.xaxis.major_label_text_color = '#7f7f7f'
        fig.yaxis.major_label_text_color = '#7f7f7f'
        fig.xaxis.minor_tick_line_color = '#7f7f7f'
        fig.yaxis.minor_tick_line_color = '#7f7f7f'
        fig.xaxis.major_tick_line_color = '#7f7f7f'
        fig.yaxis.major_tick_line_color = '#7f7f7f'
        fig.xaxis.axis_line_color = '#7f7f7f'
        fig.yaxis.axis_line_color = '#7f7f7f'
        fig.title.text_color = '#ff9900'
        fig.title.text_font_size = '14pt'
        fig.width=700

    style_my_plots(plot_history)
    style_my_plots(plot_dtcstopped_part)
    style_my_plots(plot_dtcstopped_dtc)

    # Layout of the plots and widgets
    doc.add_root(layout([
        [plot_history, column(text_interesting_vins ,text_vehicle_information, text_case_information)],
        [text_narrative],
        [slider_parts_dtcstopped,plot_dtcstopped_part, plot_dtcstopped_dtc,slider_dtcs_dtcstopped],
        [plot_map_dtc],
    ]))

    update_all()

    doc.theme = Theme(json=yaml.load("""
        attrs:
            Figure:
                background_fill_color: "#DDDDDD"
                outline_line_color: white
                toolbar_location: above
                height: 500
                width: 800
            Grid:
                grid_line_dash: [6, 4]
                grid_line_color: white
    """))