import requests

BASE_URL = "http://localhost:8003"


def erase_data():
    requests.delete(BASE_URL + "/users")
    resp = requests.delete(BASE_URL + "/patients/all")
    if resp.ok:
        print(resp.json())
    else:
        print(f"Failed: {resp.status_code} {resp.text}")

def main():
    erase_data()


if __name__ == "__main__":
    main()