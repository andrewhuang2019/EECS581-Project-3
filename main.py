
from weather import get_today_forecast

def main():
    try:
        forecast = get_today_forecast()
        print(forecast)  # replace with LCD output later
    except RuntimeError as error:
        print(f"Weather unavailable: {error}")


if __name__ == "__main__":
    main()

