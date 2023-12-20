from http import HTTPStatus
from flask import Flask, request, abort
from flask_restful import Resource, Api 
from models import smartphone as smartphoneModel
from engine import engine
from sqlalchemy import select
from sqlalchemy.orm import Session

session = Session(engine)

app = Flask(__name__)
api = Api(app)        

class BaseMethod():

    def __init__(self):
        self.raw_weight = {'harga': 8, 'ram': 6, 'kapasitas_baterai': 5, 'chipset': 7, 'memori_internal': 5}

    @property
    def weight(self):
        total_weight = sum(self.raw_weight.values())
        return {k: round(v/total_weight, 2) for k, v in self.raw_weight.items()}

    @property
    def data(self):
        query = select(smartphoneModel.nama, smartphoneModel.harga, smartphoneModel.ram, smartphoneModel.kapasitas_baterai, smartphoneModel.chipset, smartphoneModel.memori_internal)
        result = session.execute(query).fetchall()
        print(result)
        return [{'nama': smartphone.nama, 'harga': smartphone.harga, 'ram': smartphone.ram, 'kapasitas_baterai': smartphone.kapasitas_baterai, 'chipset': smartphone.chipset, 'memori_internal': smartphone.memori_internal} for smartphone in result]

    @property
    def normalized_data(self):
        harga_values = []
        ram_values = []
        kapasitas_baterai_values = []
        chipset_values = []
        memori_internal_values = []

        for data in self.data:
            harga_values.append(data['harga'])
            ram_values.append(data['ram'])
            kapasitas_baterai_values.append(data['kapasitas_baterai'])
            chipset_values.append(data['chipset'])
            memori_internal_values.append(data['memori_internal'])

        return [
            {'nama': data['nama'],
             'harga': min(harga_values) / data['harga'],
             'ram': data['ram'] / max(ram_values),
             'kapasitas_baterai': data['kapasitas_baterai'] / max(kapasitas_baterai_values),
             'chipset': data['chipset'] / max(chipset_values),
             'memori_internal': data['memori_internal'] / max(memori_internal_values)
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
        produk = []

        for row in normalized_data:
            product_score = (
                row['harga'] ** self.raw_weight['harga'] *
                row['ram'] ** self.raw_weight['ram'] *
                row['kapasitas_baterai'] ** self.raw_weight['kapasitas_baterai'] *
                row['chipset'] ** self.raw_weight['chipset'] *
                row['memori_internal'] ** self.raw_weight['memori_internal']
            )

            produk.append({
                'nama': row['nama'],
                'produk': product_score
            })

        sorted_produk = sorted(produk, key=lambda x: x['produk'], reverse=True)

        sorted_data = []

        for product in sorted_produk:
            sorted_data.append({
                'nama': product['nama'],
                'score': product['produk']
            })

        return sorted_data


class WeightedProduct(Resource):
    def get(self):
        calculator = WeightedProductCalculator()
        result = calculator.calculate
        return result, HTTPStatus.OK.value
    
    def post(self):
        new_weights = request.get_json()
        calculator = WeightedProductCalculator()
        calculator.update_weights(new_weights)
        result = calculator.calculate
        return {'data': result}, HTTPStatus.OK.value
    

class SimpleAdditiveWeightingCalculator(BaseMethod):
    @property
    def calculate(self):
        weight = self.weight
        result = {row['nama']:
                  round(row['harga'] * weight['harga'] +
                        row['ram'] * weight['ram'] +
                        row['kapasitas_baterai'] * weight['kapasitas_baterai'] +
                        row['chipset'] * weight['chipset'] +
                        row['memori_internal'] * weight['memori_internal'], 2)
                  for row in self.normalized_data
                  }
        sorted_result = dict(
            sorted(result.items(), key=lambda x: x[1], reverse=True))
        return sorted_result

    def update_weights(self, new_weights):
        self.raw_weight = new_weights

class SimpleAdditiveWeighting(Resource):
    def get(self):
        saw = SimpleAdditiveWeightingCalculator()
        result = saw.calculate
        return result, HTTPStatus.OK.value

    def post(self):
        new_weights = request.get_json()
        saw = SimpleAdditiveWeightingCalculator()
        saw.update_weights(new_weights)
        result = saw.calculate
        return {'data': result}, HTTPStatus.OK.value


class smartphone(Resource):
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
            abort(404, description=f'Halaman {page} tidak ditemukan.') 
        return {
            'page': page, 
            'page_size': page_size,
            'next': next_page, 
            'prev': prev_page,
            'Results': list[start:end]
        }

    def get(self):
        query = select(smartphoneModel)
        data = [{'nama': smartphone.nama, 'harga': smartphone.harga, 'ram': smartphone.ram, 'kapasitas_baterai': smartphone.kapasitas_baterai, 'chipset': smartphone.chipset, 'memori_internal': smartphone.memori_internal} for smartphone in session.scalars(query)]
        return self.get_paginated_result('smartphone/', data, request.args), HTTPStatus.OK.value


api.add_resource(smartphone, '/smartphone')
api.add_resource(WeightedProduct, '/wp')
api.add_resource(SimpleAdditiveWeighting, '/saw')

if __name__ == '__main__':
    app.run(port='5005', debug=True)