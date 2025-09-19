import os
from flask_bootstrap import Bootstrap5
from flask import Flask, render_template,redirect,url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship,mapped_column
from sqlalchemy import Integer, String, DateTime, Float,ForeignKey
from datetime import datetime
import pandas as pd
from FlaskForms import ScrapeForm
from scraper import scrape_amazon,fetch_snapshot
from graph import make_price_chart

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
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("scrape_job.id"),nullable=False)
    name : Mapped[str] = mapped_column(String(256),nullable=False)
    img_url : Mapped[str] = mapped_column(String(512),nullable=False)
    url : Mapped[str] = mapped_column(String(512),nullable=False,unique=True)
    price : Mapped[float] = mapped_column(Float,nullable=False)
    created_at : Mapped[datetime] = mapped_column(DateTime, default=datetime.today,nullable=False)

    job = relationship("ScrapeJob", back_populates="products")
    prices = relationship("ProductPrice", back_populates="product")


class ProductPrice(Base):
    __tablename__ = "product_price"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("product.id"), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    checked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)

    product = relationship("Product", back_populates="prices")


class ScrapeJob(Base):
    __tablename__ = "scrape_job"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    snapshot_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    keyword: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[str] = mapped_column(String(64), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.today,nullable=False)

    products = relationship("Product", back_populates="job")


with app.app_context():
    db.create_all()

data = pd.read_json("data.json")
filtered_data = data.dropna(subset=['initial_price'])

@app.route('/all_products',methods=['GET', 'POST'])
def all_products():
    form = ScrapeForm()
    if form.validate_on_submit():
        name = form.name.data
        snapshot_id = scrape_amazon([name])
        job = ScrapeJob(snapshot_id=snapshot_id, keyword=name, status="pending")
        db.session.add(job)
        db.session.commit()
        return redirect(url_for('all_products'))

    db_data = db.session.execute(db.Select(Product).order_by(Product.name)).scalars().all()
    jobs = db.session.execute(db.select(ScrapeJob).order_by(ScrapeJob.created_at)).scalars().all()
    total_entries = len(db_data)
    return render_template("home.html",db_data=db_data,form = form,total_entries=total_entries,jobs=jobs)

@app.route('/import/<snapshot_id>',methods=['GET', 'POST'])
def import_snapshot(snapshot_id):
    snapshot_data = fetch_snapshot(snapshot_id)

    job = db.session.execute(db.select(ScrapeJob).where(ScrapeJob.snapshot_id == snapshot_id)).scalar_one_or_none()

    for idx,item in snapshot_data.iterrows():
        existing = db.session.execute(
            db.select(Product).where(Product.url == item["url"])
        ).scalar_one_or_none()
        if existing:

            price_entry = ProductPrice(product_id=existing.id, price=item["initial_price"])
            db.session.add(price_entry)

            existing.name = item["title"]
            existing.img_url = item["image_url"]
            existing.price = item["initial_price"]
            existing.job_id = job.id
        else:
            new_product = Product(
                name=item["title"],
                img_url=item["image_url"],
                url=item["url"],
                price=item["initial_price"],
                job_id=job.id,
            )
            db.session.add(new_product)
            db.session.flush()
            price_entry = ProductPrice(product_id=new_product.id, price=item["initial_price"])
            db.session.add(price_entry)

    job.status = "done"
    db.session.commit()

    return redirect(url_for("all_products"))

@app.route('/product/<int:product_id>', methods=['GET', 'POST'])
def view_product(product_id):
    requested_product = db.get_or_404(Product, product_id)
    price_history = db.session.execute(db.select(ProductPrice).where(ProductPrice.product_id==product_id)).scalars().all()

    dates = [p.checked_at for p in price_history]
    prices = [p.price for p in price_history]

    img = make_price_chart(dates, prices, f"Price history for {requested_product.name[0:110]}...")
    return render_template("product.html",product=requested_product,price_history=price_history,chart_img = img)


if __name__ == "__main__":
    app.run(debug=True)