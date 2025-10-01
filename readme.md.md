# Amazon Product Scraper & Tracker

A Flask web application to scrape Amazon products, track their prices, and visualize price history. Users can favourite products, track items, and view detailed price history charts.

## Features

- **Scrape Products:** Search for products on Amazon via keywords and fetch product data using Bright Data API.
- **Import Snapshots:** Import scraped data snapshots into the database.
- **Track Prices:** Maintain historical price data for products.
- **Favourites & Tracking:** Mark products as favourites or track them for monitoring price changes.
- **Visualisations:** View price history charts for each product.
- **Web Interface:** Interactive interface with Bootstrap 5 and Flask-WTF forms.

## Technologies Used

- **Backend:** Flask, SQLAlchemy
- **Database:** SQLite
- **Data Handling:** Pandas
- **Visualization:** Matplotlib
- **Forms:** Flask-WTF
- **Styling:** Bootstrap 5, Bootstrap Icons
- **External API:** Bright Data for scraping

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/amazon-product-scraper.git
   cd amazon-product-scraper
   ```

2. **Create a virtual environment and activate it:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux / Mac
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` file with your API keys:**
   ```env
   FLASK_SECRET_KEY=your_flask_secret
   API_KEY=your_brightdata_api_key
   DATASET_ID=your_brightdata_dataset_id
   ```

5. **Run the app:**
   ```bash
   flask run
   ```
   Or for development mode:
   ```bash
   python app.py
   ```

6. **Access the app:**
   Open `http://127.0.0.1:5000/products/all` in your browser.

## Usage

- **All Products:** View all scraped products, add to favourites, or delete.
- **Scrape New Product:** Enter a keyword to scrape new items from Amazon.
- **Import Snapshot:** Import the results of a scrape job into the database.
- **Favourites Page:** View, track, or remove favourite products.
- **Product Page:** View detailed price history and visual chart.

## Project Structure

```
├── app.py                  # Main Flask application
├── FlaskForms.py           # Flask-WTF forms
├── scraper.py              # Functions for scraping and fetching snapshots
├── graph.py                # Function to generate price charts
├── templates/              # HTML templates
│   ├── home.html
│   ├── product.html
│   ├── favourites.html
├── static/                 # Static assets (if needed)
├── data.db                 # SQLite database
├── requirements.txt        # Python dependencies
└── README.md
```

## Database Models

- **Product:** Stores product info and current price.
- **ProductPrice:** Tracks historical price data.
- **ScrapeJob:** Stores scraping job metadata and snapshot ID.
- **Favourites:** Stores favourite products.
- **TrackedProducts:** Tracks products marked for monitoring price changes.

## Notes

- The app uses **Bright Data API** for scraping Amazon data; make sure your account has access.
- Price charts are generated using **Matplotlib** and displayed as base64 images.
- The app supports **Bootstrap 5** for responsive UI.

## Future Improvements

- Add user authentication and personalized favourites.
- Implement notifications for price drops on tracked products.
- Support scraping from multiple e-commerce sites.
- Deploy to a cloud platform like Heroku or AWS.

