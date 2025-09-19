import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
import io, base64

def make_price_chart(dates, prices, title="Price History"):
    matplotlib.use("Agg")
    fig, ax = plt.subplots(figsize=(15, 6))
    ax.plot(dates, prices, marker="o")
    ax.set_title(title)
    ax.set_xlabel("Date")
    ax.set_ylabel("Price (USD)")

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    img = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)

    return img