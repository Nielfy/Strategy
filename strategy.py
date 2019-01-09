#回测金额500000，2015年

import jqdata
import math
from jqlib.technical_analysis import *
import datetime
import numpy


def initialize(context):
    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    # True为开启动态复权模式，使用真实价格交易
    set_option('use_real_price', True)
    # 设定成交量比例
    set_option('order_volume_ratio', 1)
    # 关闭订单提醒
    # log.set_level('order', 'error')
    # 设定期货保证金比例
    set_option('futures_margin_rate', 0.3)
    # 设定操作金融期货
    set_subportfolios([SubPortfolioConfig(cash=context.portfolio.cash, type='index_futures')])
    # 金融期货close_today_commission可不用设定，平今仓默认0.0023
    set_order_cost(OrderCost(open_commission=0.000023, close_commission=0.000023, close_today_commission=0.0023),
                   type='index_futures')
    # 运行函数
    run_daily(set_info, time='before_open', reference_security='IF1806.CCFX')
    run_daily(trade, time='every_bar', reference_security='IF1806.CCFX')
    g.enterpricelong = 0
    g.enterpriceshort = 0
    # g.security='IF1806.CCFX'
    g.trend = 0
    g.situation = 0
    g.enterprice = 0


def set_info(context):
    # 分钟计数
    g.minute_count = 0

    g.check_date = context.current_dt.strftime('%Y-%m-%d')

    MTR2, ATR2 = ATR('000300.XSHG', check_date=g.check_date, timeperiod=14)
    g.ATR = ATR2['000300.XSHG']

    # MTR1, ATR1 = ATR(g.security, check_date=g.check_date, timeperiod=14)
    # ATR0=ATR1[g.security]
    # record(atr2=ATR2['000300.XSHG'])
    # record(ATR1=ATR1[g.security])


def trade(context):
    # 开盘第一分钟
    if g.minute_count == 0:
        # 获取当月可交易的 HS300 股指期货合约
        g.security = get_stock_index_futrue_code(context, symbol='IF', month='current_month')
        # g.security = get_stock_index_futrue_code(context, symbol='IF', month='current_month')
        # 获取 BuyLine, SellLine

        #
        # 分钟计数
        g.minute_count += 1
        g.current_open = attribute_history('000300.XSHG', 1, '1m', ['close'], df=False)['close'][0]




    # 开盘第一分钟之后
    else:
        upperband, middleband, lowerband = Bollinger_Bands('000300.XSHG', g.check_date, timeperiod=25, nbdevup=2,
                                                           nbdevdn=2)
        hist = attribute_history('000300.XSHG', 5, '1d', ['open', 'high', 'low', 'close'])
        yesterday_close = hist['close'][-1]
        tby_low = hist['low'][-2]
        tby_close = hist['close'][-2]
        tby_high = hist['high'][-2]
        # 三日低
        LL = hist['low'][-1:-4]
        # 三日高
        HH = hist['high'][-1:-4]
        if CMI('000300.XSHG') < 20:
            if (g.situation == 3):
                g.swap = 1
            else:
                g.swap = 0
            if yesterday_close >= (tby_high + tby_close + tby_low) / 3:
                g.situation = 1  # 趋卖市
            if yesterday_close < (tby_high + tby_close + tby_low) / 3:
                g.situation = 2  # 趋买市
        else:
            if (g.situation <> 3):
                g.swap = -1
            else:
                g.swap = 0
            g.situation = 3  # 趋势
        # 获取标的可平多仓
        long_closeable_amount = context.portfolio.long_positions[g.security].closeable_amount
        # 获取标的可平空仓
        short_closeable_amount = context.portfolio.short_positions[g.security].closeable_amount
        # 获取标的的最新价
        current_price = attribute_history('000300.XSHG', 1, '1m', ['close'], df=False)['close'][0]
        # if(g.situation<>3):
        #   if(g.swap==1):
        #      if(short_closeable_amount <> 0):
        #         order_target(g.security, 0, side='short')
        #    if(long_closeable_amount <> 0):
        #       order_target(g.security, 0, side='long')
        #      print('run1')
        if (g.situation == 1):
            if current_price < max(g.current_open + 1.5 * g.ATR, numpy.mean(LL)):

                if (short_closeable_amount > 0):
                    long2()
                    g.enterprice = current_price

                elif (short_closeable_amount == 0) and (long_closeable_amount == 0):
                    long1()
                    g.enterprice = current_price
            elif current_price > min(g.current_open - 1.25 * g.ATR, numpy.mean(HH)):

                if (long_closeable_amount > 0):
                    short2()
                    g.enterprice = current_price
                # 如果没有持仓，则直接开空仓；
                elif (short_closeable_amount == 0) and (long_closeable_amount == 0):
                    short1()
                    g.enterprice = current_price
        if (g.situation == 2):
            if current_price < max(g.current_open + 1.25 * g.ATR, numpy.mean(LL)):

                if (short_closeable_amount > 0):
                    long2()
                    g.enterprice = current_price

                elif (short_closeable_amount == 0) and (long_closeable_amount == 0):
                    long1()
                    g.enterprice = current_price
            elif current_price > min(g.current_open - 1.5 * g.ATR, numpy.mean(HH)):

                if (long_closeable_amount > 0):
                    short2()
                    g.enterprice = current_price
                # 如果没有持仓，则直接开空仓；
                elif (short_closeable_amount == 0) and (long_closeable_amount == 0):
                    short1()
                    g.enterprice = current_price
        if (g.situation == 3):
            if (g.swap == -1):
                if (short_closeable_amount > 0):
                    if (current_price > g.enterprice + 3 * g.ATR):
                        order_target(g.security, 0, side='short')
                        g.enterprice = 0
                if (long_closeable_amount > 0):
                    if (current_price < g.enterprice - 3 * g.ATR):
                        order_target(g.security, 0, side='long')
                        g.enterprice = 0
                        print('run2')
            if (current_price > upperband['000300.XSHG']):
                if (short_closeable_amount == 0) and (long_closeable_amount == 0):
                    long1()

            if (current_price < lowerband['000300.XSHG']):
                if (short_closeable_amount == 0) and (long_closeable_amount == 0):
                    short1()
            if (current_price == middleband['000300.XSHG']):
                if (short_closeable_amount > 0):
                    order_target(g.security, 0, side='short')
                if (long_closeable_amount > 0):
                    order_target(g.security, 0, side='long')
                    print('run3')
        record(mid=middleband['000300.XSHG'])
        record(p=current_price)

        # 当日最高
        # current_high = max(attribute_history('000300.XSHG', g.minute_count, '1m', ['high'], df=False)['high'])
        # 当日最低
        # current_low = min(attribute_history('000300.XSHG', g.minute_count, '1m', ['low'], df=False)['low'])
        # record(cmi=CMI('000300.XSHG'))
        # 判断趋势

        # 看涨信号下:
        # check_date = context.current_dt.strftime('%Y-%m-%d')
        # 计算ATR
        # MTR1, ATR1 = ATR(g.security, check_date=g.check_date, timeperiod=14)
        # ATR0=ATR1[g.security]
        # 若在趋买市

        # 分钟计数
        g.minute_count += 1


