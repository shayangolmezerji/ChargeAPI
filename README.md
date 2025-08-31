# ChargeAPI: The Modern Python API for Mobile Top-ups 🚀

ChargeAPI is a robust and secure API for handling mobile charge and top-up requests. Built with a modern Python stack, this project leverages FastAPI and Uvicorn to provide a high-performance, well-documented, and easily maintainable web service.

The focus is on security and reliability, ensuring that all API calls are validated and correctly processed before interacting with the external charge reseller service.

-----

### ✨ Features

* **FastAPI**: A modern, high-performance web framework for building APIs with Python 3.7+ based on standard Python type hints.
* **Uvicorn**: An ASGI server that powers the API, enabling fast, asynchronous request handling.
* **Secure Configuration**: Uses a `.env` file to securely manage sensitive credentials like the web service key.
* **Input Validation**: Automatic and robust data validation with Pydantic models ensures data integrity.
* **Clear Error Handling**: Returns descriptive HTTP status codes for all errors, making the API easy to debug.
* **API Documentation**: Automatic interactive API documentation (Swagger UI) available at `/docs`.

-----

### 🚀 Getting Started

These instructions will get a copy of the project up and running on your local machine.

#### 1. Prerequisites

Make sure you have Python 3.7+ and `pip` installed on your system.

#### 2. Installation

Install the required Python packages using `pip`.

```bash
pip install fastapi uvicorn python-dotenv requests
````

#### 3\. Configuration

Create a file named `.env` in the root directory of the project. This file is used to store your sensitive credentials.

To get your web service ID, you must register for an account on the official reseller's website, **`https://www.chargereseller.com/`**, and generate a key from your account dashboard.

```ini
# .env
CHARGE_RESELLER_WEB_ID="YOUR_WEB_SERVICE_ID_HERE"
```

#### 4\. Run the Project

This command will start the API server with Uvicorn. The `--reload` flag enables auto-reloading on code changes for a faster development experience.

```bash
uvicorn main:app --reload
```

-----

### 🧠 How to Test

With the server running, you can test the API directly using the interactive documentation or a tool like `curl`.

1.  **Open API Docs**: Navigate to the interactive API documentation at `http://127.0.0.1:8000/docs`. Here you can see all available endpoints and test them directly from your browser.

2.  **Test a `POST` Request**: Use `curl` to send a `POST` request to your API's `/charge` endpoint. This will process a top-up request and return a payment URL.

<!-- end list -->

```bash
curl -X POST "[http://127.0.0.1:8000/charge](http://127.0.0.1:8000/charge)" \
-H "accept: application/json" \
-H "Content-Type: application/json" \
-d '{
  "amount": 5000,
  "phone": "09123456789",
  "super": false,
  "daemi": false,
  "charge_type": "direct"
}'
```

You should receive a JSON response with the payment URL to complete the transaction.

-----

### 📜 License

This project is licensed under the [DON'T BE A DICK PUBLIC LICENSE](https://github.com/ShayanGolmezerji/ChargeAPI/blob/main/LICENSE.md).

-----

### 👨‍💻 Author

Made with ❤️ by [Shayan Golmezerji](https://github.com/shayangolmezerji)

```
```
