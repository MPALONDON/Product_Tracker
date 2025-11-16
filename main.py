import os
from flask_bootstrap import Bootstrap5
from flask import Flask, render_template,redirect,url_for,flash,request
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
    prices = relationship("ProductPrice", back_populates="product",cascade="all, delete-orphan")
    favourite_entries = relationship("Favourites", back_populates="product",cascade="all, delete-orphan")
    tracked_entries = relationship("TrackedProducts", back_populates="product", cascade="all, delete-orphan")


class Favourites(Base):
    __tablename__ = "favourites"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("product.id"), nullable=False)

    product = relationship("Product", back_populates="favourite_entries")


class ProductPrice(Base):
    __tablename__ = "product_price"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("product.id",ondelete="CASCADE"),nullable=False)
    job_id: Mapped[int] = mapped_column(ForeignKey("scrape_job.id"), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    checked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)

    product = relationship("Product", back_populates="prices")
    job = relationship("ScrapeJob")


class ScrapeJob(Base):
    __tablename__ = "scrape_job"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    snapshot_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    keyword: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[str] = mapped_column(String(64), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.today,nullable=False)

    products = relationship("Product",back_populates="job")

class TrackedProducts(Base):
    __tablename__ = "tracked_products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("product.id", ondelete="CASCADE"), nullable=False)
    product = relationship("Product", back_populates="tracked_entries")


with app.app_context():
    db.create_all()

data = pd.read_json("data.json")
filtered_data = data.dropna(subset=['initial_price'])

@app.route('/products/all',methods=['GET', 'POST'])
def all_products():
    form = ScrapeForm()
    if form.validate_on_submit():
        name = form.name.data
        snapshot_id = scrape_amazon([name])
        job = ScrapeJob(snapshot_id=snapshot_id, keyword=name, status="pending")
        db.session.add(job)
        db.session.commit()
        flash(f"Started scrape job for '{name}'", "success")
        return redirect(url_for('all_products'))

    page = request.args.get('page', 1, type=int)

    per_page = 20

    pagination = db.paginate(
        db.select(Product).order_by(Product.name),
        page=page,
        per_page=per_page,
        error_out=False
    )

    db_data = pagination.items
    jobs = db.session.execute(db.select(ScrapeJob).order_by(ScrapeJob.created_at)).scalars().all()
    total_entries = db.session.execute(db.select(Product)).scalars().all()
    total_entries_count = len(total_entries)
    return render_template("home.html",db_data=db_data,form = form,
                           total_entries=total_entries_count,jobs=jobs,pagination=pagination)

@app.route('/import/<snapshot_id>',methods=['GET', 'POST'])
def import_snapshot(snapshot_id):

    job = db.session.execute(db.select(ScrapeJob).where(ScrapeJob.snapshot_id == snapshot_id)).scalar_one_or_none()
    snapshot_data = fetch_snapshot(snapshot_id)
    for idx,item in snapshot_data.iterrows():
        existing = db.session.execute(
            db.select(Product).where(Product.url == item["url"])
        ).scalar_one_or_none()

        if existing:
            existing_price = db.session.execute(
                db.select(ProductPrice)
                .where(ProductPrice.product_id == existing.id)
                .where(ProductPrice.job_id == job.id)
            ).scalar_one_or_none()

            if not existing_price:
                price_entry = ProductPrice(
                    product_id=existing.id,
                    job_id=job.id,
                    price=item["initial_price"]
                )
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

            price_entry = ProductPrice(product_id=new_product.id,job_id=job.id, price=item["initial_price"])
            db.session.add(price_entry)

    job.status = "done"
    db.session.commit()

    flash(f"Snapshot {snapshot_id} successfully imported",category="success")
    return redirect(url_for("all_products"))

@app.route('/product/<int:product_id>', methods=['GET', 'POST'])
def view_product(product_id):
    requested_product = db.get_or_404(Product, product_id)
    price_history = (db.session.execute(db.select(ProductPrice).where(ProductPrice.product_id==product_id))
                     .scalars().all())

    last_scrape = max(p.checked_at for p in price_history)

    dates = [p.checked_at for p in price_history]
    prices = [p.price for p in price_history]
    for p in price_history:
        print(p.checked_at)

    img = make_price_chart(dates, prices, f"Price history for {requested_product.name[0:110]}...")
    return render_template("product.html",product=requested_product,price_history=price_history,
                           last_scrape = last_scrape,chart_img = img)

@app.route('/product/delete/<int:product_id>', methods=['GET', 'POST'])
def delete_product(product_id):
    product = db.session.execute(db.select(Product).where(Product.id == product_id)).scalar_one_or_none()
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for("all_products"))

@app.route('/product/favourite/<int:product_id>', methods=['GET', 'POST'])
def mark_favourites(product_id):
    product = db.get_or_404(Product, product_id)
    if product.favourite_entries:
        flash("Product already marked as favourite","danger")
        return redirect(url_for("all_products"))
    fav = Favourites(product=product)
    db.session.add(fav)
    db.session.commit()
    flash(f"added {product.name[0:110]}... to favourites","success")
    return redirect(url_for("all_products"))

@app.route('/products/favourites/<int:product_id>', methods=['GET', 'POST'])
def remove_favourites(product_id):
    favourite = (db.session.execute(db.select(Favourites).where(Favourites.product_id == product_id))
                 .scalar_one_or_none())
    product_name = favourite.product.name
    db.session.delete(favourite)
    db.session.commit()
    flash(f"removed {product_name[0:110]}... from favourites","success")
    return redirect(url_for("favourites"))

@app.route('/products/favourites', methods=['GET', 'POST'])
def favourites():
    all_favourites = db.session.execute(db.select(Favourites).order_by(Favourites.id)).scalars().all()
    tracked_favourites = db.session.execute(db.select(TrackedProducts).order_by(TrackedProducts.id)).scalars().all()
    total_entries = len(all_favourites)
    return render_template("favourites.html",all_favourites=all_favourites,
                           total_entries = total_entries,tracked_favourites = tracked_favourites)

@app.route('/products/track/<int:product_id>', methods=['GET','POST'])
def track_product(product_id):
    product = db.get_or_404(Product, product_id)

    if product.tracked_entries:
        flash("Product already tracked", "danger")
        return redirect(url_for("favourites"))

    tracked = TrackedProducts(product_id=product.id)
    db.session.add(tracked)
    db.session.commit()

    flash(f"Started tracking {product.name}", "success")
    return redirect(url_for("favourites"))

@app.route('/products/untrack/<int:product_id>', methods=['GET', 'POST'])
def remove_tracking(product_id):
    tracked = db.session.execute(
        db.select(TrackedProducts).where(TrackedProducts.product_id == product_id)
    ).scalar_one_or_none()

    db.session.delete(tracked)
    db.session.commit()
    return redirect(url_for("favourites"))

if __name__ == "__main__":
    app.run(debug=True)