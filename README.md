# Zacks Excel Data Viewer

This project provides a web interface to view and analyze Zacks Excel data. It consists of a React frontend and a Python (Flask) backend.

## 🚀 Getting Started

The easiest way to run the application is by using Docker.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Installation & Running

1.  **Clone the repository:**
    ```sh
    git clone <repository-url>
    cd zacks
    ```

2.  **Run with Docker Compose:**
    From the root directory of the project, run the following command:
    ```sh
    docker-compose up
    ```
    This command will build the Docker images for both the frontend and backend services and start them.

3.  **Access the application:**
    Once the containers are up and running, you can access the web interface in your browser at:
    [http://localhost:8080](http://localhost:8080)

## Project Structure

-   `backend/`: Contains the Python Flask application that serves the Excel data via a REST API. It reads `.xlsx` files from the `backend/excels` directory.
-   `frontend/`: A React application that provides the user interface for displaying the data.
-   `docker-compose.yml`: Defines the services, networks, and volumes for the Docker application.

## Development

If you want to run the services locally without Docker, you will need to set up each part of the stack separately.

### Backend (Python)

1.  Navigate to the backend directory:
    ```sh
    cd backend
    ```
2.  Create a virtual environment and install dependencies:
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```
3.  Run the Flask application:
    ```sh
    flask run
    ```
    The backend API will be available at `http://localhost:5000`.

### Frontend (React)

1.  Navigate to the frontend directory:
    ```sh
    cd frontend
    ```
2.  Install dependencies:
    ```sh
    npm install
    ```
3.  Start the development server:
    ```sh
    npm run dev
    ```
    The frontend will be available at `http://localhost:5173` and will proxy API requests to the backend.
