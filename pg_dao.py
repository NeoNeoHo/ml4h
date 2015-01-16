__author__ = 'BensonHo'

import pg
from mosql.query import insert, select, update, delete
from mosql.util import raw
import datetime

is_debug = False


class PGDao:
	def __init__(self, market, host, port, user, passwd):
		self.pgcon = pg.connect(dbname=market, host=host, port=port, user=user, passwd=passwd)

	def insert(self, table, dict_data):
		sql_string = insert(table, dict_data)
		if is_debug:
			print(sql_string)
		self.pgcon.query(sql_string)

	def select(self, table, where=None, columns=None, order_by=None, limit=None):
		sql_string = select(table, where=where, columns=columns, order_by=order_by, limit=limit)
		if is_debug:
			print(sql_string)
		return self.pgcon.query(sql_string).getresult()

	def update(self, table, dict_data,  where=None):
		sql_string = update(table, where, dict_data)
		if is_debug:
			print(sql_string)
		self.pgcon.query(sql_string)

	def delete(self, table, where=None):
		sql_string = delete(table, where)
		if is_debug:
			print(sql_string)
		self.pgcon.query(sql_string)

	def upsert(self, table, data, key):
		try:
			sql_string = insert(table, data)
			self.pgcon.query(sql_string)
		except pg.ProgrammingError:
			key_data = dict(filter(lambda x: x[0] in key, data.items()))
			for k in key:
				del data[k]
			sql_string = update(table, key_data, data)
			self.pgcon.query(sql_string)

	def fast_upsert(self, table, dict_data, key_list):
		try:
			sql_to_db = list()
			for data in dict_data:
				sql_string = insert(table, data)
				sql_to_db.append(sql_string)
			self.pgcon.query(';'.join(sql_to_db))
		except Exception as e:
			print('fast insert is failed. try upsert data one by one.')
			for data in dict_data:
				self.upsert(table, data, key_list)

	def __del__(self):
		self.pgcon.close()


class FinancialDao:
	def __init__(self):
		self.daos = {}
		self.today = datetime.datetime.today().strftime('%Y-%m-%d')

	def get_dao(self, market):
		if market not in self.daos:
			self.daos[market] = PGDao(market,
									  host='localhost',
									  port=5433,
									  user='postgres',
									  passwd='MaJa0416')
		return self.daos[market]

	def __del__(self):
		del self.daos

	def insert_dict_to_db(self, market, table, dict_data):
		sql_to_db = list()
		for data in dict_data:
			sql_string = insert(table, data)
			if is_debug:
				print(sql_string)
			sql_to_db.append(sql_string)
		dao = self.get_dao(market)
		dao.pgcon.query(';'.join(sql_to_db))

	def get_all_ticker_list(self, market):
		dao = self.get_dao(market)
		data = dao.select('public.symbol',
						  columns=(raw('distinct ticker')),
						  order_by='ticker asc')
		if data:
			return zip(*data)[0]

	def get_ticker_last_date(self, market, ticker):
		dao = self.get_dao(market)
		last_date = dao.select('public.daily_price',
						  columns='price_date',
						  where={'ticker': ticker},
						  order_by='price_date desc',
						  limit=1)
		if last_date:
			last_date = datetime.datetime.strptime(zip(*last_date)[0][0], '%Y-%m-%d')
			next_date = last_date + datetime.timedelta(days=1)
			return next_date

	def get_price_from_date(self, market, ticker, date):
		dao = self.get_dao(market)
		data = dao.select('daily_price',
						  where={'ticker': ticker, 'price_date >=': date},
						  columns=['price_date', 'ticker', 'adj_close'],
						  order_by='price_date asc')
		if data:
			return data
financial_dao = FinancialDao()

	#########################################################################################
	#  Test Function
	#########################################################################################


	#########################################################################################
if __name__ == '__main__':
	pass
	data = financial_dao.get_all_ticker_list('Financial')
	print data
	#test_get_last_trade_date()
	# test_get_price()
	# test_get_vol()
