__author__ = 'alpiii'

import seaborn
import xml.etree.ElementTree as XmlElement
import urllib
import Exchange as exc
from RSIAnalysis import RSIAnalysis
from ThreeLineBreakAnalysis import ThreeLineBreakAnalysis
from MongoConnector import MongoConnector
import datetime
from matplotlib.patches import Rectangle


def read_file(file_name):
    """
    Parsing the XML file and creating an array of Exchange class instances
    :param file_name: XML file name that stores rates.
    :return: An array of Exchange class instances
    """
    tree = XmlElement.parse(file_name)
    root = tree.getroot()
    values = []  # Exchange class array
    for child in root[2]:
        # creating rate array for each day
        rates = []  # Rate class array for each Exchange day
        for c in child:
            rt = exc.Rate(
                child.attrib['time'],
                c.attrib['currency'],
                float(c.attrib['rate']))
            rates.append(rt)
        values.append(exc.Exchange(child.attrib['time'], rates))
    return values


def download_file(url, file_name):
    """
    Downloads the file
    :param url: url of the XML file
    :param file_name: File name of the XML that will be created on local system
    """
    rate_file = urllib.URLopener()
    rate_file.retrieve(url, file_name)


def get_live_rates():
    """
    Gets the live rates that European Central Bank served.
    Stores the rates in MongoDB.
    """
    file_name = 'eurofxref-hist.xml'
    file_url = 'https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml'
    # downloading the XML file
    download_file(file_url, file_name)
    # parsing the XML file to get the rates
    rate_data = read_file(file_name)
    mc = MongoConnector()
    # removing the previous rates
    mc.mongo_delete_rates()
    # inserting rates to db
    mc.mongo_insert_rates(rate_data)


def rsi_analysis_sample():
    """
    rsi technical analysis sample
    """

    # RSI Parameters
    # Currency code to analyse
    currency = 'USD'
    # RSI number of days for calculation
    number_of_days = 14
    # start and end dates of analyse period
    start_day = datetime.datetime(2015, 1, 1)
    end_day = datetime.datetime(2016, 1, 20)
    # overbought and oversold values
    over_bought = 70
    over_sold = 30

    # Reading rates with given parameters to be analysed
    mc = MongoConnector()
    rates = mc.mongo_get_rates(currency, start_day, end_day, number_of_days)

    # creating RSI instance and analysing the data
    rsi = RSIAnalysis(number_of_days, rates, start_day)
    result = rsi.analyse()

    # creating the chart of the result
    values = []  # RSI result values for each day
    dates = []  # analysed days to be shown on chart
    prices = []  # real end-day prices for each day
    for rs in result:
        values.append(rs.value)
        dates.append(rs.day)
        prices.append(rs.price)

    # creating a chart with two subplots
    # one for RSI values
    # other one for real end-day prices
    fig, axes = seaborn.plt.subplots(2, 1)
    locs, labels = seaborn.plt.xticks()
    seaborn.plt.setp(labels, rotation=45)
    axes[0].plot(dates, values)
    axes[0].set_title('RSI(' + str(number_of_days) +
                      ') Overbought: ' + str(over_bought) +
                      ' Oversold: ' + str(over_sold))
    axes[0].set(xticklabels=[])
    axes[0].set(ylim=(0, 100))
    axes[0].plot(dates, [over_bought] * len(dates))
    axes[0].plot(dates, [over_sold] * len(dates))
    axes[1].plot(dates, prices)
    axes[1].set_title('Real Rates (EUR/' + currency + ')')
    # saving chart as PNG image file
    fig.savefig('RSI_Result.png', dpi=400, bbox_inches='tight')
    print("Created chart PNG file.")


def three_line_break_analysis_sample():
    """
    three line break technical analysis sample
    """

    # Three Line Break Parameters
    # Currency code to analyse
    currency = 'USD'
    # number of days to control
    line_break_control_count = 3
    # start and end dates of analyse period
    start_day = datetime.datetime(2015, 6, 1)
    end_day = datetime.datetime(2016, 1, 20)

    # Reading rates with given parameters to be analysed
    mc = MongoConnector()
    rates = mc.mongo_get_rates(currency, start_day,
                               end_day, line_break_control_count)

    # creating TLB instance and analysing the data
    tlb = ThreeLineBreakAnalysis(rates, line_break_control_count, start_day)
    result = tlb.analyse()

    # creating the chart of the result
    fig = seaborn.plt.figure()
    locs, labels = seaborn.plt.xticks()
    fig.axes[0].set_title('Three Line Break (' +
                          str(line_break_control_count) +
                          ')     EUR/' + currency + '     ' +
                          start_day.strftime('%d/%m/%Y') + ' - ' +
                          end_day.strftime('%d/%m/%Y'))
    fig.axes[0].set(xticklabels=[])

    a = 0
    for rs in result:
        fig.axes[0].plot([a, a], [rs.min_price, rs.max_price], linewidth=0)
        if rs.color == 'G':
            # increases are green
            fig.axes[0].add_patch(Rectangle((a, rs.min_price), 1,
                                            rs.max_price - rs.min_price,
                                            fill=False, edgecolor='green',
                                            lw=1))
        else:
            # decreases are red
            fig.axes[0].add_patch(Rectangle((a, rs.min_price), 1,
                                            rs.max_price - rs.min_price,
                                            fill=False, edgecolor='red',
                                            lw=1))
        a += 1

    # saving chart as PNG image file
    fig.savefig('TLB_Result.png', dpi=400, bbox_inches='tight')
    print("Created chart PNG file.")


if __name__ == '__main__':

    # getting the live rates and storing them to MongoDB
    get_live_rates()

    rsi_analysis_sample()

    three_line_break_analysis_sample()
