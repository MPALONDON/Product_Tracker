import os

from flask_bootstrap import Bootstrap5
from flask import Flask, request, render_template,redirect,url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase,Mapped
from sqlalchemy import Column, Integer, String, DateTime, Float
from datetime import datetime
import pandas as pd
from FlaskForms import ScrapeForm
from scraper import scrape_amazon

app = Flask(__name__)
bootstrap = Bootstrap5(app)

app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')


class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


class Product(Base):
    __tablename__ = 'product'
    id: Mapped[int] = Column(Integer, primary_key=True)
    name : Mapped[str] = Column(String(256),nullable=False)
    img_url : Mapped[str] = Column(String(512),nullable=False)
    url : Mapped[str] = Column(String(512),nullable=False)
    price : Mapped[float] = Column(Float,nullable=False)
    created_at : Mapped[datetime] = Column(DateTime, default=datetime.today,nullable=False)

with app.app_context():
    db.create_all()

data = pd.read_json("data.json")
filtered_data = data.dropna(subset=['initial_price'])



@app.route('/all_products',methods=['GET', 'POST'])
def all_products():
    form = ScrapeForm()
    if form.validate_on_submit():
        name = form.name.data
        scrape_amazon([name])
        return redirect(url_for('all_products'))

    db_data = db.session.execute(db.Select(Product).order_by(Product.name)).scalars().all()
    total_entries = len(db_data)
    return render_template("home.html",db_data=db_data,form = form,total_entries=total_entries)

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    products = []
    for idx, item in filtered_data.iterrows():
        products.append(
            Product(
                name=item["title"],
                img_url=item["image_url"],
                url=item["url"],
                price=item["initial_price"]
            )
        )
        db.session.add_all(products)
        db.session.commit()
    return redirect(url_for("all_products"))


@app.route('/product/<int:product_id>', methods=['GET', 'POST'])
def view_product(product_id):
    requested_product = db.get_or_404(Product, product_id)
    return render_template("product.html",product=requested_product)

if __name__ == "__main__":
    app.run(debug=True)