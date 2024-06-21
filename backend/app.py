from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///transactions.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class ProductTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.String(500))
    price = db.Column(db.Float)
    date_of_sale = db.Column(db.Date)
    category = db.Column(db.String(100))
    sold = db.Column(db.Boolean)

    def as_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "price": self.price,
            "date_of_sale": self.date_of_sale,
            "category": self.category,
            "sold": self.sold
        }

@app.route('/initialize', methods=['GET'])
def initialize():
    url = "https://s3.amazonaws.com/roxiler.com/product_transaction.json"
    response = requests.get(url)
    data = response.json()

    db.drop_all()
    db.create_all()

    for item in data:
        transaction = ProductTransaction(
            title = item.get('title'),
            description = item.get('description'),
            price = item.get('price'),
            date_of_sale = item.get('dateOfSale'),
            category = item.get('category'),
            sold = item.get('sold')
        )
        db.session.add(transaction)
    db.session.commit()

    return jsonify({"message": "Database initialized"}), 200

@app.route('/transactions', methods=['GET'])
def get_transactions():
    month = request.args.get('month')
    search = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))

    query = ProductTransaction.query

    if month:
        query = query.filter(func.strftime('%m', ProductTransaction.date_of_sale) == month.zfill(2))

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            db.or_(
                ProductTransaction.title.ilike(search_pattern),
                ProductTransaction.description.ilike(search_pattern),
                ProductTransaction.price.ilike(search_pattern)
            )
        )

    transactions = query.paginate(page, per_page, False).items

    return jsonify([t.as_dict() for t in transactions])

@app.route('/statistics', methods=['GET'])
def get_statistics():
    month = request.args.get('month')

    if not month:
        return jsonify({"error": "Month is required"}), 400

    total_sale_amount = db.session.query(func.sum(ProductTransaction.price)).filter(
        func.strftime('%m', ProductTransaction.date_of_sale) == month.zfill(2),
        ProductTransaction.sold == True
    ).scalar()

    total_sold_items = db.session.query(func.count(ProductTransaction.id)).filter(
        func.strftime('%m', ProductTransaction.date_of_sale) == month.zfill(2),
        ProductTransaction.sold == True
    ).scalar()

    total_not_sold_items = db.session.query(func.count(ProductTransaction.id)).filter(
        func.strftime('%m', ProductTransaction.date_of_sale) == month.zfill(2),
        ProductTransaction.sold == False
    ).scalar()

    return jsonify({
        "total_sale_amount": total_sale_amount,
        "total_sold_items": total_sold_items,
        "total_not_sold_items": total_not_sold_items
    })

@app.route('/bar-chart', methods=['GET'])
def get_bar_chart():
    month = request.args.get('month')

    if not month:
        return jsonify({"error": "Month is required"}), 400

    price_ranges = [
        (0, 100), (101, 200), (201, 300), (301, 400), 
        (401, 500), (501, 600), (601, 700), (701, 800), 
        (801, 900), (901, float('inf'))
    ]

    response = []

    for price_range in price_ranges:
        count = db.session.query(func.count(ProductTransaction.id)).filter(
            func.strftime('%m', ProductTransaction.date_of_sale) == month.zfill(2),
            ProductTransaction.price >= price_range[0],
            ProductTransaction.price <= price_range[1] if price_range[1] != float('inf') else True
        ).scalar()

        response.append({
            "price_range": f"{price_range[0]}-{price_range[1]}",
            "count": count
        })

    return jsonify(response)

@app.route('/pie-chart', methods=['GET'])
def get_pie_chart():
    month = request.args.get('month')

    if not month:
        return jsonify({"error": "Month is required"}), 400

    categories = db.session.query(
        ProductTransaction.category,
        func.count(ProductTransaction.id)
    ).filter(
        func.strftime('%m', ProductTransaction.date_of_sale) == month.zfill(2)
    ).group_by(ProductTransaction.category).all()

    response = {category: count for category, count in categories}

    return jsonify(response)

@app.route('/combined-data', methods=['GET'])
def get_combined_data():
    month = request.args.get('month')

    if not month:
        return jsonify({"error": "Month is required"}), 400

    transactions_response = get_transactions()
    statistics_response = get_statistics()
    bar_chart_response = get_bar_chart()
    pie_chart_response = get_pie_chart()

    return jsonify({
        "transactions": transactions_response.json,
        "statistics": statistics_response.json,
        "bar_chart": bar_chart_response.json,
        "pie_chart": pie_chart_response.json
    })

if __name__ == '__main__':
    app.run(debug=True)