## 获取当天时间正在交易的股指期货合约
def get_stock_index_futrue_code(context, symbol, month='current_month'):
    '''
    获取当天时间正在交易的股指期货合约。其中:
    symbol:
            'IF' #沪深300指数期货
            'IC' #中证500股指期货
            'IH' #上证50股指期货
    month:
            'current_month' #当月
            'next_month'    #隔月
            'next_quarter'  #下季
            'skip_quarter'  #隔季
    '''
    display_name_dict = {'IF': '沪深300指数期货', 'IC': '中证500股指期货', 'IH': '上证50股指期货'}
    month_dict = {'current_month': 0, 'next_month': 1, 'next_quarter': 2, 'skip_quarter': 3}

    display_name = display_name_dict[symbol]
    n = month_dict[month]
    dt = context.current_dt.date()
    a = get_all_securities(types=['futures'], date=dt)
    try:
        df = a[(a.display_name == display_name) & (a.start_date <= dt) & (a.end_date >= dt)]
        if (len(df) > 4) and (month in ('next_quarter', 'skip_quarter')):
            return df.index[n + 1]
        else:
            return df.index[n]
    except:
        return 'WARRING: 无此合约'


# 获取金融期货合约到期日
def get_CCFX_end_date(fature_code):
    return get_security_info(fature_code).end_date


def long1():
    # 开1手多仓
    order(g.security, 1, side='long')
    log.info('没有持仓，开多仓')


def long2():
    # 平空仓
    order_target(g.security, 0, side='short')
    # 开1手多仓
    order(g.security, 1, side='long')
    log.info('持有空仓，先平仓，再开多仓')


def short1():
    # 开1手空仓
    order(g.security, 1, side='short')
    log.info('没有持仓，则直接开空仓')


def short2():
    # 平多仓
    order_target(g.security, 0, side='long')
    # 开1手空仓
    order(g.security, 1, side='short')
    log.info('持有多仓，先平仓，再开空仓')


def CMI(security):
    hist = attribute_history(security, 14, '1d', ['high', 'low', 'close'])
    HH = max(hist['high'])
    LC = min(hist['close'])
    LL = min(hist['low'])
    thecmi = (abs(hist['close'][-1] - hist['close'][0])) * 100 / (HH - LL)
    return thecmi

