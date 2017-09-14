from flask import Flask, render_template, request, url_for
from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.resources import INLINE
from bokeh.models import Span, Label, ColumnDataSource, HoverTool, Toggle, CustomJS, CheckboxGroup, LabelSet
from bokeh.models import HoverTool, OpenURL, TapTool
from bokeh.models.glyphs import Text,Circle
from bokeh.util.string import encode_utf8
import load_data
import pandas as pd
import bokeh_plots

app = Flask(__name__)
data = pd.DataFrame()

def bokeh_time(dtstr):
   return pd.to_datetime(dtstr).value / 1e6

@app.route('/')
def index():
    return 'Hello, World'


@app.route('/bokeh')
def bokeh():
    # init a basic bar chart:
    # http://bokeh.pydata.org/en/latest/docs/user_guide/plotting.html#bars
    fig = figure(plot_width=600, plot_height=600)
    fig.vbar(
        x=[1, 2, 3, 4],
        width=0.5,
        bottom=0,
        top=[1.7, 2.2, 4.6, 3.9],
        color='navy'
    )

    # grab the static resources
    js_resources = INLINE.render_js()
    css_resources = INLINE.render_css()

    # render template
    script, div = components(fig)
    html = render_template(
        'index.html',
        plot_script=script,
        plot_div=div,
        js_resources=js_resources,
        css_resources=css_resources,
    )
    return encode_utf8(html)

@app.route('/load_data',methods=['GET','POST'])
def load_data_button():
    global data
    data = load_data.load_sqdf_labeled()
    #data.rename(columns={'PART_NUMBER':'DTC_PART_NUMBER',
    #'PART NO':'PART_NUMBER',
    #                     'REPAIR-DT':'REPAIR_DT',
    #                     'FAULT NAME':'FAULT_NAME',
    #                     'LAMP NAME':'LAMP_NAME'
    #                     }, inplace=True)
    return bokeh()

@app.route('/VIN',methods=['GET','POST'])
def plot_vin():
    #load_data.load_sqdf_labeled()

    if request.method == 'GET':
        svin = request.args.get('vin')
        print(svin)
        if not any(data['VIN8'].str.contains(svin)):
            svin = "GC303533"
    else:
        svin = "GC303533"

    print(svin)

    sample_vin = data.loc[data["VIN8"] == svin]
    sample_vin['DTC_DATE'] = pd.to_datetime(sample_vin['EVENT_OCCURRED']).dt.date
    sample_vin['DTC_DATE'] = pd.to_datetime(sample_vin['DTC_DATE'])
    claims_sample_vin = sample_vin[["RELATED_CLAIM", "PART_NUMBER", "REPAIR_DT"]]
    claims_sample_vin.drop_duplicates(inplace=True)
    claims_sample_vin.dropna(inplace=True)
    claims_sample_vin['WORKSHOP_DATE'] = pd.to_datetime(claims_sample_vin['REPAIR_DT']).dt.date
    claims_sample_vin['WORKSHOP_DATE'] = pd.to_datetime(claims_sample_vin['WORKSHOP_DATE'])
    fig = figure(x_axis_type="datetime", y_range=sorted(set(sample_vin['DTC_FULL'])))
    fig1 = bokeh_plots.scatter_with_hover(sample_vin, 'DTC_DATE', 'DTC_FULL', fig,
                                          cols=['ECU', 'EVENT_OCCURRED', 'DTC_FULL', 'FAULT_NAME', 'LAMP_NAME',
                                                'ODO_MILES', 'DTC_PART_NUMBER', 'SW_VERSION', 'DIAGNOSTIC',
                                                'DTC_STOPPED'])

    single_dates_sample_vin = pd.DataFrame(columns=claims_sample_vin.columns)
    multiple_claims = claims_sample_vin.groupby(["REPAIR_DT"]).size()

    for index, row in claims_sample_vin.iterrows():
        #     if row['CONTI_CLAIM'] == True:
        #         color = 'orange'
        #     else:
        #         color = 'blue'
        parts_in_claim = multiple_claims[row['REPAIR_DT']]
        if (parts_in_claim > 1):
            repair = single_dates_sample_vin.loc[single_dates_sample_vin["REPAIR_DT"] == row['REPAIR_DT']]
            if (len(repair.index != 0)):
                single_dates_sample_vin["PART_NUMBER"].loc[repair.index] = single_dates_sample_vin["PART_NUMBER"].loc[
                                                                               repair.index].astype(str) + "," + row[
                                                                               'PART_NUMBER']
            else:
                single_dates_sample_vin = single_dates_sample_vin.append(row)
        else:
            single_dates_sample_vin = single_dates_sample_vin.append(row)



    cds = ColumnDataSource(data=single_dates_sample_vin[["PART_NUMBER", "WORKSHOP_DATE"]])
    labels = LabelSet(x='WORKSHOP_DATE', y=1, text='PART_NUMBER', level='glyph',
                      source=cds, render_mode='canvas', angle=90, angle_units="deg", text_font_size="8pt")

    for index, row in single_dates_sample_vin.iterrows():
        #     if row['CONTI_CLAIM'] == True:
        #         color = 'orange'
        #     else:
        #         color = 'blue'
        #     width = parts_count[row['PART_NUMBER']]
        date = bokeh_time(row['WORKSHOP_DATE'])
        #     span = Span(location=date, dimension='height', line_color=color, line_dash='dashed', line_width=width)
        span = Span(location=date, dimension='height', line_dash='dashed')
        fig1.add_layout(span)

    fig1.add_layout(labels)

    glyph = Circle(x='WORKSHOP_DATE', y=0.5, size=20, name  = "parts")
    url = "www.hrforecast.de"
    glyph.js_on_event('tap', OpenURL(url=url))
    fig1.add_glyph(cds, glyph)
    tt = TapTool()
    fig1.add_tools(tt)

    url = "www.hrforecast.de"
    taptool = fig1.select(type=TapTool,name = "parts")
    taptool.callback = OpenURL(url=url)

    # grab the static resources
    js_resources = INLINE.render_js()
    css_resources = INLINE.render_css()

    # render template
    script, div = components(fig1)
    html = render_template(
        'index.html',
        plot_script=script,
        plot_div=div,
        js_resources=js_resources,
        css_resources=css_resources,
    )
    return encode_utf8(html)


if __name__ == '__main__':
    app.run(debug=True)
