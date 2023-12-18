from http import HTTPStatus
from flask import Flask, request, abort
from flask_restful import Resource, Api
from models import Mobil as MobilModel
from engine import engine
from sqlalchemy import select
from sqlalchemy.orm import Session

session = Session(engine)

app = Flask(__name__)
api = Api(app)


class BaseMethod():

    def __init__(self):
        self.raw_weight = {'harga': 5, 'konsumsi_bbm': 4, 'kapasitas_mesin': 3, 'jumlah_kursi': 4, 'kecepatan_maksimum': 5}

    @property
    def weight(self):
        total_weight = sum(self.raw_weight.values())
        return {k: round(v/total_weight, 2) for k, v in self.raw_weight.items()}

    @property
    def data(self):
        query = select(MobilModel.no, MobilModel.merek, MobilModel.model, MobilModel.harga, MobilModel.konsumsi_bbm,
                    MobilModel.kapasitas_mesin, MobilModel.jumlah_kursi, MobilModel.kecepatan_maksimum)        
        result = session.execute(query).fetchall()
        print(result)
        return [{'no': Mobil.no, 'merek': Mobil.merek, 'model': Mobil.model, 'harga': Mobil.harga, 'konsumsi_bbm': Mobil.konsumsi_bbm, 
                'kapasitas_mesin': Mobil.kapasitas_mesin, 'jumlah_kursi' : Mobil.jumlah_kursi, 'kecepatan_maksimum': Mobil.kecepatan_maksimum} for Mobil in result]
    @property
    def normalized_data(self):
        harga_values = [data.get('harga', 0) for data in self.data]
        konsumsi_bbm_values = [data['konsumsi_bbm'] for data in self.data]
        kapasitas_mesin_values = [data['kapasitas_mesin'] for data in self.data]
        jumlah_kursi_values = [int(data['jumlah_kursi']) for data in self.data]  
        kecepatan_maksimum_values = [data['kecepatan_maksimum'] for data in self.data]

        max_harga_value = max(harga_values) if harga_values else 1
        max_konsumsi_bbm_value = max(konsumsi_bbm_values) if konsumsi_bbm_values else 1
        max_kapasitas_mesin_value = max(kapasitas_mesin_values) if kapasitas_mesin_values else 1
        max_jumlah_kursi_value = max(jumlah_kursi_values) if jumlah_kursi_values else 1
        max_kecepatan_maksimum_value = max(kecepatan_maksimum_values) if kecepatan_maksimum_values else 1

        return [
            {
                'no': data['no'],
                'model': data['model'],
                'harga': data['harga'] / max_harga_value if max_harga_value != 0 else 0,
                'konsumsi_bbm': data['konsumsi_bbm'] / max_konsumsi_bbm_value,
                'kapasitas_mesin': data['kapasitas_mesin'] / max_kapasitas_mesin_value,
                'jumlah_kursi': int(data['jumlah_kursi']) / max_jumlah_kursi_value,
                'kecepatan_maksimum': data['kecepatan_maksimum'] / max_kecepatan_maksimum_value,
            }
            for data in self.data
            ]

    def update_weights(self, new_weights):
        self.raw_weight = new_weights


class WeightedProductCalculator(BaseMethod):
    def update_weights(self, new_weights):
        self.raw_weight = new_weights

    @property
    def calculate(self):
        normalized_data = self.normalized_data
        produk = [
            {
                'no': row['no'],
                'produk': row['harga'] ** self.weight['harga'] *
                    row['konsumsi_bbm'] ** self.weight['konsumsi_bbm'] *
                    row['kapasitas_mesin'] ** self.weight['kapasitas_mesin'] *
                    row['jumlah_kursi'] ** self.weight['jumlah_kursi'] *
                    row['kecepatan_maksimum'] ** self.weight['kecepatan_maksimum'],
                    'model': row.get('model', '')
            }
            for row in normalized_data
        ]
        sorted_produk = sorted(produk, key=lambda x: x['produk'], reverse=True)
        sorted_data = [
            {
                'ID': product['no'],
                'model': product['model'],
                'score': round(product['produk'], 3)
            }
            for product in sorted_produk
        ]
        return sorted_data


class WeightedProduct(Resource):
    def get(self):
        calculator = WeightedProductCalculator()
        result = calculator.calculate
        return sorted(result, key=lambda x: x['score'], reverse=True), HTTPStatus.OK.value

    def post(self):
        new_weights = request.get_json()
        calculator = WeightedProductCalculator()
        calculator.update_weights(new_weights)
        result = calculator.calculate
        return {'mobil': sorted(result, key=lambda x: x['score'], reverse=True)}, HTTPStatus.OK.value


class SimpleAdditiveWeightingCalculator(BaseMethod):
    @property
    def calculate(self):
        weight = self.weight
        result = [
            {
                'no': row['no'],
                'model': row.get('model'),
                'Score': round(row['harga'] * weight['harga'] +
                        row['konsumsi_bbm'] * weight['konsumsi_bbm'] +
                        row['kapasitas_mesin'] * weight['kapasitas_mesin'] +
                        row['jumlah_kursi'] * weight['jumlah_kursi'] +
                        row['kecepatan_maksimum'] * weight['kecepatan_maksimum'], 3)
            }
            for row in self.normalized_data
        ]
        sorted_result = sorted(result, key=lambda x: x['Score'], reverse=True)
        return sorted_result

    def update_weights(self, new_weights):
        self.raw_weight = new_weights


class SimpleAdditiveWeighting(Resource):
    def get(self):
        saw = SimpleAdditiveWeightingCalculator()
        result = saw.calculate
        return sorted(result, key=lambda x: x['Score'], reverse=True), HTTPStatus.OK.value

    def post(self):
        new_weights = request.get_json()
        saw = SimpleAdditiveWeightingCalculator()
        saw.update_weights(new_weights)
        result = saw.calculate
        return {'Mobil': sorted(result, key=lambda x: x['Score'], reverse=True)}, HTTPStatus.OK.value


class Mobil(Resource):
    def get_paginated_result(self, url, list, args):
        page_size = int(args.get('page_size', 10))
        page = int(args.get('page', 1))
        page_count = int((len(list) + page_size - 1) / page_size)
        start = (page - 1) * page_size
        end = min(start + page_size, len(list))

        if page < page_count:
            next_page = f'{url}?page={page+1}&page_size={page_size}'
        else:
            next_page = None
        if page > 1:
            prev_page = f'{url}?page={page-1}&page_size={page_size}'
        else:
            prev_page = None

        if page > page_count or page < 1:
            abort(404, description=f'Data Tidak Ditemukan.')
        return {
            'page': page,
            'page_size': page_size,
            'next': next_page,
            'prev': prev_page,
            'Results': list[start:end]
        }

    def get(self):
        query = session.query(MobilModel).order_by(MobilModel.no)
        result_set = query.all()
        data = [{'no': row.no, 'merek': row.merek, 'model': row.model, 'harga': row.harga, 'konsumsi_bbm': row.konsumsi_bbm, 
                'kapasitas_mesin': row.kapasitas_mesin, 'jumlah_kursi' : row.jumlah_kursi, 'kecepatan_maksimum': row.kecepatan_maksimum}
                for row in result_set]
        return self.get_paginated_result('mobil/', data, request.args), 200

api.add_resource(Mobil, '/mobil')
api.add_resource(WeightedProduct, '/wp')
api.add_resource(SimpleAdditiveWeighting, '/saw')

if __name__ == '__main__':
    app.run(port='5005', debug=True)