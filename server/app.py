from crawler import crawl
from server import start_server

def main():
    # Crawl the website
    crawl()

    # Start the server
    start_server()

if __name__ == "__main__":
    main()  